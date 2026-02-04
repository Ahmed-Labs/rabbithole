"""
Business logic layer for knowledge graph operations.

This module provides high-level services that use the low-level reader/writer
to accomplish business use cases like filtering, aggregating, and transforming
graph data.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from db.reader import KnowledgeGraphReader
from paper_retrieval.research_paper import ResearchPaper
from relevance_scoring.relevance_scorer import CitationEdge, RelevanceEdge


@dataclass
class GraphFilters:
    """Filter parameters for graph queries."""

    min_year: Optional[int] = None
    max_year: Optional[int] = None
    min_citations: Optional[int] = None
    min_similarity: Optional[float] = None
    include_citations: bool = True
    max_depth: int = 3


class GraphQueryService:
    """
    High-level graph query service.

    Uses KnowledgeGraphReader for data access, then applies business logic
    like filtering, aggregation, and transformations.
    """

    def __init__(self, reader: KnowledgeGraphReader):
        self.reader = reader

    def get_filtered_graph(
        self, paper_id: str, filters: GraphFilters
    ) -> Tuple[List[ResearchPaper], List[RelevanceEdge], List[CitationEdge]]:
        """
        Get graph data with filters applied.

        Args:
            paper_id: Root paper ID
            filters: Filter parameters

        Returns:
            Tuple of (filtered_papers, filtered_relevance_edges, filtered_citation_edges)
        """
        # Delegate to reader for data access
        papers, relevance_edges, citation_edges = self.reader.read(paper_id)

        if not papers:
            return [], [], []

        # Apply business logic (filtering)
        filtered_papers = self._apply_paper_filters(papers, filters)
        filtered_ids = {p.id for p in filtered_papers}

        filtered_relevance = self._apply_relevance_filters(
            relevance_edges, filtered_ids, filters
        )

        filtered_citations = self._apply_citation_filters(
            citation_edges, filtered_ids, filters
        )

        return filtered_papers, filtered_relevance, filtered_citations

    def get_paper_with_scores(self, paper_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed paper information with aggregated relevance scores.

        Args:
            paper_id: Paper ID to query

        Returns:
            Dictionary with paper details and computed scores
        """
        papers, relevance_edges, _ = self.reader.read(paper_id)

        if not papers:
            return None

        # Find target paper
        paper = next((p for p in papers if p.id == paper_id), None)
        if not paper:
            return None

        # Get edges connected to this paper
        connected_edges = [
            e for e in relevance_edges if e.src_id == paper_id or e.dest_id == paper_id
        ]

        # Apply business logic (aggregation)
        scores = self._compute_aggregate_scores(connected_edges)
        explanation = self._get_best_explanation(connected_edges)

        return {
            "paper": paper,
            "relevance_scores": scores,
            "explanation": explanation,
        }

    # ========================================================================
    # Private helper methods (business logic)
    # ========================================================================

    def _apply_paper_filters(
        self, papers: List[ResearchPaper], filters: GraphFilters
    ) -> List[ResearchPaper]:
        """Apply year and citation filters to papers."""
        result = papers

        if filters.min_year is not None:
            result = [p for p in result if p.year >= filters.min_year]

        if filters.max_year is not None:
            result = [p for p in result if p.year <= filters.max_year]

        if filters.min_citations is not None:
            result = [p for p in result if p.citation_count >= filters.min_citations]

        return result

    def _apply_relevance_filters(
        self, edges: List[RelevanceEdge], valid_ids: set[str], filters: GraphFilters
    ) -> List[RelevanceEdge]:
        """Filter relevance edges by paper IDs and similarity threshold."""
        # Filter by valid paper IDs
        result = [e for e in edges if e.src_id in valid_ids and e.dest_id in valid_ids]

        # Filter by minimum similarity
        if filters.min_similarity is not None:
            result = [
                e
                for e in result
                if e.relevance_score.llm_score
                and e.relevance_score.llm_score >= filters.min_similarity
            ]

        return result

    def _apply_citation_filters(
        self, edges: List[CitationEdge], valid_ids: set[str], filters: GraphFilters
    ) -> List[CitationEdge]:
        """Filter citation edges by paper IDs and inclusion flag."""
        if not filters.include_citations:
            return []

        return [e for e in edges if e.src_id in valid_ids and e.dest_id in valid_ids]

    def _compute_aggregate_scores(self, edges: List[RelevanceEdge]) -> Dict[str, float]:
        """Calculate average relevance scores from edges."""
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
            """Average non-None values."""
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
        """Get explanation from edge with highest LLM score."""
        if not edges:
            return None

        best = max(edges, key=lambda e: e.relevance_score.llm_score or 0.0)
        return best.llm_explanation


