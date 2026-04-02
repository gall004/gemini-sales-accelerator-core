"""Application configuration via Pydantic Settings.

All runtime values are loaded from environment variables with sensible defaults.
Docker Compose injects these; for bare-metal dev, copy .env.example → .env.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Centralized, validated application configuration.

    Every field maps 1:1 to an environment variable (case-insensitive).
    Pydantic validates types at startup — a missing required var crashes
    fast with a clear error instead of failing silently at runtime.
    """

    # ── Application ──────────────────────────────────────────────────────
    app_env: str = "development"
    app_name: str = "Gemini Sales Accelerator Core"
    app_version: str = "0.1.0"
    log_level: str = "INFO"

    # ── Authentication ───────────────────────────────────────────────────
    api_key: str = "gsa_dev_key_change_me_in_production"

    # ── Database (Async — SQLAlchemy + asyncpg) ──────────────────────────
    database_url: str = (
        "postgresql+asyncpg://gsa_user:gsa_local_password@localhost:5432/gsa_core"
    )
    # Sync URL for Alembic migrations (asyncpg driver doesn't work with Alembic)
    database_url_sync: str = (
        "postgresql://gsa_user:gsa_local_password@localhost:5432/gsa_core"
    )

    # ── Redis ────────────────────────────────────────────────────────────
    redis_url: str = "redis://localhost:6379/0"

    # ── Google Cloud Platform ────────────────────────────────────────────
    gcp_project_id: str = "your-gcp-project-id"
    gcp_location: str = "us-central1"
    briefing_agent_engine_id: str | None = None
    chat_agent_engine_id: str | None = None

    # ── Briefing Cache ───────────────────────────────────────────────────
    briefing_cache_ttl_days: int = 7

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance.

    Using @lru_cache ensures environment variables are read once at startup
    and reused across the application lifecycle without re-parsing.
    """
    return Settings()
