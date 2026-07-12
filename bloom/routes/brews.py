"""Brew routes. Reads are shared; writes are author-only. Responses include
computed ratio/diagnostics."""

from fastapi import APIRouter, Response, status

from bloom.core.dependencies import CurrentUser, DbSession
from bloom.schemas.brew import BrewCreate, BrewRead, BrewUpdate
from bloom.services import brew_service

router = APIRouter(prefix="/brews", tags=["brews"])


@router.post("", response_model=BrewRead, status_code=status.HTTP_201_CREATED)
def create_brew(data: BrewCreate, db: DbSession, user: CurrentUser) -> BrewRead:
    brew = brew_service.create_brew(db, data, user)
    return brew_service.serialize(brew)


@router.get("", response_model=list[BrewRead])
def list_brews(db: DbSession, user: CurrentUser, mine: bool = False) -> list[BrewRead]:
    brews = brew_service.list_brews(db, user, mine=mine)
    return [brew_service.serialize(brew) for brew in brews]


@router.get("/{brew_id}", response_model=BrewRead)
def get_brew(brew_id: int, db: DbSession, _user: CurrentUser) -> BrewRead:
    return brew_service.serialize(brew_service.get_brew(db, brew_id))


@router.patch("/{brew_id}", response_model=BrewRead)
def update_brew(
    brew_id: int, data: BrewUpdate, db: DbSession, user: CurrentUser
) -> BrewRead:
    brew = brew_service.get_owned_brew(db, brew_id, user)
    return brew_service.serialize(brew_service.update_brew(db, brew, data))


@router.delete("/{brew_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_brew(brew_id: int, db: DbSession, user: CurrentUser) -> Response:
    brew = brew_service.get_owned_brew(db, brew_id, user)
    brew_service.delete_brew(db, brew)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
