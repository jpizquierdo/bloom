"""Application settings, loaded from environment variables (and an optional .env)."""

from functools import lru_cache
from typing import Annotated, Any

from pydantic import AnyUrl, BeforeValidator, PostgresDsn, computed_field
from pydantic_core import MultiHostUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


def parse_cors(value: Any) -> list[str] | str:
    """Accept CORS origins as a comma-separated string as well as a JSON list."""
    if isinstance(value, str) and not value.startswith("["):
        return [origin.strip() for origin in value.split(",") if origin.strip()]
    if isinstance(value, list | str):
        return value
    raise ValueError(value)


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

    API_V1_STR: str = "/api/v1"

    POSTGRES_USER: str = "bloom"
    POSTGRES_PASSWORD: str = "bloom"
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "bloom"

    JWT_SECRET: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    LOG_LEVEL: str = "INFO"

    FRONTEND_HOST: str = "http://localhost:5173"
    BACKEND_CORS_ORIGINS: Annotated[list[AnyUrl] | str, BeforeValidator(parse_cors)] = []

    # Leave empty to skip the first-admin bootstrap.
    BLOOM_ADMIN_EMAIL: str | None = None
    BLOOM_ADMIN_PASSWORD: str | None = None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def all_cors_origins(self) -> list[str]:
        """Origins allowed to call the API from a browser: the extras plus the frontend."""
        return [str(origin).rstrip("/") for origin in self.BACKEND_CORS_ORIGINS] + [self.FRONTEND_HOST]

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
