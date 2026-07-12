"""Brew method lookup table (3: lookup, not enum)."""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy import CheckConstraint, Numeric, SmallInteger, Text
from sqlalchemy.orm import Mapped, mapped_column

from bloom.db.base import Base


class BrewMethod(Base):
    """A brewing method (V60, Espresso, AeroPress…) with a category."""

    __tablename__ = "brew_method"
    __table_args__ = (
        CheckConstraint(
            "category IN ('espresso', 'filter', 'immersion')",
            name="ck_brew_method_category",
        ),
    )

    id: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    category: Mapped[str] = mapped_column(Text, nullable=False)
    default_ratio: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
