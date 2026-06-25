"""
config.py — Centralized, type-safe application configuration.

Uses pydantic-settings for env-var parsing with validation.
All paths are resolved relative to this file's location, not CWD.
Never scatter configuration across the codebase — import `settings` from here.
"""

from pathlib import Path
from typing import Literal, Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application-wide settings loaded from environment / .env file."""

    # ---- Server ----------------------------------------------------------
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    APP_RELOAD: bool = False
    APP_WORKERS: int = 1
    ENVIRONMENT: Literal["development", "production", "test"] = "development"

    # ---- LLM Provider (passed through to existing model_router) ----------
    LLM_PROVIDER: str = "deepseek"
    DEEPSEEK_API_KEY: Optional[str] = None
    FIREWORKS_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    FIREWORKS_MODEL: Optional[str] = None
    OLLAMA_MODEL: Optional[str] = None

    # ---- Paths — resolved from project root ------------------------------
    # PROJECT_ROOT is <repo-root>/ (two levels up from this config file)
    @property
    def PROJECT_ROOT(self) -> Path:
        return Path(__file__).resolve().parent.parent.parent

    @property
    def BENCHMARKS_DIR(self) -> Path:
        return self.PROJECT_ROOT / "benchmarks"

    @property
    def SKILLS_DIR(self) -> Path:
        return self.PROJECT_ROOT / "skills"

    @property
    def WORKSPACE_DIR(self) -> Path:
        return self.PROJECT_ROOT / "workspace"

    @property
    def STATIC_DIR(self) -> Path:
        return self.PROJECT_ROOT / "ui" / "frontend"

    @property
    def LOG_DIR(self) -> Path:
        return self.PROJECT_ROOT / "logs"

    # ---- Pipeline --------------------------------------------------------
    PIPELINE_DEFAULT_VERSION: Literal["v1", "v2", "v3"] = "v1"
    PIPELINE_MAX_ITERATIONS: int = 5
    PIPELINE_TIMEOUT_SECONDS: int = 600  # 10 min per job
    PIPELINE_CLEANUP_WORKSPACE: bool = False

    # "mock" = synthetic events, no EDA tools needed (default for Phase 1)
    # "real" = run actual LangGraph pipeline (requires EDA tools + LLM key)
    PIPELINE_MODE: Literal["mock", "real"] = "mock"

    # ---- SSE (Server-Sent Events) ----------------------------------------
    SSE_HEARTBEAT_INTERVAL: int = 15  # seconds between heartbeats
    SSE_MAX_CLIENTS_PER_JOB: int = 100

    # ---- Logging ---------------------------------------------------------
    LOG_LEVEL: str = "INFO"
    LOG_RETENTION_DAYS: int = 30

    # ---- Limits ----------------------------------------------------------
    MAX_CONCURRENT_JOBS: int = 1  # EDA tools are resource-heavy
    MAX_JOBS_IN_MEMORY: int = 100  # evict oldest completed jobs beyond this
    JOB_CLEANUP_MAX_AGE_SECONDS: int = 3600  # 1 hour

    # ---- CORS ------------------------------------------------------------
    CORS_ORIGINS: list[str] = ["*"]

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


# Module-level singleton — import this everywhere.
settings = Settings()
