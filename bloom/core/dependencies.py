"""FastAPI dependencies: database session and authentication guards."""

from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from bloom.core.config import get_settings
from bloom.core.security import decode_token
from bloom.db.models.user import User
from bloom.db.session import SessionLocal
from bloom.repositories import users as users_repo

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{get_settings().API_V1_STR}/auth/token")


def get_db() -> Iterator[Session]:
    """Yield a database session, closing it when the request finishes."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


DbSession = Annotated[Session, Depends(get_db)]


def get_current_user(
    db: DbSession,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> User:
    """Resolve the authenticated, active user from a bearer token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_token(token, expected_type="access")
    if payload is None:
        raise credentials_exception
    subject = payload.get("sub")
    if subject is None:
        raise credentials_exception
    try:
        user_id = int(subject)
    except (TypeError, ValueError):
        raise credentials_exception

    user = users_repo.get_by_id(db, user_id)
    if user is None or not user.is_active:
        raise credentials_exception
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_admin(current_user: CurrentUser) -> User:
    """Ensure the current user is an admin."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return current_user


AdminUser = Annotated[User, Depends(require_admin)]
