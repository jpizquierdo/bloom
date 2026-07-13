"""Tasting model: subjective evaluation of a brew (6, 8, 9)."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from bloom.db.base import Base

if TYPE_CHECKING:
    from bloom.db.models.brew import Brew
    from bloom.db.models.user import User

_SCORE_COLUMNS = (
    "aroma",
    "acidity",
    "sweetness",
    "body",
    "bitterness",
    "aftertaste",
    "overall",
)


class Tasting(Base):
    """A subjective evaluation of a brew; a brew may have several (1:N), and
    different users may each score the same brew (6). ``user_id`` records who
    tasted."""

    __tablename__ = "tasting"
    __table_args__ = (
        *(CheckConstraint(f"{column} BETWEEN 1 AND 10", name=f"ck_tasting_{column}_range") for column in _SCORE_COLUMNS),
        Index("idx_tasting_brew_id", "brew_id"),
        Index("idx_tasting_user_id", "user_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    brew_id: Mapped[int] = mapped_column(ForeignKey("brew.id", ondelete="CASCADE"), nullable=False)
    # Who tasted. RESTRICT pairs with user soft-delete.
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="RESTRICT"), nullable=False)
    aroma: Mapped[int | None] = mapped_column(SmallInteger)
    acidity: Mapped[int | None] = mapped_column(SmallInteger)
    sweetness: Mapped[int | None] = mapped_column(SmallInteger)
    body: Mapped[int | None] = mapped_column(SmallInteger)
    bitterness: Mapped[int | None] = mapped_column(SmallInteger)
    aftertaste: Mapped[int | None] = mapped_column(SmallInteger)
    overall: Mapped[int | None] = mapped_column(SmallInteger)
    descriptors: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, server_default=text("'{}'"), default=list)
    notes: Mapped[str | None] = mapped_column(Text)
    tasted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    brew: Mapped[Brew] = relationship(back_populates="tastings")
    author: Mapped[User] = relationship()
