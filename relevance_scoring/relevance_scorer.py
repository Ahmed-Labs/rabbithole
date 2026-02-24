from dataclasses import dataclass
from typing import Optional

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from paper_retrieval import ResearchPaper
from relevance_scoring.constants import *
from relevance_scoring.embedder import Embedder


@dataclass
class RelevanceScore:
    semantic_similarity: float = 0.0
    year_similarity: float = 0.0
    citation_score: float = 0.0
    llm_score: Optional[float] = None
    llm_explanation: Optional[str] = None

    @property
    def combined(self):
        existing_score = (
            SEMANTIC_SIMILARITY_WEIGHT * self.semantic_similarity
            + YEAR_SIMILARITY_WEIGHT * self.year_similarity
            + CITATION_SCORE_WEIGHT * self.citation_score
        )

        if self.llm_score is not None:
            return (
                1 - LLM_SCORE_WEIGHT
            ) * existing_score + LLM_SCORE_WEIGHT * self.llm_score

        return existing_score

    def to_props(self):
        props = {
            "semantic_similarity": self.semantic_similarity,
            "year_similarity": self.year_similarity,
            "citation_score": self.citation_score,
        }

        if self.llm_score is not None:
            props["llm_score"] = self.llm_score
            props["llm_explanation"] = self.llm_explanation

        return props


@dataclass(frozen=True)
class RelevanceEdge:
    src_id: str
    dest_id: str
    relevance_score: RelevanceScore


@dataclass(frozen=True)
class CitationEdge:
    src_id: str
    dest_id: str


class RelevanceScorer:
    """
    Compute semantic relevance scores between papers.

    Relevance scores consist of:
    - Semantic similarity
    - Publication year proximity
    - Citation score
    - LLM relevance score
    """

    def __init__(self):
        self.embedder = Embedder()

    def _compute_year_similarity(
        self, year1: Optional[int], year2: Optional[int]
    ) -> float:
        """
        Compute year proximity score (ConnectedPapers prioritizes similar generations).
        Returns 1.0 for same year, decaying with distance.
        """
        if year1 is None or year2 is None:
            return 0.5  # neutral if year unknown

        year_diff = abs(year1 - year2)

        # Decay function: 1.0 at 0 years, 0.5 at 5 years, ~0.2 at 10 years
        return np.exp(-year_diff / 5.0)

    def _get_citation_score(self, paper) -> float:
        """
        Normalize citation count to 0-1 range.
        More citations = potentially more important paper.
        """
        if not hasattr(paper, "citation_count") or paper.citation_count is None:
            return 0.5

        # Log scale normalization (most papers have 0-1000 citations)
        # Score: 0.5 at 100 citations, ~0.7 at 1000 citations
        return min(0.5 + np.log10(paper.citation_count + 1) / 6, 1.0)

    def _cosine_similarity(
        self, embedding1: np.ndarray, embedding2: np.ndarray
    ) -> float:
        return float(
            cosine_similarity(
                embedding1.reshape(1, -1),
                embedding2.reshape(1, -1),
            )[
                0
            ][0]
        )

    def _compute_semantic_similarity(
        self,
        root_paper: ResearchPaper,
        target_paper: ResearchPaper,
    ) -> float:
        # Full text similarity
        root_text = self.embedder.store.get(root_paper.id + TEXT_TAG)
        target_text = self.embedder.store.get(target_paper.id + TEXT_TAG)

        # Title + abstract embeddings
        root_meta = self.embedder.store.get(root_paper.id + META_TAG)
        target_meta = self.embedder.store.get(target_paper.id + META_TAG)

        if any(e is None for e in (root_text, target_text, root_meta, target_meta)):
            return 0.0

        text_sim = self._cosine_similarity(root_text, target_text)
        meta_sim = self._cosine_similarity(root_meta, target_meta)

        return TEXT_SEMANTIC_WEIGHT * text_sim + META_SEMANTIC_WEIGHT * meta_sim

    def compute_relevance_score(
        self, root_paper: ResearchPaper, target_paper: ResearchPaper
    ) -> RelevanceScore:
        return RelevanceScore(
            semantic_similarity=self._compute_semantic_similarity(
                root_paper, target_paper
            ),
            year_similarity=self._compute_year_similarity(
                root_paper.year, target_paper.year
            ),
            citation_score=self._get_citation_score(target_paper),
        )
