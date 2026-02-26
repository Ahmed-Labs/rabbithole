import json
from typing import Any, Dict, List, Optional

from paper_retrieval.research_paper import ResearchPaper
from relevance_scoring.relevance_scorer import (
    CitationEdge,
    RelevanceEdge,
    RelevanceScore,
)


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
            (e.dest_id if e.src_id == root_id else e.src_id): e.relevance_score
            for e in relevance_edges
        }

        nodes = [
            ReactFlowFormatter._build_node(
                p, paper_scores.get(p.id, RelevanceScore(0, 0, 0)), p.id == root_id
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
        paper: ResearchPaper, relevance_score: RelevanceScore, is_root: bool
    ) -> Dict[str, Any]:
        props = paper.to_props()
        props["authors"] = [
            json.loads(a) if isinstance(a, str) else a
            for a in (props.get("authors") or [])
        ]

        return {
            "id": paper.id,
            "type": "paperNode",
            "data": {
                **props,
                "relevance_score": relevance_score.combined,
                "llm_explanation": relevance_score.llm_explanation,
                "is_root": is_root,
            },
            "position": {"x": 0, "y": 0},
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
