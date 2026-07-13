"""Roaster repository — the only place that runs SQL for roasters."""

from typing import Any

from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from bloom.db.models.bean import Bean
from bloom.db.models.roaster import Roaster


def get(db: Session, roaster_id: int) -> Roaster | None:
    return db.get(Roaster, roaster_id)


def get_by_name(db: Session, name: str) -> Roaster | None:
    """Look a roaster up case-insensitively (matches the unique lower(name) index)."""
    stmt = select(Roaster).where(func.lower(Roaster.name) == name.lower())
    return db.execute(stmt).scalar_one_or_none()


def list_all(db: Session) -> list[Roaster]:
    return list(db.execute(select(Roaster).order_by(func.lower(Roaster.name))).scalars().all())


def add(db: Session, *, name: str, **fields: Any) -> Roaster:
    roaster = Roaster(name=name, **fields)
    db.add(roaster)
    db.flush()
    return roaster


def get_or_create(db: Session, *, name: str) -> Roaster:
    """Return the roaster named ``name``, creating it if nobody has used it yet."""
    existing = get_by_name(db, name)
    if existing is not None:
        return existing
    try:
        # Savepoint: a concurrent request may insert the same name between the
        # SELECT above and this INSERT; the unique index catches it and we re-read
        # without poisoning the caller's transaction.
        with db.begin_nested():
            return add(db, name=name)
    except IntegrityError:
        concurrent = get_by_name(db, name)
        if concurrent is None:
            raise
        return concurrent


def count_beans(db: Session, roaster_id: int) -> int:
    stmt = select(func.count()).select_from(Bean).where(Bean.roaster_id == roaster_id)
    return db.execute(stmt).scalar_one()


def reassign_beans(db: Session, *, source_id: int, target_id: int) -> int:
    """Point every bean of ``source_id`` at ``target_id``; return how many moved."""
    stmt = update(Bean).where(Bean.roaster_id == source_id).values(roaster_id=target_id)
    return db.execute(stmt).rowcount


def delete(db: Session, roaster: Roaster) -> None:
    db.delete(roaster)
