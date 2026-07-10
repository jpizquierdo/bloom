"""Brew repository — the only place that runs SQL for brews."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from bloom.db.models.bean import Bean
from bloom.db.models.brew import Brew


def get(db: Session, brew_id: int) -> Brew | None:
    return db.get(Brew, brew_id)


def list_for_user(db: Session, user_id: int | None) -> list[Brew]:
    """List brews (most recent first), scoped to an owner via the parent bean.

    ``user_id`` of ``None`` returns every brew (admin view).
    """
    stmt = select(Brew).order_by(Brew.brewed_at.desc())
    if user_id is not None:
        stmt = stmt.join(Bean, Brew.bean_id == Bean.id).where(Bean.user_id == user_id)
    return list(db.execute(stmt).scalars().all())


def add(db: Session, **fields: Any) -> Brew:
    brew = Brew(**fields)
    db.add(brew)
    db.flush()
    return brew


def delete(db: Session, brew: Brew) -> None:
    db.delete(brew)
