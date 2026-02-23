import pickle
from pathlib import Path
from typing import Optional

import numpy as np


class EmbeddingStore:
    """Simple file-based cache for paper embeddings."""

    def __init__(self, cache_dir: str = ".embedding_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

    def get(self, key: str) -> Optional[np.ndarray]:
        """Retrieve embedding from cache."""
        cache_file = self.cache_dir / f"{key}.pkl"

        if cache_file.exists():
            with open(cache_file, "rb") as f:
                return pickle.load(f)
        return None

    def set(self, key: str, embedding: np.ndarray):
        """Store embedding in cache."""
        cache_file = self.cache_dir / f"{key}.pkl"

        with open(cache_file, "wb") as f:
            pickle.dump(embedding, f)
