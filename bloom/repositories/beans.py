"""Bean repository — the only place that runs SQL for beans."""

from typing import Any

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session, joinedload

from bloom.db.models.bean import Bean
from bloom.db.models.bean_lot import BeanLot
from bloom.db.models.brew import Brew
from bloom.db.models.recipe import Recipe


def get(db: Session, bean_id: int) -> Bean | None:
    return db.get(Bean, bean_id, options=[joinedload(Bean.roaster)])


def get_duplicate(db: Session, *, roaster_id: int, name: str, exclude_id: int | None = None) -> Bean | None:
    """Find another bean with the same name under the same roaster, case-insensitively.

    Both sides are folded by ``lower()`` in the database, never in Python: Python's
    ``str.lower()`` does not always agree with the DB collation (Turkish ``İ``), and a
    disagreement would let this miss a duplicate the user does consider one.
    """
    stmt = select(Bean).where(Bean.roaster_id == roaster_id, func.lower(Bean.name) == func.lower(name))
    if exclude_id is not None:
        stmt = stmt.where(Bean.id != exclude_id)
    return db.execute(stmt.order_by(Bean.id).limit(1)).scalars().first()


def list_all(db: Session) -> list[Bean]:
    """List every bean — beans are shared across the instance."""
    stmt = select(Bean).options(joinedload(Bean.roaster)).order_by(Bean.id)
    return list(db.execute(stmt).scalars().all())


def list_for_owner(db: Session, user_id: int) -> list[Bean]:
    """List beans owned by ``user_id``."""
    stmt = select(Bean).options(joinedload(Bean.roaster)).where(Bean.user_id == user_id).order_by(Bean.id)
    return list(db.execute(stmt).scalars().all())


def add(db: Session, *, user_id: int, **fields: Any) -> Bean:
    bean = Bean(user_id=user_id, **fields)
    db.add(bean)
    db.flush()
    return bean


def reassign_children(db: Session, *, source_id: int, target_id: int) -> tuple[int, int, int]:
    """Move every brew, lot and recipe of ``source_id`` onto ``target_id``."""
    brews = db.execute(
        update(Brew).where(Brew.bean_id == source_id).values(bean_id=target_id).execution_options(synchronize_session=False)
    ).rowcount
    lots = db.execute(
        update(BeanLot).where(BeanLot.bean_id == source_id).values(bean_id=target_id).execution_options(synchronize_session=False)
    ).rowcount
    recipes = db.execute(
        update(Recipe).where(Recipe.bean_id == source_id).values(bean_id=target_id).execution_options(synchronize_session=False)
    ).rowcount
    return brews, lots, recipes


def delete(db: Session, bean: Bean) -> None:
    db.delete(bean)
