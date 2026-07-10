"""FastAPI dependencies. Auth dependencies are added in Phase 3."""

from collections.abc import Iterator

from sqlalchemy.orm import Session

from bloom.db.session import SessionLocal


def get_db() -> Iterator[Session]:
    """Yield a database session, closing it when the request finishes."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
