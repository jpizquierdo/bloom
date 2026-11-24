"""OpenID Connect logins: link the IdP identity to a Bloom account and apply group roles."""

from typing import Any

from sqlalchemy.orm import Session

from bloom.core.config import get_settings
from bloom.core.logger import get_logger
from bloom.db.models.user import User
from bloom.domain.oidc import groups_from, resolve_role, username_from_claims, with_suffix
from bloom.repositories import users as users_repo
from bloom.services import users_service
from bloom.services.errors import ForbiddenError

logger = get_logger(__name__)

_MAX_USERNAME_ATTEMPTS = 50


def _email_is_trusted(claims: dict[str, Any]) -> bool:
    verified = claims.get("email_verified")
    # Some IdPs (Cognito) send the claim as a string.
    if verified in (True, "true"):
        return True
    return verified is None and not get_settings().OIDC_REQUIRE_EMAIL_VERIFIED


def _free_username(db: Session, base: str) -> str:
    for n in range(1, _MAX_USERNAME_ATTEMPTS + 1):
        candidate = base if n == 1 else with_suffix(base, n)
        if users_repo.get_by_username(db, candidate) is None:
            return candidate
    raise ForbiddenError("Could not pick a free username for this account")


def login_from_claims(db: Session, claims: dict[str, Any]) -> User:
    """Return the Bloom user for verified ID-token ``claims``, linking or creating it.

    Matching is by ``sub`` first, then by email for accounts not linked yet (an existing local
    user). Raises ``ForbiddenError`` when the login must be refused.
    """
    settings = get_settings()
    subject = claims.get("sub")
    email = claims.get("email")
    if not subject:
        raise ForbiddenError("The identity provider sent no subject")

    user = users_repo.get_by_oidc_subject(db, subject)
    if user is None and email:
        user = users_repo.get_by_email(db, email)
        if user is not None:
            if user.oidc_subject is not None:
                logger.warning("OIDC login refused: user %s is linked to another identity", user.id)
                raise ForbiddenError("This account is linked to another identity")
            if not _email_is_trusted(claims):
                logger.warning("OIDC login refused: unverified email for user %s", user.id)
                raise ForbiddenError("The identity provider has not verified this email")

    if user is not None and not user.is_active:
        logger.warning("OIDC login refused: inactive user %s", user.id)
        raise ForbiddenError("This account is disabled")

    groups = groups_from(claims, settings.OIDC_GROUPS_CLAIM)
    role = resolve_role(groups, settings.oidc_admin_groups, settings.oidc_allowed_groups, user.role if user else "user")
    if role is None:
        logger.warning("OIDC login refused: subject not in OIDC_ALLOWED_GROUPS")
        raise ForbiddenError("You are not in a group allowed to use Bloom")

    if user is None:
        if not settings.OIDC_AUTO_CREATE_USERS:
            logger.warning("OIDC login refused: no account and OIDC_AUTO_CREATE_USERS is off")
            raise ForbiddenError("No Bloom account exists for this identity")
        if not email:
            raise ForbiddenError("The identity provider sent no email")
        username = _free_username(db, username_from_claims(claims.get("preferred_username"), email))
        user = users_service.create_user(db, email=email, username=username, role=role, oidc_subject=subject)
        logger.info("OIDC created user %s", user.id)
        return user

    if user.oidc_subject is None:
        user.oidc_subject = subject
        logger.info("OIDC linked user %s", user.id)
    if user.role != role:
        logger.info("OIDC set role of user %s to %s", user.id, role)
        user.role = role
    db.commit()
    db.refresh(user)
    return user
