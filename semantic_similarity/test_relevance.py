"""
Test script demonstrating relevance scoring as per the diagram:
X → A → B → C
    └────→ C (direct path with 0.8 * 0.6 = 0.48)
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from paper_retrieval.research_paper import ResearchPaper
from semantic_similarity.relevance_scorer import RelevanceScorer


def create_mock_papers():
    """Create mock papers for testing the relevance scoring logic."""
    
    # Paper A (root) - about machine learning
    paper_a = ResearchPaper(
        id="A",
        url="http://example.com/a",
        title="Deep Learning for Image Classification",
        authors=[{"name": "John Doe"}],
        abstract="This paper presents a novel deep learning approach for image classification using convolutional neural networks."
    )
    
    # Paper B - closely related (neural networks)
    paper_b = ResearchPaper(
        id="B",
        url="http://example.com/b",
        title="Convolutional Neural Networks: A Comprehensive Review",
        authors=[{"name": "Jane Smith"}],
        abstract="A comprehensive survey of convolutional neural network architectures and their applications in computer vision."
    )
    
    # Paper C - somewhat related (image processing)
    paper_c = ResearchPaper(
        id="C",
        url="http://example.com/c",
        title="Image Preprocessing Techniques for Better Recognition",
        authors=[{"name": "Bob Johnson"}],
        abstract="This work explores various image preprocessing techniques including normalization and augmentation for improved recognition accuracy."
    )
    
    # Paper D - less related (general optimization)
    paper_d = ResearchPaper(
        id="D",
        url="http://example.com/d",
        title="Optimization Algorithms in Machine Learning",
        authors=[{"name": "Alice Brown"}],
        abstract="An overview of gradient descent and other optimization algorithms used in training machine learning models."
    )
    
    # Set up reference structure
    # A → B → C
    # A → D
    paper_a.references = [paper_b, paper_d]
    paper_b.references = [paper_c]
    
    return paper_a


def test_basic_similarity():
    """Test basic semantic similarity between two papers."""
    print("="*80)
    print("TEST 1: Basic Semantic Similarity")
    print("="*80)
    
    scorer = RelevanceScorer()
    
    paper_a = create_mock_papers()
    paper_b = paper_a.references[0]  # CNNs paper
    paper_d = paper_a.references[1]  # Optimization paper
    
    sim_ab = scorer.score_paper_relevance(paper_a, paper_b)
    sim_ad = scorer.score_paper_relevance(paper_a, paper_d)
    
    print(f"\nPaper A: {paper_a.title}")
    print(f"Paper B: {paper_b.title}")
    print(f"Similarity A↔B: {sim_ab:.4f}")
    print(f"\nPaper D: {paper_d.title}")
    print(f"Similarity A↔D: {sim_ad:.4f}")
    print(f"\nExpected: B should be more similar to A than D")
    print(f"Result: {'✓ PASS' if sim_ab > sim_ad else '✗ FAIL'}")


def test_path_probability():
    """Test path probability calculation through reference chain."""
    print("\n" + "="*80)
    print("TEST 2: Path Probability (A → B → C vs A → D)")
    print("="*80)
    
    scorer = RelevanceScorer()
    paper_a = create_mock_papers()
    
    results = scorer.score_references_recursive(paper_a, depth=0, max_depth=2)
    
    print(f"\nRoot Paper A: {paper_a.title}\n")
    
    for result in results:
        print(f"Paper: {result['title'][:50]}")
        print(f"  Depth: {result['depth']}")
        print(f"  Semantic Similarity: {result['semantic_similarity']:.4f}")
        print(f"  Path Probability: {result['path_probability']:.4f}")
        print(f"  Combined Relevance: {result['relevance_score']:.4f}")
        print()
    
    # Find specific papers
    paper_b_result = next((r for r in results if r['paper_id'] == 'B'), None)
    paper_c_result = next((r for r in results if r['paper_id'] == 'C'), None)
    
    if paper_b_result and paper_c_result:
        print(f"Path A→B probability: {paper_b_result['path_probability']:.2f} (expected: 0.80)")
        print(f"Path A→B→C probability: {paper_c_result['path_probability']:.2f} (expected: 0.48)")
        
        expected_c_prob = 0.8 * 0.6
        actual_c_prob = paper_c_result['path_probability']
        
        print(f"\n{'✓ PASS' if abs(actual_c_prob - expected_c_prob) < 0.01 else '✗ FAIL'}")


def test_relevance_ranking():
    """Test that papers are ranked by combined relevance score."""
    print("\n" + "="*80)
    print("TEST 3: Relevance Ranking")
    print("="*80)
    
    scorer = RelevanceScorer()
    paper_a = create_mock_papers()
    
    results = scorer.score_references_recursive(paper_a, depth=0, max_depth=2)
    results.sort(key=lambda x: x['relevance_score'], reverse=True)
    
    print(f"\nPapers ranked by relevance to root paper:\n")
    for i, result in enumerate(results, 1):
        print(f"{i}. {result['title'][:50]}")
        print(f"   Score: {result['relevance_score']:.4f} "
              f"(Sem: {result['semantic_similarity']:.4f} × "
              f"Path: {result['path_probability']:.4f})")
    
    print("\nExpected: Paper B (direct ref, high similarity) should rank highest")
    print(f"Result: {'✓ PASS' if results[0]['paper_id'] == 'B' else '✗ FAIL'}")


if __name__ == "__main__":
    print("\nRunning Relevance Scoring Tests\n")
    
    test_basic_similarity()
    test_path_probability()
    test_relevance_ranking()
    
    print("\n" + "="*80)
    print("All tests completed!")
    print("="*80)
    