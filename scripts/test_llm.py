"""Manual integration test script — runs all configured providers end-to-end."""

import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from pydantic import BaseModel

from smart_dispatch.config import settings
from smart_dispatch.core.llm.anthropic_provider import AnthropicProvider
from smart_dispatch.core.llm.base import LLMProvider
from smart_dispatch.core.llm.groq_provider import GroqProvider
from smart_dispatch.core.llm.openai_provider import OpenAIProvider


class TestResponse(BaseModel):
    greeting: str
    language: str
    word_count: int


def _row(provider: str, check: str, complete: str, structured: str) -> None:
    print(f"  {provider:<12}  {check:<6}  {complete:<30}  {structured}")


async def run_provider(name: str, provider: LLMProvider) -> None:
    print(f"\n{'─' * 60}")
    print(f"Provider: {name.upper()}  (model: {provider.model})")
    print(f"{'─' * 60}")

    # Health check
    healthy = await provider.health_check()
    health_icon = "✅" if healthy else "❌"
    print(f"  Health check : {health_icon}")

    if not healthy:
        print("  Skipping further tests — provider unreachable.")
        return

    # Plain completion
    try:
        resp = await provider.complete("Say hello in exactly 3 words.")
        print(f"  Completion   : {resp.content.strip()!r}")
        print(f"  Tokens used  : {resp.usage.total_tokens}")
    except Exception as exc:
        print(f"  Completion   : ❌ {exc}")

    # Structured output
    try:
        result: TestResponse = await provider.structured_output(  # type: ignore[assignment]
            prompt="Respond with a greeting in Spanish and count its words.",
            schema=TestResponse,
            system="You are a helpful assistant.",
        )
        print(f"  Structured   : greeting={result.greeting!r}, language={result.language!r}, words={result.word_count}")
    except Exception as exc:
        print(f"  Structured   : ❌ {exc}")


async def main() -> None:
    print("=" * 60)
    print("  Smart Dispatch — LLM Provider Integration Test")
    print("=" * 60)

    candidates: list[tuple[str, LLMProvider]] = []

    if settings.groq_api_key:
        candidates.append(("groq", GroqProvider(api_key=settings.groq_api_key, model=settings.groq_model)))
    else:
        print("\n  [groq]       Skipped — GROQ_API_KEY not set")

    if settings.anthropic_api_key:
        candidates.append(("anthropic", AnthropicProvider(api_key=settings.anthropic_api_key, model=settings.anthropic_model)))
    else:
        print("  [anthropic]  Skipped — ANTHROPIC_API_KEY not set")

    if settings.openai_api_key:
        candidates.append(("openai", OpenAIProvider(api_key=settings.openai_api_key, model=settings.openai_model)))
    else:
        print("  [openai]     Skipped — OPENAI_API_KEY not set")

    if not candidates:
        print("\n  No providers configured. Copy .env.example to .env and add at least one API key.")
        return

    for name, provider in candidates:
        await run_provider(name, provider)

    print(f"\n{'=' * 60}")
    print("  Done.")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
