import json
from typing import Any, Dict, Iterable, List, Tuple

from db.client import Neo4jClient
from paper_retrieval.research_paper import ResearchPaper
from relevance_scoring.relevance_scorer import RelevanceEdge


class KnowledgeGraphWriter:
    def __init__(self, client: Neo4jClient):
        self.client = client

    def ensure_schema(self) -> None:
        self.client.run_write(
            """
            CREATE CONSTRAINT paper_id_unique IF NOT EXISTS
            FOR (p:Paper) REQUIRE p.id IS UNIQUE
            """
        )

    def upsert_papers(self, papers: Iterable[ResearchPaper]) -> None:
        rows = [{"id": p.id, "props": p.to_props()} for p in papers]
        self.client.run_write(
            """
            UNWIND $rows AS row
            MERGE (p:Paper {id: row.id})
            SET p += row.props
            """,
            {"rows": rows},
        )

    def upsert_citation_edges(self, edges: Iterable[Tuple[str, str]]) -> None:
        rows = [{"src": s, "dst": d} for (s, d) in edges]
        self.client.run_write(
            """
            UNWIND $rows AS row
            MATCH (a:Paper {id: row.src})
            MATCH (b:Paper {id: row.dst})
            MERGE (a)-[:CITES]->(b)
            """,
            {"rows": rows},
        )

    def upsert_relevance_edges(self, edges: Iterable[RelevanceEdge]) -> None:
        rows: List[dict] = []
        for e in edges:
            s = e.relevance_score
            props = {
                "semantic_similarity": s.semantic_similarity,
                "year_similarity": s.year_similarity,
                "citation_score": s.citation_score,
                "llm_score": s.llm_score,
            }
            if e.llm_explanation is not None:
                props["llm_explanation"] = e.llm_explanation

            rows.append({"src": e.src_id, "dst": e.dest_id, "props": props})

        self.client.run_write(
            """
            UNWIND $rows AS row
            MATCH (a:Paper {id: row.src})
            MATCH (b:Paper {id: row.dst})
            MERGE (a)-[r:RELEVANT_TO]->(b)
            SET r += row.props
            """,
            {"rows": rows},
        )

    def persist_knowledge_graph(
        self, root: ResearchPaper, relevance_edges: Iterable[RelevanceEdge]
    ) -> None:
        seen: set[str] = set()
        stack: List[ResearchPaper] = [root]
        papers: List[ResearchPaper] = []

        while stack:
            p = stack.pop()
            if p.id in seen:
                continue
            seen.add(p.id)
            papers.append(p)
            stack.extend(p.references)
            stack.extend(p.citations)

        self.upsert_papers(papers)

        cite_edges: List[Tuple[str, str]] = []
        for p in papers:
            cite_edges.extend(p.bidirectional_citations)

        if cite_edges:
            self.upsert_citation_edges(cite_edges)

        self.upsert_relevance_edges(relevance_edges)
