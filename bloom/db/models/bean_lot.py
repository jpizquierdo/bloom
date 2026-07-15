"""Bean lot model (1: a physical purchase of a bean/coffee).

A ``bean`` is the coffee concept (name, roaster, origin…); a ``bean_lot`` is one
bag actually bought, with its own roast/purchase dates, price, weight and
finished flag. One coffee has many lots.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from bloom.db.base import Base

if TYPE_CHECKING:
    from bloom.db.models.bean import Bean
    from bloom.db.models.user import User


class BeanLot(Base):
    """A single purchase of a bean: the per-bag physical data."""

    __tablename__ = "bean_lot"
    __table_args__ = (
        CheckConstraint("weight_grams > 0", name="ck_bean_lot_weight_positive"),
        Index("idx_bean_lot_bean_id", "bean_id"),
        Index("idx_bean_lot_user_id", "user_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # CASCADE: deleting a coffee removes its lots (mirrors bean -> brew).
    bean_id: Mapped[int] = mapped_column(ForeignKey("bean.id", ondelete="CASCADE"), nullable=False)
    # Buyer/owner. RESTRICT pairs with user soft-delete.
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="RESTRICT"), nullable=False)
    roast_date: Mapped[date | None] = mapped_column(Date)
    purchase_date: Mapped[date | None] = mapped_column(Date)
    weight_grams: Mapped[int | None] = mapped_column(Integer)
    price: Mapped[Decimal | None] = mapped_column(Numeric(7, 2))
    is_finished: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    bean: Mapped[Bean] = relationship(back_populates="lots")
    owner: Mapped[User] = relationship()
