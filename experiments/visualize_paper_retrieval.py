from pathlib import Path

from pyvis.network import Network

from paper_retrieval.paper_metadata import get_references_recur, search
from paper_retrieval.research_paper import ResearchPaper


def build_graph(root: ResearchPaper):
    net = Network(
        directed=True,
        height="900px",
        width="100%",
        bgcolor="#ffffff",
        font_color="black",
    )
    net.force_atlas_2based()

    def add_paper(paper: ResearchPaper):
        net.add_node(paper.id, label=paper.title[:30], title=paper.title)
        for ref in paper.references:
            net.add_node(ref.id, label=ref.title[:30], title=ref.title)
            net.add_edge(paper.id, ref.id)
            add_paper(ref)

    add_paper(root)
    return net


if __name__ == "__main__":
    query = "antioxidants"
    papers = search(query)

    if not papers:
        print("No papers found for the query")
        exit()

    root_paper = papers[0]
    print("Chosen Paper:", root_paper.title)

    max_depth, max_references = 1, 10
    print(
        f"Getting references (max_depth={max_depth}, max_references={max_references})..."
    )
    root_paper = get_references_recur(
        root_paper, depth=max_depth, max_references=max_references
    )

    net = build_graph(root_paper)

    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)

    output_file = output_dir / "references_graph.html"
    net.write_html(str(output_file))
