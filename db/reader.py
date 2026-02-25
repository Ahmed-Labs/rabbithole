from typing import Any, Dict, Tuple

from db.client import Neo4jClient
from paper_retrieval.research_paper import ResearchPaper
from relevance_scoring.relevance_scorer import CitationEdge, RelevanceEdge

Props = Dict[str, Any]


class KnowledgeGraphReader:
    def __init__(self, client: Neo4jClient):
        self.client = client

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
                relevance_edges.append(RelevanceEdge.from_props(edge))
            elif edge_type == "CITES":
                citation_edges.append(CitationEdge.from_props(edge))

        return papers_by_id, relevance_edges, citation_edges
