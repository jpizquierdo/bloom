"""Tasting repository — the only place that runs SQL for tastings."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from bloom.db.models.tasting import Tasting


def get(db: Session, tasting_id: int) -> Tasting | None:
    return db.get(Tasting, tasting_id)


def list_for_brew(db: Session, brew_id: int) -> list[Tasting]:
    stmt = select(Tasting).where(Tasting.brew_id == brew_id).order_by(Tasting.id)
    return list(db.execute(stmt).scalars().all())


def add(db: Session, *, brew_id: int, user_id: int, **fields: Any) -> Tasting:
    tasting = Tasting(brew_id=brew_id, user_id=user_id, **fields)
    db.add(tasting)
    db.flush()
    return tasting


def delete(db: Session, tasting: Tasting) -> None:
    db.delete(tasting)
