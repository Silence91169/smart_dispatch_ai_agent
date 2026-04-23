"""Groq LLM provider implementation."""

import asyncio
import json
import logging
import re
from typing import Type

from groq import AsyncGroq, RateLimitError
from pydantic import BaseModel

from .base import LLMProvider, LLMStructuredOutputError
from .schemas import LLMResponse, LLMUsage

logger = logging.getLogger(__name__)

_RETRY_AFTER_RE = re.compile(r"try again in ([\d.]+)s", re.IGNORECASE)
_MAX_RATE_RETRIES = 6


def _parse_retry_seconds(msg: str) -> float:
    """Extract the retry-after delay from a Groq 429 error message."""
    m = _RETRY_AFTER_RE.search(msg)
    return float(m.group(1)) if m else 5.0


async def _with_rate_retry(coro_factory):
    """Call coro_factory() and retry transparently on Groq TPM/TPD 429s."""
    for attempt in range(_MAX_RATE_RETRIES):
        try:
            return await coro_factory()
        except RateLimitError as exc:
            wait = _parse_retry_seconds(str(exc))
            if attempt == _MAX_RATE_RETRIES - 1:
                raise
            logger.warning("Groq rate limit — waiting %.1fs then retrying (attempt %d/%d)…",
                           wait, attempt + 1, _MAX_RATE_RETRIES)
            await asyncio.sleep(wait + 0.5)  # small buffer


class GroqProvider(LLMProvider):
    """LLM provider backed by the Groq API.

    Uses JSON mode for structured outputs with a single automatic retry on
    parse failure.

    Args:
        api_key: Groq API key.
        model: Groq model identifier.  Defaults to ``llama-3.3-70b-versatile``.
    """

    provider_name = "groq"

    def __init__(
        self,
        api_key: str,
        model: str = "llama-3.3-70b-versatile",
    ) -> None:
        super().__init__(api_key=api_key, model=model)
        self._client = AsyncGroq(api_key=api_key)

    async def complete(
        self,
        prompt: str,
        system: str = "",
        temperature: float = 0.3,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        """Plain chat completion via Groq.

        Args:
            prompt: User prompt text.
            system: Optional system instruction.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens to generate.

        Returns:
            Standardised :class:`LLMResponse`.
        """
        messages = self._build_messages(prompt, system)
        response = await _with_rate_retry(lambda: self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        ))
        choice = response.choices[0]
        usage = response.usage
        return LLMResponse(
            content=choice.message.content or "",
            model=response.model,
            provider=self.provider_name,
            usage=LLMUsage(
                prompt_tokens=usage.prompt_tokens if usage else 0,
                completion_tokens=usage.completion_tokens if usage else 0,
                total_tokens=usage.total_tokens if usage else 0,
            ),
            raw=response.model_dump(),
        )

    async def structured_output(
        self,
        prompt: str,
        schema: Type[BaseModel],
        system: str = "",
        temperature: float = 0.1,
        max_tokens: int = 1024,
    ) -> BaseModel:
        """Return a validated Pydantic model using Groq's JSON mode.

        Retries once with a stricter prompt on parse failure.

        Args:
            prompt: User prompt text.
            schema: Pydantic model class describing the desired output shape.
            system: Optional system instruction.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens to generate.

        Returns:
            A validated instance of ``schema``.

        Raises:
            :class:`LLMStructuredOutputError`: If parsing fails after the retry.
        """
        schema_instruction = (
            f"You MUST respond with valid JSON matching this exact schema:\n"
            f"{json.dumps(schema.model_json_schema(), indent=2)}"
        )
        combined_system = f"{system}\n\n{schema_instruction}".strip() if system else schema_instruction

        for attempt in range(2):
            if attempt == 1:
                combined_system = (
                    "CRITICAL: You MUST return ONLY a valid JSON object. "
                    "No explanation, no markdown, no code fences. "
                    f"The JSON must exactly match this schema:\n"
                    f"{json.dumps(schema.model_json_schema(), indent=2)}"
                )
            messages = self._build_messages(prompt, combined_system)
            response = await _with_rate_retry(lambda: self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                response_format={"type": "json_object"},
                temperature=temperature,
                max_tokens=max_tokens,
            ))
            raw_content = response.choices[0].message.content or ""
            try:
                return schema.model_validate_json(raw_content)
            except Exception as exc:
                if attempt == 0:
                    logger.warning(
                        "Groq structured output parse failed (attempt 1), retrying: %s", exc
                    )
                    continue
                raise LLMStructuredOutputError(
                    f"Groq structured output failed after retry. "
                    f"Schema: {schema.__name__}. Error: {exc}. Raw: {raw_content!r}"
                ) from exc

        raise LLMStructuredOutputError("Groq structured output: unreachable state")

    async def health_check(self) -> bool:
        """Ping Groq to verify connectivity and credentials.

        Returns:
            ``True`` on success, ``False`` on any error.
        """
        try:
            await asyncio.wait_for(
                self.complete("ping", max_tokens=10),
                timeout=5.0,
            )
            return True
        except Exception as exc:
            logger.warning("Groq health check failed: %s", exc)
            return False
