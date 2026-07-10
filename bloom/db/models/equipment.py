"""Equipment model (5A: single table with a type discriminator)."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from bloom.db.base import Base


class Equipment(Base):
    """A grinder, espresso machine, kettle or other piece of gear."""

    __tablename__ = "equipment"
    __table_args__ = (
        CheckConstraint(
            "type IN ('grinder', 'espresso_machine', 'kettle', 'other')",
            name="ck_equipment_type",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    type: Mapped[str] = mapped_column(Text, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    brand: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
