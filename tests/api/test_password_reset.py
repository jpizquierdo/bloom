"""Password recovery: link delivery, resetting, and the ways a reset token must fail."""

import re

import pytest

from bloom.core.security import create_access_token, create_password_reset_token
from bloom.services import email_service


@pytest.fixture
def mailbox(monkeypatch) -> list[dict]:
    """Capture outgoing mail at the SMTP boundary.

    Patching ``send_email`` rather than the service functions means the Jinja templates
    are really rendered, so a broken template fails these tests.
    """
    sent: list[dict] = []

    def fake_send_email(*, to: str, subject: str, html: str, text: str) -> None:
        sent.append({"to": to, "subject": subject, "html": html, "text": text})

    monkeypatch.setattr(email_service, "send_email", fake_send_email)
    return sent


def _token_from(message: dict) -> str:
    """Pull the reset token out of the link in a captured email."""
    match = re.search(r"/reset-password\?token=([\w.\-]+)", message["text"])
    assert match, f"no reset link in email body:\n{message['text']}"
    return match.group(1)


def test_recover_password_sends_link(client, users, mailbox):
    resp = client.post("/auth/recover-password", json={"email": "alice@example.com"})
    assert resp.status_code == 202

    assert len(mailbox) == 1
    message = mailbox[0]
    assert message["to"] == "alice@example.com"
    # The templates rendered with real context, not leftover placeholders.
    assert "alice" in message["text"]
    assert "{{" not in message["html"]
    assert _token_from(message)


def test_recover_password_unknown_email_is_indistinguishable(client, users, mailbox):
    unknown = client.post("/auth/recover-password", json={"email": "nobody@example.com"})
    known = client.post("/auth/recover-password", json={"email": "alice@example.com"})

    # Same status and same body, so the endpoint cannot be used to enumerate accounts...
    assert unknown.status_code == known.status_code == 202
    assert unknown.json() == known.json()
    # ...but only the real account actually gets mail.
    assert [m["to"] for m in mailbox] == ["alice@example.com"]


def test_recover_password_inactive_user_gets_no_mail(client, db, users, mailbox):
    users["alice"].is_active = False
    db.commit()

    resp = client.post("/auth/recover-password", json={"email": "alice@example.com"})
    assert resp.status_code == 202
    assert mailbox == []


def test_reset_password_changes_the_password(client, users, mailbox):
    client.post("/auth/recover-password", json={"email": "alice@example.com"})
    token = _token_from(mailbox[0])

    resp = client.post("/auth/reset-password", json={"token": token, "new_password": "brand-new-pass1"})
    assert resp.status_code == 200

    # The new password works...
    assert client.post("/auth/token", data={"username": "alice@example.com", "password": "brand-new-pass1"}).status_code == 200
    # ...and the old one no longer does.
    assert client.post("/auth/token", data={"username": "alice@example.com", "password": "alicepass1"}).status_code == 401


def test_reset_token_is_not_an_access_token(client, users, mailbox):
    """The reason tokens carry a `type` claim: a reset link must not grant API access."""
    client.post("/auth/recover-password", json={"email": "alice@example.com"})
    token = _token_from(mailbox[0])

    assert client.get("/auth/me", headers={"Authorization": f"Bearer {token}"}).status_code == 401


def test_access_token_cannot_reset_a_password(client, users):
    """And the inverse: a stolen access token must not be spendable as a reset token."""
    access = create_access_token(str(users["alice"].id))

    resp = client.post("/auth/reset-password", json={"token": access, "new_password": "brand-new-pass1"})
    assert resp.status_code == 422


def test_reset_token_is_single_use(client, users, mailbox):
    client.post("/auth/recover-password", json={"email": "alice@example.com"})
    token = _token_from(mailbox[0])

    assert client.post("/auth/reset-password", json={"token": token, "new_password": "first-new-pass1"}).status_code == 200
    # password_changed_at now postdates the token's iat, so a replay is refused.
    second = client.post("/auth/reset-password", json={"token": token, "new_password": "second-new-pass1"})
    assert second.status_code == 422
    # The first reset stands.
    assert client.post("/auth/token", data={"username": "alice@example.com", "password": "first-new-pass1"}).status_code == 200


def test_expired_reset_token_is_refused(client, users):
    expired = create_password_reset_token(str(users["alice"].id), expires_minutes=-1)

    resp = client.post("/auth/reset-password", json={"token": expired, "new_password": "brand-new-pass1"})
    assert resp.status_code == 422


def test_garbage_reset_token_is_refused(client, users):
    resp = client.post("/auth/reset-password", json={"token": "not-a-jwt", "new_password": "brand-new-pass1"})
    assert resp.status_code == 422


def test_reset_token_for_inactive_user_is_refused(client, db, users, mailbox):
    client.post("/auth/recover-password", json={"email": "alice@example.com"})
    token = _token_from(mailbox[0])

    # Deactivated after the link was mailed but before it was followed.
    users["alice"].is_active = False
    db.commit()

    resp = client.post("/auth/reset-password", json={"token": token, "new_password": "brand-new-pass1"})
    assert resp.status_code == 422


def test_reset_password_rejects_a_short_password(client, users, mailbox):
    client.post("/auth/recover-password", json={"email": "alice@example.com"})
    token = _token_from(mailbox[0])

    resp = client.post("/auth/reset-password", json={"token": token, "new_password": "short"})
    assert resp.status_code == 422


def test_create_user_without_password_sends_an_invite(client, admin_headers, mailbox):
    resp = client.post(
        "/users",
        headers=admin_headers,
        json={"email": "carol@example.com", "username": "carol"},
    )
    assert resp.status_code == 201

    assert len(mailbox) == 1
    invite = mailbox[0]
    assert invite["to"] == "carol@example.com"
    assert "carol" in invite["text"]

    # The account exists but has no password anyone knows; the invite link is the way in.
    token = _token_from(invite)
    assert client.post("/auth/reset-password", json={"token": token, "new_password": "carols-pass1"}).status_code == 200
    assert client.post("/auth/token", data={"username": "carol@example.com", "password": "carols-pass1"}).status_code == 200


def test_create_user_with_password_still_works_and_mails(client, admin_headers, mailbox):
    resp = client.post(
        "/users",
        headers=admin_headers,
        json={"email": "dave@example.com", "username": "dave", "password": "daves-pass1"},
    )
    assert resp.status_code == 201

    # The admin-chosen password is usable immediately...
    assert client.post("/auth/token", data={"username": "dave@example.com", "password": "daves-pass1"}).status_code == 200
    # ...and the welcome mail still goes out, carrying a link but never the password.
    assert len(mailbox) == 1
    assert "daves-pass1" not in mailbox[0]["text"]
    assert "daves-pass1" not in mailbox[0]["html"]
