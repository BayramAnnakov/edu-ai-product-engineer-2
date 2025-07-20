from __future__ import annotations

"""Global configuration for the Windsurf Summarization Agent.
Loads values from environment variables and optional `.env` file using Pydantic
settings management. All modules should import `settings` from this file.
"""

from pathlib import Path
from typing import Optional

from pydantic import Field, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ------------------------------------------------------------------
    # OpenAI / LLM settings
    # ------------------------------------------------------------------
    # Choose provider: "openai" (default) or "openrouter"
    llm_provider: str = Field("openai", env="LLM_PROVIDER")

    # --- OpenAI settings ---
    openai_api_key: Optional[str] = Field(None, env="OPENAI_API_KEY")
    openai_model: str = Field("gpt-4o-mini", env="OPENAI_MODEL")
    openai_timeout: int = Field(60, env="OPENAI_TIMEOUT")

    # --- OpenRouter settings ---
    openrouter_api_key: Optional[str] = Field(None, env="OPENROUTER_API_KEY")
    openrouter_model: str = Field("gpt-4o-mini", env="OPENROUTER_MODEL")
    openrouter_base_url: str = Field("https://openrouter.ai/api/v1", env="OPENROUTER_BASE_URL")

    # ------------------------------------------------------------------
    # Extractive summarizer parameters
    # ------------------------------------------------------------------
    extraction_max_sentences: int = Field(5, env="EXTRACTION_MAX_SENTENCES")

    # ------------------------------------------------------------------
    # Paths
    # ------------------------------------------------------------------
    prompt_templates_dir: Path = Field("shared_utils/prompt_templates.py")

    # ------------------------------------------------------------------
    # Misc
    # ------------------------------------------------------------------
    log_level: str = Field("INFO", env="LOG_LEVEL")

    class Config:
        env_file = ".env"
        case_sensitive = False

    # ------------------------------------------------------------------
    # Validators
    # ------------------------------------------------------------------
    @validator("openai_api_key", always=True)
    def _validate_openai(cls, v: Optional[str], values):  # noqa: N805
        if values.get("llm_provider") == "openai":
            if not v or not v.startswith("sk-"):
                raise ValueError(
                    "OPENAI_API_KEY is required and must start with 'sk-' when LLM_PROVIDER=openai."
                )
        return v

    @validator("openrouter_api_key", always=True)
    def _validate_openrouter(cls, v: Optional[str], values):  # noqa: N805
        if values.get("llm_provider") == "openrouter":
            if not v:
                raise ValueError("OPENROUTER_API_KEY is required when LLM_PROVIDER=openrouter.")
        return v


# Instance exported for convenience
settings = Settings()
auto_env_settings = settings  # backward-compat alias
