"""Authentication logic, password recovery, and first-admin bootstrap."""

from sqlalchemy.orm import Session

from bloom.core.config import get_settings
from bloom.core.logger import get_logger
from bloom.core.security import create_password_reset_token, decode_token, verify_password
from bloom.db.models.user import User
from bloom.repositories import users as users_repo
from bloom.services import users_service
from bloom.services.errors import UnprocessableError

logger = get_logger(__name__)

_INVALID_TOKEN = "Invalid or expired password-reset token"


def authenticate(db: Session, identifier: str, password: str) -> User | None:
    """Return the user if credentials are valid and the account is active.

    ``identifier`` may be either an email or a username — the login form field is
    a single "email or username" box, so we resolve it against both.
    """
    user = users_repo.get_by_email(db, identifier) or users_repo.get_by_username(db, identifier)
    if user is None:
        logger.warning("Failed login: unknown identifier %s", identifier)
        return None
    if not user.is_active:
        logger.warning("Failed login: inactive user %s (%s)", user.id, user.email)
        return None
    if not verify_password(password, user.hashed_password):
        logger.warning("Failed login: wrong password for user %s (%s)", user.id, user.email)
        return None
    return user


def build_password_recovery(db: Session, email: str) -> tuple[User, str] | None:
    """Mint a reset token for ``email``, or ``None`` if there is no active account for it.

    The caller answers identically either way, so an outsider cannot use the endpoint to
    learn which addresses are registered.
    """
    user = users_repo.get_by_email(db, email)
    if user is None:
        logger.info("Password recovery requested for unknown email %s", email)
        return None
    if not user.is_active:
        logger.info("Password recovery requested for inactive user %s (%s)", user.id, email)
        return None
    return user, create_password_reset_token(str(user.id))


def reset_password(db: Session, token: str, new_password: str) -> User:
    """Consume a reset token and set a new password. Raises if the token is not usable."""
    payload = decode_token(token, expected_type="reset")
    if payload is None:
        raise UnprocessableError(_INVALID_TOKEN)

    try:
        user_id = int(payload.get("sub"))  # type: ignore[arg-type]
    except (TypeError, ValueError):
        raise UnprocessableError(_INVALID_TOKEN) from None

    user = users_repo.get_by_id(db, user_id)
    if user is None or not user.is_active:
        raise UnprocessableError(_INVALID_TOKEN)

    issued_at = payload.get("iat_ms")
    if issued_at is None or issued_at < int(user.password_changed_at.timestamp() * 1000):
        logger.warning("Rejected a spent password-reset token for user %s", user.id)
        raise UnprocessableError(_INVALID_TOKEN)

    return users_service.set_password(db, user, new_password)


def bootstrap_admin(db: Session) -> User | None:
    """Create the configured first admin on startup, if it does not exist yet.

    Reads ``BLOOM_ADMIN_EMAIL`` / ``BLOOM_ADMIN_PASSWORD`` from settings. Does
    nothing when they are unset or when a user with that email already exists,
    so it is safe to run on every boot.
    """
    settings = get_settings()
    email = settings.BLOOM_ADMIN_EMAIL
    password = settings.BLOOM_ADMIN_PASSWORD
    if not email or not password:
        return None

    if users_repo.get_by_email(db, email) is not None:
        return None

    username = email.split("@", 1)[0].lower()
    admin = users_service.create_user(db, email=email, username=username, password=password, role="admin")
    logger.info("Bootstrapped initial admin user: %s (%s)", email, username)
    return admin
