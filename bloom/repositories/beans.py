"""Bean repository — the only place that runs SQL for beans."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from bloom.db.models.bean import Bean


def get(db: Session, bean_id: int) -> Bean | None:
    return db.get(Bean, bean_id, options=[joinedload(Bean.roaster)])


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


def delete(db: Session, bean: Bean) -> None:
    db.delete(bean)
