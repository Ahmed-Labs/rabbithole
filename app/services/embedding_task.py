from celery import shared_task

from db import KnowledgeGraphWriter, Neo4jClient, Neo4jConfig
from paper_retrieval.paper_metadata import build_citation_graph, search
from relevance_scoring.embedder import Embedder


@shared_task(bind=True)
def generate_embeddings_task(
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

    embedder = Embedder()
    embedder.embed_citation_graph(root_paper)

    cfg = Neo4jConfig.from_env()
    with Neo4jClient(cfg) as client:
        writer = KnowledgeGraphWriter(client)
        writer.ensure_schema()
        writer.persist_knowledge_graph(root_paper)

    return {
        "status": "success",
        "query": query,
        "root_paper": root_paper.id,
        "root_paper_title": root_paper.title,
    }
