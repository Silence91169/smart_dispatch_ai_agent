"""Unit tests for the LLM provider abstraction layer."""

import pytest
import pytest_asyncio
from pydantic import BaseModel
from unittest.mock import AsyncMock, MagicMock, patch

from smart_dispatch.core.llm.base import LLMProvider, LLMStructuredOutputError
from smart_dispatch.core.llm.schemas import LLMResponse, LLMUsage
from smart_dispatch.core.llm.factory import get_llm_provider


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_response(content: str = "hello", model: str = "test-model") -> LLMResponse:
    return LLMResponse(
        content=content,
        model=model,
        provider="mock",
        usage=LLMUsage(prompt_tokens=5, completion_tokens=3, total_tokens=8),
    )


class _ConcreteSchema(BaseModel):
    greeting: str
    language: str


# ---------------------------------------------------------------------------
# Base class validation
# ---------------------------------------------------------------------------

def test_llm_provider_rejects_empty_api_key():
    from smart_dispatch.core.llm.groq_provider import GroqProvider

    with pytest.raises(ValueError, match="non-empty api_key"):
        GroqProvider(api_key="", model="llama-3.3-70b-versatile")


def test_build_messages_with_system():
    from smart_dispatch.core.llm.groq_provider import GroqProvider

    provider = GroqProvider.__new__(GroqProvider)
    provider.api_key = "key"
    provider.model = "model"

    msgs = provider._build_messages("hello", system="be helpful")
    assert msgs[0] == {"role": "system", "content": "be helpful"}
    assert msgs[1] == {"role": "user", "content": "hello"}


def test_build_messages_without_system():
    from smart_dispatch.core.llm.groq_provider import GroqProvider

    provider = GroqProvider.__new__(GroqProvider)
    msgs = provider._build_messages("hello")
    assert len(msgs) == 1
    assert msgs[0]["role"] == "user"


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def test_factory_raises_on_unknown_provider():
    with pytest.raises(ValueError, match="Unknown LLM provider"):
        get_llm_provider("nonexistent")


def test_factory_instantiates_groq(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "fake-key")
    from smart_dispatch import config
    config.settings.groq_api_key = "fake-key"

    provider = get_llm_provider("groq")
    assert provider.provider_name == "groq"


def test_factory_instantiates_anthropic(monkeypatch):
    from smart_dispatch import config
    config.settings.anthropic_api_key = "fake-key"

    provider = get_llm_provider("anthropic")
    assert provider.provider_name == "anthropic"


def test_factory_instantiates_openai(monkeypatch):
    from smart_dispatch import config
    config.settings.openai_api_key = "fake-key"

    provider = get_llm_provider("openai")
    assert provider.provider_name == "openai"


# ---------------------------------------------------------------------------
# Groq provider
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_groq_complete():
    from smart_dispatch.core.llm.groq_provider import GroqProvider

    mock_usage = MagicMock(prompt_tokens=5, completion_tokens=3, total_tokens=8)
    mock_message = MagicMock(content="hi there")
    mock_choice = MagicMock(message=mock_message)
    mock_api_response = MagicMock(
        choices=[mock_choice],
        model="llama-3.3-70b-versatile",
        usage=mock_usage,
    )
    mock_api_response.model_dump.return_value = {}

    provider = GroqProvider(api_key="fake", model="llama-3.3-70b-versatile")
    provider._client.chat = MagicMock()
    provider._client.chat.completions = MagicMock()
    provider._client.chat.completions.create = AsyncMock(return_value=mock_api_response)

    result = await provider.complete("hello")
    assert result.content == "hi there"
    assert result.provider == "groq"


@pytest.mark.asyncio
async def test_groq_structured_output_success():
    from smart_dispatch.core.llm.groq_provider import GroqProvider

    mock_usage = MagicMock(prompt_tokens=10, completion_tokens=20, total_tokens=30)
    mock_message = MagicMock(content='{"greeting": "Hola", "language": "Spanish"}')
    mock_choice = MagicMock(message=mock_message)
    mock_api_response = MagicMock(
        choices=[mock_choice],
        model="llama-3.3-70b-versatile",
        usage=mock_usage,
    )

    provider = GroqProvider(api_key="fake", model="llama-3.3-70b-versatile")
    provider._client.chat = MagicMock()
    provider._client.chat.completions = MagicMock()
    provider._client.chat.completions.create = AsyncMock(return_value=mock_api_response)

    result = await provider.structured_output("greet me", _ConcreteSchema)
    assert isinstance(result, _ConcreteSchema)
    assert result.greeting == "Hola"


@pytest.mark.asyncio
async def test_groq_structured_output_retry_then_fail():
    from smart_dispatch.core.llm.groq_provider import GroqProvider

    mock_usage = MagicMock(prompt_tokens=5, completion_tokens=5, total_tokens=10)
    mock_message = MagicMock(content="not valid json {{{{")
    mock_choice = MagicMock(message=mock_message)
    mock_api_response = MagicMock(
        choices=[mock_choice],
        model="llama-3.3-70b-versatile",
        usage=mock_usage,
    )

    provider = GroqProvider(api_key="fake", model="llama-3.3-70b-versatile")
    provider._client.chat = MagicMock()
    provider._client.chat.completions = MagicMock()
    provider._client.chat.completions.create = AsyncMock(return_value=mock_api_response)

    with pytest.raises(LLMStructuredOutputError):
        await provider.structured_output("greet me", _ConcreteSchema)


@pytest.mark.asyncio
async def test_groq_health_check_success():
    from smart_dispatch.core.llm.groq_provider import GroqProvider

    provider = GroqProvider(api_key="fake", model="llama-3.3-70b-versatile")
    provider.complete = AsyncMock(return_value=_mock_response())

    assert await provider.health_check() is True


@pytest.mark.asyncio
async def test_groq_health_check_failure():
    from smart_dispatch.core.llm.groq_provider import GroqProvider

    provider = GroqProvider(api_key="fake", model="llama-3.3-70b-versatile")
    provider.complete = AsyncMock(side_effect=Exception("network error"))

    assert await provider.health_check() is False


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

def test_llm_usage_defaults():
    usage = LLMUsage()
    assert usage.total_tokens == 0


def test_llm_response_roundtrip():
    resp = LLMResponse(
        content="test",
        model="m",
        provider="groq",
        usage=LLMUsage(prompt_tokens=1, completion_tokens=2, total_tokens=3),
    )
    dumped = resp.model_dump()
    restored = LLMResponse.model_validate(dumped)
    assert restored.content == "test"
