"""Bean model (1: a physical bag/lot; 4: process as TEXT + CHECK)."""

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
    Text,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from bloom.db.base import Base

if TYPE_CHECKING:
    from bloom.db.models.brew import Brew
    from bloom.db.models.user import User


class Bean(Base):
    """A physical bag/lot of coffee, owned by a user."""

    __tablename__ = "bean"
    __table_args__ = (
        CheckConstraint(
            "process IN ('washed', 'natural', 'honey', 'anaerobic', 'carbonic_maceration', 'other')",
            name="ck_bean_process",
        ),
        CheckConstraint(
            "roast_level IN ('light', 'medium_light', 'medium', 'medium_dark', 'dark')",
            name="ck_bean_roast_level",
        ),
        CheckConstraint("weight_grams > 0", name="ck_bean_weight_positive"),
        Index("idx_bean_roaster", "roaster"),
        Index("idx_bean_user_id", "user_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # Ownership: a bean belongs to a user. RESTRICT protects brew history —
    # users are soft-deleted (is_active), never hard-deleted.
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="RESTRICT"), nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    roaster: Mapped[str] = mapped_column(Text, nullable=False)
    origin_country: Mapped[str | None] = mapped_column(Text)
    region: Mapped[str | None] = mapped_column(Text)
    producer: Mapped[str | None] = mapped_column(Text)
    variety: Mapped[str | None] = mapped_column(Text)
    process: Mapped[str | None] = mapped_column(Text)
    roast_level: Mapped[str | None] = mapped_column(Text)
    roast_date: Mapped[date | None] = mapped_column(Date)
    purchase_date: Mapped[date | None] = mapped_column(Date)
    weight_grams: Mapped[int | None] = mapped_column(Integer)
    price: Mapped[Decimal | None] = mapped_column(Numeric(7, 2))
    altitude_masl: Mapped[int | None] = mapped_column(Integer)
    tasting_notes_label: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)
    is_finished: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    owner: Mapped[User] = relationship(back_populates="beans")
    brews: Mapped[list[Brew]] = relationship(back_populates="bean", cascade="all, delete-orphan", passive_deletes=True)
