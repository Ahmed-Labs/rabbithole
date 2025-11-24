from pathlib import Path
from typing import Dict, List

from dotenv import load_dotenv
from pyvis.network import Network

from paper_retrieval.paper_metadata import search, build_full_graph
from paper_retrieval.research_paper import ResearchPaper
from relevance_scoring.relevance_scorer import (
    compute_relevance_scores,
    RelevanceEdge,
    RelevanceScore,
)

# Load environment variables from .env file
load_dotenv()


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
    root: ResearchPaper, scores_map: Dict[str, RelevanceScore]
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
        if score >= 0.7:
            return "#22c55e"  # Green
        elif score >= 0.5:
            return "#eab308"  # Yellow
        elif score >= 0.3:
            return "#f97316"  # Orange
        else:
            return "#ef4444"  # Red

    seen_nodes: set[str] = set()
    added_edges: set[tuple[str, str, str]] = set()

    def add_paper(paper: ResearchPaper, depth: int = 0):
        if paper.id in seen_nodes:
            return
        seen_nodes.add(paper.id)

        # Root node is blue
        if depth == 0:
            color = "#3b82f6"
            score_info = (
                f"ROOT\n"
                f"Year: {paper.year or 'N/A'} | "
                f"Citations: {paper.citation_count or 0}"
            )
        else:
            score = scores_map.get(paper.id)
            if score is None:
                relevance = 0.0
                semantic = 0.0
                year_sim = 0.0
                citation_score = 0.0
            else:
                relevance = score.combined
                semantic = score.semantic_similarity
                year_sim = score.year_similarity
                citation_score = score.citation_score
                llm_score = score.llm_semantic_score
                llm_explanation = score.llm_explanation

            color = get_color_by_score(relevance)
            
            # Build score info with LLM explanation if available
            score_info = (
                f"Relevance: {relevance:.3f}\n"
                f"Semantic: {semantic:.3f} | "
                f"YearSim: {year_sim:.3f} | "
                f"CitationScore: {citation_score:.3f}\n"
            )
            
            if llm_score is not None:
                score_info += f"LLM Score: {llm_score:.3f}\n"
            
            score_info += (
                f"Year: {paper.year or 'N/A'} | "
                f"Citations: {paper.citation_count or 0}"
            )
            
            # Add LLM explanation if available (wrapped to multiple lines)
            if llm_explanation:
                # Wrap explanation to multiple lines (max 60 chars per line for tooltip readability)
                max_line_length = 150
                words = llm_explanation.split()
                wrapped_lines = []
                current_line = []
                current_length = 0
                
                for word in words:
                    word_len = len(word)
                    # If adding this word would exceed the line length, start a new line
                    if current_length + word_len + 1 > max_line_length and current_line:
                        wrapped_lines.append(' '.join(current_line))
                        current_line = [word]
                        current_length = word_len
                    else:
                        current_line.append(word)
                        current_length += word_len + (1 if current_line else 0)
                
                # Add the last line
                if current_line:
                    wrapped_lines.append(' '.join(current_line))
                
                # Join with newlines for display
                wrapped_explanation = '\n'.join(wrapped_lines)
                score_info += f"\n\n💡 LLM Explanation:\n{wrapped_explanation}"

        # Add node with score information
        if depth == 0:
            node_label = paper.title[:30]
        else:
            relevance_for_label = (
                scores_map.get(paper.id).combined if paper.id in scores_map else 0.0
            )
            node_label = (
                f"{paper.title[:30]}\n"
                f"Rel: {relevance_for_label:.3f}"
            )

        # Use newlines directly - pyvis tooltips handle them automatically
        node_title = f"{paper.title}\n\n{score_info}"

        net.add_node(
            paper.id,
            label=node_label,
            title=node_title,
            color=color,
        )

    def add_edges(paper: ResearchPaper, depth: int = 0):
        """Add edges for both references and citations."""
        # References: paper → ref
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

        # Citations: cit → paper
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
    sorted_edges = sorted(
        edges, key=lambda e: e.relevance_score.combined, reverse=True
    )

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
        print(f"      ├─ Citation Score: {score.citation_score:.4f}")
        if score.llm_semantic_score is not None:
            print(f"      ├─ LLM Score: {score.llm_semantic_score:.4f}")
        print(f"      └─ (Year: {year}, Citations: {citations})")
        if edge.llm_explanation:
            print(f"\n      💡 LLM Explanation: {edge.llm_explanation}")
        print()


