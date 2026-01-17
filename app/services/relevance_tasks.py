from pathlib import Path

from celery import shared_task
from pyvis.network import Network

from paper_retrieval.paper_metadata import get_references_recur, search
from paper_retrieval.research_paper import ResearchPaper


def build_graph(root: ResearchPaper) -> Network:
    net = Network(
        directed=True,
        height="900px",
        width="100%",
        bgcolor="#ffffff",
        font_color="black",
    )
    net.force_atlas_2based()

    visited = set()

    def add_paper(paper: ResearchPaper):
        if paper.id in visited:
            return
        visited.add(paper.id)

        net.add_node(paper.id, label=paper.title[:30], title=paper.title)

        for ref in paper.references:
            net.add_node(ref.id, label=ref.title[:30], title=ref.title)
            net.add_edge(paper.id, ref.id)
            add_paper(ref)

    add_paper(root)
    return net


@shared_task(bind=True)
def get_relevance_task(
    self,
    query: str,
    max_depth: int = 1,
    max_references: int = 10,
) -> dict:
    """
    Heavy background task:
    - search for papers
    - recursively fetch references
    - build PyVis graph
    - write HTML to disk
    """

    papers = search(query)
    if not papers:
        return {"status": "error", "message": "No papers found"}

    root_paper = papers[0]

    root_paper = get_references_recur(
        root_paper,
        depth=max_depth,
        max_references=max_references,
    )

    net = build_graph(root_paper)

    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    output_file = output_dir / f"references_graph_{self.request.id}.html"
    net.write_html(str(output_file))

    return {
        "status": "success",
        "query": query,
        "root_paper": root_paper.title,
        "output_file": str(output_file),
    }
