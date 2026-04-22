"""Abstract base class and shared exceptions for LLM providers."""

from abc import ABC, abstractmethod
from typing import Type

from pydantic import BaseModel

from .schemas import LLMResponse


class LLMProviderError(Exception):
    """Raised when an LLM provider call fails unexpectedly."""


class LLMStructuredOutputError(LLMProviderError):
    """Raised when structured output parsing fails after all retries."""


class LLMProvider(ABC):
    """Abstract base for all LLM provider implementations.

    Subclasses must implement :meth:`complete`, :meth:`structured_output`,
    and :meth:`health_check`.  All three are async.

    Args:
        api_key: Provider API key.  Raises ``ValueError`` if blank.
        model: Model identifier string.
    """

    provider_name: str = "base"

    def __init__(self, api_key: str, model: str) -> None:
        if not api_key:
            raise ValueError(
                f"{self.__class__.__name__} requires a non-empty api_key. "
                "Set the corresponding environment variable."
            )
        self.api_key = api_key
        self.model = model

    @abstractmethod
    async def complete(
        self,
        prompt: str,
        system: str = "",
        temperature: float = 0.3,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        """Plain text completion.

        Args:
            prompt: User prompt text.
            system: Optional system instruction.
            temperature: Sampling temperature (0–1).
            max_tokens: Maximum tokens to generate.

        Returns:
            Standardised :class:`LLMResponse`.
        """
        ...

    @abstractmethod
    async def structured_output(
        self,
        prompt: str,
        schema: Type[BaseModel],
        system: str = "",
        temperature: float = 0.1,
        max_tokens: int = 1024,
    ) -> BaseModel:
        """Return a validated Pydantic model instance matching ``schema``.

        Args:
            prompt: User prompt text.
            schema: Pydantic model class describing the desired output shape.
            system: Optional system instruction.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens to generate.

        Returns:
            An instance of ``schema`` populated from the model's response.

        Raises:
            :class:`LLMStructuredOutputError`: If parsing fails after retries.
        """
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """Verify that the provider is reachable and credentials are valid.

        Returns:
            ``True`` on success, ``False`` on any failure.
        """
        ...

    def _build_messages(self, prompt: str, system: str = "") -> list[dict]:
        """Build an OpenAI-style message list from prompt and optional system text.

        Args:
            prompt: User message content.
            system: Optional system instruction (prepended as a system message).

        Returns:
            List of ``{"role": ..., "content": ...}`` dicts.
        """
        messages: list[dict] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        return messages
