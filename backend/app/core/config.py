"""Application configuration and environment settings."""
import os
from pathlib import Path
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Core application settings with environment variable fallback."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # API & Service
    PROJECT_NAME: str = "Multi-Agent HITL Orchestrator"
    API_PREFIX: str = "/api"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False
    CORS_ORIGINS: List[str] = ["*"]

    # Default LLM Configuration
    # Options: "mock", "openai", "anthropic", "gemini", "bedrock", "ollama"
    LLM_PROVIDER: str = "mock"
    MODEL_NAME: Optional[str] = None
    TEMPERATURE: float = 0.7

    # Role-specific model overrides (optional)
    SUPERVISOR_MODEL: Optional[str] = None
    RESEARCHER_MODEL: Optional[str] = None
    WRITER_MODEL: Optional[str] = None
    REVIEWER_MODEL: Optional[str] = None

    # Provider Credentials & Endpoints
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: str = "us-east-1"
    OLLAMA_BASE_URL: str = "http://localhost:11434"

    # Persistence / Checkpointer
    # Local zero-setup SQLite checkpointer file
    DATABASE_PATH: str = "backend/data/checkpoints.sqlite"

    # Multi-Agent Workflow Parameters
    MAX_REVISIONS: int = 2


settings = Settings()

# Ensure local data directory exists for checkpointer
os.makedirs(Path(settings.DATABASE_PATH).parent, exist_ok=True)
