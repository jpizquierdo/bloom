"""Brew repository — the only place that runs SQL for brews."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from bloom.db.models.brew import Brew


def get(db: Session, brew_id: int) -> Brew | None:
    return db.get(Brew, brew_id)


def list_all(db: Session) -> list[Brew]:
    """List every brew (most recent first) — brews are a shared log."""
    return list(db.execute(select(Brew).order_by(Brew.brewed_at.desc())).scalars().all())


def list_for_author(db: Session, user_id: int) -> list[Brew]:
    """List brews authored by ``user_id`` (most recent first)."""
    stmt = select(Brew).where(Brew.user_id == user_id).order_by(Brew.brewed_at.desc())
    return list(db.execute(stmt).scalars().all())


def add(db: Session, **fields: Any) -> Brew:
    brew = Brew(**fields)
    db.add(brew)
    db.flush()
    return brew


def delete(db: Session, brew: Brew) -> None:
    db.delete(brew)
