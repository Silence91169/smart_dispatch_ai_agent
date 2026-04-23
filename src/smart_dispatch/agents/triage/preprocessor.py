"""Transcript cleanup before LLM extraction — does NOT change meaning."""

from __future__ import annotations

import re


class TranscriptPreprocessor:
    """Light normalization before LLM extraction."""

    def clean(self, transcript: str) -> str:
        text = transcript.strip()
        text = re.sub(r"\s+", " ", text)
        text = re.sub(r"([!?])\1{2,}", r"\1\1", text)
        text = re.sub(r"\.{4,}", "...", text)
        return text

    def extract_hints(self, transcript: str) -> dict:
        """Heuristic hints for logging/debugging — NOT passed to the LLM."""
        hints: dict = {}
        hints["caps_ratio"] = sum(1 for c in transcript if c.isupper()) / max(len(transcript), 1)
        hints["has_numbers"] = bool(re.search(r"\d", transcript))
        panic_words = ["help", "bachao", "bhagwan", "please", "jaldi", "emergency", "urgent"]
        hints["has_panic_words"] = any(w in transcript.lower() for w in panic_words)
        hints["length"] = len(transcript)
        return hints
