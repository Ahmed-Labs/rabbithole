from typing import Dict, List

from celery import shared_task

from app.extensions import get_graph_writer, get_llm_scorer
from paper_retrieval import ResearchPaper
from relevance_scoring.relevance_scorer import RelevanceEdge


@shared_task(bind=True)
def generate_llm_score(self, root_paper: Dict, target_papers: List[List[Dict]]):
    llm = get_llm_scorer()

    root = ResearchPaper.from_props(root_paper)
    targets = [
        (ResearchPaper.from_props(p), RelevanceEdge.from_props(e))
        for p, e in target_papers
    ]

    edges = llm.compute_scores_batched(root, targets)

    db = get_graph_writer()
    db.upsert_llm_relevance(edges)

    return {"status": "success", "num_updated": len(edges)}
