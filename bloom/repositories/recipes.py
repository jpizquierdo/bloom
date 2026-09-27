"""Recipe repository — the only place that runs SQL for recipes."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from bloom.db.models.recipe import Recipe


def get(db: Session, recipe_id: int) -> Recipe | None:
    return db.get(Recipe, recipe_id)


def list_for_bean(db: Session, bean_id: int) -> list[Recipe]:
    stmt = select(Recipe).where(Recipe.bean_id == bean_id).order_by(Recipe.id)
    return list(db.execute(stmt).scalars().all())


def add(db: Session, *, bean_id: int, user_id: int, **fields: Any) -> Recipe:
    recipe = Recipe(bean_id=bean_id, user_id=user_id, **fields)
    db.add(recipe)
    db.flush()
    return recipe


def delete(db: Session, recipe: Recipe) -> None:
    db.delete(recipe)
