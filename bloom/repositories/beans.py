"""Bean repository — the only place that runs SQL for beans."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from bloom.db.models.bean import Bean


def get(db: Session, bean_id: int) -> Bean | None:
    return db.get(Bean, bean_id)


def list_for_user(db: Session, user_id: int | None) -> list[Bean]:
    """List beans, filtered to ``user_id`` unless it is ``None`` (admin: all)."""
    stmt = select(Bean).order_by(Bean.id)
    if user_id is not None:
        stmt = stmt.where(Bean.user_id == user_id)
    return list(db.execute(stmt).scalars().all())


def add(db: Session, *, user_id: int, **fields: Any) -> Bean:
    bean = Bean(user_id=user_id, **fields)
    db.add(bean)
    db.flush()
    return bean


def delete(db: Session, bean: Bean) -> None:
    db.delete(bean)
