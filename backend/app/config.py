"""Application configuration, loaded from environment / `.env` (see `.env.example`)."""

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Repo root holds the committed `.env` (backend/ is one level down).
_REPO_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(str(_REPO_ROOT / ".env"), ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database
    database_url: str = (
        "postgresql+asyncpg://claimpilot:claimpilot@localhost:5432/claimpilot"
    )

    # LLM / embeddings (OpenAI-compatible)
    openai_base_url: str = "http://localhost:11434/v1"
    openai_api_key: str = "ollama"
    llm_model: str = "llama3.1"
    embed_model: str = "nomic-embed-text"
    embed_dim: int = 768

    # Retrieval
    retrieval_top_k: int = 5

    # App
    log_level: str = "INFO"


settings = Settings()
