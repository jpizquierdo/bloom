"""Recipe model: reusable brewing intent for a bean."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, Numeric, SmallInteger, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from bloom.db.base import Base

if TYPE_CHECKING:
    from bloom.db.models.bean import Bean
    from bloom.db.models.brew import Brew
    from bloom.db.models.brew_method import BrewMethod
    from bloom.db.models.equipment import Equipment
    from bloom.db.models.user import User


class Recipe(Base):
    """Reusable preparation parameters for a bean, shared across the instance."""

    __tablename__ = "recipe"
    __table_args__ = (
        CheckConstraint("btrim(name) <> ''", name="ck_recipe_name_not_blank"),
        CheckConstraint("dose_grams > 0", name="ck_recipe_dose_positive"),
        CheckConstraint("yield_grams > 0", name="ck_recipe_yield_positive"),
        CheckConstraint("water_grams > 0", name="ck_recipe_water_positive"),
        CheckConstraint("brew_time_seconds > 0", name="ck_recipe_time_positive"),
        Index("idx_recipe_bean_id", "bean_id"),
        Index("idx_recipe_method_id", "method_id"),
        Index("idx_recipe_user_id", "user_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="RESTRICT"), nullable=False)
    bean_id: Mapped[int] = mapped_column(ForeignKey("bean.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    method_id: Mapped[int] = mapped_column(
        SmallInteger,
        ForeignKey("brew_method.id", ondelete="RESTRICT"),
        nullable=False,
    )
    grinder_id: Mapped[int | None] = mapped_column(ForeignKey("equipment.id", ondelete="SET NULL"))
    dose_grams: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    yield_grams: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))
    water_grams: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))
    grind_setting: Mapped[str | None] = mapped_column(Text)
    water_temp_celsius: Mapped[Decimal | None] = mapped_column(Numeric(4, 1))
    brew_time_seconds: Mapped[int | None] = mapped_column(Integer)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    owner: Mapped[User] = relationship(back_populates="recipes")
    bean: Mapped[Bean] = relationship(back_populates="recipes")
    method: Mapped[BrewMethod] = relationship()
    grinder: Mapped[Equipment | None] = relationship()
    brews: Mapped[list[Brew]] = relationship(back_populates="recipe", passive_deletes="all")
