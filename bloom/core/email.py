"""SMTP delivery and Jinja rendering for the app's transactional emails."""

import smtplib
from email.message import EmailMessage
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from bloom.core.config import get_settings
from bloom.core.logger import get_logger

logger = get_logger(__name__)

_TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates" / "email"

_env = Environment(
    loader=FileSystemLoader(_TEMPLATE_DIR),
    autoescape=select_autoescape(["html"]),
)


def render(template_name: str, **context: object) -> str:
    """Render ``template_name`` from ``bloom/templates/email`` with ``context``."""
    return _env.get_template(template_name).render(**context)


def send_email(*, to: str, subject: str, html: str, text: str) -> None:
    """Deliver a multipart (text + HTML) email over SMTP.

    With no SMTP host configured the message is logged instead of sent, which keeps the
    app usable out of the box: reset links can be copied straight from the log.
    """
    settings = get_settings()
    if not settings.emails_enabled:
        logger.info("Email not sent (SMTP not configured). To: %s | Subject: %s\n%s", to, subject, text)
        return

    message = EmailMessage()
    message["From"] = f"{settings.EMAILS_FROM_NAME} <{settings.EMAILS_FROM_EMAIL}>"
    message["To"] = to
    message["Subject"] = subject
    message.set_content(text)
    message.add_alternative(html, subtype="html")

    try:
        if settings.SMTP_SSL:
            smtp: smtplib.SMTP = smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10)
        else:
            smtp = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10)
        with smtp:
            if settings.SMTP_TLS and not settings.SMTP_SSL:
                smtp.starttls()
            if settings.SMTP_USER and settings.SMTP_PASSWORD:
                smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            smtp.send_message(message)
    except (OSError, smtplib.SMTPException):
        # Sending runs in a background task, so raising here would only produce an
        # unhandled error after the response has already gone out.
        logger.exception("Failed to send email to %s (subject: %s)", to, subject)
        return

    logger.info("Email sent to %s (subject: %s)", to, subject)
