"""Brew-method routes: reads for any user, writes for admins (3A lookup table)."""

from fastapi import APIRouter, status

from bloom.core.dependencies import AdminUser, CurrentUser, DbSession
from bloom.schemas.lookups import BrewMethodCreate, BrewMethodRead
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
