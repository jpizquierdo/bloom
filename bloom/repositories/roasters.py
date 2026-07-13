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
    """Look a roaster up case-insensitively.

    Both sides are folded by ``lower()`` in the database, never in Python: the unique
    index is ``lower(name)`` under the DB's collation, and Python's ``str.lower()`` does
    not always agree with it (Turkish ``İ``, for one). A disagreement would let this
    lookup miss a row the index still rejects as a duplicate.
    """
    stmt = select(Roaster).where(func.lower(Roaster.name) == func.lower(name))
    return db.execute(stmt).scalar_one_or_none()


def list_all(db: Session) -> list[Roaster]:
    return list(db.execute(select(Roaster).order_by(func.lower(Roaster.name))).scalars().all())


def add_if_absent(db: Session, *, name: str, **fields: Any) -> Roaster | None:
    """Insert a roaster, or return ``None`` if the unique lower(name) index rejects it.

    The insert runs in a savepoint so that losing the race against a concurrent insert
    of the same name does not poison the caller's transaction.
    """
    try:
        with db.begin_nested():
            roaster = Roaster(name=name, **fields)
            db.add(roaster)
            db.flush()
            return roaster
    except IntegrityError:
        return None


def get_or_create(db: Session, *, name: str) -> Roaster:
    """Return the roaster named ``name``, creating it if nobody has used it yet."""
    existing = get_by_name(db, name)
    if existing is not None:
        return existing
    created = add_if_absent(db, name=name)
    if created is not None:
        return created
    concurrent = get_by_name(db, name)
    if concurrent is None:
        raise RuntimeError(f"Roaster '{name}' was rejected as a duplicate but cannot be found")
    return concurrent


def try_update(db: Session, roaster: Roaster, changes: dict[str, Any]) -> bool:
    """Apply ``changes``; return ``False`` if the new name collides with another roaster."""
    try:
        with db.begin_nested():
            for field, value in changes.items():
                setattr(roaster, field, value)
            db.flush()
    except IntegrityError:
        return False
    return True


def try_delete(db: Session, roaster: Roaster) -> bool:
    """Delete a roaster; return ``False`` if beans still reference it (FK RESTRICT)."""
    try:
        with db.begin_nested():
            db.delete(roaster)
            db.flush()
    except IntegrityError:
        return False
    return True


def count_beans(db: Session, roaster_id: int) -> int:
    stmt = select(func.count()).select_from(Bean).where(Bean.roaster_id == roaster_id)
    return db.execute(stmt).scalar_one()


def reassign_beans(db: Session, *, source_id: int, target_id: int) -> int:
    """Point every bean of ``source_id`` at ``target_id``; return how many moved."""
    stmt = update(Bean).where(Bean.roaster_id == source_id).values(roaster_id=target_id)
    return db.execute(stmt).rowcount
