"""Abstract base class for embedding providers."""

from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np


class EmbeddingProvider(ABC):
    """Abstract interface for text embedding providers."""

    def __init__(self, model_name: str) -> None:
        self.model_name = model_name
        self._dimension: int | None = None

    @property
    def dimension(self) -> int:
        """Embedding vector dimension. Set after model loads."""
        if self._dimension is None:
            raise RuntimeError("Model not loaded — call embed() or load() first.")
        return self._dimension

    @abstractmethod
    async def embed(self, text: str) -> np.ndarray:
        """Embed a single string → 1D numpy array of shape (dimension,)."""
        ...

    @abstractmethod
    async def embed_batch(self, texts: list[str]) -> np.ndarray:
        """Embed multiple strings → 2D numpy array of shape (len(texts), dimension)."""
        ...

    @abstractmethod
    async def load(self) -> None:
        """Explicitly load the model (for preloading at startup)."""
        ...
