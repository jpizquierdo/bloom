"""Roaster model (13: user-creatable entity, get-or-create by name)."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, Index, Integer, Text, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from bloom.db.base import Base

if TYPE_CHECKING:
    from bloom.db.models.bean import Bean


class Roaster(Base):
    """A coffee roaster, created on demand when a bean first names it."""

    __tablename__ = "roaster"
    __table_args__ = (
        Index("uq_roaster_name_lower", text("lower(name)"), unique=True),
        CheckConstraint("btrim(name) <> ''", name="ck_roaster_name_not_blank"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    country: Mapped[str | None] = mapped_column(Text)
    city: Mapped[str | None] = mapped_column(Text)
    website: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # passive_deletes: let the FK's RESTRICT reject a delete that beans still reference,
    # instead of SQLAlchemy loading them to NULL out a NOT NULL column.
    beans: Mapped[list[Bean]] = relationship(back_populates="roaster", passive_deletes="all")
