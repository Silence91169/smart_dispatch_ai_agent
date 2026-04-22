"""Anthropic Claude LLM provider implementation."""

import asyncio
import logging
from typing import Type

from anthropic import AsyncAnthropic
from pydantic import BaseModel

from .base import LLMProvider, LLMStructuredOutputError
from .schemas import LLMResponse, LLMUsage

logger = logging.getLogger(__name__)


class AnthropicProvider(LLMProvider):
    """LLM provider backed by the Anthropic Messages API.

    Uses tool use for structured outputs so the model is forced to emit
    a conforming JSON object rather than free-form text.

    Args:
        api_key: Anthropic API key.
        model: Anthropic model identifier.  Defaults to ``claude-sonnet-4-5``.
    """

    provider_name = "anthropic"

    def __init__(
        self,
        api_key: str,
        model: str = "claude-sonnet-4-5",
    ) -> None:
        super().__init__(api_key=api_key, model=model)
        self._client = AsyncAnthropic(api_key=api_key)

    async def complete(
        self,
        prompt: str,
        system: str = "",
        temperature: float = 0.3,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        """Plain chat completion via the Anthropic Messages API.

        Args:
            prompt: User prompt text.
            system: Optional system instruction (passed as top-level param).
            temperature: Sampling temperature.
            max_tokens: Maximum tokens to generate.

        Returns:
            Standardised :class:`LLMResponse`.
        """
        kwargs: dict = dict(
            model=self.model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
        )
        if system:
            kwargs["system"] = system

        response = await self._client.messages.create(**kwargs)

        content_text = ""
        for block in response.content:
            if hasattr(block, "text"):
                content_text += block.text

        return LLMResponse(
            content=content_text,
            model=response.model,
            provider=self.provider_name,
            usage=LLMUsage(
                prompt_tokens=response.usage.input_tokens,
                completion_tokens=response.usage.output_tokens,
                total_tokens=response.usage.input_tokens + response.usage.output_tokens,
            ),
            raw={
                "id": response.id,
                "stop_reason": response.stop_reason,
            },
        )

    async def structured_output(
        self,
        prompt: str,
        schema: Type[BaseModel],
        system: str = "",
        temperature: float = 0.1,
        max_tokens: int = 1024,
    ) -> BaseModel:
        """Return a validated Pydantic model using Anthropic tool use.

        Defines a single ``extract`` tool whose ``input_schema`` matches
        ``schema``, then forces the model to call it.

        Args:
            prompt: User prompt text.
            schema: Pydantic model class describing the desired output shape.
            system: Optional system instruction.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens to generate.

        Returns:
            A validated instance of ``schema``.

        Raises:
            :class:`LLMStructuredOutputError`: If the tool use block is missing
                or input validation fails.
        """
        tool = {
            "name": "extract",
            "description": f"Extract structured {schema.__name__} data from the input.",
            "input_schema": schema.model_json_schema(),
        }

        kwargs: dict = dict(
            model=self.model,
            max_tokens=max_tokens,
            tools=[tool],
            tool_choice={"type": "tool", "name": "extract"},
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
        )
        if system:
            kwargs["system"] = system

        try:
            response = await self._client.messages.create(**kwargs)
        except Exception as exc:
            raise LLMStructuredOutputError(
                f"Anthropic API call failed for schema {schema.__name__}: {exc}"
            ) from exc

        for block in response.content:
            if hasattr(block, "type") and block.type == "tool_use" and block.name == "extract":
                try:
                    return schema.model_validate(block.input)
                except Exception as exc:
                    raise LLMStructuredOutputError(
                        f"Anthropic tool input failed validation for {schema.__name__}: {exc}. "
                        f"Input: {block.input!r}"
                    ) from exc

        raise LLMStructuredOutputError(
            f"Anthropic response contained no 'extract' tool use block for schema {schema.__name__}."
        )

    async def health_check(self) -> bool:
        """Ping Anthropic to verify connectivity and credentials.

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
            logger.warning("Anthropic health check failed: %s", exc)
            return False