def print_stats(edges: List[RelevanceEdge]):
    """Print statistics about the scoring."""
    if not edges:
        return

    print(f"\n{'=' * 100}")
    print("SCORING STATISTICS")
    print(f"{'=' * 100}\n")

    print(f"Total papers scored: {len(edges)}")

    avg_semantic = (
        sum(e.relevance_score.semantic_similarity for e in edges) / len(edges)
    )
    avg_year = sum(e.relevance_score.year_similarity for e in edges) / len(edges)
    avg_citation = (
        sum(e.relevance_score.citation_score for e in edges) / len(edges)
    )
    avg_combined = sum(e.relevance_score.combined for e in edges) / len(edges)

    print(f"\nAverage semantic similarity: {avg_semantic:.4f}")
    print(f"Average year similarity: {avg_year:.4f}")
    print(f"Average citation score: {avg_citation:.4f}")
    print(f"Average combined relevance: {avg_combined:.4f}")
    print()


if __name__ == "__main__":
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
    depth = 1  # How many levels deep to traverse (both references and citations)
    max_per_level = 1  # Max papers per level (both references and citations)
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

    # LLM scoring is now automatically enabled
    # Set use_llm=False to disable if needed
    use_llm = True  # LLM scoring is automatic by default
    
    print("\nComputing relevance scores with LLM (automatic)...")
    print("(This will use API calls - make sure you have API keys set)")
    print("(Using GPT-5-nano for scoring and explanations)")
    
    # LLM scorer will be created automatically by compute_relevance_scores
    llm_scorer = None
    
    results, scorer = compute_relevance_scores(
        root_paper,
        use_llm=use_llm,
        llm_scorer=llm_scorer,
        max_depth=depth,
        use_cache=True
    )
    
    # Get edges from scorer for visualization
    edges = scorer.compute_relevance_edges(root_paper)
    paper_index = index_papers(root_paper)
    
    # Create lookup map for visualization (paper_id -> RelevanceScore)
    scores_map: Dict[str, RelevanceScore] = {
        edge.dest_id: edge.relevance_score for edge in edges
    }

    # Print statistics and top papers
    print_stats(edges)
    print_top_papers(edges, paper_index, top_n=15)

    # Build and save graph
    print("\nGenerating visualization...")
    print("Legend:")
    print("  • Solid gray lines (→): References (this paper cites that paper)")
    print("  • Dashed purple lines (→): Citations (that paper cites this paper)")

    net = build_graph_with_scores(root_paper, scores_map)

    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)

    output_file = output_dir / "references_graph.html"
    net.write_html(str(output_file))
    print(f"✓ Graph saved to: {output_file}")

    # Save scores to CSV
    import csv

    csv_file = output_dir / "relevance_scores.csv"
    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "src_id",
            "dest_id",
            "paper_id",
            "title",
            "year",
            "citation_count",
            "semantic_similarity",
            "year_similarity",
            "citation_score",
            "llm_relevance_score",
            "llm_explanation",
            "combined",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for edge in edges:
            paper = paper_index.get(edge.dest_id)
            score = edge.relevance_score

            writer.writerow(
                {
                    "src_id": edge.src_id,
                    "dest_id": edge.dest_id,
                    "paper_id": edge.dest_id,
                    "title": paper.title if paper else "",
                    "year": paper.year if paper else "",
                    "citation_count": paper.citation_count if paper else "",
                    "semantic_similarity": score.semantic_similarity,
                    "year_similarity": score.year_similarity,
                    "citation_score": score.citation_score,
                    "llm_relevance_score": score.llm_semantic_score if score.llm_semantic_score is not None else "",
                    "llm_explanation": edge.llm_explanation if edge.llm_explanation else "",
                    "combined": score.combined,
                }
            )

    print(f"✓ Scores saved to: {csv_file}")

    print(f"\n{'=' * 100}")
    print("Done! Open the HTML file in your browser to explore the graph.")
    print(f"{'=' * 100}")
