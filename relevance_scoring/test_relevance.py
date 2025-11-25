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
        abstract="We explore various image preprocessing methods that improve recognition accuracy in computer vision systems."
    )
    
    # Paper D - unrelated (biology)
    paper_d = ResearchPaper(
        id="D",
        url="http://example.com/d",
        title="CRISPR Gene Editing in Cancer Treatment",
        authors=[{"name": "Alice Williams"}],
        abstract="This study investigates the use of CRISPR technology for targeted cancer therapy and gene modification."
    )
    
    # Set up references (A references B and C)
    paper_a.references = [paper_b, paper_c]
    paper_b.references = []
    paper_c.references = []
    paper_d.references = []
    
    return paper_a, paper_b, paper_c, paper_d


def test_relevance_scoring():
    """Test the relevance scoring system with mock papers."""
    print("=" * 80)
    print("Testing Relevance Scoring System")
    print("=" * 80)
    
    # Create mock papers
    root, paper_b, paper_c, paper_d = create_mock_papers()
    
    # Initialize scorer (without LLM for testing)
    scorer = RelevanceScorer(llm_scorer=None)
    
    # Test scoring
    print(f"\nRoot Paper: {root.title}")
    print(f"Abstract: {root.abstract[:60]}...")
    print("\n" + "-" * 80)
    
    test_papers = [
        ("Paper B (Related - Neural Networks)", paper_b),
        ("Paper C (Somewhat Related - Image Processing)", paper_c),
        ("Paper D (Unrelated - Biology)", paper_d),
    ]
    
    for name, paper in test_papers:
        print(f"\n{name}:")
        print(f"  Title: {paper.title}")
        print(f"  Abstract: {paper.abstract[:60]}...")
        
        score = scorer.compute_score(root, paper)
        if score:
            print(f"\n  Relevance Score Breakdown:")
            print(f"    Combined: {score.combined:.4f}")
            print(f"    Semantic Similarity: {score.semantic_similarity:.4f}")
            print(f"    Bibliographic Coupling: {score.bibliographic_coupling:.4f}")
            print(f"    Year Similarity: {score.year_similarity:.4f}")
            print(f"    Citation Score: {score.citation_score:.4f}")
        else:
            print("  Could not compute score")
    
    print("\n" + "=" * 80)
    print("Test Complete")
    print("=" * 80)


if __name__ == "__main__":
    test_relevance_scoring()

