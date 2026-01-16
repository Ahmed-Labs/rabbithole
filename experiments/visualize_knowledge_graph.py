import textwrap
from pathlib import Path
from typing import Dict, List, Optional

from pyvis.network import Network

from paper_retrieval.paper_metadata import build_full_graph, search
from paper_retrieval.research_paper import ResearchPaper
from relevance_scoring.relevance_scorer import (
    RelevanceEdge,
    RelevanceScore,
    compute_relevance_scores,
)


def wrap_text(text: str, width: int = 80) -> str:
    """Wrap LLM explanation to avoid overflow in hover tooltip."""
    return "\n".join(textwrap.wrap(text, width))


def index_papers(root: ResearchPaper) -> Dict[str, ResearchPaper]:
    """Build a mapping from paper id → ResearchPaper by traversing the graph."""
    index: Dict[str, ResearchPaper] = {}
    visited: set[str] = set()

    def dfs(paper: ResearchPaper):
        if paper.id in visited:
            return
        visited.add(paper.id)
        index[paper.id] = paper
        for ref in paper.references:
            dfs(ref)
        for cit in paper.citations:
            dfs(cit)

    dfs(root)
    return index


def build_graph_with_scores(
    root: ResearchPaper,
    scores_map: Dict[str, RelevanceScore],
    llm_map: Dict[str, Optional[str]],
) -> Network:
    """Build network graph with relevance scores and visual distinction for citations."""
    net = Network(
        directed=True,
        height="900px",
        width="100%",
        bgcolor="#ffffff",
        font_color="black",
    )
    net.force_atlas_2based()

    def get_color_by_score(score: float) -> str:
        """Get color gradient from red (low) to green (high)."""
        if score >= 0.8:
            return "#22c55e"  # Green
        if score >= 0.7:
            return "#6ec522"  # Green-ish
        if score >= 0.6:
            return "#c5c522"  # Yellow-green
        if score >= 0.5:
            return "#c59c22"  # Yellow-orange
        elif score >= 0.4:
            return "#ea8808"  # Orange
        elif score >= 0.3:
            return "#f97316"  # Deep orange
        else:
            return "#ef4444"  # Red

    seen_nodes: set[str] = set()
    added_edges: set[tuple[str, str, str]] = set()

    def add_paper(paper: ResearchPaper, depth: int = 0) -> bool:
        """
        Add a paper node to the graph.

        Returns True if the node was added (or already present), False if it
        should be skipped (e.g., gray / no LLM score).
        """
        if paper.id in seen_nodes:
            return True

        # Root node is always shown
        if depth == 0:
            color = "#3b82f6"
            relevance_for_label = 1.0
            node_label = paper.title[:30]
            llm_explanation = None
            pdf_url = getattr(paper, "pdf_url", None)

            # Hover: just link + note that it's the root
            tooltip_parts = []
            tooltip_parts.append("Root paper")
            if pdf_url:
                tooltip_parts.append(
                    f'<a href="{pdf_url}" target="_blank">Open PDF</a>'
                )
            node_title = "<br><br>".join(tooltip_parts) if tooltip_parts else ""
        else:
            score = scores_map.get(paper.id)
            if score is None:
                # No score at all → skip
                return False

            relevance = score.combined
            llm_score = score.llm_score

            # Hide any "gray" ones: if no LLM score, we don't display this node
            if llm_score is None:
                return False

            # Color and size based purely on final relevance score
            color = get_color_by_score(relevance)

            # Node label: short title, keep relevance in label so you can see it at a glance
            node_label = f"{paper.title[:30]}"
            relevance_for_label = relevance

            # Hover content: ONLY final relevance, LLM explanation, and PDF link
            llm_explanation = llm_map.get(paper.id)
            pdf_url = getattr(paper, "pdf_url", None)

            tooltip_parts = [paper.title + " | " + f"Relevance score: {relevance:.3f}"]

            if pdf_url:
                tooltip_parts.append(
                    f'<a href="{pdf_url}" target="_blank">Open PDF</a>'
                )

            if llm_explanation:
                wrapped = wrap_text(llm_explanation)
                wrapped_html = wrapped.replace("\n", "<br>")
                tooltip_parts.append(wrapped_html)

            node_title = "<br><br>".join(tooltip_parts)

        # Size: larger nodes for higher relevance (root is maxed)
        if depth == 0:
            value = 60
        else:
            # Map relevance in [0,1] to a reasonable size range [10, 60]
            value = max(10, min(60, int(relevance_for_label * 50) + 10))

        net.add_node(
            paper.id,
            label=node_label,
            title=node_title,
            color=color,
            value=value,
        )
        seen_nodes.add(paper.id)
        return True

    def add_edges(paper: ResearchPaper, depth: int = 0):
        """Add edges for both references and citations, only between visible nodes."""
        # References: paper → ref
        for ref in paper.references:
            # Only add edge + recurse if the referenced paper is visible
            if add_paper(ref, depth + 1):
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
                add_edges(ref, depth + 1)

        # Citations: cit → paper
        for cit in paper.citations:
            # Only add edge + recurse if the citing paper is visible
            if add_paper(cit, depth + 1):
                key = (cit.id, paper.id, "citation")
                if key not in added_edges:
                    net.add_edge(
                        cit.id,
                        paper.id,
                        dashes=False,  # Dashed line pattern
                        color="#666666",  # Purple for citations
                        arrows="to",
                    )
                    added_edges.add(key)
                add_edges(cit, depth + 1)

    # Start with root paper
    add_paper(root, 0)
    add_edges(root, 0)

    return net


