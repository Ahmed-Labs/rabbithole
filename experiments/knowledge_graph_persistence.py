from db import Neo4jClient, Neo4jConfig, KnowledgeGraphWriter
from paper_retrieval.paper_metadata import search, build_citation_graph
from relevance_scoring.relevance_scorer import compute_relevance_scores
from dotenv import load_dotenv


if __name__ == "__main__":
    load_dotenv()

    query = "phasor"
    papers = search(query)

    if not papers:
        print("No papers found for the query")
        raise SystemExit(1)

    root_paper = papers[0]
    print("=" * 100)
    print(f"Root Paper: {root_paper.title}")
    print(f"Year: {root_paper.year or 'N/A'}")
    print(f"Citations: {root_paper.citation_count or 0}")
    print("=" * 100)

    # Configuration
    depth = 3
    max_per_level = 20
    include_citations = True

    print(f"\nBuilding paper graph:")
    print(f"  Depth: {depth} levels")
    print(f"  Max per level: {max_per_level} papers")
    print(f"  Include citations: {include_citations}")

    root_paper = build_citation_graph(
        root_paper,
        depth=depth,
        max_per_level=max_per_level,
        include_citations=include_citations,
    )
    print("\nComputing relevance scores...")
    edges = compute_relevance_scores(root_paper)

    # Persist to neo4j
    cfg = Neo4jConfig.from_env()

    with Neo4jClient(cfg) as client:
        writer = KnowledgeGraphWriter(client)
        writer.ensure_schema()
        writer.persist_knowledge_graph(root_paper, edges)
