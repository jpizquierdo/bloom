"""Recipe repository — the only place that runs SQL for recipes."""

from typing import Any

from sqlalchemy import delete as sql_delete
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from bloom.db.models.recipe import Recipe
from bloom.db.models.recipe_favorite import RecipeFavorite


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


def favorite_ids_for_user(db: Session, user_id: int, recipe_ids: list[int]) -> set[int]:
    stmt = select(RecipeFavorite.recipe_id).where(
        RecipeFavorite.user_id == user_id,
        RecipeFavorite.recipe_id.in_(recipe_ids),
    )
    return set(db.execute(stmt).scalars().all())


def add_favorite(db: Session, *, recipe_id: int, user_id: int) -> None:
    stmt = insert(RecipeFavorite).values(recipe_id=recipe_id, user_id=user_id).on_conflict_do_nothing()
    db.execute(stmt)


def remove_favorite(db: Session, *, recipe_id: int, user_id: int) -> None:
    stmt = sql_delete(RecipeFavorite).where(
        RecipeFavorite.recipe_id == recipe_id,
        RecipeFavorite.user_id == user_id,
    )
    db.execute(stmt)
