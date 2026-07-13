"""Roaster business logic.

Roasters are an open set that grows with every new bag, so any user may create one
(explicitly, or implicitly by naming it on a bean). Editing, merging and deleting are
admin-gated at the route layer: they affect every user's beans at once.
"""

from sqlalchemy.orm import Session

from bloom.core.logger import get_logger
from bloom.db.models.roaster import Roaster
from bloom.repositories import roasters as roasters_repo
from bloom.schemas.roaster import RoasterCreate, RoasterUpdate
from bloom.services.errors import ConflictError, NotFoundError

logger = get_logger(__name__)


def list_roasters(db: Session) -> list[Roaster]:
    return roasters_repo.list_all(db)


def get_roaster(db: Session, roaster_id: int) -> Roaster:
    roaster = roasters_repo.get(db, roaster_id)
    if roaster is None:
        raise NotFoundError("Roaster not found")
    return roaster


def create_roaster(db: Session, data: RoasterCreate) -> Roaster:
    """Create a roaster explicitly, with its metadata."""
    existing = roasters_repo.get_by_name(db, data.name)
    if existing is not None:
        raise ConflictError(f"Roaster '{existing.name}' already exists")
    roaster = roasters_repo.add(db, **data.model_dump())
    db.commit()
    db.refresh(roaster)
    logger.info("Roaster %s (%s) created", roaster.id, roaster.name)
    return roaster


def update_roaster(db: Session, roaster_id: int, data: RoasterUpdate) -> Roaster:
    """Apply a partial update. A rename follows through to every bean automatically."""
    roaster = get_roaster(db, roaster_id)
    changes = data.model_dump(exclude_unset=True)
    new_name = changes.get("name")
    if new_name is not None:
        clash = roasters_repo.get_by_name(db, new_name)
        if clash is not None and clash.id != roaster.id:
            raise ConflictError(f"Roaster '{clash.name}' already exists — merge into it instead")
    for field, value in changes.items():
        setattr(roaster, field, value)
    db.commit()
    db.refresh(roaster)
    logger.info("Roaster %s updated: %s", roaster.id, ", ".join(changes) or "no fields")
    return roaster


def delete_roaster(db: Session, roaster_id: int) -> None:
    """Delete an unused roaster. One with beans must be merged away, not deleted."""
    roaster = get_roaster(db, roaster_id)
    in_use = roasters_repo.count_beans(db, roaster_id)
    if in_use:
        raise ConflictError(f"Roaster is referenced by {in_use} bean(s) — merge it into another instead")
    roasters_repo.delete(db, roaster)
    db.commit()
    logger.info("Roaster %s deleted", roaster_id)


def merge_roasters(db: Session, *, target_id: int, source_id: int) -> Roaster:
    """Move every bean of ``source_id`` onto ``target_id``, then delete the source."""
    if target_id == source_id:
        raise ConflictError("Cannot merge a roaster into itself")
    target = get_roaster(db, target_id)
    source = get_roaster(db, source_id)
    moved = roasters_repo.reassign_beans(db, source_id=source.id, target_id=target.id)
    roasters_repo.delete(db, source)
    db.commit()
    db.refresh(target)
    logger.info("Roaster %s merged into %s (%s beans moved)", source_id, target_id, moved)
    return target
