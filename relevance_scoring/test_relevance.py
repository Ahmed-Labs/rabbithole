from paper_retrieval import ResearchPaper
from relevance_scoring.relevance_scorer import RelevanceScorer


def create_mock_papers():
    """Create mock papers for testing the relevance scoring logic."""

    # Paper A (root) - about machine learning
    paper_a = ResearchPaper(
        id="A",
        url="http://example.com/a",
        title="Deep Learning for Image Classification",
        authors=[{"name": "John Doe"}],
        abstract="This paper presents a novel deep learning approach for image classification using convolutional neural networks.",
    )

    # Paper B - closely related (neural networks)
    paper_b = ResearchPaper(
        id="B",
        url="http://example.com/b",
        title="Convolutional Neural Networks: A Comprehensive Review",
        authors=[{"name": "Jane Smith"}],
        abstract="A comprehensive survey of convolutional neural network architectures and their applications in computer vision.",
    )

    # Paper C - somewhat related (image processing)
    paper_c = ResearchPaper(
        id="C",
        url="http://example.com/c",
        title="Image Preprocessing Techniques for Better Recognition",
        authors=[{"name": "Bob Johnson"}],
        abstract="This work explores various image preprocessing techniques including normalization and augmentation for improved recognition accuracy.",
    )

    # Paper D - less related (general optimization)
    paper_d = ResearchPaper(
        id="D",
        url="http://example.com/d",
        title="Optimization Algorithms in Machine Learning",
        authors=[{"name": "Alice Brown"}],
        abstract="An overview of gradient descent and other optimization algorithms used in training machine learning models.",
    )

    # Set up reference structure
    # A → B → C
    # A → D
    paper_a.references = [paper_b, paper_d]
    paper_b.references = [paper_c]

    return paper_a


def test_basic_similarity():
    """Test basic semantic similarity between two papers."""
    print("=" * 80)
    print("TEST 1: Basic Semantic Similarity")
    print("=" * 80)

    scorer = RelevanceScorer()

    paper_a = create_mock_papers()
    paper_b = paper_a.references[0]  # CNNs paper
    paper_d = paper_a.references[1]  # Optimization paper

    sim_ab = scorer.compute_score(paper_a, paper_b).combined
    sim_ad = scorer.compute_score(paper_a, paper_d).combined

    print(f"\nPaper A: {paper_a.title}")
    print(f"Paper B: {paper_b.title}")
    print(f"Similarity A↔B: {sim_ab:.4f}")
    print(f"\nPaper D: {paper_d.title}")
    print(f"Similarity A↔D: {sim_ad:.4f}")
    print(f"\nExpected: B should be more similar to A than D")
    print(f"Result: {'✓ PASS' if sim_ab > sim_ad else '✗ FAIL'}")


def test_relevance_ranking():
    """Test that papers are ranked by combined relevance score."""
    print("\n" + "=" * 80)
    print("TEST 2: Relevance Ranking")
    print("=" * 80)

    scorer = RelevanceScorer()
    paper_a = create_mock_papers()

    results = scorer.compute_relevance_edges(paper_a)
    results.sort(key=lambda x: x.relevance_score.combined, reverse=True)

    print(f"\nPapers ranked by relevance to root paper:\n")
    for i, edge in enumerate(results, 1):
        print(f"{i}. ID: {edge.dest_id}")
        print(f"   Score: {edge.relevance_score.combined}")
        print(f"   Semantic Similarity: {edge.relevance_score.semantic_similarity}")

    print("\nExpected: Paper B (direct ref, high similarity) should rank highest")
    print(f"Result: {'✓ PASS' if results[0].dest_id == 'B' else '✗ FAIL'}")


if __name__ == "__main__":
    print("\nRunning Relevance Scoring Tests\n")

    test_basic_similarity()
    test_relevance_ranking()

    print("\n" + "=" * 80)
    print("All tests completed!")
    print("=" * 80)
