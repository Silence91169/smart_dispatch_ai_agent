"""Shared Pydantic models for the LLM abstraction layer."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class LLMRole(str, Enum):
    """Valid roles in a chat message."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class LLMMessage(BaseModel):
    """A single message in a conversation."""

    role: LLMRole
    content: str


class LLMUsage(BaseModel):
    """Token usage tracking — useful for cost monitoring."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class LLMResponse(BaseModel):
    """Standard response wrapper so all providers return the same shape."""

    content: str
    model: str
    provider: str
    usage: LLMUsage
    raw: Optional[dict] = Field(default=None, description="Raw provider response for debugging")
