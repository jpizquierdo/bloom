"""Tasting business logic.

Brews are a shared log, so anyone may taste any brew and read its tastings; a
tasting records its author (``tasting.user_id``) and only that author (or an
admin) may edit or delete it.
"""

from sqlalchemy.orm import Session

from bloom.db.models.tasting import Tasting
from bloom.db.models.user import User
from bloom.repositories import tastings as tastings_repo
from bloom.schemas.tasting import TastingCreate, TastingUpdate
from bloom.services import brew_service
from bloom.services.access import owns_or_admin
from bloom.services.errors import ForbiddenError, NotFoundError


def list_for_brew(db: Session, brew_id: int) -> list[Tasting]:
    """List a brew's tastings (shared), after confirming the brew exists."""
    brew_service.get_brew(db, brew_id)  # 404 if the brew does not exist
    return tastings_repo.list_for_brew(db, brew_id)


def list_tastings(db: Session, user: User, mine: bool = False) -> list[Tasting]:
    """List tastings. By default the whole shared log; ``mine`` restricts to
    the user's own (tastings they made)."""
    if mine:
        return tastings_repo.list_for_user(db, user.id)
    return tastings_repo.list_all(db)


def get_tasting(db: Session, tasting_id: int) -> Tasting:
    """Fetch a tasting (any user may read any tasting), else 404."""
    tasting = tastings_repo.get(db, tasting_id)
    if tasting is None:
        raise NotFoundError("Tasting not found")
    return tasting


def get_owned_tasting(db: Session, tasting_id: int, user: User) -> Tasting:
    """Fetch a tasting the user may modify (its author or an admin), else 404/403."""
    tasting = get_tasting(db, tasting_id)
    if not owns_or_admin(user, tasting.user_id):
        raise ForbiddenError("You are not the author of this tasting")
    return tasting


def create_tasting(
    db: Session, brew_id: int, data: TastingCreate, user: User
) -> Tasting:
    """Add a tasting (authored by ``user``) to any existing brew."""
    brew_service.get_brew(db, brew_id)  # 404 if the brew does not exist
    tasting = tastings_repo.add(
        db, brew_id=brew_id, user_id=user.id, **data.model_dump(exclude_none=True)
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
