"""FastAPI application factory and entrypoint."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.orm import Session

from bloom.core.dependencies import get_db
from bloom.db.session import SessionLocal
from bloom.routes import auth, users
from bloom.services import auth_service


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Run startup tasks: bootstrap the configured first admin if needed."""
    db = SessionLocal()
    try:
        auth_service.bootstrap_admin(db)
    finally:
        db.close()
    yield


def create_app() -> FastAPI:
    """Build and configure the Bloom FastAPI application."""
    app = FastAPI(title="Bloom", version="0.1.0", lifespan=lifespan)

    @app.get("/health", tags=["system"])
    def health(db: Session = Depends(get_db)) -> dict[str, str]:
        """Liveness/readiness check: confirms the API and its DB are reachable."""
        db.execute(text("SELECT 1"))
        return {"status": "ok", "db": "ok"}

    app.include_router(auth.router)
    app.include_router(users.router)

    return app


app = create_app()
