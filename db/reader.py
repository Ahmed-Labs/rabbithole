from typing import Any, Dict, Tuple

from db.client import Neo4jClient
from paper_retrieval.research_paper import ResearchPaper
from relevance_scoring.relevance_scorer import (
    CitationEdge,
    RelevanceEdge,
    RelevanceScore,
)

Props = Dict[str, Any]


class KnowledgeGraphReader:
    def __init__(self, client: Neo4jClient):
        self.client = client

    def _parse_relevance_edge(self, edge: dict) -> list[RelevanceEdge]:
        relevance_score_data: Props = edge.get("props", {})
        score = RelevanceScore(
            semantic_similarity=relevance_score_data.get("semantic_similarity"),
            year_similarity=relevance_score_data.get("year_similarity"),
            citation_score=relevance_score_data.get("citation_score"),
            llm_score=relevance_score_data.get("llm_score"),
        )

        return RelevanceEdge(
            src_id=edge.get("src"),
            dest_id=edge.get("dest"),
            relevance_score=score,
            llm_explanation=edge.get("llm_explanation"),
        )

    def _parse_citation_edge(self, edge: dict) -> list[CitationEdge]:
        return CitationEdge(
            src_id=edge.get("src"),
            dest_id=edge.get("dest"),
        )

    def read(
        self, paper_id: str
    ) -> Tuple[list[ResearchPaper], list[RelevanceEdge], list[CitationEdge]]:
        cypher = """
        MATCH (root:Paper {id: $id})

        MATCH p1 = (root)-[:CITES*1..3]-(c)
        MATCH p2 = (root)-[:RELEVANT_TO]-(r)

        WITH collect(p1) + collect(p2) AS ps
        RETURN
          [n IN apoc.coll.toSet(apoc.coll.flatten([p IN ps | nodes(p)]))
            | n {.*, id: n.id }
          ] AS nodes,
          [e IN apoc.coll.toSet(apoc.coll.flatten([p IN ps | relationships(p)]))
            | {
                type: type(e),
                src: startNode(e).id,
                dest: endNode(e).id,
                props: properties(e)
              }
          ] AS edges
        """

        rows = self.client.run_read(cypher, {"id": paper_id})
        if not rows:
            return None

        data = rows[0]
        nodes: list[dict] = data.get("nodes", [])
        edges: list[dict] = data.get("edges", [])

        papers = [ResearchPaper.from_props(p) for p in nodes]
        relevance_edges, citation_edges = [], []

        for edge in edges:
            edge_type = edge.get("type")
            if edge_type == "RELEVANT_TO":
                relevance_edges.append(self._parse_relevance_edge(edge))
            elif edge_type == "CITES":
                citation_edges.append(self._parse_citation_edge(edge))

        return papers, relevance_edges, citation_edges
