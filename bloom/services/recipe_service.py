"""Recipe business logic: shared reads and creator-owned writes."""

from sqlalchemy.orm import Session

from bloom.core.logger import get_logger
from bloom.db.models.recipe import Recipe
from bloom.db.models.user import User
from bloom.repositories import recipes as recipes_repo
from bloom.schemas.recipe import RecipeCreate, RecipeUpdate
from bloom.services import bean_service, lookups_service
from bloom.services.access import owns_or_admin
from bloom.services.errors import ForbiddenError, NotFoundError

logger = get_logger(__name__)


def list_for_bean(db: Session, bean_id: int) -> list[Recipe]:
    """List a bean's recipes after confirming the shared bean exists."""
    bean_service.get_bean(db, bean_id)
    return recipes_repo.list_for_bean(db, bean_id)


def get_recipe(db: Session, recipe_id: int) -> Recipe:
    """Fetch a shared recipe, else raise NotFoundError."""
    recipe = recipes_repo.get(db, recipe_id)
    if recipe is None:
        raise NotFoundError("Recipe not found")
    return recipe


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
