"""Recipe business logic: shared reads and creator-owned writes."""

from sqlalchemy.orm import Session

from bloom.core.logger import get_logger
from bloom.db.models.recipe import Recipe
from bloom.db.models.user import User
from bloom.repositories import recipes as recipes_repo
from bloom.schemas.recipe import RecipeCreate, RecipeRead, RecipeUpdate
from bloom.services import bean_service, lookups_service
from bloom.services.access import owns_or_admin
from bloom.services.errors import ForbiddenError, NotFoundError

logger = get_logger(__name__)


def serialize(recipe: Recipe, *, is_favorite: bool = False) -> RecipeRead:
    """Shape a shared recipe with favorite state for the requesting user."""
    return RecipeRead.model_validate(recipe).model_copy(update={"is_favorite": is_favorite})


def list_for_bean(db: Session, bean_id: int, user_id: int) -> list[RecipeRead]:
    """List a bean's recipes after confirming the shared bean exists."""
    bean_service.get_bean(db, bean_id)
    recipes = recipes_repo.list_for_bean(db, bean_id)
    favorite_ids = recipes_repo.favorite_ids_for_user(db, user_id, [recipe.id for recipe in recipes])
    return [serialize(recipe, is_favorite=recipe.id in favorite_ids) for recipe in recipes]


def get_recipe(db: Session, recipe_id: int) -> Recipe:
    """Fetch a shared recipe, else raise NotFoundError."""
    recipe = recipes_repo.get(db, recipe_id)
    if recipe is None:
        raise NotFoundError("Recipe not found")
    return recipe


def get_recipe_read(db: Session, recipe_id: int, user_id: int) -> RecipeRead:
    """Fetch a shared recipe with favorite state for the requesting user."""
    recipe = get_recipe(db, recipe_id)
    favorite_ids = recipes_repo.favorite_ids_for_user(db, user_id, [recipe.id])
    return serialize(recipe, is_favorite=recipe.id in favorite_ids)


def get_owned_recipe(db: Session, recipe_id: int, user: User) -> Recipe:
    """Fetch a recipe its creator or an admin may modify."""
    recipe = get_recipe(db, recipe_id)
    if not owns_or_admin(user, recipe.user_id):
        raise ForbiddenError("You do not own this recipe")
    return recipe


def create_recipe(db: Session, bean_id: int, data: RecipeCreate, user: User) -> Recipe:
    """Create a recipe for any shared bean, owned by ``user``."""
    bean_service.get_bean(db, bean_id)
    lookups_service.get_brew_method(db, data.method_id)
    if data.grinder_id is not None:
        lookups_service.get_equipment(db, data.grinder_id)
    recipe = recipes_repo.add(db, bean_id=bean_id, user_id=user.id, **data.model_dump(exclude_none=True))
    db.commit()
    db.refresh(recipe)
    logger.info("Recipe %s created by user %s (bean %s)", recipe.id, user.id, bean_id)
    return recipe


def update_recipe(db: Session, recipe: Recipe, data: RecipeUpdate) -> Recipe:
    """Apply a partial update to an already-authorized recipe."""
    changes = data.model_dump(exclude_unset=True)
    if changes.get("method_id") is not None:
        lookups_service.get_brew_method(db, changes["method_id"])
    if changes.get("grinder_id") is not None:
        lookups_service.get_equipment(db, changes["grinder_id"])
    for field, value in changes.items():
        setattr(recipe, field, value)
    db.commit()
    db.refresh(recipe)
    logger.info("Recipe %s updated: %s", recipe.id, ", ".join(changes) or "no fields")
    return recipe


def delete_recipe(db: Session, recipe: Recipe) -> None:
    """Delete an already-authorized recipe without deleting its brews."""
    recipe_id = recipe.id
    recipes_repo.delete(db, recipe)
    db.commit()
    logger.info("Recipe %s deleted", recipe_id)


def favorite_recipe(db: Session, recipe_id: int, user: User) -> None:
    """Idempotently add the shared recipe to the user's personal favorites."""
    get_recipe(db, recipe_id)
    recipes_repo.add_favorite(db, recipe_id=recipe_id, user_id=user.id)
    db.commit()
    logger.info("Recipe %s favorited by user %s", recipe_id, user.id)


def unfavorite_recipe(db: Session, recipe_id: int, user: User) -> None:
    """Idempotently remove the shared recipe from the user's personal favorites."""
    get_recipe(db, recipe_id)
    recipes_repo.remove_favorite(db, recipe_id=recipe_id, user_id=user.id)
    db.commit()
    logger.info("Recipe %s unfavorited by user %s", recipe_id, user.id)
