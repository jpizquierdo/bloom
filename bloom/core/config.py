"""Application settings, loaded from environment variables (and an optional .env)."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for the Bloom API.

    Values are read from environment variables (case-insensitive) or a local
    ``.env`` file. Every field has a development-friendly default so the app can
    boot out of the box; override them in production.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database
    database_url: str = "postgresql+psycopg://bloom:bloom@localhost:5432/bloom"

    # JWT / auth
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # First-admin bootstrap (created on startup if absent). Leave empty to skip.
    bloom_admin_email: str | None = None
    bloom_admin_password: str | None = None


@lru_cache
def get_settings() -> Settings:
    """Return a cached ``Settings`` instance."""
    return Settings()
