"""
Simple script to compare two papers manually.

You can:
1. Search for papers and select which ones to compare
2. Manually enter paper information
3. Compare papers by their Semantic Scholar IDs

Usage:
    python compare_two_papers.py
"""

import os
from pathlib import Path

# Try to load .env file if it exists
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        # API key loaded from .env file
except ImportError:
    # python-dotenv not installed, will use environment variables only
    pass
except Exception as e:
    # If .env file has issues, continue with environment variables
    pass

from paper_retrieval.paper_metadata import search, get_paper_by_id
from paper_retrieval.research_paper import ResearchPaper
from relevance_scoring import LLMScorer, RelevanceScorer


def create_paper_manually():
    """Create a paper object from manual input."""
    print("\nEnter paper information:")
    title = input("Title: ").strip()
    authors_str = input("Authors (comma-separated): ").strip()
    authors = [{"name": name.strip()} for name in authors_str.split(",") if name.strip()]
    
    abstract = input("Abstract: ").strip()
    year_str = input("Year (optional, press Enter to skip): ").strip()
    year = int(year_str) if year_str else None
    
    citations_str = input("Citation count (optional, press Enter to skip): ").strip()
    citation_count = int(citations_str) if citations_str else None
    
    return ResearchPaper(
        id=f"manual_{hash(title)}",
        url="",
        title=title,
        authors=authors,
        abstract=abstract,
        year=year,
        citation_count=citation_count
    )


def search_and_select_paper(query: str = None):
    """Search for papers and let user select one."""
    if query is None:
        query = input("\nEnter search query: ").strip()
    
    print(f"\nSearching for: {query}...")
    papers = search(query, limit=10)
    
    if not papers:
        print("No papers found. Try a different query.")
        return None
    
    print(f"\nFound {len(papers)} papers:")
    for i, paper in enumerate(papers, 1):
        authors_str = ", ".join([a.get("name", "") for a in paper.authors[:2]])
        if len(paper.authors) > 2:
            authors_str += " et al."
        print(f"{i}. {paper.title[:70]}")
        print(f"   {authors_str} ({paper.year or 'N/A'})")
    
    while True:
        try:
            choice = input(f"\nSelect paper (1-{len(papers)}) or 'q' to cancel: ").strip()
            if choice.lower() == 'q':
                return None
            idx = int(choice) - 1
            if 0 <= idx < len(papers):
                return papers[idx]
            else:
                print(f"Please enter a number between 1 and {len(papers)}")
        except ValueError:
            print("Please enter a valid number or 'q' to cancel")


def compare_papers(paper1: ResearchPaper, paper2: ResearchPaper, use_llm: bool = True):
    """Compare two papers and display results."""
    print("\n" + "="*80)
    print("COMPARING PAPERS")
    print("="*80)
    
    print(f"\n📄 Paper 1:")
    print(f"   Title: {paper1.title}")
    authors1 = ", ".join([a.get("name", "") for a in paper1.authors[:3]])
    if len(paper1.authors) > 3:
        authors1 += " et al."
    print(f"   Authors: {authors1}")
    print(f"   Year: {paper1.year or 'N/A'}")
    print(f"   Abstract: {paper1.abstract[:200]}..." if len(paper1.abstract) > 200 else f"   Abstract: {paper1.abstract}")
    
    print(f"\n📄 Paper 2:")
    print(f"   Title: {paper2.title}")
    authors2 = ", ".join([a.get("name", "") for a in paper2.authors[:3]])
    if len(paper2.authors) > 3:
        authors2 += " et al."
    print(f"   Authors: {authors2}")
    print(f"   Year: {paper2.year or 'N/A'}")
    print(f"   Abstract: {paper2.abstract[:200]}..." if len(paper2.abstract) > 200 else f"   Abstract: {paper2.abstract}")
    
    print("\n" + "="*80)
    print("COMPUTING SIMILARITY...")
    print("="*80)
    
    # This function now only supports LLM scoring (use_llm must be True)
    if not use_llm:
        raise ValueError("This function only supports LLM scoring. use_llm must be True.")
    
    if use_llm:
        # Use LLM for comparison (pure LLM scoring only)
        provider = "openai" if os.getenv("OPENAI_API_KEY") else "anthropic"
        model = "gpt-4o-mini" if provider == "openai" else "claude-3-haiku-20240307"
        
        print(f"\nUsing LLM ({provider}) for comparison...")
        print("(Pure LLM-based similarity score and explanation)")
        print("(This may take 10-20 seconds)")
        
        try:
            llm_scorer = LLMScorer(
                provider=provider,
                model=model,
                use_explanations=True  # Always get explanation
            )
            
            # Pure LLM scoring - single prompt returns both score and explanation
            result = llm_scorer.compute_score(paper1, paper2)
            score = result["relevance_score"]
            explanation = result.get("explanation", "")
            
            print("\n" + "="*80)
            print("RESULTS (Pure LLM Scoring)")
            print("="*80)
            print(f"\n🎯 Similarity Score: {score:.3f} (on 0.0-1.0 scale)")
            print(f"   Equivalent to: {score*10:.1f}/10")
            
            if explanation:
                print(f"\n💡 Explanation:")
                print(f"   {explanation}")
            else:
                print("\n⚠️  No explanation provided by LLM")
            
        except Exception as e:
            print(f"\n❌ LLM comparison failed: {e}")
            print("\nPlease check:")
            print("  1. API key is set correctly")
            print("  2. You have credits/balance in your account")
            print("  3. Internet connection is working")
            print("\nCannot proceed without LLM scoring.")
            return
    
    print("\n" + "="*80)


