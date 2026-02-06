"""
Business logic for graph operations.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from db.reader import KnowledgeGraphReader
from paper_retrieval.research_paper import ResearchPaper
from relevance_scoring.relevance_scorer import CitationEdge, RelevanceEdge


@dataclass
class GraphFilters:
    min_year: Optional[int] = None
    max_year: Optional[int] = None
    min_citations: Optional[int] = None
    min_similarity: Optional[float] = None
    max_depth: int = 3


class GraphQueryService:
    """Business logic for graph queries with filtering and aggregation."""

    def __init__(self, reader: KnowledgeGraphReader):
        self.reader = reader

    def get_filtered_graph(
        self, paper_id: str, filters: GraphFilters
    ) -> Tuple[List[ResearchPaper], List[RelevanceEdge], List[CitationEdge]]:
        papers, relevance_edges, citation_edges = self.reader.read(paper_id)

        if not papers:
            return [], [], []

        filtered_papers = self._apply_paper_filters(papers, filters)
        filtered_ids = {p.id for p in filtered_papers}

        filtered_relevance = self._filter_by_paper_ids(relevance_edges, filtered_ids)

        filtered_citations = self._filter_by_paper_ids(citation_edges, filtered_ids)

        if filters.min_similarity is not None:
            filtered_relevance = self._filter_by_similarity(
                filtered_relevance, filters.min_similarity
            )

        return filtered_papers, filtered_relevance, filtered_citations

    def get_paper_with_scores(self, paper_id: str) -> Optional[Dict[str, Any]]:
        papers, relevance_edges, _ = self.reader.read(paper_id)

        if not papers:
            return None

        paper = next((p for p in papers if p.id == paper_id), None)
        if not paper:
            return None

        connected_edges = [
            e for e in relevance_edges if e.src_id == paper_id or e.dest_id == paper_id
        ]

        scores = self._compute_aggregate_scores(connected_edges)
        explanation = self._get_best_explanation(connected_edges)

        return {
            "paper": paper,
            "relevance_scores": scores,
            "explanation": explanation,
        }

    def _apply_paper_filters(
        self, papers: List[ResearchPaper], filters: GraphFilters
    ) -> List[ResearchPaper]:
        result = papers

        if filters.min_year is not None:
            result = [p for p in result if p.year >= filters.min_year]

        if filters.max_year is not None:
            result = [p for p in result if p.year <= filters.max_year]

        if filters.min_citations is not None:
            result = [p for p in result if p.citation_count >= filters.min_citations]

        return result

    def _filter_by_paper_ids(self, edges: List, valid_ids: set[str]) -> List:
        return [e for e in edges if e.src_id in valid_ids and e.dest_id in valid_ids]

    def _filter_by_similarity(
        self, edges: List[RelevanceEdge], min_similarity: float
    ) -> List[RelevanceEdge]:
        return [
            e
            for e in edges
            if e.relevance_score.llm_score
            and e.relevance_score.llm_score >= min_similarity
        ]

    def _compute_aggregate_scores(self, edges: List[RelevanceEdge]) -> Dict[str, float]:
        if not edges:
            return {
                "overall": 0.0,
                "semantic_similarity": 0.0,
                "llm_similarity": 0.0,
                "year_similarity": 0.0,
                "citation_score": 0.0,
            }

        scores = [e.relevance_score for e in edges]

        def safe_avg(values: List[Optional[float]]) -> float:
            valid = [v for v in values if v is not None]
            return sum(valid) / len(valid) if valid else 0.0

        return {
            "overall": safe_avg([s.llm_score for s in scores]),
            "semantic_similarity": safe_avg([s.semantic_similarity for s in scores]),
            "llm_similarity": safe_avg([s.llm_score for s in scores]),
            "year_similarity": safe_avg([s.year_similarity for s in scores]),
            "citation_score": safe_avg([s.citation_score for s in scores]),
        }

    def _get_best_explanation(self, edges: List[RelevanceEdge]) -> Optional[str]:
        if not edges:
            return None

        best = max(edges, key=lambda e: e.relevance_score.llm_score or 0.0)
        return best.llm_explanation
