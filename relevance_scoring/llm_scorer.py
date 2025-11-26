import os
import re
from typing import Dict, Any
from paper_retrieval import ResearchPaper, session as r
from dotenv import load_dotenv

GPT_MODEL = "gpt-5-nano"


class LLMScorer:
    def __init__(self):
        load_dotenv()

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OpenAI API key required. Set OPENAI_API_KEY environment variable or pass api_key parameter."
            )
        self.api_key = api_key

    def _create_prompt(
        self, root_paper: ResearchPaper, target_paper: ResearchPaper
    ) -> str:
        """Create a prompt for the LLM to score relevance."""
        root_text = root_paper.meta
        taget_text = target_paper.meta

        prompt = f"""Compare the following papers by providing a precise score from 0 to 100 indicating how relevant they are to each other and also provide a brief 1 paragraph explanation of how they are similar or different. Format the output so that the first line is just the similarity score and then on a new line output the explanation and do not say anything else. 
        Root paper:
        {root_text}

        Current paper:
        {taget_text}"""

        return prompt

    def _parse_response(self, content: str) -> Dict[str, Any]:
        """Parse LLM response to extract score and explanation."""
        content = content.strip()

        # Parse format: first line is score (e.g., "8.5 / 10" or "7/10"), then explanation
        lines = content.split("\n", 1)

        # Extract score from first line
        score_match = re.search(r"(\d+(?:\.\d+)?)\s*/\s*10", lines[0])
        if score_match:
            score = float(score_match.group(1)) / 100.0  # Convert 1-10 to 0-1 scale
        else:
            # Try to find just a number
            num_match = re.search(r"(\d+(?:\.\d+)?)", lines[0])
            if num_match:
                raw_score = float(num_match.group(1))
                score = raw_score / 100.0
            else:
                score = 0.5

        # Get explanation (everything after first line)
        explanation = lines[1].strip() if len(lines) > 1 else ""

        result = {
            "relevance_score": max(0.0, min(1.0, score)),
            "explanation": explanation,
        }

        return result

    def compute_score(
        self, root_paper: ResearchPaper, target_paper: ResearchPaper
    ) -> tuple[float, str]:
        """
        Compute relevance score and explanation.

        Returns:
            Tuple with:
            - "relevance_score": float (0.0 to 1.0)
            - "explanation": str
        """
        prompt = self._create_prompt(root_paper, target_paper)

        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": GPT_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a research paper analysis expert. Provide clear, concise comparisons.",
                },
                {"role": "user", "content": prompt},
            ],
        }

        try:
            resp = r.post(url, headers=headers, json=payload, timeout=60)
            resp.raise_for_status()
            data = resp.json()

            content = data["choices"][0]["message"]["content"].strip()
            result = self._parse_response(content)

            # Validate and normalize score
            score = float(result.get("relevance_score", 0.5))
            score = max(0.0, min(1.0, score))  # Clamp to [0, 1]
            
            return (score, result.get("explanation", ""))
        
        except Exception as e:
            print(f"LLM scoring failed: {e}")
            return (-1, "")
