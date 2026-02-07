from typing import Any, Dict, List, Optional

from paper_retrieval.research_paper import ResearchPaper
from relevance_scoring.relevance_scorer import CitationEdge, RelevanceEdge


class ReactFlowFormatter:
    """Transform domain objects to React Flow format."""

    @staticmethod
    def format_graph(
        papers: dict[str, ResearchPaper],
        relevance_edges: List[RelevanceEdge],
        citation_edges: List[CitationEdge],
        root_id: str,
    ) -> Dict[str, Any]:
        paper_scores = {
            (e.dest_id if e.src_id == root_id else e.src_id): e.relevance_score.combined
            for e in relevance_edges
        }

        nodes = [
            ReactFlowFormatter._build_node(
                p, paper_scores.get(p.id, 0.0), p.id == root_id
            )
            for p in papers.values()
        ]

        edges = [ReactFlowFormatter._build_citation_edge(e) for e in citation_edges]

        return {
            "nodes": nodes,
            "edges": edges,
            "root_id": root_id,
        }

    @staticmethod
    def _build_node(
        paper: ResearchPaper, relevance_score: float, is_root: bool
    ) -> Dict[str, Any]:
        return {
            "id": paper.id,
            "type": "paperNode",
            "data": {
                **paper.to_props(),
                "relevance_score": relevance_score,
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
            "data": edge.to_props(),
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
