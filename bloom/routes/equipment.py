"""Equipment routes: reads for any user, writes for admins (single table, decision 5)."""

from fastapi import APIRouter, Response, status

from bloom.core.dependencies import AdminUser, CurrentUser, DbSession
from bloom.schemas.lookups import EquipmentCreate, EquipmentRead, EquipmentUpdate
from bloom.services import lookups_service

router = APIRouter(prefix="/equipment", tags=["equipment"])


@router.get("", response_model=list[EquipmentRead])
def list_equipment(db: DbSession, _user: CurrentUser) -> list[EquipmentRead]:
    """List all equipment (grinders, machines, kettles…). Any authenticated user."""
    return lookups_service.list_equipment(db)


@router.get("/{equipment_id}", response_model=EquipmentRead)
def get_equipment(equipment_id: int, db: DbSession, _user: CurrentUser) -> EquipmentRead:
    """Get an equipment item by id. Any authenticated user."""
    return lookups_service.get_equipment(db, equipment_id)


@router.post("", response_model=EquipmentRead, status_code=status.HTTP_201_CREATED)
def create_equipment(data: EquipmentCreate, db: DbSession, _admin: AdminUser) -> EquipmentRead:
    """Register a piece of equipment (shared lookup data). Admin only."""
    return lookups_service.create_equipment(db, data)


@router.patch("/{equipment_id}", response_model=EquipmentRead)
def update_equipment(equipment_id: int, data: EquipmentUpdate, db: DbSession, _admin: AdminUser) -> EquipmentRead:
    """Edit a piece of equipment (shared lookup data). Admin only."""
    return lookups_service.update_equipment(db, equipment_id, data)


@router.delete("/{equipment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_equipment(equipment_id: int, db: DbSession, _admin: AdminUser) -> Response:
    """Delete a piece of equipment. Admin only; any brew that used it keeps its data, unlinked."""
    lookups_service.delete_equipment(db, equipment_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
