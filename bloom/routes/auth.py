"""Authentication routes: OAuth2 password-flow login and current-user lookup."""

from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from bloom.core.dependencies import CurrentUser, DbSession
from bloom.core.security import create_access_token
from bloom.schemas.common import Message
from bloom.schemas.user import RecoverPassword, ResetPassword, Token, UserRead
from bloom.services import auth_service, email_service

router = APIRouter(prefix="/auth", tags=["auth"])

_RECOVERY_SENT = "If that email is registered, a reset link is on its way."


@router.post("/token", response_model=Token)
def login(
    db: DbSession,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    """Exchange an email or username (``username`` field) + password for a JWT access token."""
    user = auth_service.authenticate(db, form_data.username, form_data.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return Token(access_token=create_access_token(str(user.id)))


@router.post("/recover-password", response_model=Message, status_code=status.HTTP_202_ACCEPTED)
def recover_password(data: RecoverPassword, db: DbSession, background_tasks: BackgroundTasks) -> Message:
    """Email a password-reset link. Public.

    Always answers 202 with the same message, whether or not the address has an account,
    so it cannot be used to discover who is registered.
    """
    recovery = auth_service.build_password_recovery(db, data.email)
    if recovery is not None:
        user, token = recovery
        background_tasks.add_task(email_service.send_reset_password_email, email=user.email, username=user.username, token=token)
    return Message(message=_RECOVERY_SENT)


@router.post("/reset-password", response_model=Message)
def reset_password(data: ResetPassword, db: DbSession) -> Message:
    """Set a new password using a token from a reset email. Public; the token is single-use."""
    auth_service.reset_password(db, data.token, data.new_password)
    return Message(message="Your password has been changed. You can now log in.")


@router.get("/me", response_model=UserRead)
def read_current_user(current_user: CurrentUser) -> UserRead:
    """Return the authenticated user's profile."""
    return current_user
