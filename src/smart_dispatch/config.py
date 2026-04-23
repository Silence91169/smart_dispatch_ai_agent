"""Application configuration loaded from environment variables."""

import logging
import os

from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()

logger = logging.getLogger(__name__)


class Settings(BaseModel):
    """All application settings sourced from environment variables.

    Fields default to empty strings so missing keys don't crash import —
    they only raise when the provider is actually instantiated without its key.
    """

    # Provider selection
    llm_provider: str = "groq"

    # Groq
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"

    # Anthropic
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-5"

    # OpenAI
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    # App
    log_level: str = "INFO"

    # Database
    db_path: str = "sqlite+aiosqlite:///./dispatch.db"


settings = Settings(
    llm_provider=os.getenv("LLM_PROVIDER", "groq"),
    groq_api_key=os.getenv("GROQ_API_KEY", ""),
    groq_model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
    anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", ""),
    anthropic_model=os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5"),
    openai_api_key=os.getenv("OPENAI_API_KEY", ""),
    openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
    log_level=os.getenv("LOG_LEVEL", "INFO"),
    db_path=os.getenv("DB_PATH", "sqlite+aiosqlite:///./dispatch.db"),
)

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
