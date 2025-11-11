from pathlib import Path
from pyvis.network import Network
import sys
sys.path.append(str(Path(__file__).parent.parent))

from paper_retrieval.paper_metadata import search, build_full_graph
from paper_retrieval.research_paper import ResearchPaper
from semantic_similarity import compute_relevance_scores


def build_graph_with_scores(root: ResearchPaper, scores_map: dict):
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

    seen_nodes = set()
    
    def add_paper(paper: ResearchPaper, depth: int = 0, is_citation: bool = False):
        if paper.id in seen_nodes:
            return
        seen_nodes.add(paper.id)
        
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
            edge_type = score_data.get("edge_type", "reference")
            
            color = get_color_by_score(relevance)
            edge_icon = "↓" if edge_type == "reference" else "↑"
            score_info = (
                f"{edge_icon} {edge_type.upper()}\n"
                f"Relevance: {relevance:.3f}\n"
                f"Semantic: {semantic:.3f} | BibCoupling: {bib_coupling:.3f}\n"
                f"YearSim: {year_sim:.3f} | Path: {path_prob:.3f}\n"
                f"Year: {paper.year or 'N/A'} | Citations: {paper.citation_count or 0}"
            )
        
        # Add node with score information
        node_label = (
            f"{paper.title[:30]}\n"
            f"Rel: {scores_map.get(paper.id, {}).get('relevance_score', 0):.3f}"
            if depth > 0 else paper.title[:30]
        )
        node_title = f"{paper.title}\n\n{score_info}"
        
        net.add_node(
            paper.id, 
            label=node_label,
            title=node_title,
            color=color
        )
    
    def add_edges(paper: ResearchPaper, depth: int = 0):
        """Add edges for both references and citations."""
        # Add reference edges (solid lines - this paper cites them)
        for ref in paper.references:
            if ref.id not in seen_nodes:
                add_paper(ref, depth + 1, is_citation=False)
            
            if ref.id in scores_map:
                edge_prob = scores_map[ref.id].get("path_probability", 0)
                edge_label = f"{edge_prob:.2f}"
            else:
                edge_label = ""
            
            # Solid line for references (paper → reference)
            net.add_edge(
                paper.id, 
                ref.id, 
                label=edge_label,
                dashes=False,  # Solid line
                color="#666666",
                arrows="to"
            )
            
            # Recursively add edges for referenced papers
            add_edges(ref, depth + 1)
        
        # Add citation edges (dashed lines - these papers cite this one)
        for cit in paper.citations:
            if cit.id not in seen_nodes:
                add_paper(cit, depth + 1, is_citation=True)
            
            if cit.id in scores_map:
                edge_prob = scores_map[cit.id].get("path_probability", 0)
                edge_label = f"{edge_prob:.2f}"
            else:
                edge_label = ""
            
            # Dashed line for citations (citation → paper)
            net.add_edge(
                cit.id,
                paper.id,
                label=edge_label,
                dashes=[5, 5],  # Dashed line pattern
                color="#9333ea",  # Purple for citations
                arrows="to"
            )
            
            # Recursively add edges for citing papers
            add_edges(cit, depth + 1)

    # Start with root paper
    add_paper(root, 0)
    add_edges(root, 0)
    
    return net


def print_top_papers(results: list, top_n: int = 10):
    """Print top N papers by relevance score, separated by type."""
    print(f"\n{'='*100}")
    print(f"TOP {top_n} MOST RELEVANT PAPERS (SPECTER2 + ConnectedPapers-style scoring)")
    print(f"{'='*100}\n")
    
    # Separate by edge type
    references = [r for r in results if r.get('edge_type') == 'reference']
    citations = [r for r in results if r.get('edge_type') == 'citation']
    
    print(f"📚 REFERENCES (papers cited by root or its references):")
    print(f"{'─'*100}")
    for i, result in enumerate(references[:top_n], 1):
        print(f"{i}. {result['title'][:70]}")
        print(f"   └─ Relevance: {result['relevance_score']:.4f}")
        print(f"      ├─ Semantic (SPECTER2): {result['semantic_similarity']:.4f}")
        print(f"      ├─ Bib. Coupling: {result['bibliographic_coupling']:.4f}")
        print(f"      ├─ Year Similarity: {result['year_similarity']:.4f}")
        print(f"      ├─ Citation Score: {result['citation_score']:.4f}")
        print(f"      └─ Path Probability: {result['path_probability']:.4f} (depth: {result['depth']})")
        print()
    
    print(f"\n📖 CITATIONS (papers that cite root or papers citing root):")
    print(f"{'─'*100}")
    for i, result in enumerate(citations[:top_n], 1):
        print(f"{i}. {result['title'][:70]}")
        print(f"   └─ Relevance: {result['relevance_score']:.4f}")
        print(f"      ├─ Semantic (SPECTER2): {result['semantic_similarity']:.4f}")
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
    
    references = [r for r in results if r.get('edge_type') == 'reference']
    citations = [r for r in results if r.get('edge_type') == 'citation']
    
    print(f"Total papers scored: {len(results)}")
    print(f"  └─ References (solid lines): {len(references)}")
    print(f"  └─ Citations (dashed lines): {len(citations)}")
    
    if results:
        avg_semantic = sum(r['semantic_similarity'] for r in results) / len(results)
        avg_bib = sum(r['bibliographic_coupling'] for r in results) / len(results)
        avg_year = sum(r['year_similarity'] for r in results) / len(results)
        
        print(f"\nAverage semantic similarity: {avg_semantic:.4f}")
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

    # Configuration for graph building
    ref_depth = 2  # How many levels of references to fetch
    cit_depth = 1  # How many levels of citations to fetch
    max_references = 10  # Max references per paper per level
    max_citations = 5   # Max citations per paper per level (usually want fewer)
    
    print(f"\nBuilding paper graph:")
    print(f"  References: depth={ref_depth}, max_per_level={max_references}")
    print(f"  Citations: depth={cit_depth}, max_per_level={max_citations}")
    
    root_paper = build_full_graph(
        root_paper,
        ref_depth=ref_depth,
        cit_depth=cit_depth,
        max_references=max_references,
        max_citations=max_citations
    )

    print("\nComputing relevance scores with SPECTER2...")
    print("(This may take a few minutes on first run - downloading model and computing embeddings)")
    
    results, scorer = compute_relevance_scores(
        root_paper,
        max_ref_depth=ref_depth,
        max_cit_depth=cit_depth,
        use_cache=True
    )
    
    # Create lookup map for visualization
    scores_map = {r["paper_id"]: r for r in results}
    
    # Print statistics and top papers
    print_stats(results)
    print_top_papers(results, top_n=15)
    
    # Build and save graph
    print("\nGenerating visualization...")
    print("Legend:")
    print("  • Solid gray lines (→): References (this paper cites that paper)")
    print("  • Dashed purple lines (→): Citations (that paper cites this paper)")
    
    net = build_graph_with_scores(root_paper, scores_map)
    
    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)
    
    output_file = output_dir / "references_graph_specter2.html"
    net.write_html(str(output_file))
    print(f"✓ Graph saved to: {output_file}")
    
    # Save scores to CSV
    import csv
    csv_file = output_dir / "relevance_scores_specter2.csv"
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        if results:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)
    print(f"✓ Scores saved to: {csv_file}")
    
    print(f"\n{'='*100}")
    print("Done! Open the HTML file in your browser to explore the graph.")
    print(f"{'='*100}")