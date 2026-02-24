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

    def _parse_relevance_edge(self, edge: dict) -> RelevanceEdge:
        relevance_score_data: Props = edge.get("props", {})
        score = RelevanceScore(
            semantic_similarity=relevance_score_data.get("semantic_similarity"),
            year_similarity=relevance_score_data.get("year_similarity"),
            citation_score=relevance_score_data.get("citation_score"),
            llm_score=relevance_score_data.get("llm_score", None),
            llm_explanation=relevance_score_data.get("llm_explanation", None),
        )

        return RelevanceEdge(
            src_id=edge.get("src"),
            dest_id=edge.get("dest"),
            relevance_score=score,
        )

    def _parse_citation_edge(self, edge: dict) -> CitationEdge:
        return CitationEdge(
            src_id=edge.get("src"),
            dest_id=edge.get("dest"),
        )

    def read(
        self, paper_id: str, cite_depth: int = 3
    ) -> Tuple[dict[str, ResearchPaper], list[RelevanceEdge], list[CitationEdge]]:
        cypher = f"""
        MATCH (root:Paper {{id: $id}})

        OPTIONAL MATCH p1 = (root)-[:CITES*1..{cite_depth}]-(c)
        OPTIONAL MATCH p2 = (root)-[:RELEVANT_TO]-(r)

        WITH
        [p IN collect(p1) WHERE p IS NOT NULL] +
        [p IN collect(p2) WHERE p IS NOT NULL] AS ps,
        root

        WITH
        apoc.coll.toSet(apoc.coll.flatten([p IN ps | relationships(p)])) AS rels,
        root

        WITH
        rels,
        apoc.coll.toSet(
            [root] +
            [e IN rels | startNode(e)] +
            [e IN rels | endNode(e)]
        ) AS ns

        RETURN
        [n IN ns | n {{.*, id: n.id }}] AS nodes,
        [e IN rels | {{
            type: type(e),
            src: startNode(e).id,
            dest: endNode(e).id,
            props: properties(e)
        }}] AS edges
        """

        rows = self.client.run_read(cypher, {"id": paper_id})
        if not rows:
            return None

        data = rows[0]
        nodes: list[dict] = data.get("nodes", [])
        edges: list[dict] = data.get("edges", [])

        papers = [ResearchPaper.from_props(p) for p in nodes]
        papers_by_id = {paper.id: paper for paper in papers}

        relevance_edges, citation_edges = [], []

        for edge in edges:
            edge_type = edge.get("type")
            if edge_type == "RELEVANT_TO":
                relevance_edges.append(self._parse_relevance_edge(edge))
            elif edge_type == "CITES":
                citation_edges.append(self._parse_citation_edge(edge))

        return papers_by_id, relevance_edges, citation_edges
