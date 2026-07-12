"""User-management business logic (orchestrates the users repository)."""

from sqlalchemy.orm import Session

from bloom.core.logger import get_logger
from bloom.core.security import hash_password
from bloom.db.models.user import User
from bloom.repositories import users as users_repo

logger = get_logger(__name__)


def list_users(db: Session) -> list[User]:
    """Return all users."""
    return users_repo.list_all(db)


def create_user(db: Session, *, email: str, password: str, role: str = "user") -> User:
    """Create a user with a hashed password and commit."""
    user = users_repo.add(db, email=email, hashed_password=hash_password(password), role=role)
    db.commit()
    db.refresh(user)
    logger.info("User %s created: %s (role %s)", user.id, email, role)
    return user


def update_user(
    db: Session,
    user: User,
    *,
    role: str | None = None,
    is_active: bool | None = None,
) -> User:
    """Apply role/activation changes to ``user`` and commit."""
    changes = []
    if role is not None:
        user.role = role
        changes.append(f"role={role}")
    if is_active is not None:
        user.is_active = is_active
        changes.append("activated" if is_active else "deactivated")
    db.commit()
    db.refresh(user)
    logger.info("User %s updated: %s", user.id, ", ".join(changes) or "no changes")
    return user
