"""OpenAI LLM provider implementation."""

import asyncio
import logging
from typing import Type

from openai import AsyncOpenAI
from pydantic import BaseModel

from .base import LLMProvider, LLMStructuredOutputError
from .schemas import LLMResponse, LLMUsage

logger = logging.getLogger(__name__)


class OpenAIProvider(LLMProvider):
    """LLM provider backed by the OpenAI Chat Completions API.

    Uses the native structured outputs feature (``json_schema`` response format
    with ``strict: true``) rather than function calling or ``json_object`` mode.

    Args:
        api_key: OpenAI API key.
        model: OpenAI model identifier.  Defaults to ``gpt-4o-mini``.
    """

    provider_name = "openai"

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
    ) -> None:
        super().__init__(api_key=api_key, model=model)
        self._client = AsyncOpenAI(api_key=api_key)

    async def complete(
        self,
        prompt: str,
        system: str = "",
        temperature: float = 0.3,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        """Plain chat completion via the OpenAI API.

        Args:
            prompt: User prompt text.
            system: Optional system instruction.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens to generate.

        Returns:
            Standardised :class:`LLMResponse`.
        """
        messages = self._build_messages(prompt, system)
        response = await self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
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
            raw={"id": response.id, "finish_reason": choice.finish_reason},
        )

    async def structured_output(
        self,
        prompt: str,
        schema: Type[BaseModel],
        system: str = "",
        temperature: float = 0.1,
        max_tokens: int = 1024,
    ) -> BaseModel:
        """Return a validated Pydantic model using OpenAI native structured outputs.

        Uses ``response_format`` with ``type: json_schema`` and ``strict: true``
        (the modern approach — not function calling or json_object mode).

        Args:
            prompt: User prompt text.
            schema: Pydantic model class describing the desired output shape.
            system: Optional system instruction.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens to generate.

        Returns:
            A validated instance of ``schema``.

        Raises:
            :class:`LLMStructuredOutputError`: If the response is missing or
                validation fails.
        """
        messages = self._build_messages(prompt, system)
        try:
            response = await self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": schema.__name__,
                        "schema": schema.model_json_schema(),
                        "strict": True,
                    },
                },
            )
        except Exception as exc:
            raise LLMStructuredOutputError(
                f"OpenAI API call failed for schema {schema.__name__}: {exc}"
            ) from exc

        raw_content = response.choices[0].message.content or ""
        if not raw_content:
            raise LLMStructuredOutputError(
                f"OpenAI returned empty content for schema {schema.__name__}."
            )

        try:
            return schema.model_validate_json(raw_content)
        except Exception as exc:
            raise LLMStructuredOutputError(
                f"OpenAI structured output validation failed for {schema.__name__}: {exc}. "
                f"Raw: {raw_content!r}"
            ) from exc

    async def health_check(self) -> bool:
        """Ping OpenAI to verify connectivity and credentials.

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
            logger.warning("OpenAI health check failed: %s", exc)
            return False
