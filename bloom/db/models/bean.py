"""Bean model (1: the coffee concept; its physical purchases live in bean_lot)."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from bloom.db.base import Base

if TYPE_CHECKING:
    from bloom.db.models.bean_lot import BeanLot
    from bloom.db.models.brew import Brew
    from bloom.db.models.roaster import Roaster
    from bloom.db.models.user import User


class Bean(Base):
    """A coffee (a farm/lot from a roaster): its stable identity, shared by everyone.

    The per-purchase physical data (roast/purchase dates, price, weight, finished
    flag) lives in ``bean_lot`` — one coffee bought several times has several lots.
    """

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
        Index("idx_bean_roaster_id", "roaster_id"),
        Index("idx_bean_user_id", "user_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # Ownership: a bean belongs to a user. RESTRICT protects brew history —
    # users are soft-deleted (is_active), never hard-deleted.
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="RESTRICT"), nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    # RESTRICT: a roaster with beans cannot be deleted — merge it into another instead.
    roaster_id: Mapped[int] = mapped_column(ForeignKey("roaster.id", ondelete="RESTRICT"), nullable=False)
    origin_country: Mapped[str | None] = mapped_column(Text)
    region: Mapped[str | None] = mapped_column(Text)
    producer: Mapped[str | None] = mapped_column(Text)
    variety: Mapped[str | None] = mapped_column(Text)
    process: Mapped[str | None] = mapped_column(Text)
    roast_level: Mapped[str | None] = mapped_column(Text)
    altitude_masl: Mapped[int | None] = mapped_column(Integer)
    tasting_notes_label: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    owner: Mapped[User] = relationship(back_populates="beans")
    roaster: Mapped[Roaster] = relationship(back_populates="beans")
    lots: Mapped[list[BeanLot]] = relationship(back_populates="bean", cascade="all, delete-orphan", passive_deletes=True)
    brews: Mapped[list[Brew]] = relationship(back_populates="bean", cascade="all, delete-orphan", passive_deletes=True)
