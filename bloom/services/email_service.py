"""Composition of the app's transactional emails (delivery lives in ``bloom.core.email``)."""

from bloom.core.config import get_settings
from bloom.core.email import render, send_email


def _reset_link(token: str) -> str:
    settings = get_settings()
    return f"{settings.FRONTEND_HOST.rstrip('/')}/reset-password?token={token}"


def send_reset_password_email(*, email: str, username: str, token: str) -> None:
    """Email a password-reset link to a user who asked to recover their account."""
    settings = get_settings()
    context = {
        "username": username,
        "link": _reset_link(token),
        "expire_minutes": settings.RESET_TOKEN_EXPIRE_MINUTES,
        "subject": "Reset your Bloom password",
    }
    send_email(
        to=email,
        subject="Reset your Bloom password",
        html=render("reset_password.html", **context),
        text=render("reset_password.txt", **context),
    )


def send_new_account_email(*, email: str, username: str, token: str) -> None:
    """Welcome a user an admin just created, with a link to set their own password."""
    settings = get_settings()
    context = {
        "username": username,
        "link": _reset_link(token),
        "expire_minutes": settings.RESET_TOKEN_EXPIRE_MINUTES,
        "subject": "Your Bloom account is ready",
    }
    send_email(
        to=email,
        subject="Your Bloom account is ready",
        html=render("new_account.html", **context),
        text=render("new_account.txt", **context),
    )
