"""Repository for the shared lookup tables (brew_method, equipment)."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from bloom.db.models.brew_method import BrewMethod
from bloom.db.models.equipment import Equipment


def list_brew_methods(db: Session) -> list[BrewMethod]:
    return list(db.execute(select(BrewMethod).order_by(BrewMethod.id)).scalars().all())


def get_brew_method(db: Session, method_id: int) -> BrewMethod | None:
    return db.get(BrewMethod, method_id)


def add_brew_method(db: Session, *, name: str, category: str, default_ratio: object | None) -> BrewMethod:
    method = BrewMethod(name=name, category=category, default_ratio=default_ratio)
    db.add(method)
    db.flush()
    return method


def try_update_brew_method(db: Session, method: BrewMethod, changes: dict[str, Any]) -> bool:
    """Apply ``changes``; return ``False`` if the new name collides (unique index)."""
    try:
        with db.begin_nested():
            for field, value in changes.items():
                setattr(method, field, value)
            db.flush()
    except IntegrityError:
        return False
    return True


def try_delete_brew_method(db: Session, method: BrewMethod) -> bool:
    """Delete a method; return ``False`` if a brew still references it (FK RESTRICT)."""
    try:
        with db.begin_nested():
            db.delete(method)
            db.flush()
    except IntegrityError:
        return False
    return True


def list_equipment(db: Session) -> list[Equipment]:
    return list(db.execute(select(Equipment).order_by(Equipment.id)).scalars().all())


def get_equipment(db: Session, equipment_id: int) -> Equipment | None:
    return db.get(Equipment, equipment_id)


def add_equipment(db: Session, *, type: str, name: str, brand: str | None, notes: str | None) -> Equipment:
    equipment = Equipment(type=type, name=name, brand=brand, notes=notes)
    db.add(equipment)
    db.flush()
    return equipment


def update_equipment(db: Session, equipment: Equipment, changes: dict[str, Any]) -> None:
    for field, value in changes.items():
        setattr(equipment, field, value)
    db.flush()


def delete_equipment(db: Session, equipment: Equipment) -> None:
    """Delete equipment. A referencing brew's ``grinder_id`` is nulled (FK SET NULL)."""
    db.delete(equipment)
    db.flush()
