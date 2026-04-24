"""Deterministic LLM stand-in for unit tests — no network calls."""

from typing import Optional, Type

from pydantic import BaseModel

from smart_dispatch.core.llm.base import LLMProvider
from smart_dispatch.core.llm.schemas import LLMResponse, LLMUsage


class MockLLMProvider(LLMProvider):
    """Returns pre-programmed responses. Use for unit tests — never hits a network."""

    provider_name = "mock"

    def __init__(self, model: str = "mock-model") -> None:
        super().__init__(api_key="mock-key", model=model)
        self.structured_responses: dict[str, BaseModel] = {}
        self.default_structured: Optional[BaseModel] = None
        self.completion_responses: dict[str, str] = {}
        self.default_completion = "mock response"
        self.structured_calls: list[tuple[str, type]] = []
        self.completion_calls: list[str] = []

    def set_structured_response(self, key: str, response: BaseModel) -> None:
        """Register a response matched by substring in the prompt."""
        self.structured_responses[key] = response

    def set_default_structured(self, response: BaseModel) -> None:
        self.default_structured = response

    def set_completion_response(self, key: str, response: str) -> None:
        self.completion_responses[key] = response

    async def complete(
        self,
        prompt: str,
        system: str = "",
        temperature: float = 0.3,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        self.completion_calls.append(prompt)
        for key, resp in self.completion_responses.items():
            if key in prompt:
                return LLMResponse(
                    content=resp,
                    model=self.model,
                    provider=self.provider_name,
                    usage=LLMUsage(),
                    raw=None,
                )
        return LLMResponse(
            content=self.default_completion,
            model=self.model,
            provider=self.provider_name,
            usage=LLMUsage(),
            raw=None,
        )

    async def structured_output(
        self,
        prompt: str,
        schema: Type[BaseModel],
        system: str = "",
        temperature: float = 0.1,
        max_tokens: int = 1024,
    ) -> BaseModel:
        self.structured_calls.append((prompt, schema))
        for key, resp in self.structured_responses.items():
            if key in prompt and isinstance(resp, schema):
                return resp
        if self.default_structured and isinstance(self.default_structured, schema):
            return self.default_structured
        raise RuntimeError(
            f"MockLLMProvider has no response for schema={schema.__name__}. "
            "Set one with set_structured_response() or set_default_structured()."
        )

    async def health_check(self) -> bool:
        return True
