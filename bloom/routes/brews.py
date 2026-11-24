"""Brew routes. Reads are shared; writes are author-only. Responses include
computed ratio/diagnostics."""

from typing import Annotated

from fastapi import APIRouter, Query, Response, status

from bloom.core.dependencies import CurrentUser, DbSession
from bloom.schemas.brew import BrewCreate, BrewFilters, BrewPage, BrewRead, BrewUpdate
from bloom.services import brew_service

router = APIRouter(prefix="/brews", tags=["brews"])


@router.post("", response_model=BrewRead, status_code=status.HTTP_201_CREATED)
def create_brew(data: BrewCreate, db: DbSession, user: CurrentUser) -> BrewRead:
    """Create a brew from any bean; you are recorded as its author.

    Extraction yield is computed and stored when only TDS (and beverage mass) is
    given. The response includes the computed brew ratio and control-chart diagnostics.
    """
    brew = brew_service.create_brew(db, data, user)
    return brew_service.serialize(brew, user)


@router.get("", response_model=BrewPage)
def list_brews(filters: Annotated[BrewFilters, Query()], db: DbSession, user: CurrentUser) -> BrewPage:
    """One page of the shared brew log, most recent first, with the total matching the filters.

    Any authenticated user. Each brew carries your own tasting of it (`my_tasting`), if any.
    """
    brews, total = brew_service.list_brews(db, user, filters)
    return BrewPage(items=[brew_service.serialize(brew, user) for brew in brews], total=total)


@router.get("/{brew_id}", response_model=BrewRead)
def get_brew(brew_id: int, db: DbSession, user: CurrentUser) -> BrewRead:
    """Get a brew by id (any authenticated user), with computed ratio and diagnostics."""
    return brew_service.serialize(brew_service.get_brew(db, brew_id), user)


@router.patch("/{brew_id}", response_model=BrewRead)
def update_brew(brew_id: int, data: BrewUpdate, db: DbSession, user: CurrentUser) -> BrewRead:
    """Update a brew. Only its author (or an admin) may edit it."""
    brew = brew_service.get_owned_brew(db, brew_id, user)
    return brew_service.serialize(brew_service.update_brew(db, brew, data), user)


@router.delete("/{brew_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_brew(brew_id: int, db: DbSession, user: CurrentUser) -> Response:
    """Delete a brew (cascades to its tastings). Author or admin only."""
    brew = brew_service.get_owned_brew(db, brew_id, user)
    brew_service.delete_brew(db, brew)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
