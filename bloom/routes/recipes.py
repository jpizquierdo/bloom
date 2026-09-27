"""Recipe routes — shared reads, creator-owned writes, and brew creation."""

from fastapi import APIRouter, Response, status

from bloom.core.dependencies import CurrentUser, DbSession
from bloom.schemas.brew import BrewRead
from bloom.schemas.recipe import BrewFromRecipeCreate, RecipeCreate, RecipeRead, RecipeUpdate
from bloom.services import brew_service, recipe_service

router = APIRouter(tags=["recipes"])


@router.post("/beans/{bean_id}/recipes", response_model=RecipeRead, status_code=status.HTTP_201_CREATED)
def create_recipe(bean_id: int, data: RecipeCreate, db: DbSession, user: CurrentUser) -> RecipeRead:
    """Create a recipe for any shared bean; you are recorded as its creator."""
    return recipe_service.create_recipe(db, bean_id, data, user)


@router.get("/beans/{bean_id}/recipes", response_model=list[RecipeRead])
def list_recipes(bean_id: int, db: DbSession, _user: CurrentUser) -> list[RecipeRead]:
    """List a bean's recipes. Any authenticated user may read them."""
    return recipe_service.list_for_bean(db, bean_id)


@router.get("/recipes/{recipe_id}", response_model=RecipeRead)
def get_recipe(recipe_id: int, db: DbSession, _user: CurrentUser) -> RecipeRead:
    """Get a recipe by id. Any authenticated user may read it."""
    return recipe_service.get_recipe(db, recipe_id)


@router.patch("/recipes/{recipe_id}", response_model=RecipeRead)
def update_recipe(recipe_id: int, data: RecipeUpdate, db: DbSession, user: CurrentUser) -> RecipeRead:
    """Update a recipe. Only its creator (or an admin) may edit it."""
    recipe = recipe_service.get_owned_recipe(db, recipe_id, user)
    return recipe_service.update_recipe(db, recipe, data)


@router.delete("/recipes/{recipe_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_recipe(recipe_id: int, db: DbSession, user: CurrentUser) -> Response:
    """Delete a recipe. Creator or admin only; existing brews remain unchanged."""
    recipe = recipe_service.get_owned_recipe(db, recipe_id, user)
    recipe_service.delete_recipe(db, recipe)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/recipes/{recipe_id}/brews", response_model=BrewRead, status_code=status.HTTP_201_CREATED)
def create_brew_from_recipe(
    recipe_id: int,
    data: BrewFromRecipeCreate,
    db: DbSession,
    user: CurrentUser,
) -> BrewRead:
    """Create a brew from a recipe snapshot; any authenticated user may use it."""
    brew = brew_service.create_brew_from_recipe(db, recipe_id, data, user)
    return brew_service.serialize(brew)
