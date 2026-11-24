"""FastAPI application factory and entrypoint."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from importlib.metadata import version
from pathlib import Path

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from sqlalchemy import text
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware

from bloom.core.config import get_settings
from bloom.core.dependencies import get_db
from bloom.core.logger import configure_logging
from bloom.db import init_db
from bloom.routes import auth, bean_lots, beans, brew_methods, brews, equipment, recipes, roasters, tastings, users
from bloom.services.errors import BadRequestError, ConflictError, ForbiddenError, NotFoundError, UnprocessableError


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Run startup tasks: check the JWT secret and auth config, wait for the DB, migrate to head, bootstrap the admin.

    Several processes may start together: ``init_db`` serialises them with an advisory
    lock, and the ``db_is_at_head`` guard makes restarts cheap.
    """
    settings = get_settings()
    settings.require_strong_jwt_secret()
    settings.require_valid_auth_config()
    init_db.init_db()
    yield


# Service errors stay framework-agnostic; this is where each becomes an HTTP status.
DOMAIN_ERRORS: dict[type[Exception], tuple[int, str]] = {
    BadRequestError: (400, "Bad request"),
    ForbiddenError: (403, "Forbidden"),
    NotFoundError: (404, "Not found"),
    ConflictError: (409, "Conflict"),
    UnprocessableError: (422, "Unprocessable"),
}


async def _domain_error_handler(request: Request, exc: Exception) -> JSONResponse:
    status_code, default_detail = next(mapping for error, mapping in DOMAIN_ERRORS.items() if isinstance(exc, error))
    return JSONResponse(status_code=status_code, content={"detail": str(exc) or default_detail})


def custom_generate_unique_id(route: APIRoute) -> str:
    """Name operations ``<tag>-<handler>`` so generated clients get readable method names."""
    return f"{route.tags[0]}-{route.name}"


# The Docker build drops the compiled web UI here; in a source checkout it simply does not exist.
STATIC_DIR = Path(__file__).parent / "static"


def mount_frontend(app: FastAPI) -> None:
    """Serve the built web UI from the API's own origin, if it was bundled into the image.

    Same-origin means the UI calls the API with relative URLs, so one image works behind any
    hostname or reverse proxy, with no rebuild and no CORS. ``fallback="index.html"`` hands
    unknown browser navigations to the SPA so client-side routes like ``/brews/3`` survive a
    refresh, while missing assets and non-GET requests still get a real 404.
    """
    if not STATIC_DIR.is_dir():
        return

    app.frontend("/", directory=STATIC_DIR, fallback="index.html")


def create_app() -> FastAPI:
    """Build and configure the Bloom FastAPI application."""
    configure_logging()
    settings = get_settings()
    app = FastAPI(
        title="Bloom",
        version=version("bloom"),
        lifespan=lifespan,
        generate_unique_id_function=custom_generate_unique_id,
    )

    if settings.all_cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.all_cors_origins,
            # Auth is a bearer header, never a cookie, so credentialed requests are not needed.
            allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
            allow_headers=["Authorization", "Content-Type"],
        )

    if settings.oidc_enabled:
        # Only carries OIDC state, nonce and PKCE verifier across the IdP round-trip; API auth stays bearer.
        app.add_middleware(
            SessionMiddleware,
            secret_key=settings.JWT_SECRET,
            session_cookie="bloom_oidc",
            max_age=600,
            same_site="lax",
            https_only=settings.OIDC_REDIRECT_URI.startswith("https://"),
        )

    for error in DOMAIN_ERRORS:
        app.add_exception_handler(error, _domain_error_handler)

    # Deliberately outside the API prefix: container healthchecks probe /health.
    @app.get("/health", tags=["system"])
    def health(db: Session = Depends(get_db)) -> dict[str, str]:
        """Liveness/readiness check: confirms the API and its DB are reachable."""
        db.execute(text("SELECT 1"))
        return {"status": "ok", "db": "ok"}

    for router in (
        auth.router,
        users.router,
        roasters.router,
        beans.router,
        bean_lots.router,
        brew_methods.router,
        equipment.router,
        recipes.router,
        brews.router,
        tastings.router,
    ):
        app.include_router(router, prefix=settings.API_V1_STR)

    mount_frontend(app)

    return app


app = create_app()
