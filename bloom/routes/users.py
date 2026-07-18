"""User-management routes (admin-only). No public self-registration."""

from fastapi import APIRouter, BackgroundTasks, HTTPException, status

from bloom.core.dependencies import AdminUser, DbSession
from bloom.core.security import create_password_reset_token
from bloom.repositories import users as users_repo
from bloom.schemas.user import UserCreate, UserRead, UserUpdate
from bloom.services import email_service, users_service

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(data: UserCreate, db: DbSession, background_tasks: BackgroundTasks, _admin: AdminUser) -> UserRead:
    """Create a new user (role 'user'). Admin-only.

    Emails them a welcome message with a link to set their own password; omitting
    ``password`` makes that link the only way in.
    """
    if users_repo.get_by_email(db, data.email) is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    if users_repo.get_by_username(db, data.username) is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already taken")

    user = users_service.create_user(db, email=data.email, username=data.username, password=data.password)
    token = create_password_reset_token(str(user.id))
    background_tasks.add_task(email_service.send_new_account_email, email=user.email, username=user.username, token=token)
    return user


@router.get("", response_model=list[UserRead])
def list_users(db: DbSession, _admin: AdminUser) -> list[UserRead]:
    """List all users. Admin-only."""
    return users_service.list_users(db)


@router.patch("/{user_id}", response_model=UserRead)
def update_user(user_id: int, data: UserUpdate, db: DbSession, admin: AdminUser) -> UserRead:
    """Promote/demote or activate/deactivate a user. Admin-only."""
    user = users_repo.get_by_id(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if data.username is not None:
        clash = users_repo.get_by_username(db, data.username)
        if clash is not None and clash.id != user.id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already taken")

    # Guard against an admin locking themselves out (demoting or deactivating
    # their own account), which could leave the system with no active admin.
    if user.id == admin.id:
        if data.role is not None and data.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An admin cannot demote their own account",
            )
        if data.is_active is False:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An admin cannot deactivate their own account",
            )

    return users_service.update_user(db, user, username=data.username, role=data.role, is_active=data.is_active)
