"""Business logic for shared lookup data (brew_method, equipment).

Reads are available to any authenticated user; writes are admin-gated at the
route layer.
"""

from sqlalchemy.orm import Session

from bloom.core.logger import get_logger
from bloom.db.models.brew_method import BrewMethod
from bloom.db.models.equipment import Equipment
from bloom.repositories import lookups as lookups_repo
from bloom.schemas.lookups import BrewMethodCreate, BrewMethodUpdate, EquipmentCreate, EquipmentUpdate
from bloom.services.errors import ConflictError, NotFoundError

logger = get_logger(__name__)


def list_brew_methods(db: Session) -> list[BrewMethod]:
    return lookups_repo.list_brew_methods(db)


def get_brew_method(db: Session, method_id: int) -> BrewMethod:
    method = lookups_repo.get_brew_method(db, method_id)
    if method is None:
        raise NotFoundError("Brew method not found")
    return method


def create_brew_method(db: Session, data: BrewMethodCreate) -> BrewMethod:
    method = lookups_repo.add_brew_method(db, name=data.name, category=data.category, default_ratio=data.default_ratio)
    db.commit()
    db.refresh(method)
    return method


def update_brew_method(db: Session, method_id: int, data: BrewMethodUpdate) -> BrewMethod:
    method = get_brew_method(db, method_id)
    changes = data.model_dump(exclude_unset=True)
    if not lookups_repo.try_update_brew_method(db, method, changes):
        raise ConflictError(f"A brew method named '{changes.get('name')}' already exists")
    db.commit()
    db.refresh(method)
    logger.info("Brew method %s updated: %s", method.id, ", ".join(changes) or "no fields")
    return method


def delete_brew_method(db: Session, method_id: int) -> None:
    method = get_brew_method(db, method_id)
    # brew.method_id is RESTRICT: a method still used by a brew cannot be deleted.
    if not lookups_repo.try_delete_brew_method(db, method):
        raise ConflictError("Brew method is used by a brew and cannot be deleted")
    db.commit()
    logger.info("Brew method %s deleted", method_id)


def list_equipment(db: Session) -> list[Equipment]:
    return lookups_repo.list_equipment(db)


def get_equipment(db: Session, equipment_id: int) -> Equipment:
    equipment = lookups_repo.get_equipment(db, equipment_id)
    if equipment is None:
        raise NotFoundError("Equipment not found")
    return equipment


def create_equipment(db: Session, data: EquipmentCreate) -> Equipment:
    equipment = lookups_repo.add_equipment(db, type=data.type, name=data.name, brand=data.brand, notes=data.notes)
    db.commit()
    db.refresh(equipment)
    logger.info("Equipment %s (%s '%s') created", equipment.id, equipment.type, equipment.name)
    return equipment


def update_equipment(db: Session, equipment_id: int, data: EquipmentUpdate) -> Equipment:
    equipment = get_equipment(db, equipment_id)
    changes = data.model_dump(exclude_unset=True)
    lookups_repo.update_equipment(db, equipment, changes)
    db.commit()
    db.refresh(equipment)
    logger.info("Equipment %s updated: %s", equipment.id, ", ".join(changes) or "no fields")
    return equipment


def delete_equipment(db: Session, equipment_id: int) -> None:
    equipment = get_equipment(db, equipment_id)
    # brew.grinder_id is SET NULL: deleting a grinder leaves past brews, just unlinked.
    lookups_repo.delete_equipment(db, equipment)
    db.commit()
    logger.info("Equipment %s deleted", equipment_id)
