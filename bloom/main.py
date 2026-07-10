"""FastAPI application factory and entrypoint."""

from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.orm import Session

from bloom.core.dependencies import get_db


def create_app() -> FastAPI:
    """Build and configure the Bloom FastAPI application."""
    app = FastAPI(title="Bloom", version="0.1.0")

    @app.get("/health", tags=["system"])
    def health(db: Session = Depends(get_db)) -> dict[str, str]:
        """Liveness/readiness check: confirms the API and its DB are reachable."""
        db.execute(text("SELECT 1"))
        return {"status": "ok", "db": "ok"}

    return app


app = create_app()
