"""User-management business logic (orchestrates the users repository)."""

import secrets
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from bloom.core.logger import get_logger
from bloom.core.security import hash_password
from bloom.db.models.user import User
from bloom.repositories import users as users_repo
from bloom.services.errors import BadRequestError, ConflictError, NotFoundError

logger = get_logger(__name__)


def list_users(db: Session) -> list[User]:
    """Return all users."""
    return users_repo.list_all(db)


def _ensure_username_free(db: Session, username: str, *, owner_id: int | None = None) -> None:
    clash = users_repo.get_by_username(db, username)
    if clash is not None and clash.id != owner_id:
        raise ConflictError("Username already taken")


def create_user(db: Session, *, email: str, username: str, password: str | None = None, role: str = "user") -> User:
    """Create a user with a hashed password and commit.

    Without a ``password`` the account gets an unguessable random one nobody holds, so the
    only way in is the set-password link mailed to the user. A taken email or username is a
    ``ConflictError``, including when a concurrent request wins the race for it.
    """
    if users_repo.get_by_email(db, email) is not None:
        raise ConflictError("Email already registered")
    _ensure_username_free(db, username)
    secret = password if password is not None else secrets.token_urlsafe(32)
    user = users_repo.add_if_free(db, email=email, username=username, hashed_password=hash_password(secret), role=role)
    if user is None:
        raise ConflictError("Email or username already in use")
    db.commit()
    db.refresh(user)
    logger.info("User %s created: %s / %s (role %s)", user.id, email, username, role)
    return user


def set_password(db: Session, user: User, password: str) -> User:
    """Replace ``user``'s password and stamp the change, invalidating older reset tokens."""
    user.hashed_password = hash_password(password)
    user.password_changed_at = datetime.now(UTC)
    db.commit()
    db.refresh(user)
    logger.info("Password changed for user %s (%s)", user.id, user.email)
    return user


def update_user(
    db: Session,
    user_id: int,
    *,
    admin: User,
    username: str | None = None,
    role: str | None = None,
    is_active: bool | None = None,
) -> User:
    """Apply rename/role/activation changes requested by ``admin`` and commit.

    An admin may not demote or deactivate their own account, which could leave the system
    with no active admin.
    """
    user = users_repo.get_by_id(db, user_id)
    if user is None:
        raise NotFoundError("User not found")
    if username is not None:
        _ensure_username_free(db, username, owner_id=user.id)
    if user.id == admin.id:
        if role is not None and role != "admin":
            raise BadRequestError("An admin cannot demote their own account")
        if is_active is False:
            raise BadRequestError("An admin cannot deactivate their own account")

    changes = {name: value for name, value in (("username", username), ("role", role), ("is_active", is_active)) if value is not None}
    if not users_repo.try_update(db, user, changes):
        raise ConflictError("Username already taken")
    db.commit()
    db.refresh(user)
    logger.info("User %s updated: %s", user.id, ", ".join(f"{k}={v}" for k, v in changes.items()) or "no changes")
    return user
