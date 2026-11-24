"""User repository — the only place that runs SQL for users.

Functions here mutate the session (add/flush) but do not commit; committing is
the service layer's responsibility so it can own the transaction boundary.
"""

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from bloom.db.models.user import User


def get_by_id(db: Session, user_id: int) -> User | None:
    """Return the user with ``user_id`` or ``None``."""
    return db.get(User, user_id)


def get_by_email(db: Session, email: str) -> User | None:
    """Return the user whose email matches ``email`` (case-insensitive) or ``None``.

    Both sides are folded by ``lower()`` in the database, never in Python, so the lookup
    agrees with the ``lower(email)`` unique index.
    """
    return db.execute(select(User).where(func.lower(User.email) == func.lower(email))).scalar_one_or_none()


def get_by_username(db: Session, username: str) -> User | None:
    """Return the user whose handle matches ``username`` (case-insensitive) or ``None``."""
    return db.execute(select(User).where(func.lower(User.username) == username.lower())).scalar_one_or_none()


def list_all(db: Session) -> list[User]:
    """Return all users ordered by id."""
    return list(db.execute(select(User).order_by(User.id)).scalars().all())


def add_if_free(db: Session, *, email: str, username: str, hashed_password: str, role: str) -> User | None:
    """Insert a user, or return ``None`` if the unique email / ``lower(username)`` index rejects it.

    Runs in a savepoint so losing a race against a concurrent insert leaves the caller's
    transaction usable.
    """
    try:
        with db.begin_nested():
            user = User(email=email, username=username, hashed_password=hashed_password, role=role)
            db.add(user)
            db.flush()
            return user
    except IntegrityError:
        return None


def try_update(db: Session, user: User, changes: dict[str, Any]) -> bool:
    """Apply ``changes``; return ``False`` if the new username collides (unique index)."""
    try:
        with db.begin_nested():
            for field, value in changes.items():
                setattr(user, field, value)
            db.flush()
    except IntegrityError:
        return False
    return True
