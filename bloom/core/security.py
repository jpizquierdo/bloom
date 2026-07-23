"""Password hashing (argon2) and JWT token creation/verification."""

from datetime import UTC, datetime, timedelta
from typing import Any, Literal

from argon2 import PasswordHasher
from argon2.exceptions import Argon2Error
from jose import JWTError, jwt

from bloom.core.config import get_settings

_password_hasher = PasswordHasher()

TokenType = Literal["access", "reset"]


def hash_password(password: str) -> str:
    """Hash a plaintext password with argon2id."""
    return _password_hasher.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    """Return True if ``password`` matches the stored argon2 hash."""
    try:
        return _password_hasher.verify(hashed_password, password)
    except Argon2Error:
        return False


def _create_token(subject: str, token_type: TokenType, minutes: int) -> str:
    settings = get_settings()
    issued_at = datetime.now(UTC)
    payload = {
        "sub": subject,
        "type": token_type,
        "iat": issued_at,
        # The standard ``iat`` above is truncated to whole seconds, too coarse to tell a
        # reset token apart from a password change made in the same second. This private
        # claim keeps the millisecond precision that ``users.password_changed_at`` has.
        "iat_ms": int(issued_at.timestamp() * 1000),
        "exp": issued_at + timedelta(minutes=minutes),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def create_access_token(subject: str, expires_minutes: int | None = None) -> str:
    """Create a signed JWT access token whose ``sub`` claim is ``subject``."""
    settings = get_settings()
    minutes = expires_minutes if expires_minutes is not None else settings.ACCESS_TOKEN_EXPIRE_HOURS * 60
    return _create_token(subject, "access", minutes)


def create_password_reset_token(subject: str, expires_minutes: int | None = None) -> str:
    """Create a short-lived JWT that authorises a password reset for ``subject``."""
    settings = get_settings()
    minutes = expires_minutes if expires_minutes is not None else settings.RESET_TOKEN_EXPIRE_MINUTES
    return _create_token(subject, "reset", minutes)


def decode_token(token: str, *, expected_type: TokenType) -> dict[str, Any] | None:
    """Decode and verify a JWT, returning its claims or ``None`` if invalid.

    A token is rejected unless its ``type`` claim matches ``expected_type``, so a reset
    token can never be replayed as an access token (or vice versa).
    """
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except JWTError:
        return None
    if payload.get("type") != expected_type:
        return None
    return payload
