"""
LLM-based relevance scorer for computing semantic similarity and generating explanations.

Supports multiple LLM providers:
- OpenAI (GPT-3.5, GPT-4, etc.)
- Anthropic (Claude)
- Open-source models via HuggingFace Transformers
"""

import os
import json
from typing import Optional, Dict, Any
from paper_retrieval import ResearchPaper


class LLMScorer:
    """
    LLM-based scorer that can compute relevance scores and generate explanations.
    """
    
    def __init__(
        self,
        provider: str = "openai",
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        use_explanations: bool = True
    ):
        """
        Initialize LLM scorer.
        
        Args:
            provider: LLM provider ("openai", "anthropic", or "huggingface")
            model: Model name (e.g., "gpt-4", "claude-3-opus", "meta-llama/Llama-2-7b-chat-hf")
            api_key: API key for the provider (or use environment variable)
            use_explanations: Whether to generate explanations (slower but more informative)
        """
        self.provider = provider.lower()
        self.use_explanations = use_explanations
        
        # Set default models
        if model is None:
            if self.provider == "openai":
                self.model = "gpt-4o-mini"  # Cost-effective default
            elif self.provider == "anthropic":
                self.model = "claude-3-haiku-20240307"  # Fast and cost-effective
            elif self.provider == "huggingface":
                self.model = "meta-llama/Llama-2-7b-chat-hf"
            else:
                raise ValueError(f"Unknown provider: {provider}")
        else:
            self.model = model
        
        # Initialize provider-specific client
        self.client = self._initialize_client(api_key)
    
    def _initialize_client(self, api_key: Optional[str]):
        """Initialize the appropriate LLM client."""
        if self.provider == "openai":
            try:
                import openai
                api_key = api_key or os.getenv("OPENAI_API_KEY")
                if not api_key:
                    raise ValueError("OpenAI API key required. Set OPENAI_API_KEY environment variable or pass api_key parameter.")
                return openai.OpenAI(api_key=api_key)
            except ImportError:
                raise ImportError("OpenAI package required. Install with: pip install openai")
        
        elif self.provider == "anthropic":
            try:
                import anthropic
                api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
                if not api_key:
                    raise ValueError("Anthropic API key required. Set ANTHROPIC_API_KEY environment variable or pass api_key parameter.")
                return anthropic.Anthropic(api_key=api_key)
            except ImportError:
                raise ImportError("Anthropic package required. Install with: pip install anthropic")
        
        elif self.provider == "huggingface":
            try:
                from transformers import AutoTokenizer, AutoModelForCausalLM
                import torch
                
                print(f"Loading HuggingFace model: {self.model}")
                print("(This may take a few minutes and requires significant memory)")
                
                tokenizer = AutoTokenizer.from_pretrained(self.model)
                model = AutoModelForCausalLM.from_pretrained(
                    self.model,
                    torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                    device_map="auto" if torch.cuda.is_available() else None
                )
                
                return {
                    "tokenizer": tokenizer,
                    "model": model,
                    "device": "cuda" if torch.cuda.is_available() else "cpu"
                }
            except ImportError:
                raise ImportError("Transformers package required. Install with: pip install transformers")
        
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
    
    def _get_paper_summary(self, paper: ResearchPaper) -> str:
        """Extract a concise summary of a paper for LLM processing."""
        authors_str = ", ".join([a.get("name", "") for a in paper.authors[:3]])
        if len(paper.authors) > 3:
            authors_str += " et al."
        
        summary = f"Title: {paper.title}\n"
        if authors_str:
            summary += f"Authors: {authors_str}\n"
        if paper.year:
            summary += f"Year: {paper.year}\n"
        if paper.abstract:
            # Truncate abstract if too long
            abstract = paper.abstract[:1000] if len(paper.abstract) > 1000 else paper.abstract
            summary += f"Abstract: {abstract}\n"
        if paper.citation_count is not None:
            summary += f"Citations: {paper.citation_count}\n"
        
        return summary
    
    def _create_prompt(self, root_paper: ResearchPaper, target_paper: ResearchPaper) -> str:
        """Create a prompt for the LLM to score relevance."""
        root_summary = self._get_paper_summary(root_paper)
        target_summary = self._get_paper_summary(target_paper)
        
        if self.use_explanations:
            # Use the tested prompt format: 1-10 scale with brief paragraph explanation
            prompt = f"""Compare the following papers by providing a score from 1 to 10 on how similar they are and also provide a brief 1 paragraph explanation of how they are similar and different. Format the output so that the first line is just the similarity score and then on a new line output the explanation and do not say anything else.

PAPER 1:
{root_summary}

PAPER 2:
{target_summary}"""
        else:
            # Simplified version without explanations
            prompt = f"""Compare the following papers by providing a score from 1 to 10 on how similar they are. Output only the score as a number.

PAPER 1:
{root_summary}

PAPER 2:
{target_summary}"""
        
        return prompt
    
    def _call_openai(self, prompt: str) -> Dict[str, Any]:
        """Call OpenAI API."""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a research paper analysis expert. Provide clear, concise comparisons."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,  # Lower temperature for more consistent scoring
        )
        
        content = response.choices[0].message.content.strip()
        
        if self.use_explanations:
            # Parse format: first line is score (e.g., "8.5 / 10" or "7/10"), then explanation
            import re
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
            
            return {
                "relevance_score": max(0.0, min(1.0, score)),  # Clamp to [0, 1]
                "explanation": explanation
            }
        else:
            # Just extract score
            import re
            score_match = re.search(r'(\d+(?:\.\d+)?)\s*/\s*10', content)
            if score_match:
                score = float(score_match.group(1)) / 10.0
            else:
                num_match = re.search(r'(\d+(?:\.\d+)?)', content)
                if num_match:
                    raw_score = float(num_match.group(1))
                    score = raw_score / 10.0 if raw_score > 1 else raw_score
                else:
                    score = 0.5
            
            return {"relevance_score": max(0.0, min(1.0, score))}
    
    def _call_anthropic(self, prompt: str) -> Dict[str, Any]:
        """Call Anthropic API."""
        response = self.client.messages.create(
            model=self.model,
            max_tokens=500,
            temperature=0.3,
            system="You are a research paper analysis expert. Provide clear, concise comparisons.",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        content = response.content[0].text.strip()
        
        if self.use_explanations:
            # Parse format: first line is score, then explanation
            import re
            lines = content.split('\n', 1)
            
            # Extract score from first line
            score_match = re.search(r'(\d+(?:\.\d+)?)\s*/\s*10', lines[0])
            if score_match:
                score = float(score_match.group(1)) / 10.0
            else:
                num_match = re.search(r'(\d+(?:\.\d+)?)', lines[0])
                if num_match:
                    raw_score = float(num_match.group(1))
                    score = raw_score / 10.0 if raw_score > 1 else raw_score
                else:
                    score = 0.5
            
            explanation = lines[1].strip() if len(lines) > 1 else ""
            
            return {
                "relevance_score": max(0.0, min(1.0, score)),
                "explanation": explanation
            }
        else:
            import re
            score_match = re.search(r'(\d+(?:\.\d+)?)\s*/\s*10', content)
            if score_match:
                score = float(score_match.group(1)) / 10.0
            else:
                num_match = re.search(r'(\d+(?:\.\d+)?)', content)
                if num_match:
                    raw_score = float(num_match.group(1))
                    score = raw_score / 10.0 if raw_score > 1 else raw_score
                else:
                    score = 0.5
            
            return {"relevance_score": max(0.0, min(1.0, score))}
    
    def _call_huggingface(self, prompt: str) -> Dict[str, Any]:
        """Call HuggingFace model."""
        tokenizer = self.client["tokenizer"]
        model = self.client["model"]
        device = self.client["device"]
        
        # Format prompt for chat model
        if "llama" in self.model.lower() or "chat" in self.model.lower():
            formatted_prompt = f"<s>[INST] {prompt} [/INST]"
        else:
            formatted_prompt = prompt
        
        inputs = tokenizer(formatted_prompt, return_tensors="pt", truncation=True, max_length=2048)
        inputs = {k: v.to(device) for k, v in inputs.items()}
        
        with tokenizer.as_target_tokenizer():
            outputs = model.generate(
                **inputs,
                max_new_tokens=200,
                temperature=0.3,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id
            )
        
        response_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        if self.use_explanations:
            # Parse format: first line is score, then explanation
            import re
            lines = response_text.split('\n', 1)
            
            score_match = re.search(r'(\d+(?:\.\d+)?)\s*/\s*10', lines[0])
            if score_match:
                score = float(score_match.group(1)) / 10.0
            else:
                num_match = re.search(r'(\d+(?:\.\d+)?)', lines[0])
                if num_match:
                    raw_score = float(num_match.group(1))
                    score = raw_score / 10.0 if raw_score > 1 else raw_score
                else:
                    score = 0.5
            
            explanation = lines[1].strip() if len(lines) > 1 else "Could not parse LLM response"
            
            return {
                "relevance_score": max(0.0, min(1.0, score)),
                "explanation": explanation
            }
        else:
            import re
            score_match = re.search(r'(\d+(?:\.\d+)?)\s*/\s*10', response_text)
            if score_match:
                score = float(score_match.group(1)) / 10.0
            else:
                num_match = re.search(r'(\d+(?:\.\d+)?)', response_text)
                if num_match:
                    raw_score = float(num_match.group(1))
                    score = raw_score / 10.0 if raw_score > 1 else raw_score
                else:
                    score = 0.5
            
            return {"relevance_score": max(0.0, min(1.0, score))}
    
    def compute_score(
        self,
        root_paper: ResearchPaper,
        target_paper: ResearchPaper
    ) -> Dict[str, Any]:
        """
        Compute relevance score and explanation using LLM.
        
        Returns:
            Dictionary with:
            - "relevance_score": float (0.0 to 1.0)
            - "explanation": str (optional, if use_explanations=True)
        """
        prompt = self._create_prompt(root_paper, target_paper)
        
        try:
            if self.provider == "openai":
                result = self._call_openai(prompt)
            elif self.provider == "anthropic":
                result = self._call_anthropic(prompt)
            elif self.provider == "huggingface":
                result = self._call_huggingface(prompt)
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")
            
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

