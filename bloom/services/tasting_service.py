"""Tasting business logic; ownership is resolved through the parent brew's bean."""

from sqlalchemy.orm import Session

from bloom.db.models.tasting import Tasting
from bloom.db.models.user import User
from bloom.repositories import tastings as tastings_repo
from bloom.schemas.tasting import TastingCreate, TastingUpdate
from bloom.services import brew_service
from bloom.services.access import owns_or_admin
from bloom.services.errors import NotFoundError


def list_for_brew(db: Session, brew_id: int, user: User) -> list[Tasting]:
    """List a brew's tastings, after confirming the user may see the brew."""
    brew_service.get_brew(db, brew_id, user)  # raises NotFoundError if inaccessible
    return tastings_repo.list_for_brew(db, brew_id)


def get_tasting(db: Session, tasting_id: int, user: User) -> Tasting:
    """Fetch a tasting the user may access (via the brew's author), else 404."""
    tasting = tastings_repo.get(db, tasting_id)
    if tasting is None or not owns_or_admin(user, tasting.brew.user_id):
        raise NotFoundError("Tasting not found")
    return tasting


def create_tasting(
    db: Session, brew_id: int, data: TastingCreate, user: User
) -> Tasting:
    """Add a tasting to a brew the user owns (or any brew, for an admin)."""
    brew_service.get_brew(db, brew_id, user)  # authorize against the brew
    tasting = tastings_repo.add(
        db, brew_id=brew_id, **data.model_dump(exclude_none=True)
    )
    db.commit()
    db.refresh(tasting)
    return tasting


def update_tasting(db: Session, tasting: Tasting, data: TastingUpdate) -> Tasting:
    """Apply a partial update to an already-authorized tasting."""
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(tasting, field, value)
    db.commit()
    db.refresh(tasting)
    return tasting


def delete_tasting(db: Session, tasting: Tasting) -> None:
    """Delete an already-authorized tasting."""
    tastings_repo.delete(db, tasting)
    db.commit()
