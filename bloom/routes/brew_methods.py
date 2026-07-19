"""Brew-method routes: reads for any user, writes for admins (lookup table, decision 3)."""

from fastapi import APIRouter, Response, status

from bloom.core.dependencies import AdminUser, CurrentUser, DbSession
from bloom.schemas.lookups import BrewMethodCreate, BrewMethodRead, BrewMethodUpdate
from bloom.services import lookups_service

router = APIRouter(prefix="/brew-methods", tags=["brew-methods"])


@router.get("", response_model=list[BrewMethodRead])
def list_brew_methods(db: DbSession, _user: CurrentUser) -> list[BrewMethodRead]:
    """List all brew methods. Any authenticated user."""
    return lookups_service.list_brew_methods(db)


@router.get("/{method_id}", response_model=BrewMethodRead)
def get_brew_method(method_id: int, db: DbSession, _user: CurrentUser) -> BrewMethodRead:
    """Get a brew method by id. Any authenticated user."""
    return lookups_service.get_brew_method(db, method_id)


@router.post("", response_model=BrewMethodRead, status_code=status.HTTP_201_CREATED)
def create_brew_method(data: BrewMethodCreate, db: DbSession, _admin: AdminUser) -> BrewMethodRead:
    """Create a brew method (shared lookup data). Admin only."""
    return lookups_service.create_brew_method(db, data)


@router.patch("/{method_id}", response_model=BrewMethodRead)
def update_brew_method(method_id: int, data: BrewMethodUpdate, db: DbSession, _admin: AdminUser) -> BrewMethodRead:
    """Edit a brew method (shared lookup data). Admin only; 409 if the name is taken."""
    return lookups_service.update_brew_method(db, method_id, data)


@router.delete("/{method_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_brew_method(method_id: int, db: DbSession, _admin: AdminUser) -> Response:
    """Delete a brew method. Admin only; 409 if a brew still uses it."""
    lookups_service.delete_brew_method(db, method_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
