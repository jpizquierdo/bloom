"""Application settings, loaded from environment variables (and an optional .env)."""

from functools import lru_cache

from pydantic import PostgresDsn, computed_field
from pydantic_core import MultiHostUrl
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

    # PostgreSQL connection parts
    POSTGRES_USER: str = "bloom"
    POSTGRES_PASSWORD: str = "bloom"
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "bloom"

    # JWT / auth
    JWT_SECRET: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # First-admin bootstrap (created on startup if absent). Leave empty to skip.
    BLOOM_ADMIN_EMAIL: str | None = None
    BLOOM_ADMIN_PASSWORD: str | None = None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> PostgresDsn:
        """SQLAlchemy/psycopg connection URL assembled from the parts above."""
        return MultiHostUrl.build(
            scheme="postgresql+psycopg",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_SERVER,
            port=self.POSTGRES_PORT,
            path=self.POSTGRES_DB,
        )


@lru_cache
def get_settings() -> Settings:
    """Return a cached ``Settings`` instance."""
    return Settings()
