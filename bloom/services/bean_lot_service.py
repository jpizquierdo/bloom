"""Bean-lot business logic.

A lot is a physical purchase of a bean (coffee). Lots are a shared log like beans:
anyone may read them, but only the buyer (``lot.user_id``) or an admin may edit or
delete one.
"""

from sqlalchemy.orm import Session

from bloom.core.logger import get_logger
from bloom.db.models.bean_lot import BeanLot
from bloom.db.models.user import User
from bloom.repositories import bean_lots as lots_repo
from bloom.schemas.bean_lot import BeanLotCreate, BeanLotUpdate
from bloom.services import bean_service
from bloom.services.access import owns_or_admin
from bloom.services.errors import ForbiddenError, NotFoundError

logger = get_logger(__name__)


def list_for_bean(db: Session, bean_id: int) -> list[BeanLot]:
    """List a bean's lots (shared), after confirming the bean exists."""
    bean_service.get_bean(db, bean_id)  # 404 if the bean does not exist
    return lots_repo.list_for_bean(db, bean_id)


def get_lot(db: Session, lot_id: int) -> BeanLot:
    """Fetch a lot (any user may read any lot), else 404."""
    lot = lots_repo.get(db, lot_id)
    if lot is None:
        raise NotFoundError("Lot not found")
    return lot


def get_owned_lot(db: Session, lot_id: int, user: User) -> BeanLot:
    """Fetch a lot the user may modify (its buyer or an admin), else 404/403."""
    lot = get_lot(db, lot_id)
    if not owns_or_admin(user, lot.user_id):
        raise ForbiddenError("You do not own this lot")
    return lot


def create_lot(db: Session, bean_id: int, data: BeanLotCreate, user: User) -> BeanLot:
    """Add a lot (bought by ``user``) to an existing bean."""
    bean_service.get_bean(db, bean_id)  # 404 if the bean does not exist
    lot = lots_repo.add(db, bean_id=bean_id, user_id=user.id, **data.model_dump(exclude_none=True))
    db.commit()
    db.refresh(lot)
    logger.info("Lot %s created by user %s (bean %s)", lot.id, user.id, bean_id)
    return lot


def update_lot(db: Session, lot: BeanLot, data: BeanLotUpdate) -> BeanLot:
    """Apply a partial update to an already-authorized lot."""
    changes = data.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(lot, field, value)
    db.commit()
    db.refresh(lot)
    logger.info("Lot %s updated: %s", lot.id, ", ".join(changes) or "no fields")
    return lot


def delete_lot(db: Session, lot: BeanLot) -> None:
    """Delete an already-authorized lot (brews that referenced it keep their history)."""
    lot_id = lot.id
    lots_repo.delete(db, lot)
    db.commit()
    logger.info("Lot %s deleted", lot_id)
