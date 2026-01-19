import time
from typing import Callable, Iterable, List, Optional

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
        batch_size: int = 128,
        use_fp16: bool = True,
    ):
        print(f"Loading SPECTER2 base model: {base_model}")

        self.tokenizer = AutoTokenizer.from_pretrained(base_model)
        self.model = AutoAdapterModel.from_pretrained(base_model)
        self.model.load_adapter(adapter_name, source="hf", set_active=True)

        self.model_name = f"{base_model}+{adapter_name}"
        self.cache = EmbeddingCache(cache_dir)

        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.batch_size = batch_size
        self.use_fp16 = use_fp16 and self.device == "cuda"

        self.model.to(self.device)

        if self.use_fp16:
            self.model = self.model.half()

        self.model.eval()

        print("torch:", torch.__version__)
        print("hip:", torch.version.hip)
        print("device:", self.device)
        if self.device == "cuda":
            print("gpu:", torch.cuda.get_device_name(0))
            print("fp16:", self.use_fp16)

        print("✓ Embedder ready")

    def _batch(self, items: List[str]) -> Iterable[List[str]]:
        for i in range(0, len(items), self.batch_size):
            yield items[i : i + self.batch_size]

    def _encode_batch(self, texts: List[str]) -> np.ndarray:
        inputs = self.tokenizer(
            texts,
            padding=True,
            truncation=True,
            max_length=512,
            return_tensors="pt",
            return_token_type_ids=False,
        )

        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        with torch.no_grad():
            outputs = self.model(**inputs)
            embeddings = outputs.last_hidden_state[:, 0, :]  # CLS

        return embeddings

    def embed(self, text: str, cache_key: Optional[str] = None) -> np.ndarray:
        if cache_key:
            cached = self.cache.get(cache_key)
            if cached is not None:
                return cached

        emb = self.embed_chunks([text], cache_key)
        return emb

    def embed_chunks(
        self, chunks: List[str], cache_key: Optional[str] = None
    ) -> np.ndarray:
        if cache_key:
            cached = self.cache.get(cache_key)
            if cached is not None:
                return cached

        if not chunks:
            return np.zeros(768, dtype=np.float32)

        all_embeddings = []

        for batch in self._batch(chunks):
            emb = self._encode_batch(batch)
            all_embeddings.append(emb)

        # [num_chunks, hidden]
        stacked = torch.cat(all_embeddings, dim=0)

        # pool across chunks (max-pool)
        pooled = torch.max(stacked, dim=0).values

        result = pooled.float().cpu().numpy()

        if cache_key:
            self.cache.set(cache_key, result)

        return result

    def lazy_embed_chunks(
        self,
        get_chunks: Callable[[], List[str]],
        cache_key: Optional[str] = None,
    ) -> np.ndarray:
        if cache_key:
            cached = self.cache.get(cache_key)
            if cached is not None:
                return cached

        return self.embed_chunks(get_chunks(), cache_key)

    def compute_similarity(
        self, embedding1: np.ndarray, embedding2: np.ndarray
    ) -> float:
        return float(
            cosine_similarity(
                embedding1.reshape(1, -1),
                embedding2.reshape(1, -1),
            )[
                0
            ][0]
        )
