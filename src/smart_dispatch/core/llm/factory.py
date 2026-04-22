"""Factory for constructing LLM provider instances from configuration."""

import logging
from typing import Optional

from smart_dispatch.config import settings

from .anthropic_provider import AnthropicProvider
from .base import LLMProvider
from .groq_provider import GroqProvider
from .openai_provider import OpenAIProvider

logger = logging.getLogger(__name__)

_PROVIDERS: dict[str, type[LLMProvider]] = {
    "groq": GroqProvider,
    "anthropic": AnthropicProvider,
    "openai": OpenAIProvider,
}


def get_llm_provider(provider_name: Optional[str] = None) -> LLMProvider:
    """Instantiate and return the requested LLM provider.

    Reads ``LLM_PROVIDER`` from settings when ``provider_name`` is ``None``.

    Args:
        provider_name: One of ``"groq"``, ``"anthropic"``, ``"openai"``, or
            ``None`` to use the value from :data:`~smart_dispatch.config.settings`.

    Returns:
        A concrete :class:`~smart_dispatch.core.llm.base.LLMProvider` instance.

    Raises:
        ValueError: If ``provider_name`` is not recognised.
        ValueError: If the provider's API key is missing (propagated from
            :class:`~smart_dispatch.core.llm.base.LLMProvider.__init__`).
    """
    name = (provider_name or settings.llm_provider).lower()

    if name not in _PROVIDERS:
        valid = ", ".join(sorted(_PROVIDERS))
        raise ValueError(
            f"Unknown LLM provider '{name}'. Valid options: {valid}."
        )

    provider_cls = _PROVIDERS[name]
    logger.info("Instantiating LLM provider: %s", name)

    if name == "groq":
        return provider_cls(api_key=settings.groq_api_key, model=settings.groq_model)
    if name == "anthropic":
        return provider_cls(api_key=settings.anthropic_api_key, model=settings.anthropic_model)
    if name == "openai":
        return provider_cls(api_key=settings.openai_api_key, model=settings.openai_model)

    raise ValueError(f"Unhandled provider name: {name}")


def get_default_provider() -> LLMProvider:
    """Return the provider selected by ``LLM_PROVIDER`` in the environment.

    Returns:
        A concrete :class:`~smart_dispatch.core.llm.base.LLMProvider` instance.
    """
    return get_llm_provider(None)
