from dataclasses import dataclass
from typing import List, Optional, Set, Tuple

import numpy as np

from paper_retrieval import ResearchPaper
from relevance_scoring.constants import *
from relevance_scoring.embedder import Embedder
from relevance_scoring.llm_scorer import LLMScorer


@dataclass
class RelevanceScore:
    semantic_similarity: float
    year_similarity: float
    citation_score: float
    llm_score: Optional[float] = None

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


@dataclass(frozen=True)
class RelevanceEdge:
    src_id: str
    dest_id: str
    relevance_score: RelevanceScore
    llm_explanation: Optional[str] = None


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
        self.llm_scorer = LLMScorer()

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

    def _compute_semantic_similarity(
        self, root_paper: ResearchPaper, target_paper: ResearchPaper
    ) -> float:
        root_embs = self.embedder.lazy_embed_chunks(
            lambda: root_paper.full_text_chunks, cache_key=root_paper.id + ":text"
        )
        target_embs = self.embedder.lazy_embed_chunks(
            lambda: target_paper.full_text_chunks, cache_key=target_paper.id + ":text"
        )

        full_text_sim = self.embedder.compute_similarity(root_embs, target_embs)

        root_meta_emb = self.embedder.embed(root_paper.meta, root_paper.id + ":meta")
        target_meta_emb = self.embedder.embed(
            target_paper.meta, target_paper.id + ":meta"
        )
        meta_sim = self.embedder.compute_similarity(root_meta_emb, target_meta_emb)
        return 0.8 * full_text_sim + 0.2 * meta_sim

    def compute_score(
        self, root_paper: ResearchPaper, target_paper: ResearchPaper
    ) -> tuple[Optional[RelevanceScore], Optional[str]]:
        relevance_score = RelevanceScore(
            semantic_similarity=self._compute_semantic_similarity(
                root_paper, target_paper
            ),
            year_similarity=self._compute_year_similarity(
                root_paper.year, target_paper.year
            ),
            citation_score=self._get_citation_score(target_paper),
        )

        if relevance_score.combined >= LLM_SCORING_THRESHOLD:
            llm_score, llm_description = self.llm_scorer.compute_score(
                root_paper, target_paper
            )
            relevance_score.llm_score = llm_score
            return relevance_score, llm_description

        return relevance_score, None

    def compute_relevance_edges(
        self,
        root_paper: ResearchPaper,
    ) -> List[RelevanceEdge]:
        """
        Recursively score all papers in reference tree against root paper.
        """
        edges: List[RelevanceEdge] = []

        visited: Set[str] = set()
        scored: Set[str] = set()

        def dfs(paper: ResearchPaper):
            if paper.id in visited:
                return
            visited.add(paper.id)

            adjacent_papers = paper.references + paper.citations

            for adj in adjacent_papers:
                if adj.id not in scored:
                    score, llm_description = self.compute_score(root_paper, adj)
                    if score:
                        edges.append(
                            RelevanceEdge(
                                src_id=root_paper.id,
                                dest_id=adj.id,
                                relevance_score=score,
                                llm_explanation=llm_description,
                            )
                        )
                    scored.add(adj.id)

                dfs(adj)

        dfs(root_paper)
        return edges


def compute_relevance_scores(root_paper) -> Tuple[List[RelevanceEdge]]:
    scorer = RelevanceScorer()

    print("\nComputing relevance scores...")
    edges = scorer.compute_relevance_edges(root_paper)

    edges.sort(key=lambda x: x.relevance_score.combined, reverse=True)

    return edges
