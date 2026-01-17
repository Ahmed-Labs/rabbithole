from celery import shared_task

from db import KnowledgeGraphWriter, Neo4jClient, Neo4jConfig
from paper_retrieval.paper_metadata import build_citation_graph, search
from relevance_scoring.relevance_scorer import compute_relevance_scores


@shared_task(bind=True)
def get_relevance_task(
    self,
    query: str,
    max_depth: int = 1,
    max_references: int = 10,
) -> dict:
    papers = search(query)
    if not papers:
        return {"status": "error", "message": "No papers found"}

    root_paper = papers[0]

    root_paper = build_citation_graph(
        root_paper,
        depth=max_depth,
        max_per_level=max_references,
        include_citations=True,
    )

    edges = compute_relevance_scores(root_paper)

    cfg = Neo4jConfig.from_env()
    with Neo4jClient(cfg) as client:
        writer = KnowledgeGraphWriter(client)
        writer.ensure_schema()
        writer.persist_knowledge_graph(root_paper, edges)

    return {
        "status": "success",
        "query": query,
        "root_paper": root_paper.title,
        "papers_processed": len(edges),
    }
