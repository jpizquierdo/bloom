"""Roaster routes: anyone may add, only admins may edit, merge or delete."""

from fastapi import APIRouter, Response, status

from bloom.core.dependencies import AdminUser, CurrentUser, DbSession
from bloom.schemas.roaster import RoasterCreate, RoasterMerge, RoasterRead, RoasterUpdate
from bloom.services import roaster_service

router = APIRouter(prefix="/roasters", tags=["roasters"])


@router.get("", response_model=list[RoasterRead])
def list_roasters(db: DbSession, _user: CurrentUser) -> list[RoasterRead]:
    """List every roaster, alphabetically. Any authenticated user."""
    return roaster_service.list_roasters(db)


@router.get("/{roaster_id}", response_model=RoasterRead)
def get_roaster(roaster_id: int, db: DbSession, _user: CurrentUser) -> RoasterRead:
    """Get a roaster by id. Any authenticated user."""
    return roaster_service.get_roaster(db, roaster_id)


@router.post("", response_model=RoasterRead, status_code=status.HTTP_201_CREATED)
def create_roaster(data: RoasterCreate, db: DbSession, _user: CurrentUser) -> RoasterRead:
    """Create a roaster with its metadata. Any authenticated user; 409 if the name is taken.

    Not required to add a bean — posting a bean with an unknown roaster name creates it.
    """
    return roaster_service.create_roaster(db, data)


@router.patch("/{roaster_id}", response_model=RoasterRead)
def update_roaster(roaster_id: int, data: RoasterUpdate, db: DbSession, _admin: AdminUser) -> RoasterRead:
    """Edit or rename a roaster (every bean referencing it follows). Admin only."""
    return roaster_service.update_roaster(db, roaster_id, data)


@router.post("/{roaster_id}/merge", response_model=RoasterRead)
def merge_roaster(roaster_id: int, data: RoasterMerge, db: DbSession, _admin: AdminUser) -> RoasterRead:
    """Fold a duplicate into this roaster: its beans move here and it is deleted. Admin only."""
    return roaster_service.merge_roasters(db, target_id=roaster_id, source_id=data.source_id)


@router.delete("/{roaster_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_roaster(roaster_id: int, db: DbSession, _admin: AdminUser) -> Response:
    """Delete a roaster that has no beans. Admin only; 409 if it is still in use."""
    roaster_service.delete_roaster(db, roaster_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
