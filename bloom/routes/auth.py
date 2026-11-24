"""Authentication routes: password and OIDC login, password recovery, current-user lookup."""

from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from starlette.concurrency import run_in_threadpool

from bloom.core import rate_limit
from bloom.core.config import get_settings
from bloom.core.dependencies import CurrentUser, DbSession
from bloom.core.logger import get_logger
from bloom.core.oidc import oidc_client
from bloom.core.security import create_access_token
from bloom.schemas.common import Message
from bloom.schemas.user import AuthConfig, RecoverPassword, ResetPassword, Token, UserRead
from bloom.services import auth_service, email_service, oidc_service
from bloom.services.errors import ForbiddenError, NotFoundError

logger = get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


def require_local_auth() -> None:
    """Refuse password-based endpoints when ``DISABLE_LOCAL_AUTH`` forces SSO."""
    if get_settings().DISABLE_LOCAL_AUTH:
        raise ForbiddenError("Password login is disabled; sign in with SSO")


LocalAuth = Depends(require_local_auth)

_RECOVERY_SENT = "If that email is registered, a reset link is on its way."


@router.get("/config", response_model=AuthConfig)
def read_auth_config() -> AuthConfig:
    """Which login methods are available, so the UI can show the right ones. Public."""
    settings = get_settings()
    return AuthConfig(local_auth_enabled=not settings.DISABLE_LOCAL_AUTH, oidc_enabled=settings.oidc_enabled)


@router.get("/oidc/login", response_class=RedirectResponse, status_code=status.HTTP_302_FOUND)
async def oidc_login(request: Request) -> RedirectResponse:
    """Start single sign-on: redirect the browser to the identity provider. Public; 404 when OIDC is off."""
    settings = get_settings()
    if not settings.oidc_enabled:
        raise NotFoundError("Single sign-on is not configured")
    return await oidc_client().authorize_redirect(request, settings.OIDC_REDIRECT_URI)


@router.get("/oidc/callback", response_class=RedirectResponse, status_code=status.HTTP_302_FOUND)
async def oidc_callback(request: Request, db: DbSession) -> RedirectResponse:
    """Finish single sign-on and hand the web UI an access token. Public; 404 when OIDC is off.

    Redirects to ``/login#token=<jwt>`` (a fragment never reaches server or proxy logs), or to
    ``/login?error=oidc_denied|oidc_failed`` when the login is refused or the exchange fails.
    """
    if not get_settings().oidc_enabled:
        raise NotFoundError("Single sign-on is not configured")
    try:
        token = await oidc_client().authorize_access_token(request)
        claims = token["userinfo"]
    except Exception:
        logger.exception("OIDC callback failed")
        return RedirectResponse("/login?error=oidc_failed", status_code=status.HTTP_302_FOUND)
    try:
        user = await run_in_threadpool(oidc_service.login_from_claims, db, dict(claims))
    except ForbiddenError:
        return RedirectResponse("/login?error=oidc_denied", status_code=status.HTTP_302_FOUND)
    return RedirectResponse(f"/login#token={create_access_token(str(user.id))}", status_code=status.HTTP_302_FOUND)


@router.post("/token", response_model=Token, dependencies=[LocalAuth])
def login(
    request: Request,
    db: DbSession,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    """Exchange an email or username (``username`` field) + password for a JWT access token.

    Public; 403 when ``DISABLE_LOCAL_AUTH`` is on. Repeated failures from one client return 429
    with a ``Retry-After`` header.
    """
    client = rate_limit.client_ip(request)
    account_key = f"{client}|{form_data.username.strip().lower()}"
    rate_limit.enforce(rate_limit.login_by_account, account_key)
    rate_limit.enforce(rate_limit.login_by_client, client)
    user = auth_service.authenticate(db, form_data.username, form_data.password)
    if user is None:
        rate_limit.login_by_account.record(account_key)
        rate_limit.login_by_client.record(client)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    rate_limit.login_by_account.clear(account_key)
    return Token(access_token=create_access_token(str(user.id)))


@router.post("/recover-password", response_model=Message, status_code=status.HTTP_202_ACCEPTED, dependencies=[LocalAuth])
def recover_password(request: Request, data: RecoverPassword, db: DbSession, background_tasks: BackgroundTasks) -> Message:
    """Email a password-reset link. Public; 403 when ``DISABLE_LOCAL_AUTH`` is on.

    Always answers 202 with the same message, whether or not the address has an account,
    so it cannot be used to discover who is registered. Rate-limited per address and per
    client (429 with ``Retry-After``) so it cannot be used to flood an inbox.
    """
    client = rate_limit.client_ip(request)
    email_key = data.email.lower()
    rate_limit.enforce(rate_limit.recovery_by_email, email_key)
    rate_limit.enforce(rate_limit.recovery_by_client, client)
    rate_limit.recovery_by_email.record(email_key)
    rate_limit.recovery_by_client.record(client)
    recovery = auth_service.build_password_recovery(db, data.email)
    if recovery is not None:
        user, token = recovery
        background_tasks.add_task(email_service.send_reset_password_email, email=user.email, username=user.username, token=token)
    return Message(message=_RECOVERY_SENT)


@router.post("/reset-password", response_model=Message, dependencies=[LocalAuth])
def reset_password(data: ResetPassword, db: DbSession) -> Message:
    """Set a new password using a token from a reset email. Public; the token is single-use.

    403 when ``DISABLE_LOCAL_AUTH`` is on.
    """
    auth_service.reset_password(db, data.token, data.new_password)
    return Message(message="Your password has been changed. You can now log in.")


@router.get("/me", response_model=UserRead)
def read_current_user(current_user: CurrentUser) -> UserRead:
    """Return the authenticated user's profile."""
    return current_user