class ReactFlowFormatter:
    """
    Transform domain objects to React Flow format.

    This is presentation logic - how we format data for the frontend.
    Separated from business logic so it can change independently.
    """

    @staticmethod
    def format_graph(
        papers: List[ResearchPaper],
        relevance_edges: List[RelevanceEdge],
        citation_edges: List[CitationEdge],
        root_id: str,
    ) -> Dict[str, Any]:
        """
        Convert graph data to React Flow format.

        Args:
            papers: List of papers
            relevance_edges: List of relevance edges
            citation_edges: List of citation edges
            root_id: ID of root paper

        Returns:
            Dictionary with nodes and edges in React Flow format
        """
        # Calculate node colors (max relevance per paper)
        paper_scores = ReactFlowFormatter._calc_paper_scores(papers, relevance_edges)

        # Build nodes and edges
        nodes = [
            ReactFlowFormatter._build_node(
                p, paper_scores.get(p.id, 0.0), p.id == root_id
            )
            for p in papers
        ]

        edges = []
        edges.extend(
            ReactFlowFormatter._build_relevance_edge(e) for e in relevance_edges
        )
        edges.extend(ReactFlowFormatter._build_citation_edge(e) for e in citation_edges)

        return {
            "nodes": nodes,
            "edges": edges,
            "root_id": root_id,
        }

    @staticmethod
    def format_paper_details(
        paper: ResearchPaper, scores: Dict[str, float], explanation: Optional[str]
    ) -> Dict[str, Any]:
        """Format paper details for Inspector panel."""
        return {
            "id": paper.id,
            "title": paper.title,
            "authors": paper.authors,
            "year": paper.year,
            "citation_count": paper.citation_count,
            "abstract": paper.abstract,
            "url": paper.url,
            "pdf_url": paper.pdf_url,
            "relevance_score": scores,
            "relevance_explanation": explanation,
        }

    # ========================================================================
    # Private formatting helpers
    # ========================================================================

    @staticmethod
    def _calc_paper_scores(
        papers: List[ResearchPaper], relevance_edges: List[RelevanceEdge]
    ) -> Dict[str, float]:
        """Calculate max relevance score for each paper (for node coloring)."""
        scores = {}

        for paper in papers:
            connected = [
                e
                for e in relevance_edges
                if e.src_id == paper.id or e.dest_id == paper.id
            ]

            if connected:
                scores[paper.id] = max(
                    e.relevance_score.llm_score or 0.0 for e in connected
                )
            else:
                scores[paper.id] = 0.0

        return scores

    @staticmethod
    def _build_node(
        paper: ResearchPaper, max_relevance: float, is_root: bool
    ) -> Dict[str, Any]:
        """Build a single React Flow node."""
        # Truncate authors for display
        display_authors = paper.authors[:3] if len(paper.authors) > 3 else paper.authors

        return {
            "id": paper.id,
            "type": "paperNode",
            "data": {
                "title": paper.title,
                "authors": display_authors,
                "year": paper.year,
                "citation_count": paper.citation_count,
                "abstract": paper.abstract,
                "url": paper.url,
                "pdf_url": paper.pdf_url,
                "max_relevance_score": max_relevance,
                "is_root": is_root,
            },
            "position": {"x": 0, "y": 0},  # React Flow handles layout
        }

    @staticmethod
    def _build_relevance_edge(edge: RelevanceEdge) -> Dict[str, Any]:
        """Build a relevance edge for React Flow."""
        return {
            "id": f"rel-{edge.src_id}-{edge.dest_id}",
            "source": edge.src_id,
            "target": edge.dest_id,
            "type": "relevanceEdge",
            "data": {
                "semantic_similarity": edge.relevance_score.semantic_similarity,
                "year_similarity": edge.relevance_score.year_similarity,
                "citation_score": edge.relevance_score.citation_score,
                "llm_score": edge.relevance_score.llm_score,
                "llm_explanation": edge.llm_explanation,
                "edge_type": "relevance",
            },
            "animated": True,
            "style": {"stroke": "#888"},
        }

    @staticmethod
    def _build_citation_edge(edge: CitationEdge) -> Dict[str, Any]:
        """Build a citation edge for React Flow."""
        return {
            "id": f"cite-{edge.src_id}-{edge.dest_id}",
            "source": edge.src_id,
            "target": edge.dest_id,
            "type": "citationEdge",
            "data": {"edge_type": "citation"},
            "animated": False,
            "style": {"stroke": "#444", "strokeDasharray": "5,5"},
        }
