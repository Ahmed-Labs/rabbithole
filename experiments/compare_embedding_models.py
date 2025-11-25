"""
Quick comparison script to show difference between generic embeddings and SPECTER2.
Run this to validate that SPECTER2 performs better for scientific papers.
"""

import torch
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer
from adapters import AutoAdapterModel
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np


def test_generic_embedding(model_name: str):
    """Test generic sentence-transformers model."""
    print(f"\n{'='*80}")
    print(f"Testing: {model_name}")
    print(f"{'='*80}\n")
    
    model = SentenceTransformer(model_name)
    
    # Test papers
    papers = {
        "ML1": "Deep learning methods for image classification using convolutional neural networks",
        "ML2": "Convolutional neural networks for computer vision tasks and image recognition",
        "ML3": "Gradient descent optimization algorithms for training deep neural networks",
        "BIO": "CRISPR gene editing techniques for therapeutic applications in cancer treatment",
        "PHYS": "Quantum entanglement and non-locality in quantum mechanical systems"
    }
    
    # Generate embeddings
    embeddings = {}
    for name, text in papers.items():
        embeddings[name] = model.encode(text)
    
    # Compute similarities
    print("Similarity Matrix:")
    print(f"{'':>6}", end="")
    for name in papers.keys():
        print(f"{name:>8}", end="")
    print()
    
    for name1 in papers.keys():
        print(f"{name1:>6}", end="")
        for name2 in papers.keys():
            sim = cosine_similarity(
                embeddings[name1].reshape(1, -1),
                embeddings[name2].reshape(1, -1)
            )[0][0]
            print(f"{sim:>8.3f}", end="")
        print()
    
    # Expected: ML1 and ML2 should be most similar
    ml1_ml2_sim = cosine_similarity(
        embeddings["ML1"].reshape(1, -1),
        embeddings["ML2"].reshape(1, -1)
    )[0][0]
    
    ml1_bio_sim = cosine_similarity(
        embeddings["ML1"].reshape(1, -1),
        embeddings["BIO"].reshape(1, -1)
    )[0][0]
    
    print(f"\nKey Comparison:")
    print(f"  ML1 vs ML2 (both about CNNs): {ml1_ml2_sim:.3f}")
    print(f"  ML1 vs BIO (unrelated): {ml1_bio_sim:.3f}")
    print(f"  Difference: {ml1_ml2_sim - ml1_bio_sim:.3f}")
    print(f"  {'✓ Good separation' if ml1_ml2_sim > ml1_bio_sim else '✗ Poor separation'}")


def test_specter2():
    """Test SPECTER2 model (specialized for scientific papers)."""
    print(f"\n{'='*80}")
    print("Testing: SPECTER2 (allenai/specter2)")
    print(f"{'='*80}\n")
    
    from relevance_scoring.embedder import Embedder
    
    embedder = Embedder()
    
    # Test papers (same as above)
    papers = {
        "ML1": "Deep learning methods for image classification using convolutional neural networks",
        "ML2": "Convolutional neural networks for computer vision tasks and image recognition",
        "ML3": "Gradient descent optimization algorithms for training deep neural networks",
        "BIO": "CRISPR gene editing techniques for therapeutic applications in cancer treatment",
        "PHYS": "Quantum entanglement and non-locality in quantum mechanical systems"
    }
    
    # Generate embeddings
    embeddings = {}
    for name, text in papers.items():
        embeddings[name] = embedder.embed(text)
    
    # Compute similarities
    print("Similarity Matrix:")
    print(f"{'':>6}", end="")
    for name in papers.keys():
        print(f"{name:>8}", end="")
    print()
    
    for name1 in papers.keys():
        print(f"{name1:>6}", end="")
        for name2 in papers.keys():
            sim = cosine_similarity(
                embeddings[name1].reshape(1, -1),
                embeddings[name2].reshape(1, -1)
            )[0][0]
            print(f"{sim:>8.3f}", end="")
        print()
    
    # Expected: ML1 and ML2 should be most similar
    ml1_ml2_sim = cosine_similarity(
        embeddings["ML1"].reshape(1, -1),
        embeddings["ML2"].reshape(1, -1)
    )[0][0]
    
    ml1_bio_sim = cosine_similarity(
        embeddings["ML1"].reshape(1, -1),
        embeddings["BIO"].reshape(1, -1)
    )[0][0]
    
    print(f"\nKey Comparison:")
    print(f"  ML1 vs ML2 (both about CNNs): {ml1_ml2_sim:.3f}")
    print(f"  ML1 vs BIO (unrelated): {ml1_bio_sim:.3f}")
    print(f"  Difference: {ml1_ml2_sim - ml1_bio_sim:.3f}")
    print(f"  {'✓ Good separation' if ml1_ml2_sim > ml1_bio_sim else '✗ Poor separation'}")


if __name__ == "__main__":
    print("=" * 80)
    print("Embedding Model Comparison")
    print("=" * 80)
    print("\nThis script compares generic embeddings vs SPECTER2 for scientific papers.")
    print("SPECTER2 should show better separation between related and unrelated papers.\n")
    
    # Test generic model
    test_generic_embedding("all-MiniLM-L6-v2")
    
    # Test SPECTER2
    test_specter2()
    
    print("\n" + "=" * 80)
    print("Comparison Complete")
    print("=" * 80)
    print("\nSPECTER2 should show:")
    print("  - Higher similarity between related papers (ML1 vs ML2)")
    print("  - Lower similarity between unrelated papers (ML1 vs BIO)")
    print("  - Better overall separation for scientific content")

