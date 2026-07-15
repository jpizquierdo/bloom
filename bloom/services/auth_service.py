"""Authentication logic and first-admin bootstrap."""

from sqlalchemy.orm import Session

from bloom.core.config import get_settings
from bloom.core.logger import get_logger
from bloom.core.security import verify_password
from bloom.db.models.user import User
from bloom.repositories import users as users_repo
from bloom.services import users_service

logger = get_logger(__name__)


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