def print_top_papers(
    edges: List[RelevanceEdge],
    paper_index: Dict[str, ResearchPaper],
    top_n: int = 10,
):
    """Print top N papers by combined relevance score."""
    print(f"\n{'=' * 100}")
    print(f"TOP {top_n} MOST RELEVANT PAPERS")
    print(f"{'=' * 100}\n")

    # Sort by combined score (descending)
    sorted_edges = sorted(edges, key=lambda e: e.relevance_score.combined, reverse=True)

    for i, edge in enumerate(sorted_edges[:top_n], 1):
        paper = paper_index.get(edge.dest_id)
        title = paper.title if paper else f"[Unknown title] ({edge.dest_id})"
        year = paper.year if paper else "N/A"
        citations = paper.citation_count if paper else "N/A"

        score = edge.relevance_score

        print(f"{i}. {title[:70]}")
        print(f"   └─ Relevance: {score.combined:.4f}")
        print(f"      ├─ Semantic: {score.semantic_similarity:.4f}")
        print(f"      ├─ Year Similarity: {score.year_similarity:.4f}")
        print(f"      └─ Citation Score: {score.citation_score:.4f}")
        print(f"         (Year: {year}, Citations: {citations})")
        print()


def print_stats(edges: List[RelevanceEdge]):
    """Print statistics about the scoring."""
    if not edges:
        return

    print(f"\n{'=' * 100}")
    print("SCORING STATISTICS")
    print(f"{'=' * 100}\n")

    print(f"Total papers scored: {len(edges)}")

    avg_semantic = sum(e.relevance_score.semantic_similarity for e in edges) / len(
        edges
    )
    avg_year = sum(e.relevance_score.year_similarity for e in edges) / len(edges)
    avg_citation = sum(e.relevance_score.citation_score for e in edges) / len(edges)
    avg_combined = sum(e.relevance_score.combined for e in edges) / len(edges)

    print(f"\nAverage semantic similarity: {avg_semantic:.4f}")
    print(f"Average year similarity: {avg_year:.4f}")
    print(f"Average citation score: {avg_citation:.4f}")
    print(f"Average combined relevance: {avg_combined:.4f}")
    print()


if __name__ == "__main__":
    query = input("Enter search query: ").strip()
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

    depth = int(input("Enter search depth: ").strip() or 3)
    max_per_level = int(input("Enter max papers per level (e.g., 20): ").strip() or 20)

    print(f"\nBuilding paper graph:")
    print(f"  Depth: {depth} levels")
    print(f"  Max per level: {max_per_level} papers")

    root_paper = build_full_graph(
        root_paper,
        depth=depth,
        max_per_level=max_per_level,
    )

    print("\nComputing relevance scores...")
    edges = compute_relevance_scores(root_paper)

    # Build paper index for easy lookup by id (for printing)
    paper_index = index_papers(root_paper)

    # Create lookup map for visualization
    scores_map: Dict[str, RelevanceScore] = {
        edge.dest_id: edge.relevance_score for edge in edges
    }
    llm_map: Dict[str, Optional[str]] = {
        edge.dest_id: edge.llm_explanation for edge in edges
    }

    # Print statistics and top papers (CLI only, doesn't affect graph)
    print_stats(edges)
    print_top_papers(edges, paper_index, top_n=15)

    # Build and save graph
    print("\nGenerating visualization...")
    print("Legend:")
    print("  • Solid gray lines (→): References (this paper cites that paper)")
    print("  • Dashed purple lines (→): Citations (that paper cites this paper)")

    net = build_graph_with_scores(root_paper, scores_map, llm_map)

    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)

    output_file = output_dir / "knowledge_graph.html"
    net.write_html(str(output_file))
    print(f"✓ Graph saved to: {output_file}")

    print(f"\n{'=' * 100}")
    print("Done! Open the HTML file in your browser to explore the graph.")
    print(f"{'=' * 100}")
