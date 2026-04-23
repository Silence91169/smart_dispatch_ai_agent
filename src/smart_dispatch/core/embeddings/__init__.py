"""Embedding providers — local and API-backed implementations."""

from smart_dispatch.core.embeddings.base import EmbeddingProvider
from smart_dispatch.core.embeddings.sentence_transformer_provider import SentenceTransformerProvider

__all__ = ["EmbeddingProvider", "SentenceTransformerProvider"]
