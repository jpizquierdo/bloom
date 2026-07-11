"""Bean repository — the only place that runs SQL for beans."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from bloom.db.models.bean import Bean


def get(db: Session, bean_id: int) -> Bean | None:
    return db.get(Bean, bean_id)


def list_all(db: Session) -> list[Bean]:
    """List every bean — beans are shared across the instance."""
    return list(db.execute(select(Bean).order_by(Bean.id)).scalars().all())


def add(db: Session, *, user_id: int, **fields: Any) -> Bean:
    bean = Bean(user_id=user_id, **fields)
    db.add(bean)
    db.flush()
    return bean


def delete(db: Session, bean: Bean) -> None:
    db.delete(bean)
