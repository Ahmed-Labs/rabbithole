"""
LLM-based relevance scorer using OpenAI GPT-5-nano.

Simplified to only support OpenAI GPT-5-nano for computing semantic similarity 
and generating explanations.
"""

import os
import re
from typing import Dict, Any, Optional
from paper_retrieval import ResearchPaper


class LLMScorer:
    """
    LLM-based scorer using OpenAI GPT-5-nano.
    Computes relevance scores and generates explanations.
    """
    
    def __init__(
        self,
        model: str = "gpt-5-nano",
        api_key: Optional[str] = None,
        use_explanations: bool = True
    ):
        """
        Initialize LLM scorer.
        
        Args:
            model: OpenAI model name (default: "gpt-5-nano")
            api_key: OpenAI API key (or use OPENAI_API_KEY environment variable)
            use_explanations: Whether to generate explanations (default: True)
        """
        self.model = model
        self.use_explanations = use_explanations
        
        # Initialize OpenAI client
        try:
            import openai
            api_key = api_key or os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OpenAI API key required. Set OPENAI_API_KEY environment variable or pass api_key parameter.")
            self.client = openai.OpenAI(api_key=api_key)
        except ImportError:
            raise ImportError("OpenAI package required. Install with: pip install openai")
    
    def _get_paper_summary(self, paper: ResearchPaper) -> str:
        """
        Extract paper summary for LLM processing.
        Uses the same text format as SPECTER2 embeddings: title + abstract.
        The text is truncated to match SPECTER2's 512 token limit (~2048 characters).
        """
        # Use the same format as SPECTER2: title + abstract (via paper.meta property)
        # SPECTER2 uses max_length=512 tokens, which is approximately 2048 characters
        # (assuming ~4 characters per token, as used in chunk_text_for_embedding)
        meta_text = paper.meta  # This is f"{paper.title} {paper.abstract}"
        
        # Truncate to match SPECTER2's effective limit (~2048 chars for 512 tokens)
        # This ensures LLM sees the same text that SPECTER2 uses for embeddings
        max_chars = 2048  # ~512 tokens * 4 chars/token
        if len(meta_text) > max_chars:
            meta_text = meta_text[:max_chars]
        
        return meta_text
    
    def _create_prompt(self, root_paper: ResearchPaper, target_paper: ResearchPaper) -> str:
        """Create a prompt for the LLM to score relevance."""
        root_summary = self._get_paper_summary(root_paper)
        target_summary = self._get_paper_summary(target_paper)
        
        # Single prompt format: 1-10 scale with brief paragraph explanation
        prompt = f"""Compare the following papers by providing a score from 1 to 10 on how similar they are and also provide a brief 1 paragraph explanation of how they are similar and different. Format the output so that the first line is just the similarity score and then on a new line output the explanation and do not say anything else.

PAPER 1:
{root_summary}

PAPER 2:
{target_summary}"""
        
        return prompt
    
    def _parse_response(self, content: str) -> Dict[str, Any]:
        """Parse LLM response to extract score and explanation."""
        content = content.strip()
        
        # Parse format: first line is score (e.g., "8.5 / 10" or "7/10"), then explanation
        lines = content.split('\n', 1)
        
        # Extract score from first line
        score_match = re.search(r'(\d+(?:\.\d+)?)\s*/\s*10', lines[0])
        if score_match:
            score = float(score_match.group(1)) / 10.0  # Convert 1-10 to 0-1 scale
        else:
            # Try to find just a number
            num_match = re.search(r'(\d+(?:\.\d+)?)', lines[0])
            if num_match:
                raw_score = float(num_match.group(1))
                score = raw_score / 10.0 if raw_score > 1 else raw_score
            else:
                score = 0.5  # Default fallback
        
        # Get explanation (everything after first line)
        explanation = lines[1].strip() if len(lines) > 1 else ""
        
        result = {
            "relevance_score": max(0.0, min(1.0, score)),  # Clamp to [0, 1]
            "explanation": explanation
        }
        
        # Only include explanation in result if use_explanations is True (for backward compatibility)
        if not self.use_explanations:
            result.pop("explanation", None)
        
        return result
    
    def compute_score(
        self,
        root_paper: ResearchPaper,
        target_paper: ResearchPaper
    ) -> Dict[str, Any]:
        """
        Compute relevance score and explanation using OpenAI GPT-5-nano.
        
        Returns:
            Dictionary with:
            - "relevance_score": float (0.0 to 1.0)
            - "explanation": str (optional, if use_explanations=True)
        """
        prompt = self._create_prompt(root_paper, target_paper)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a research paper analysis expert. Provide clear, concise comparisons."},
                    {"role": "user", "content": prompt}
                ],
                # Note: GPT-5-nano only supports default temperature (1), so we don't set it
            )
            
            content = response.choices[0].message.content.strip()
            result = self._parse_response(content)
            
            # Validate and normalize score
            score = float(result.get("relevance_score", 0.5))
            score = max(0.0, min(1.0, score))  # Clamp to [0, 1]
            
            return {
                "relevance_score": score,
                "explanation": result.get("explanation") if self.use_explanations else None
            }
        
        except Exception as e:
            print(f"Warning: LLM scoring failed: {e}. Using fallback score.")
            return {
                "relevance_score": 0.5,
                "explanation": f"LLM scoring failed: {str(e)}"
            }
