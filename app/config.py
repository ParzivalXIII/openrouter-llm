"""Configuration management for OpenRouter service."""

from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings

# Load .env file at module import time
env_file = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_file, override=True)


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    openrouter_api_key: SecretStr = Field(
        ...,
        alias="OPENROUTER_API_KEY",
        description="OpenRouter API key for authentication",
    )
    model_id: str = Field(
        ...,
        alias="MODEL_ID",
        description="Default model ID to use for LLM requests (e.g., 'anthropic/claude-sonnet-4.5')",
    )
    app_title: str = Field(
        default="OpenRouter FastAPI Service",
        alias="APP_TITLE",
        description="Application title for attribution",
    )
    app_url: str | None = Field(
        default=None,
        alias="APP_URL",
        description="Application URL for attribution",
    )
    environment: str = Field(
        default="development",
        alias="ENVIRONMENT",
        description="Deployment environment (development, staging, production)",
    )
    log_level: str = Field(
        default="INFO",
        alias="LOG_LEVEL",
        description="Logging level",
    )

    class Config:
        """Pydantic settings config."""

        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Get cached settings instance.

    Returns:
        Settings: Cached application settings singleton.
    """
    return Settings()
