"""
Quick comparison script to show difference between generic embeddings and SPECTER2.
Run this to validate that SPECTER2 performs better for scientific papers.
"""

import numpy as np
import torch
from adapters import AutoAdapterModel
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from transformers import AutoTokenizer


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
        "PHYS": "Quantum entanglement and non-locality in quantum mechanical systems",
    }

    embeddings = {
        name: model.encode(text, convert_to_numpy=True) for name, text in papers.items()
    }

    # Compare ML1 with others
    print("Similarity to ML1 (CNN image classification):\n")
    ml1_emb = embeddings["ML1"].reshape(1, -1)

    comparisons = []
    for name, emb in embeddings.items():
        if name == "ML1":
            continue
        similarity = float(cosine_similarity(ml1_emb, emb.reshape(1, -1))[0][0])
        comparisons.append((name, similarity))

    comparisons.sort(key=lambda x: x[1], reverse=True)

    for name, sim in comparisons:
        paper_type = "✓ Related" if name.startswith("ML") else "✗ Unrelated"
        print(f"{name:6} ({paper_type:12}): {sim:.4f} - {papers[name][:60]}...")

    # Check if ranking is correct
    ml_scores = [s for n, s in comparisons if n.startswith("ML")]
    non_ml_scores = [s for n, s in comparisons if not n.startswith("ML")]

    if ml_scores and non_ml_scores and min(ml_scores) > max(non_ml_scores):
        print(f"\n✓ GOOD: Related papers scored higher than unrelated papers")
    else:
        print(f"\n⚠ MIXED: Some scoring overlap between related/unrelated papers")


def test_specter2():
    """Test SPECTER2 with proximity adapter."""
    print(f"\n{'='*80}")
    print(f"Testing: SPECTER2 (allenai/specter2_base + proximity adapter)")
    print(f"{'='*80}\n")

    # Load model
    print("Loading SPECTER2...")
    tokenizer = AutoTokenizer.from_pretrained("allenai/specter2_base")
    model = AutoAdapterModel.from_pretrained("allenai/specter2_base")
    model.load_adapter("allenai/specter2", source="hf", set_active=True)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model.to(device)
    print(f"Model loaded on {device}\n")

    # Test papers (SPECTER2 format with SEP token)
    papers = {
        "ML1": f"Deep learning methods for image classification using convolutional neural networks",
        "ML2": f"Convolutional neural networks for computer vision tasks and image recognition",
        "ML3": f"Gradient descent optimization algorithms for training deep neural networks",
        "BIO": f"CRISPR gene editing techniques for therapeutic applications in cancer treatment",
        "PHYS": f"Quantum entanglement and non-locality in quantum mechanical systems",
    }

    # Compute embeddings
    embeddings = {}
    for name, text in papers.items():
        inputs = tokenizer(
            [text],
            padding=True,
            truncation=True,
            return_tensors="pt",
            max_length=512,
            return_token_type_ids=False,
        )
        inputs = {k: v.to(device) for k, v in inputs.items()}

        with torch.no_grad():
            output = model(**inputs)
            embedding = output.last_hidden_state[:, 0, :].cpu().numpy()[0]
            embeddings[name] = embedding

    # Compare ML1 with others
    print("Similarity to ML1 (CNN image classification):\n")
    ml1_emb = embeddings["ML1"].reshape(1, -1)

    comparisons = []
    for name, emb in embeddings.items():
        if name == "ML1":
            continue
        similarity = float(cosine_similarity(ml1_emb, emb.reshape(1, -1))[0][0])
        comparisons.append((name, similarity))

    comparisons.sort(key=lambda x: x[1], reverse=True)

    for name, sim in comparisons:
        paper_type = "✓ Related" if name.startswith("ML") else "✗ Unrelated"
        print(f"{name:6} ({paper_type:12}): {sim:.4f} - {papers[name][:60]}...")

    # Check if ranking is correct
    ml_scores = [s for n, s in comparisons if n.startswith("ML")]
    non_ml_scores = [s for n, s in comparisons if not n.startswith("ML")]

    if ml_scores and non_ml_scores and min(ml_scores) > max(non_ml_scores):
        print(f"\n✓ EXCELLENT: Related papers scored higher than unrelated papers")
        print(
            f"  Min ML score: {min(ml_scores):.4f}, Max non-ML score: {max(non_ml_scores):.4f}"
        )
    else:
        print(f"\n⚠ MIXED: Some scoring overlap between related/unrelated papers")


if __name__ == "__main__":
    print("Comparing embedding models for scientific paper similarity")
    print("This helps validate SPECTER2 performs better than generic models\n")

    # Test generic model
    test_generic_embedding("all-MiniLM-L6-v2")

    # Test SPECTER2
    print("\n" + "=" * 80)
    input("Press Enter to test SPECTER2 (will download ~450MB model if not cached)...")
    test_specter2()

    print("\n" + "=" * 80)
    print("CONCLUSION:")
    print(
        "SPECTER2 should show clearer separation between related and unrelated papers"
    )
    print("This is because it's trained on citation graphs from 6M+ scientific papers")
    print("=" * 80)
