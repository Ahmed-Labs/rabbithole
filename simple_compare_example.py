"""
Simple example: Compare two papers directly.

This shows the core comparison code - you can use this as a template.
"""

from paper_retrieval.paper_metadata import search
from paper_retrieval.research_paper import ResearchPaper
from relevance_scoring import LLMScorer

# ============================================
# OPTION 1: Search for papers and compare
# ============================================

# Search for papers
papers1 = search("science mapping tools", limit=5)
papers2 = search("bibliometric analysis", limit=5)

# Select papers to compare
paper1 = papers1[0]  # First result from first search
paper2 = papers2[0]  # First result from second search

print(f"Comparing:")
print(f"  Paper 1: {paper1.title}")
print(f"  Paper 2: {paper2.title}")

# Initialize LLM scorer
llm_scorer = LLMScorer(
    provider="openai",      # or "anthropic"
    model="gpt-4o-mini",    # Cost-effective
    use_explanations=True
)

# Compare the papers
result = llm_scorer.compute_score(paper1, paper2)

# Display results
print(f"\nSimilarity Score: {result['relevance_score']:.2f} (on 0.0-1.0 scale)")
print(f"Equivalent to: {result['relevance_score']*10:.1f}/10")
print(f"\nExplanation:\n{result.get('explanation', 'N/A')}")


# ============================================
# OPTION 2: Manually create papers
# ============================================

# You can also create papers manually:
paper1_manual = ResearchPaper(
    id="manual1",
    url="",
    title="Machine Learning for Image Classification",
    authors=[{"name": "John Doe"}, {"name": "Jane Smith"}],
    abstract="This paper presents a deep learning approach for image classification using convolutional neural networks.",
    year=2020,
    citation_count=100
)

paper2_manual = ResearchPaper(
    id="manual2",
    url="",
    title="Convolutional Neural Networks: A Survey",
    authors=[{"name": "Alice Brown"}],
    abstract="A comprehensive survey of convolutional neural network architectures and their applications in computer vision.",
    year=2021,
    citation_count=200
)

# Compare manually created papers
result_manual = llm_scorer.compute_score(paper1_manual, paper2_manual)
print(f"\n\nManual comparison score: {result_manual['relevance_score']:.2f}")


# ============================================
# WHERE IS THE COMPARISON CODE?
# ============================================
# 
# The core comparison happens in:
# - relevance_scoring/llm_scorer.py
#   - Method: LLMScorer.compute_score(paper1, paper2)
#   - This creates a prompt and calls the LLM API
#   - Returns: {"relevance_score": float, "explanation": str}
#
# You can also use:
# - relevance_scoring/relevance_scorer.py
#   - Method: RelevanceScorer.compute_score(paper1, paper2)
#   - This uses SPECTER2 embeddings (no LLM, no API needed)
#   - Returns: RelevanceScore object with multiple factors
#
# ============================================

