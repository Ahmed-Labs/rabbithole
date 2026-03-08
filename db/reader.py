from typing import Any, Dict, List, Optional, Tuple

from db.client import Neo4jClient
from paper_retrieval.research_paper import ResearchPaper
from relevance_scoring.relevance_scorer import CitationEdge, RelevanceEdge

Props = Dict[str, Any]


class KnowledgeGraphReader:
    def __init__(self, client: Neo4jClient):
        self.client = client

    def read(
        self,
        paper_id: str,
        depth: int = 3,
        node_limit: int = 1000,
    ) -> Optional[
        Tuple[dict[str, ResearchPaper], list[RelevanceEdge], list[CitationEdge]]
    ]:
        # Node limit is equally split between nodes collected from both inwards and outwards traversals.
        # Without this, we could end up with an imbalanced graph that hits the node limit in one subgraph and
        # fully skips over the other.
        out_limit = max(1, node_limit // 2)
        in_limit = max(1, node_limit - out_limit)

        citation_query = """
        MATCH (root:Paper {id: $id})

        CALL (root) {
        CALL apoc.path.expandConfig(root, {
            relationshipFilter: "CITES>",
            minLevel: 1,
            maxLevel: $depth,
            bfs: true,
            uniqueness: "NODE_GLOBAL",
            limit: $out_limit
        })
        YIELD path
        RETURN
            collect(DISTINCT last(nodes(path))) AS outNodes,
            apoc.coll.toSet(apoc.coll.flatten(collect(relationships(path)))) AS outRels
        }

        CALL (root) {
        CALL apoc.path.expandConfig(root, {
            relationshipFilter: "<CITES",
            minLevel: 1,
            maxLevel: $depth,
            bfs: true,
            uniqueness: "NODE_GLOBAL",
            limit: $in_limit
        })
        YIELD path
        RETURN
            collect(DISTINCT last(nodes(path))) AS inNodes,
            apoc.coll.toSet(apoc.coll.flatten(collect(relationships(path)))) AS inRels
        }

        WITH
        apoc.coll.toSet(coalesce(outNodes, []) + coalesce(inNodes, []) + [root]) AS ns,
        apoc.coll.toSet(coalesce(outRels, []) + coalesce(inRels, [])) AS citeRels

        RETURN
        [n IN ns | n{.*, id: n.id}] AS nodes,
        [e IN citeRels | {
            type: type(e),
            src: startNode(e).id,
            dest: endNode(e).id,
            props: properties(e)
        }] AS citationEdges,
        [n IN ns | n.id] AS nodeIds
        """

        relevance_query = """
        MATCH (root:Paper {id: $id})
        MATCH (root)-[re:RELEVANT_TO]-(r:Paper)
        WHERE r.id IN $nodeIds
        RETURN
          type(re) AS type,
          startNode(re).id AS src,
          endNode(re).id AS dest,
          properties(re) AS props
        """

        rows = self.client.run_read(
            citation_query,
            {
                "id": paper_id,
                "depth": depth,
                "out_limit": out_limit,
                "in_limit": in_limit,
            },
        )

        if not rows:
            root_rows = self.client.run_read(
                "MATCH (p:Paper {id: $id}) RETURN p{.*, id:p.id} AS node",
                {"id": paper_id},
            )
            if not root_rows:
                return None
            root_paper = ResearchPaper.from_props(root_rows[0]["node"])
            return {root_paper.id: root_paper}, [], []

        data = rows[0] or {}
        node_props: List[dict] = data.get("nodes") or []
        node_ids: List[str] = data.get("nodeIds") or []
        cite_edges_raw: List[dict] = data.get("citationEdges") or []

        if not node_props or not node_ids:
            return None

        rel_rows = (
            self.client.run_read(
                relevance_query,
                {"id": paper_id, "nodeIds": node_ids},
            )
            or []
        )

        papers = [ResearchPaper.from_props(p) for p in node_props]
        papers_by_id = {p.id: p for p in papers}

        citation_edges = [CitationEdge.from_props(e) for e in cite_edges_raw]
        relevance_edges = [RelevanceEdge.from_props(e) for e in rel_rows]

        return papers_by_id, relevance_edges, citation_edges
