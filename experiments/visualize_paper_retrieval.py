"""
Visualize paper retrieval graph without relevance scoring.

This script builds and visualizes the citation/reference graph of papers
without computing relevance scores. Useful for exploring paper relationships.
"""

from pathlib import Path
from pyvis.network import Network
from paper_retrieval.paper_metadata import search, build_full_graph
from paper_retrieval.research_paper import ResearchPaper


def build_graph(root: ResearchPaper) -> Network:
    """Build network graph showing paper relationships (references and citations)."""
    net = Network(
        directed=True,
        height="900px",
        width="100%",
        bgcolor="#ffffff",
        font_color="black",
    )
    net.force_atlas_2based()

    seen_nodes: set[str] = set()
    added_edges: set[tuple[str, str, str]] = set()

    def add_paper(paper: ResearchPaper, depth: int = 0):
        """Add a paper node to the graph."""
        if paper.id in seen_nodes:
            return
        seen_nodes.add(paper.id)

        # Root node is blue, others are gray
        if depth == 0:
            color = "#3b82f6"  # Blue for root
        else:
            color = "#9ca3af"  # Gray for other nodes

        # Build tooltip with paper info
        tooltip = (
            f"{paper.title}\n\n"
            f"Year: {paper.year or 'N/A'}\n"
            f"Citations: {paper.citation_count or 0}\n"
            f"Authors: {', '.join([a.get('name', 'Unknown') for a in paper.authors[:3]])}"
        )

        # Node label (truncated title)
        if depth == 0:
            node_label = paper.title[:40]
        else:
            node_label = paper.title[:30]

        net.add_node(
            paper.id,
            label=node_label,
            title=tooltip,
            color=color,
        )

    def add_edges(paper: ResearchPaper, depth: int = 0):
        """Add edges for both references and citations."""
        # References: paper → ref (solid gray lines)
        for ref in paper.references:
            if ref.id not in seen_nodes:
                add_paper(ref, depth + 1)

            key = (paper.id, ref.id, "reference")
            if key not in added_edges:
                net.add_edge(
                    paper.id,
                    ref.id,
                    dashes=False,  # Solid line
                    color="#666666",
                    arrows="to",
                )
                added_edges.add(key)

            # Recursively add edges for referenced papers
            add_edges(ref, depth + 1)

        # Citations: cit → paper (dashed purple lines)
        for cit in paper.citations:
            if cit.id not in seen_nodes:
                add_paper(cit, depth + 1)

            key = (cit.id, paper.id, "citation")
            if key not in added_edges:
                net.add_edge(
                    cit.id,
                    paper.id,
                    dashes=[5, 5],  # Dashed line pattern
                    color="#9333ea",  # Purple for citations
                    arrows="to",
                )
                added_edges.add(key)

            # Recursively add edges for citing papers
            add_edges(cit, depth + 1)

    # Start with root paper
    add_paper(root, 0)
    add_edges(root, 0)

    return net


if __name__ == "__main__":
    # Search for a paper
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
    depth = 1  # How many levels deep to traverse
    max_per_level = 5  # Max papers per level
    include_citations = True  # Whether to include citation edges

    print(f"\nBuilding paper graph:")
    print(f"  Depth: {depth} levels")
    print(f"  Max per level: {max_per_level} papers")
    print(f"  Include citations: {include_citations}")

    root_paper = build_full_graph(
        root_paper,
        depth=depth,
        max_per_level=max_per_level,
        include_citations=include_citations,
    )

    # Build visualization
    print("\nBuilding visualization...")
    net = build_graph(root_paper)

    # Save to file
    output_dir = Path("experiments/output")
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / "paper_retrieval_graph.html"

    net.save_graph(str(output_file))
    print(f"\n✓ Graph saved to: {output_file}")
    print(f"  Open in your browser to view the interactive graph.")
    print(f"\n  Legend:")
    print(f"    - Blue node: Root paper")
    print(f"    - Gray nodes: Other papers")
    print(f"    - Solid gray edges: References (paper → referenced paper)")
    print(f"    - Dashed purple edges: Citations (citing paper → paper)")

