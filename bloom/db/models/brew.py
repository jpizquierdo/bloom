"""Brew model: a single extraction — the central entity (2, 7)."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    Text,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from bloom.db.base import Base

if TYPE_CHECKING:
    from bloom.db.models.bean import Bean
    from bloom.db.models.bean_lot import BeanLot
    from bloom.db.models.brew_method import BrewMethod
    from bloom.db.models.equipment import Equipment
    from bloom.db.models.tasting import Tasting
    from bloom.db.models.user import User


class Brew(Base):
    """A single extraction and its objective parameters.

    ``ratio`` is never stored (computed in the domain layer). ``tds_percent``
    and ``extraction_yield_percent`` are real refractometer measurements; EY is
    computed once at write time when only TDS is provided.

    ``user_id`` is the **author** — who prepared this brew. Beans are shared
    across the instance, so the author is not necessarily the bean's owner.
    """

    __tablename__ = "brew"
    __table_args__ = (
        CheckConstraint("dose_grams > 0", name="ck_brew_dose_positive"),
        CheckConstraint("yield_grams > 0", name="ck_brew_yield_positive"),
        CheckConstraint("water_grams > 0", name="ck_brew_water_positive"),
        CheckConstraint("brew_time_seconds > 0", name="ck_brew_time_positive"),
        CheckConstraint("tds_percent >= 0", name="ck_brew_tds_nonneg"),
        CheckConstraint("extraction_yield_percent >= 0", name="ck_brew_ey_nonneg"),
        Index("idx_brew_bean_id", "bean_id"),
        Index("idx_brew_lot_id", "lot_id"),
        Index("idx_brew_method_id", "method_id"),
        Index("idx_brew_user_id", "user_id"),
        Index("idx_brew_brewed_at", text("brewed_at DESC")),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # Author: who prepared the brew. RESTRICT pairs with user soft-delete.
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="RESTRICT"), nullable=False)
    bean_id: Mapped[int] = mapped_column(ForeignKey("bean.id", ondelete="CASCADE"), nullable=False)
    # Optional: which physical lot this brew came from. SET NULL preserves brew history.
    lot_id: Mapped[int | None] = mapped_column(ForeignKey("bean_lot.id", ondelete="SET NULL"))
    method_id: Mapped[int] = mapped_column(
        SmallInteger,
        ForeignKey("brew_method.id", ondelete="RESTRICT"),
        nullable=False,
    )
    grinder_id: Mapped[int | None] = mapped_column(ForeignKey("equipment.id", ondelete="SET NULL"))
    brewed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    dose_grams: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    yield_grams: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))
    water_grams: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))
    grind_setting: Mapped[str | None] = mapped_column(Text)
    water_temp_celsius: Mapped[Decimal | None] = mapped_column(Numeric(4, 1))
    brew_time_seconds: Mapped[int | None] = mapped_column(Integer)

    # Measured extraction (nullable; requires a refractometer)
    tds_percent: Mapped[Decimal | None] = mapped_column(Numeric(4, 2))
    extraction_yield_percent: Mapped[Decimal | None] = mapped_column(Numeric(4, 2))

    notes: Mapped[str | None] = mapped_column(Text)

    author: Mapped[User] = relationship()
    bean: Mapped[Bean] = relationship(back_populates="brews")
    lot: Mapped[BeanLot | None] = relationship()
    method: Mapped[BrewMethod] = relationship()
    grinder: Mapped[Equipment | None] = relationship()
    tastings: Mapped[list[Tasting]] = relationship(back_populates="brew", cascade="all, delete-orphan", passive_deletes=True)
