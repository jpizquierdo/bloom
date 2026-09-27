"""Personal recipe favorite association."""

from sqlalchemy import ForeignKey, Index, Integer
from sqlalchemy.orm import Mapped, mapped_column

from bloom.db.base import Base


class RecipeFavorite(Base):
    """A user's bookmark of a shared recipe."""

    __tablename__ = "recipe_favorite"
    __table_args__ = (Index("idx_recipe_favorite_recipe_id", "recipe_id"),)

    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("user.id", ondelete="CASCADE"),
        primary_key=True,
    )
    recipe_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("recipe.id", ondelete="CASCADE"),
        primary_key=True,
    )
