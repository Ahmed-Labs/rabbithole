from dotenv import load_dotenv

from db.client import Neo4jClient, Neo4jConfig
from db.reader import KnowledgeGraphReader

if __name__ == "__main__":
    load_dotenv()

    cfg = Neo4jConfig.from_env()
    with Neo4jClient(cfg) as client:
        reader = KnowledgeGraphReader(client)
        test_paper_id = "41b1d0c1be11cb53cd9258c3a1d7dfab11af1f47"

        res = reader.read(test_paper_id)
        if res == None:
            print("Paper not found")
        else:
            papers, relevance_scores, citations = res
            print(f"Found {len(papers)} papers")
            print(f"Found {len(relevance_scores)} relevance scores")
            print(f"Found {len(citations)} citations")
