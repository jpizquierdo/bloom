"""The OpenID Connect client, built once from settings (discovery is fetched lazily by Authlib)."""

from functools import cache

from authlib.integrations.starlette_client import OAuth, StarletteOAuth2App

from bloom.core.config import get_settings


@cache
def oidc_client() -> StarletteOAuth2App:
    """Return the configured OIDC client (Authorization Code + PKCE S256, ID token checked via JWKS)."""
    settings = get_settings()
    oauth = OAuth()
    return oauth.register(
        "oidc",
        client_id=settings.OIDC_CLIENT_ID,
        client_secret=settings.OIDC_CLIENT_SECRET,
        server_metadata_url=f"{settings.OIDC_ISSUER.rstrip('/')}/.well-known/openid-configuration",
        client_kwargs={"scope": settings.OIDC_SCOPES, "code_challenge_method": "S256"},
    )
