"""Application settings, loaded from environment variables (and an optional .env)."""

from decimal import Decimal
from functools import lru_cache
from typing import Annotated, Any

from pydantic import AnyUrl, BeforeValidator, PostgresDsn, computed_field
from pydantic_core import MultiHostUrl
from pydantic_settings import BaseSettings, SettingsConfigDict

from bloom.domain import constants
from bloom.domain.calculations import ControlChartRanges

MIN_JWT_SECRET_LENGTH = 32


def parse_cors(value: Any) -> list[str] | str:
    """Accept CORS origins as a comma-separated string as well as a JSON list."""
    if isinstance(value, str) and not value.startswith("["):
        return [origin.strip() for origin in value.split(",") if origin.strip()]
    if isinstance(value, list | str):
        return value
    raise ValueError(value)


def _csv(value: str) -> set[str]:
    return {item.strip() for item in value.split(",") if item.strip()}


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

    # The default is a placeholder that fails the startup check; there is deliberately no usable one.
    JWT_SECRET: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_HOURS: int = 12
    RESET_TOKEN_EXPIRE_MINUTES: int = 30

    LOG_LEVEL: str = "INFO"

    # Brewing-control-chart target bands (inclusive), tunable per taste. Strength is TDS % and
    # each brew category has its own band (immersion brews stronger than filter, espresso far
    # more than either). The extraction-yield band is shared across every category.
    STRENGTH_RANGE_FILTER_LOW: Decimal = constants.STRENGTH_RANGE_FILTER[0]
    STRENGTH_RANGE_FILTER_HIGH: Decimal = constants.STRENGTH_RANGE_FILTER[1]
    STRENGTH_RANGE_IMMERSION_LOW: Decimal = constants.STRENGTH_RANGE_IMMERSION[0]
    STRENGTH_RANGE_IMMERSION_HIGH: Decimal = constants.STRENGTH_RANGE_IMMERSION[1]
    STRENGTH_RANGE_ESPRESSO_LOW: Decimal = constants.STRENGTH_RANGE_ESPRESSO[0]
    STRENGTH_RANGE_ESPRESSO_HIGH: Decimal = constants.STRENGTH_RANGE_ESPRESSO[1]
    EY_RANGE_LOW: Decimal = constants.EY_RANGE[0]
    EY_RANGE_HIGH: Decimal = constants.EY_RANGE[1]

    # Outgoing mail. With SMTP_HOST unset the app still boots and password-reset links are
    # written to the log instead of being sent.
    SMTP_HOST: str | None = None
    SMTP_PORT: int = 587
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_TLS: bool = True
    SMTP_SSL: bool = False
    EMAILS_FROM_EMAIL: str | None = None
    EMAILS_FROM_NAME: str = "Bloom"

    FRONTEND_HOST: str = "http://localhost:5173"
    BACKEND_CORS_ORIGINS: Annotated[list[AnyUrl] | str, BeforeValidator(parse_cors)] = []

    # Leave empty to skip the first-admin bootstrap.
    BLOOM_ADMIN_EMAIL: str | None = None
    BLOOM_ADMIN_PASSWORD: str | None = None

    # OpenID Connect single sign-on. Enabled once the issuer, client id/secret and redirect URI
    # are all set. Group lists are comma-separated; names may contain spaces.
    OIDC_ISSUER: str | None = None
    OIDC_CLIENT_ID: str | None = None
    OIDC_CLIENT_SECRET: str | None = None
    OIDC_REDIRECT_URI: str | None = None
    OIDC_SCOPES: str = "openid profile email"
    OIDC_AUTO_CREATE_USERS: bool = True
    OIDC_GROUPS_CLAIM: str = "groups"
    OIDC_ADMIN_GROUPS: str = ""
    OIDC_ALLOWED_GROUPS: str = ""
    OIDC_REQUIRE_EMAIL_VERIFIED: bool = True
    DISABLE_LOCAL_AUTH: bool = False

    def require_strong_jwt_secret(self) -> None:
        """Refuse to run with a placeholder or short signing key.

        Checked at startup rather than on construction, so tooling that only builds the app
        (OpenAPI dump, tests) does not need a real secret.
        """
        if len(self.JWT_SECRET) < MIN_JWT_SECRET_LENGTH:
            raise RuntimeError(
                f"JWT_SECRET must be at least {MIN_JWT_SECRET_LENGTH} characters; "
                "generate one with `openssl rand -hex 32` and set it in the environment or .env."
            )

    def require_valid_auth_config(self) -> None:
        """Refuse a half-configured OIDC client, or disabling local login with no SSO to replace it."""
        oidc_vars = (self.OIDC_ISSUER, self.OIDC_CLIENT_ID, self.OIDC_CLIENT_SECRET, self.OIDC_REDIRECT_URI)
        if any(oidc_vars) and not all(oidc_vars):
            raise RuntimeError("OIDC_ISSUER, OIDC_CLIENT_ID, OIDC_CLIENT_SECRET and OIDC_REDIRECT_URI must all be set to enable OIDC.")
        if self.DISABLE_LOCAL_AUTH and not self.oidc_enabled:
            raise RuntimeError("DISABLE_LOCAL_AUTH=true needs OIDC configured, otherwise nobody can log in.")

    @property
    def oidc_enabled(self) -> bool:
        """True when every required OIDC setting is present."""
        return all((self.OIDC_ISSUER, self.OIDC_CLIENT_ID, self.OIDC_CLIENT_SECRET, self.OIDC_REDIRECT_URI))

    @property
    def oidc_admin_groups(self) -> set[str]:
        """IdP groups that grant the admin role."""
        return _csv(self.OIDC_ADMIN_GROUPS)

    @property
    def oidc_allowed_groups(self) -> set[str]:
        """IdP groups allowed to log in; empty allows everyone."""
        return _csv(self.OIDC_ALLOWED_GROUPS)

    @property
    def control_chart_ranges(self) -> ControlChartRanges:
        """Assemble the tunable control-chart bands for the domain calculations."""
        return ControlChartRanges(
            strength_filter=(self.STRENGTH_RANGE_FILTER_LOW, self.STRENGTH_RANGE_FILTER_HIGH),
            strength_immersion=(self.STRENGTH_RANGE_IMMERSION_LOW, self.STRENGTH_RANGE_IMMERSION_HIGH),
            strength_espresso=(self.STRENGTH_RANGE_ESPRESSO_LOW, self.STRENGTH_RANGE_ESPRESSO_HIGH),
            extraction_yield=(self.EY_RANGE_LOW, self.EY_RANGE_HIGH),
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def emails_enabled(self) -> bool:
        """True when there is enough SMTP configuration to actually send mail."""
        return bool(self.SMTP_HOST and self.EMAILS_FROM_EMAIL)

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
