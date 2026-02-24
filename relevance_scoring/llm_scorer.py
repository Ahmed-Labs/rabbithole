import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence

from paper_retrieval import ResearchPaper
from paper_retrieval import session as r
from relevance_scoring.constants import *
from relevance_scoring.relevance_scorer import RelevanceEdge, RelevanceScore


@dataclass
class LLMResult:
    relevance_score: float
    explanation: str


class LLMScorer:
    def __init__(self, api_key: Optional[str] = None):
        resolved_key = api_key or os.getenv("OPENAI_API_KEY")
        if not resolved_key:
            raise ValueError(
                "OpenAI API key required. Set OPENAI_API_KEY environment variable or pass api_key parameter."
            )
        self.api_key = resolved_key

    def _clip(self, s: Optional[str], max_chars: int) -> str:
        return (s or "")[:max_chars]

    def _create_batch_prompt(
        self, root_paper: ResearchPaper, targets: Sequence[ResearchPaper]
    ) -> str:
        root_text = self._clip(root_paper.meta, 2500)
        n = len(targets)

        items: List[Dict[str, Any]] = []
        for i, p in enumerate(targets):
            items.append(
                {
                    "idx": i,
                    "paper_id": getattr(p, "id", None),
                    "title": getattr(p, "title", None),
                    "meta": self._clip(p.meta, 1200),
                }
            )

        return (
            "You will compare one root paper to multiple candidate papers.\n\n"
            f"You MUST return exactly {n} results (idx 0 to {n-1}).\n"
            "Return ONLY valid JSON. No markdown. No commentary.\n\n"
            "Exact required format:\n"
            '{"results":[{"idx":0,"score_0_100":0,"explanation":"..."}]}\n\n'
            "Hard rules:\n"
            "- Each candidate must produce exactly one result object.\n"
            "- explanation MUST be non-empty.\n"
            "- explanation must be 1-2 sentences.\n"
            "- Even if score_0_100 is 0, explanation must state why they are unrelated.\n\n"
            "Root paper:\n"
            f"{root_text}\n\n"
            "Candidate papers (JSON array):\n"
            f"{json.dumps(items, ensure_ascii=False)}"
        )

    def _call_llm_json(self, prompt: str) -> Dict[str, Any]:
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
                    "content": "You are a research paper analysis expert. Output JSON only.",
                },
                {"role": "user", "content": prompt},
            ],
            "response_format": {"type": "json_object"},
        }

        resp = r.post(url, headers=headers, json=payload, timeout=120)

        if resp.status_code != 200:
            resp.raise_for_status()

        data = resp.json()
        content = data["choices"][0]["message"]["content"]
        return json.loads(content)

    def _parse_batch(self, data: Dict[str, Any], n: int) -> List[LLMResult]:
        out: List[LLMResult] = [LLMResult(0.0, "") for _ in range(n)]
        results = data.get("results", [])

        if not isinstance(results, list):
            print("Unexpected results:", data)
            return out

        for item in results:
            try:
                idx = int(item.get("idx"))
                raw_score = item.get("score_0_100", 0)
                score_0_100 = int(float(raw_score))
                score_0_100 = max(0, min(100, score_0_100))
                score = score_0_100 / 100.0

                explanation = str(item.get("explanation", "")).strip()

                if 0 <= idx < n:
                    out[idx] = LLMResult(score, explanation)

            except Exception as e:
                print("Bad LLM item:", item, "err:", e)

        return out

    def compute_scores_batched(
        self,
        root_paper: ResearchPaper,
        target_papers: List[ResearchPaper],
        batch_size: int = LLM_BATCH_SIZE,
    ) -> List[RelevanceEdge]:
        edges: List[RelevanceEdge] = []

        for i in range(0, len(target_papers), batch_size):
            chunk = list(target_papers[i : i + batch_size])
            prompt = self._create_batch_prompt(root_paper, chunk)

            try:
                data = self._call_llm_json(prompt)
                parsed = self._parse_batch(data, n=len(chunk))

                for target, result in zip(chunk, parsed):
                    score_obj = RelevanceScore(
                        llm_score=result.relevance_score,
                        llm_explanation=result.explanation,
                    )
                    edge = RelevanceEdge(
                        src_id=root_paper.id,
                        dest_id=target.id,
                        relevance_score=score_obj,
                    )
                    edges.append(edge)

            except Exception as e:
                print(f"LLM scoring failed: {e}")

        return edges
