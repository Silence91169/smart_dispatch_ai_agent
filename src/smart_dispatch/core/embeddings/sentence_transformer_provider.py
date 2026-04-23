"""Local embeddings via sentence-transformers. CPU-only, no API cost."""

from __future__ import annotations

import asyncio

import numpy as np

from smart_dispatch.core.embeddings.base import EmbeddingProvider


class SentenceTransformerProvider(EmbeddingProvider):
    """Wraps sentence-transformers for local multilingual embeddings.

    Embeddings are L2-normalised so cosine similarity equals dot product —
    compatible with FAISS IndexFlatIP out of the box.
    """

    DEFAULT_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

    def __init__(self, model_name: str = DEFAULT_MODEL) -> None:
        super().__init__(model_name)
        self._model = None
        self._lock = asyncio.Lock()

    async def load(self) -> None:
        """Load the model if not already loaded. Thread-safe."""
        if self._model is not None:
            return
        async with self._lock:
            if self._model is not None:
                return
            from sentence_transformers import SentenceTransformer

            loop = asyncio.get_event_loop()
            self._model = await loop.run_in_executor(
                None, SentenceTransformer, self.model_name
            )
            self._dimension = self._model.get_embedding_dimension()

    async def embed(self, text: str) -> np.ndarray:
        """Embed a single string → normalised 1D array."""
        await self.load()
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self._model.encode(text, normalize_embeddings=True),
        )

    async def embed_batch(self, texts: list[str]) -> np.ndarray:
        """Embed multiple strings → normalised 2D array (n, dim)."""
        await self.load()
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self._model.encode(
                texts, normalize_embeddings=True, batch_size=32, show_progress_bar=False
            ),
        )
