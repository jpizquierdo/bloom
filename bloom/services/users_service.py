"""User-management business logic (orchestrates the users repository)."""

from sqlalchemy.orm import Session

from bloom.core.security import hash_password
from bloom.db.models.user import User
from bloom.repositories import users as users_repo


def list_users(db: Session) -> list[User]:
    """Return all users."""
    return users_repo.list_all(db)


def create_user(db: Session, *, email: str, password: str, role: str = "user") -> User:
    """Create a user with a hashed password and commit."""
    user = users_repo.add(
        db, email=email, hashed_password=hash_password(password), role=role
    )
    db.commit()
    db.refresh(user)
    return user


def update_user(
    db: Session,
    user: User,
    *,
    role: str | None = None,
    is_active: bool | None = None,
) -> User:
    """Apply role/activation changes to ``user`` and commit."""
    if role is not None:
        user.role = role
    if is_active is not None:
        user.is_active = is_active
    db.commit()
    db.refresh(user)
    return user
