from typing import Callable, List, Optional

import numpy as np
import torch
from adapters import AutoAdapterModel
from sklearn.metrics.pairwise import cosine_similarity
from transformers import AutoTokenizer

from relevance_scoring.embedding_cache import EmbeddingCache


class Embedder:
    def __init__(
        self,
        base_model: str = "allenai/specter2_base",
        adapter_name: str = "allenai/specter2",
        cache_dir: str = ".embedding_cache",
    ):
        print(f"Loading SPECTER2 base model: {base_model}")
        print("(This may take a few minutes on first run)")

        # Load tokenizer and model
        self.tokenizer = AutoTokenizer.from_pretrained(base_model)
        self.model = AutoAdapterModel.from_pretrained(base_model)

        # Load and activate the proximity adapter for paper similarity
        print(f"Loading adapter: {adapter_name}")
        self.model.load_adapter(adapter_name, source="hf", set_active=True)

        self.model_name = f"{base_model}+{adapter_name}"
        self.cache = EmbeddingCache(cache_dir)

        # Move to GPU if available
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model.to(self.device)

        print(f"✓ Model loaded successfully on {self.device}")

    def embed(self, text: str, cache_key: Optional[str] = None) -> np.ndarray:
        """
        Compute embedding for a text string with caching.
        """
        # Retrieve embedding from cache if present
        if cache_key:
            cached = self.cache.get(cache_key)
            if cached is not None:
                return cached

        # Tokenize
        inputs = self.tokenizer(
            [text],
            padding=True,
            truncation=True,
            return_tensors="pt",
            max_length=512,
            return_token_type_ids=False,
        )

        # Move to device
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        # Get embeddings
        with torch.no_grad():
            output = self.model(**inputs)
            # Take the [CLS] token embedding (first token)
            embedding = output.last_hidden_state[:, 0, :].cpu().numpy()[0]

        if cache_key:
            self.cache.set(cache_key, embedding)

        return embedding

    def embed_chunks(
        self, chunks: List[str], cache_key: Optional[str] = None
    ) -> np.ndarray:
        # Try cache first
        if cache_key:
            cached = self.cache.get(cache_key)
            if cached is not None:
                return cached

        if not chunks:
            fallback = self.embed("", cache_key)
            return fallback

        # Tokenize all chunks together
        inputs = self.tokenizer(
            chunks,
            padding=True,
            truncation=True,
            max_length=512,
            return_tensors="pt",
            return_token_type_ids=False,
        )
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        # Single forward pass for all chunks
        with torch.no_grad():
            outputs = self.model(**inputs)
            # [batch, seq, hidden] → [batch, hidden] using CLS
            embeddings = outputs.last_hidden_state[:, 0, :].cpu().numpy()

        # Max pool across chunks
        max_pool_embedding = embeddings.max(axis=0)

        if cache_key:
            self.cache.set(cache_key, max_pool_embedding)

        return max_pool_embedding

    def lazy_embed_chunks(
        self,
        get_chunks: Callable[[], List[str]],
        cache_key: Optional[str] = None,
    ) -> np.ndarray:
        # Check cache before attempting to fetch full text
        if cache_key:
            cached = self.cache.get(cache_key)
            if cached is not None:
                return cached

        chunks = get_chunks()
        return self.embed_chunks(chunks, cache_key=cache_key)

    def compute_similarity(
        self, embedding1: np.ndarray, embedding2: np.ndarray
    ) -> float:
        """Compute cosine similarity between two embeddings."""
        emb1 = embedding1.reshape(1, -1)
        emb2 = embedding2.reshape(1, -1)
        return float(cosine_similarity(emb1, emb2)[0][0])
