"""Bean-lot repository — the only place that runs SQL for bean lots."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from bloom.db.models.bean_lot import BeanLot


def get(db: Session, lot_id: int) -> BeanLot | None:
    return db.get(BeanLot, lot_id)


def list_for_bean(db: Session, bean_id: int) -> list[BeanLot]:
    """List a bean's lots, most recently purchased first (nulls last), then newest."""
    stmt = select(BeanLot).where(BeanLot.bean_id == bean_id).order_by(BeanLot.purchase_date.desc().nullslast(), BeanLot.id.desc())
    return list(db.execute(stmt).scalars().all())


def add(db: Session, *, bean_id: int, user_id: int, **fields: Any) -> BeanLot:
    lot = BeanLot(bean_id=bean_id, user_id=user_id, **fields)
    db.add(lot)
    db.flush()
    return lot


def delete(db: Session, lot: BeanLot) -> None:
    db.delete(lot)
