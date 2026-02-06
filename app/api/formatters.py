"""
Formatters for API responses.
"""

from typing import Any, Dict, List, Optional

from paper_retrieval.research_paper import ResearchPaper
from relevance_scoring.relevance_scorer import CitationEdge, RelevanceEdge


class ReactFlowFormatter:
    """Transform domain objects to React Flow format."""

    @staticmethod
    def format_graph(
        papers: List[ResearchPaper],
        relevance_edges: List[RelevanceEdge],
        citation_edges: List[CitationEdge],
        root_id: str,
    ) -> Dict[str, Any]:
        paper_scores = ReactFlowFormatter._calc_paper_scores(papers, relevance_edges)

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
        return {
            **paper.to_props(),
            "relevance_score": scores,
            "relevance_explanation": explanation,
        }

    @staticmethod
    def _calc_paper_scores(
        papers: List[ResearchPaper], relevance_edges: List[RelevanceEdge]
    ) -> Dict[str, float]:
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
        return {
            "id": paper.id,
            "type": "paperNode",
            "data": {
                **paper.to_props(),
                "max_relevance_score": max_relevance,
                "is_root": is_root,
            },
            "position": {"x": 0, "y": 0},
        }

    @staticmethod
    def _build_relevance_edge(edge: RelevanceEdge) -> Dict[str, Any]:
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
            },
        }

    @staticmethod
    def _build_citation_edge(edge: CitationEdge) -> Dict[str, Any]:
        return {
            "id": f"cite-{edge.src_id}-{edge.dest_id}",
            "source": edge.src_id,
            "target": edge.dest_id,
            "type": "citationEdge",
            "data": {},
        }
