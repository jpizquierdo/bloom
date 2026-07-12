"""Authentication logic and first-admin bootstrap."""

from sqlalchemy.orm import Session

from bloom.core.config import get_settings
from bloom.core.logger import get_logger
from bloom.core.security import verify_password
from bloom.db.models.user import User
from bloom.repositories import users as users_repo
from bloom.services import users_service

logger = get_logger(__name__)


def authenticate(db: Session, email: str, password: str) -> User | None:
    """Return the user if credentials are valid and the account is active."""
    user = users_repo.get_by_email(db, email)
    if user is None:
        logger.warning("Failed login: unknown email %s", email)
        return None
    if not user.is_active:
        logger.warning("Failed login: inactive user %s (%s)", user.id, email)
        return None
    if not verify_password(password, user.hashed_password):
        logger.warning("Failed login: wrong password for user %s (%s)", user.id, email)
        return None
    return user


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

    admin = users_service.create_user(db, email=email, password=password, role="admin")
    logger.info("Bootstrapped initial admin user: %s", email)
    return admin
