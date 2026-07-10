"""Equipment routes: reads for any user, writes for admins (5A single table)."""

from fastapi import APIRouter, status

from bloom.core.dependencies import AdminUser, CurrentUser, DbSession
from bloom.schemas.lookups import EquipmentCreate, EquipmentRead
from bloom.services import lookups_service

router = APIRouter(prefix="/equipment", tags=["equipment"])


@router.get("", response_model=list[EquipmentRead])
def list_equipment(db: DbSession, _user: CurrentUser) -> list[EquipmentRead]:
    return lookups_service.list_equipment(db)


@router.get("/{equipment_id}", response_model=EquipmentRead)
def get_equipment(equipment_id: int, db: DbSession, _user: CurrentUser) -> EquipmentRead:
    return lookups_service.get_equipment(db, equipment_id)


@router.post("", response_model=EquipmentRead, status_code=status.HTTP_201_CREATED)
def create_equipment(
    data: EquipmentCreate, db: DbSession, _admin: AdminUser
) -> EquipmentRead:
    return lookups_service.create_equipment(db, data)
