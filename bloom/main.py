"""FastAPI application factory and entrypoint."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from bloom.core.dependencies import get_db
from bloom.db import init_db
from bloom.routes import auth, beans, brew_methods, brews, equipment, tastings, users
from bloom.services.errors import ForbiddenError, NotFoundError


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Run startup tasks: wait for the DB, migrate to head, bootstrap the admin.

    Single-instance deployment, so migrating in-process is safe; the
    ``db_is_at_head`` guard makes restarts cheap.
    """
    init_db.init_db()
    yield


def create_app() -> FastAPI:
    """Build and configure the Bloom FastAPI application."""
    app = FastAPI(title="Bloom", version="0.1.0", lifespan=lifespan)

    @app.exception_handler(NotFoundError)
    async def _not_found_handler(request: Request, exc: NotFoundError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc) or "Not found"})

    @app.exception_handler(ForbiddenError)
    async def _forbidden_handler(request: Request, exc: ForbiddenError) -> JSONResponse:
        return JSONResponse(status_code=403, content={"detail": str(exc) or "Forbidden"})

    @app.get("/health", tags=["system"])
    def health(db: Session = Depends(get_db)) -> dict[str, str]:
        """Liveness/readiness check: confirms the API and its DB are reachable."""
        db.execute(text("SELECT 1"))
        return {"status": "ok", "db": "ok"}

    app.include_router(auth.router)
    app.include_router(users.router)
    app.include_router(beans.router)
    app.include_router(brew_methods.router)
    app.include_router(equipment.router)
    app.include_router(brews.router)
    app.include_router(tastings.router)

    return app


app = create_app()
