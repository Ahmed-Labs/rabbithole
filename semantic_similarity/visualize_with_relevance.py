from pathlib import Path
from pyvis.network import Network
import sys
sys.path.append(str(Path(__file__).parent.parent))

from paper_retrieval.paper_metadata import search, get_references_recur
from paper_retrieval.research_paper import ResearchPaper
from semantic_similarity import compute_relevance_scores


def build_graph_with_scores(root: ResearchPaper, scores_map: dict):
    """Build network graph with relevance scores displayed."""
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

    def add_paper(paper: ResearchPaper, depth: int = 0):
        # Root node is blue
        if depth == 0:
            color = "#3b82f6"
            score_info = f"ROOT | Year: {paper.year or 'N/A'} | Citations: {paper.citation_count or 0}"
        else:
            score_data = scores_map.get(paper.id, {})
            relevance = score_data.get("relevance_score", 0)
            semantic = score_data.get("semantic_similarity", 0)
            bib_coupling = score_data.get("bibliographic_coupling", 0)
            year_sim = score_data.get("year_similarity", 0)
            path_prob = score_data.get("path_probability", 0)
            
            color = get_color_by_score(relevance)
            score_info = (
                f"Relevance: {relevance:.3f}\n"
                f"Semantic: {semantic:.3f} | BibCoupling: {bib_coupling:.3f}\n"
                f"YearSim: {year_sim:.3f} | Path: {path_prob:.3f}\n"
                f"Year: {paper.year or 'N/A'} | Citations: {paper.citation_count or 0}"
            )
        
        # Add node with score information
        node_label = f"{paper.title[:30]}\nRel: {scores_map.get(paper.id, {}).get('relevance_score', 0):.3f}" if depth > 0 else paper.title[:30]
        node_title = f"{paper.title}\n\n{score_info}"
        
        net.add_node(
            paper.id, 
            label=node_label,
            title=node_title,
            color=color
        )
        
        for ref in paper.references:
            add_paper(ref, depth + 1)
            
            # Add edge with probability label
            if ref.id in scores_map:
                edge_prob = scores_map[ref.id].get("path_probability", 0)
                edge_label = f"{edge_prob:.2f}"
            else:
                edge_label = ""
            
            net.add_edge(paper.id, ref.id, label=edge_label)

    add_paper(root)
    return net


def print_top_papers(results: list, top_n: int = 10):
    """Print top N papers by relevance score."""
    print(f"\n{'='*100}")
    print(f"TOP {top_n} MOST RELEVANT PAPERS (SPECTER + ConnectedPapers-style scoring)")
    print(f"{'='*100}\n")
    
    for i, result in enumerate(results[:top_n], 1):
        print(f"{i}. {result['title'][:70]}")
        print(f"   └─ Relevance: {result['relevance_score']:.4f}")
        print(f"      ├─ Semantic (SPECTER): {result['semantic_similarity']:.4f}")
        print(f"      ├─ Bib. Coupling: {result['bibliographic_coupling']:.4f}")
        print(f"      ├─ Year Similarity: {result['year_similarity']:.4f}")
        print(f"      ├─ Citation Score: {result['citation_score']:.4f}")
        print(f"      └─ Path Probability: {result['path_probability']:.4f} (depth: {result['depth']})")
        print()


def print_stats(results: list):
    """Print statistics about the scoring."""
    if not results:
        return
    
    print(f"\n{'='*100}")
    print("SCORING STATISTICS")
    print(f"{'='*100}\n")
    
    avg_semantic = sum(r['semantic_similarity'] for r in results) / len(results)
    avg_bib = sum(r['bibliographic_coupling'] for r in results) / len(results)
    avg_year = sum(r['year_similarity'] for r in results) / len(results)
    
    print(f"Total papers scored: {len(results)}")
    print(f"Average semantic similarity: {avg_semantic:.4f}")
    print(f"Average bibliographic coupling: {avg_bib:.4f}")
    print(f"Average year similarity: {avg_year:.4f}")
    print()


if __name__ == "__main__":
    query = "antioxidants"
    papers = search(query)

    if not papers:
        print("No papers found for the query")
        exit()

    root_paper = papers[0]
    print("="*100)
    print(f"Root Paper: {root_paper.title}")
    print(f"Year: {root_paper.year or 'N/A'}")
    print(f"Citations: {root_paper.citation_count or 0}")
    print("="*100)

    max_depth, max_references = 2, 10
    print(f"\nFetching references (max_depth={max_depth}, max_references={max_references})...")
    root_paper = get_references_recur(
        root_paper, depth=max_depth, max_references=max_references
    )

    print("\nComputing relevance scores with SPECTER2...")
    print("(This may take a few minutes on first run - downloading model and computing embeddings)")
    results, scorer = compute_relevance_scores(root_paper, max_depth=max_depth, use_cache=True)
    
    # Create lookup map for visualization
    scores_map = {r["paper_id"]: r for r in results}
    
    # Print statistics and top papers
    print_stats(results)
    print_top_papers(results, top_n=15)
    
    # Build and save graph
    print("\nGenerating visualization...")
    net = build_graph_with_scores(root_paper, scores_map)
    
    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)
    
    output_file = output_dir / "references_graph_specter.html"
    net.write_html(str(output_file))
    print(f"✓ Graph saved to: {output_file}")
    
    # Save scores to CSV
    import csv
    csv_file = output_dir / "relevance_scores_specter.csv"
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        if results:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)
    print(f"✓ Scores saved to: {csv_file}")
    
    print(f"\n{'='*100}")
    print("Done! Open the HTML file in your browser to explore the graph.")
    print(f"{'='*100}")