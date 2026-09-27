"""Bean routes — owner-scoped CRUD."""

from typing import Annotated

from fastapi import APIRouter, Query, Response, status

from bloom.core.dependencies import CurrentUser, DbSession
from bloom.schemas.bean import BeanCreate, BeanMerge, BeanRead, BeanUpdate
from bloom.services import bean_service

router = APIRouter(prefix="/beans", tags=["beans"])

AllowDuplicate = Annotated[
    bool,
    Query(description="Accept a name that already exists under this roaster instead of failing with 409."),
]


@router.post("", response_model=BeanRead, status_code=status.HTTP_201_CREATED)
def create_bean(data: BeanCreate, db: DbSession, user: CurrentUser, allow_duplicate: AllowDuplicate = False) -> BeanRead:
    """Create a bean. It is shared with everyone; you are recorded as its owner.

    409 if this roaster already has a bean with that name (matched case-insensitively) —
    open that one, or resend with `?allow_duplicate=true` if it really is another coffee.
    """
    return bean_service.create_bean(db, data, user, allow_duplicate)


@router.get("", response_model=list[BeanRead])
def list_beans(db: DbSession, user: CurrentUser, mine: bool = False) -> list[BeanRead]:
    """List all beans (shared). Use `?mine=true` to return only the beans you own."""
    return bean_service.list_beans(db, user, mine=mine)


@router.get("/{bean_id}", response_model=BeanRead)
def get_bean(bean_id: int, db: DbSession, _user: CurrentUser) -> BeanRead:
    """Get a bean by id. Any authenticated user may read any bean."""
    return bean_service.get_bean(db, bean_id)


@router.patch("/{bean_id}", response_model=BeanRead)
def update_bean(bean_id: int, data: BeanUpdate, db: DbSession, user: CurrentUser, allow_duplicate: AllowDuplicate = False) -> BeanRead:
    """Update a bean. Only its owner (or an admin) may edit it.

    409 if the new name and roaster are already taken by another bean; merge into it
    instead, or resend with `?allow_duplicate=true`.
    """
    bean = bean_service.get_owned_bean(db, bean_id, user)
    return bean_service.update_bean(db, bean, data, allow_duplicate)


@router.post("/{bean_id}/merge", response_model=BeanRead)
def merge_bean(bean_id: int, data: BeanMerge, db: DbSession, user: CurrentUser) -> BeanRead:
    """Fold a duplicate into this bean: its brews, lots and recipes move here.

    You must own both beans (or be an admin). This bean keeps its own values and adopts
    the duplicate's for anything it left empty.
    """
    return bean_service.merge_beans(db, target_id=bean_id, source_id=data.source_id, user=user)


@router.delete("/{bean_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_bean(bean_id: int, db: DbSession, user: CurrentUser) -> Response:
    """Delete a bean (cascades to its brews and tastings). Owner or admin only."""
    bean = bean_service.get_owned_bean(db, bean_id, user)
    bean_service.delete_bean(db, bean)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
