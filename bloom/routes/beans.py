"""Bean routes — owner-scoped CRUD."""

from fastapi import APIRouter, Response, status

from bloom.core.dependencies import CurrentUser, DbSession
from bloom.schemas.bean import BeanCreate, BeanRead, BeanUpdate
from bloom.services import bean_service

router = APIRouter(prefix="/beans", tags=["beans"])


@router.post("", response_model=BeanRead, status_code=status.HTTP_201_CREATED)
def create_bean(data: BeanCreate, db: DbSession, user: CurrentUser) -> BeanRead:
    return bean_service.create_bean(db, data, user)


@router.get("", response_model=list[BeanRead])
def list_beans(db: DbSession, user: CurrentUser, mine: bool = False) -> list[BeanRead]:
    # Shared by default; ?mine=true restricts to beans you own.
    return bean_service.list_beans(db, user, mine=mine)


@router.get("/{bean_id}", response_model=BeanRead)
def get_bean(bean_id: int, db: DbSession, _user: CurrentUser) -> BeanRead:
    return bean_service.get_bean(db, bean_id)


@router.patch("/{bean_id}", response_model=BeanRead)
def update_bean(
    bean_id: int, data: BeanUpdate, db: DbSession, user: CurrentUser
) -> BeanRead:
    bean = bean_service.get_owned_bean(db, bean_id, user)
    return bean_service.update_bean(db, bean, data)


@router.delete("/{bean_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_bean(bean_id: int, db: DbSession, user: CurrentUser) -> Response:
    bean = bean_service.get_owned_bean(db, bean_id, user)
    bean_service.delete_bean(db, bean)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
