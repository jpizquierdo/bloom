"""User repository — the only place that runs SQL for users.

Functions here mutate the session (add/flush) but do not commit; committing is
the service layer's responsibility so it can own the transaction boundary.
"""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from bloom.db.models.user import User


def get_by_id(db: Session, user_id: int) -> User | None:
    """Return the user with ``user_id`` or ``None``."""
    return db.get(User, user_id)


def get_by_email(db: Session, email: str) -> User | None:
    """Return the user with ``email`` or ``None``."""
    return db.execute(select(User).where(User.email == email)).scalar_one_or_none()


def get_by_username(db: Session, username: str) -> User | None:
    """Return the user whose handle matches ``username`` (case-insensitive) or ``None``."""
    return db.execute(select(User).where(func.lower(User.username) == username.lower())).scalar_one_or_none()


def list_all(db: Session) -> list[User]:
    """Return all users ordered by id."""
    return list(db.execute(select(User).order_by(User.id)).scalars().all())


def add(db: Session, *, email: str, username: str, hashed_password: str, role: str) -> User:
    """Add a new user to the session and flush to assign its id."""
    user = User(email=email, username=username, hashed_password=hashed_password, role=role)
    db.add(user)
    db.flush()
    return user
