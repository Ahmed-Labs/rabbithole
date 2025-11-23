"""
Example script demonstrating LLM-based relevance scoring with explanations.

This script shows how to use LLM (OpenAI, Anthropic, or HuggingFace) to:
1. Compute semantic similarity scores between papers
2. Generate natural language explanations of why papers are similar

Usage:
    # Set your API key as environment variable
    export OPENAI_API_KEY="your-key-here"
    # or
    export ANTHROPIC_API_KEY="your-key-here"
    
    # Run the script
    python experiments/visualize_with_llm.py
"""

from pathlib import Path
from pyvis.network import Network

from paper_retrieval.paper_metadata import search, build_full_graph
from paper_retrieval.research_paper import ResearchPaper
from relevance_scoring import compute_relevance_scores, LLMScorer


def build_graph_with_llm_explanations(root: ResearchPaper, scores_map: dict):
    """Build network graph with LLM explanations in tooltips."""
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
    
    def add_paper(paper: ResearchPaper, depth: int = 0):
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
            llm_explanation = score_data.get("llm_explanation", "")
            edge_type = score_data.get("edge_type", "reference")
            
            color = get_color_by_score(relevance)
            edge_icon = "↓" if edge_type == "reference" else "↑"
            
            # Include LLM explanation prominently
            explanation_section = ""
            if llm_explanation:
                explanation_section = f"\n\n🤖 LLM Explanation:\n{llm_explanation}"
            
            score_info = (
                f"{edge_icon} {edge_type.upper()}\n"
                f"Relevance: {relevance:.3f}\n"
                f"Semantic (LLM): {semantic:.3f} | BibCoupling: {bib_coupling:.3f}\n"
                f"YearSim: {year_sim:.3f}\n"
                f"Year: {paper.year or 'N/A'} | Citations: {paper.citation_count or 0}"
                f"{explanation_section}"
            )
        
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
        for ref in paper.references:
            if ref.id not in seen_nodes:
                add_paper(ref, depth + 1)
            
            edge_label = f"{scores_map.get(ref.id, {}).get('relevance_score', 0):.2f}"
            net.add_edge(
                paper.id, 
                ref.id, 
                label=edge_label,
                dashes=False,
                color="#666666",
                arrows="to"
            )
            add_edges(ref, depth + 1)
        
        for cit in paper.citations:
            if cit.id not in seen_nodes:
                add_paper(cit, depth + 1)
            
            edge_label = f"{scores_map.get(cit.id, {}).get('relevance_score', 0):.2f}"
            net.add_edge(
                cit.id,
                paper.id,
                label=edge_label,
                dashes=[5, 5],
                color="#9333ea",
                arrows="to"
            )
            add_edges(cit, depth + 1)

    add_paper(root, 0)
    add_edges(root, 0)
    
    return net


def print_top_papers_with_explanations(results: list, top_n: int = 10):
    """Print top N papers with LLM explanations."""
    print(f"\n{'='*100}")
    print(f"TOP {top_n} MOST RELEVANT PAPERS (LLM-based scoring with explanations)")
    print(f"{'='*100}\n")
    
    references = [r for r in results if r.get('edge_type') == 'reference']
    citations = [r for r in results if r.get('edge_type') == 'citation']
    
    print(f"📚 REFERENCES:")
    print(f"{'─'*100}")
    for i, result in enumerate(references[:top_n], 1):
        print(f"{i}. {result['title'][:70]}")
        print(f"   └─ Relevance: {result['relevance_score']:.4f}")
        print(f"      ├─ Semantic (LLM): {result['semantic_similarity']:.4f}")
        print(f"      ├─ Bib. Coupling: {result['bibliographic_coupling']:.4f}")
        print(f"      ├─ Year Similarity: {result['year_similarity']:.4f}")
        print(f"      └─ Citation Score: {result['citation_score']:.4f}")
        if result.get('llm_explanation'):
            print(f"\n      💡 Explanation: {result['llm_explanation']}")
        print()
    
    print(f"\n📖 CITATIONS:")
    print(f"{'─'*100}")
    for i, result in enumerate(citations[:top_n], 1):
        print(f"{i}. {result['title'][:70]}")
        print(f"   └─ Relevance: {result['relevance_score']:.4f}")
        print(f"      ├─ Semantic (LLM): {result['semantic_similarity']:.4f}")
        print(f"      ├─ Bib. Coupling: {result['bibliographic_coupling']:.4f}")
        print(f"      ├─ Year Similarity: {result['year_similarity']:.4f}")
        print(f"      └─ Citation Score: {result['citation_score']:.4f}")
        if result.get('llm_explanation'):
            print(f"\n      💡 Explanation: {result['llm_explanation']}")
        print()


