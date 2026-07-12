"""Tasting routes — owner-scoped, nested under brews for create/list."""

from fastapi import APIRouter, Response, status

from bloom.core.dependencies import CurrentUser, DbSession
from bloom.schemas.tasting import TastingCreate, TastingRead, TastingUpdate
from bloom.services import tasting_service

router = APIRouter(tags=["tastings"])


@router.post(
    "/brews/{brew_id}/tastings",
    response_model=TastingRead,
    status_code=status.HTTP_201_CREATED,
)
def create_tasting(
    brew_id: int, data: TastingCreate, db: DbSession, user: CurrentUser
) -> TastingRead:
    """Add a tasting to any brew; you are recorded as its taster.

    A brew can be scored by several users, so multiple tastings per brew are allowed.
    """
    return tasting_service.create_tasting(db, brew_id, data, user)


@router.get("/brews/{brew_id}/tastings", response_model=list[TastingRead])
def list_tastings(brew_id: int, db: DbSession, _user: CurrentUser) -> list[TastingRead]:
    """List all tastings of a brew (shared). Any authenticated user."""
    return tasting_service.list_for_brew(db, brew_id)


@router.get("/tastings", response_model=list[TastingRead])
def list_all_tastings(db: DbSession, user: CurrentUser, mine: bool = False) -> list[TastingRead]:
    """List the shared tasting log. Use `?mine=true` to return only your own tastings."""
    return tasting_service.list_tastings(db, user, mine=mine)


@router.get("/tastings/{tasting_id}", response_model=TastingRead)
def get_tasting(tasting_id: int, db: DbSession, _user: CurrentUser) -> TastingRead:
    """Get a tasting by id. Any authenticated user."""
    return tasting_service.get_tasting(db, tasting_id)


@router.patch("/tastings/{tasting_id}", response_model=TastingRead)
def update_tasting(
    tasting_id: int, data: TastingUpdate, db: DbSession, user: CurrentUser
) -> TastingRead:
    """Update a tasting. Only its author (or an admin) may edit it."""
    tasting = tasting_service.get_owned_tasting(db, tasting_id, user)
    return tasting_service.update_tasting(db, tasting, data)


@router.delete("/tastings/{tasting_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tasting(tasting_id: int, db: DbSession, user: CurrentUser) -> Response:
    """Delete a tasting. Only its author (or an admin) may delete it."""
    tasting = tasting_service.get_owned_tasting(db, tasting_id, user)
    tasting_service.delete_tasting(db, tasting)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
