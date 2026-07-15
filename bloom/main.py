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

from bloom.core.config import get_settings
from bloom.core.dependencies import get_db
from bloom.core.logger import configure_logging
from bloom.db import init_db
from bloom.routes import auth, bean_lots, beans, brew_methods, brews, equipment, roasters, tastings, users
from bloom.services.errors import ConflictError, ForbiddenError, NotFoundError, UnprocessableError


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Run startup tasks: wait for the DB, migrate to head, bootstrap the admin.

    Single-instance deployment, so migrating in-process is safe; the
    ``db_is_at_head`` guard makes restarts cheap.
    """
    init_db.init_db()
    yield


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
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    @app.exception_handler(NotFoundError)
    async def _not_found_handler(request: Request, exc: NotFoundError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc) or "Not found"})

    @app.exception_handler(ForbiddenError)
    async def _forbidden_handler(request: Request, exc: ForbiddenError) -> JSONResponse:
        return JSONResponse(status_code=403, content={"detail": str(exc) or "Forbidden"})

    @app.exception_handler(ConflictError)
    async def _conflict_handler(request: Request, exc: ConflictError) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detail": str(exc) or "Conflict"})

    @app.exception_handler(UnprocessableError)
    async def _unprocessable_handler(request: Request, exc: UnprocessableError) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": str(exc) or "Unprocessable"})

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
        brews.router,
        tastings.router,
    ):
        app.include_router(router, prefix=settings.API_V1_STR)

    mount_frontend(app)

    return app


app = create_app()