if __name__ == "__main__":
    # ============================================
    # CONFIGURATION - EDIT THESE VALUES
    # ============================================
    
    # Paper search query
    query = "antioxidants"  # Change to your search term
    
    # Graph building (start small to save API costs)
    depth = 1  # How many levels deep (1-2 recommended for LLM)
    max_per_level = 5  # Papers per level (5-10 recommended)
    include_citations = True
    
    # LLM Configuration
    llm_provider = "openai"  # Options: "openai", "anthropic", "huggingface"
    llm_model = "gpt-4o-mini"  # Cost-effective default
    # For Anthropic: use "claude-3-haiku-20240307"
    # For HuggingFace: use model name like "meta-llama/Llama-2-7b-chat-hf"
    
    # API Key (optional - can also set via environment variable)
    # Uncomment and set if you prefer to hardcode (not recommended):
    # api_key = "sk-proj-your-key-here"
    api_key = None  # Will use environment variable if None
    
    print("="*100)
    print("LLM-Based Paper Relevance Scoring")
    print("="*100)
    print(f"\nConfiguration:")
    print(f"  Provider: {llm_provider}")
    print(f"  Model: {llm_model}")
    print(f"  Query: {query}")
    print(f"  Depth: {depth}")
    print(f"  Max per level: {max_per_level}")
    print()
    
    # Search for papers
    papers = search(query)
    if not papers:
        print("No papers found for the query")
        exit()
    
    root_paper = papers[0]
    print(f"Root Paper: {root_paper.title}")
    print(f"Year: {root_paper.year or 'N/A'}")
    print(f"Citations: {root_paper.citation_count or 0}")
    print("="*100)
    
    # Build paper graph
    print(f"\nBuilding paper graph...")
    root_paper = build_full_graph(
        root_paper,
        depth=depth,
        max_per_level=max_per_level,
        include_citations=include_citations
    )
    
    # Initialize LLM scorer
    print(f"\nInitializing LLM scorer ({llm_provider})...")
    print("Note: Make sure you have set your API key as an environment variable!")
    print("  Windows: $env:OPENAI_API_KEY='your-key'")
    print("  Mac/Linux: export OPENAI_API_KEY='your-key'")
    print()
    
    try:
        llm_scorer = LLMScorer(
            provider=llm_provider,
            model=llm_model,
            api_key=api_key,  # Use provided key or None (will use env var)
            use_explanations=True
        )
    except Exception as e:
        print(f"Error initializing LLM scorer: {e}")
        print("\nMake sure you have:")
        print("  1. Installed the required package (pip install openai or pip install anthropic)")
        print("  2. Set the API key as environment variable (OPENAI_API_KEY or ANTHROPIC_API_KEY)")
        exit(1)
    
    # Compute relevance scores with LLM
    print("\nComputing relevance scores with LLM...")
    print("(This may take a while and incur API costs)")
    print("(Progress will be shown as papers are scored)\n")
    
    results, scorer = compute_relevance_scores(
        root_paper,
        use_llm=True,
        llm_scorer=llm_scorer,
        max_depth=depth,
        use_cache=True
    )
    
    # Create lookup map for visualization
    scores_map = {r["paper_id"]: r for r in results}
    
    # Print top papers with explanations
    print_top_papers_with_explanations(results, top_n=10)
    
    # Build and save graph
    print("\nGenerating visualization with LLM explanations...")
    net = build_graph_with_llm_explanations(root_paper, scores_map)
    
    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)
    
    output_file = output_dir / "references_graph_llm.html"
    net.write_html(str(output_file))
    print(f"✓ Graph saved to: {output_file}")
    
    # Save scores to CSV (including explanations)
    import csv
    csv_file = output_dir / "relevance_scores_llm.csv"
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        if results:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)
    print(f"✓ Scores saved to: {csv_file}")
    
    print(f"\n{'='*100}")
    print("Done! Open the HTML file in your browser to explore the graph.")
    print("Hover over nodes to see LLM explanations in tooltips.")
    print(f"{'='*100}")

