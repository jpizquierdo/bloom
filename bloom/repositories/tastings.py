"""Tasting repository — the only place that runs SQL for tastings."""

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from bloom.db.models.tasting import Tasting


def get(db: Session, tasting_id: int) -> Tasting | None:
    return db.get(Tasting, tasting_id)


def list_for_brew(db: Session, brew_id: int) -> list[Tasting]:
    stmt = select(Tasting).where(Tasting.brew_id == brew_id).order_by(Tasting.id)
    return list(db.execute(stmt).scalars().all())


def list_page(db: Session, *, limit: int, offset: int, author_id: int | None = None) -> tuple[list[Tasting], int]:
    """One page of tastings (most recent first), optionally only ``author_id``'s, plus the total."""
    stmt = select(Tasting)
    if author_id is not None:
        stmt = stmt.where(Tasting.user_id == author_id)
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    page = stmt.options(joinedload(Tasting.brew), joinedload(Tasting.author)).order_by(Tasting.id.desc()).limit(limit).offset(offset)
    return list(db.execute(page).scalars().all()), total


def get_for_brew_user(db: Session, brew_id: int, user_id: int) -> Tasting | None:
    """Fetch ``user_id``'s tasting of ``brew_id``, if any (at most one exists)."""
    stmt = select(Tasting).where(Tasting.brew_id == brew_id, Tasting.user_id == user_id)
    return db.execute(stmt).scalars().first()


def add_if_absent(db: Session, *, brew_id: int, user_id: int, **fields: Any) -> Tasting | None:
    """Insert a tasting, or return ``None`` if ``(brew_id, user_id)`` already has one.

    Runs in a savepoint so losing a race against a concurrent insert leaves the caller's
    transaction usable.
    """
    try:
        with db.begin_nested():
            tasting = Tasting(brew_id=brew_id, user_id=user_id, **fields)
            db.add(tasting)
            db.flush()
            return tasting
    except IntegrityError:
        return None


def delete(db: Session, tasting: Tasting) -> None:
    db.delete(tasting)