def main():
    print("="*80)
    print("PAPER COMPARISON TOOL")
    print("="*80)
    print("\nThis tool lets you compare two research papers.")
    print("You can search for papers, enter by ID, or enter manually.\n")
    
    # Get first paper
    print("PAPER 1:")
    print("1. Search for paper")
    print("2. Enter by Semantic Scholar ID")
    print("3. Enter manually")
    choice1 = input("Choose option (1, 2, or 3): ").strip()
    
    if choice1 == "1":
        paper1 = search_and_select_paper()
        if paper1 is None:
            print("Cancelled.")
            return
    elif choice1 == "2":
        paper_id = input("Enter Semantic Scholar paper ID: ").strip()
        paper1 = get_paper_by_id(paper_id)
        if paper1 is None:
            print("Failed to fetch paper. Please check the ID and try again.")
            return
        print(f"✓ Found: {paper1.title}")
    else:
        paper1 = create_paper_manually()
    
    # Get second paper
    print("\nPAPER 2:")
    print("1. Search for paper")
    print("2. Enter by Semantic Scholar ID")
    print("3. Enter manually")
    choice2 = input("Choose option (1, 2, or 3): ").strip()
    
    if choice2 == "1":
        paper2 = search_and_select_paper()
        if paper2 is None:
            print("Cancelled.")
            return
    elif choice2 == "2":
        paper_id = input("Enter Semantic Scholar paper ID: ").strip()
        paper2 = get_paper_by_id(paper_id)
        if paper2 is None:
            print("Failed to fetch paper. Please check the ID and try again.")
            return
        print(f"✓ Found: {paper2.title}")
    else:
        paper2 = create_paper_manually()
    
    # Force LLM-only mode (no SPECTER2 fallback)
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
    
    if not api_key:
        print("\n" + "="*80)
        print("⚠️  API KEY REQUIRED FOR PURE LLM SCORING")
        print("="*80)
        print("\nNo API key found. This program uses pure LLM scoring only.")
        print("\nTo set your API key:")
        print("  PowerShell: $env:OPENAI_API_KEY='your-key-here'")
        print("  CMD: set OPENAI_API_KEY=your-key-here")
        print("\nExiting...")
        return
    
    print("\n" + "="*80)
    print("SCORING METHOD: Pure LLM Only")
    print("="*80)
    print("\n✓ API key detected. Using pure LLM scoring.")
    print("  (Single prompt returns both similarity score and explanation)")
    print()
    
    # Compare papers (force LLM-only)
    compare_papers(paper1, paper2, use_llm=True)
    
    # Ask if user wants to compare again
    again = input("\nCompare another pair? (y/n): ").strip().lower()
    if again == 'y':
        main()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nCancelled by user.")
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()

