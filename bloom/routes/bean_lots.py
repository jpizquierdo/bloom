"""Bean-lot routes — owner-scoped, nested under beans for create/list."""

from fastapi import APIRouter, Response, status

from bloom.core.dependencies import CurrentUser, DbSession
from bloom.schemas.bean_lot import BeanLotCreate, BeanLotRead, BeanLotUpdate
from bloom.services import bean_lot_service

router = APIRouter(tags=["lots"])


@router.post(
    "/beans/{bean_id}/lots",
    response_model=BeanLotRead,
    status_code=status.HTTP_201_CREATED,
)
def create_lot(bean_id: int, data: BeanLotCreate, db: DbSession, user: CurrentUser) -> BeanLotRead:
    """Add a lot (a physical bag bought) to a bean; you are recorded as its buyer."""
    return bean_lot_service.create_lot(db, bean_id, data, user)


@router.get("/beans/{bean_id}/lots", response_model=list[BeanLotRead])
def list_lots(bean_id: int, db: DbSession, _user: CurrentUser) -> list[BeanLotRead]:
    """List a bean's lots (shared). Any authenticated user."""
    return bean_lot_service.list_for_bean(db, bean_id)


@router.get("/lots/{lot_id}", response_model=BeanLotRead)
def get_lot(lot_id: int, db: DbSession, _user: CurrentUser) -> BeanLotRead:
    """Get a lot by id. Any authenticated user."""
    return bean_lot_service.get_lot(db, lot_id)


@router.patch("/lots/{lot_id}", response_model=BeanLotRead)
def update_lot(lot_id: int, data: BeanLotUpdate, db: DbSession, user: CurrentUser) -> BeanLotRead:
    """Update a lot. Only its buyer (or an admin) may edit it."""
    lot = bean_lot_service.get_owned_lot(db, lot_id, user)
    return bean_lot_service.update_lot(db, lot, data)


@router.delete("/lots/{lot_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_lot(lot_id: int, db: DbSession, user: CurrentUser) -> Response:
    """Delete a lot. Only its buyer (or an admin) may delete it."""
    lot = bean_lot_service.get_owned_lot(db, lot_id, user)
    bean_lot_service.delete_lot(db, lot)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
