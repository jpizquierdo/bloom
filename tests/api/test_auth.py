"""Auth flow: token issuance, current user, and rejection paths."""

from datetime import UTC, datetime, timedelta

import jwt
import pytest

from bloom.core.config import get_settings
from bloom.core.security import create_access_token
from bloom.services import users_service


def test_login_and_me(client, users):
    resp = client.post(
        "/auth/token",
        data={"username": "alice@example.com", "password": "alicepass1"},
    )
    assert resp.status_code == 200
    token = resp.json()["access_token"]

    me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    body = me.json()
    assert body["email"] == "alice@example.com"
    assert body["username"] == "alice"
    assert body["role"] == "user"


def test_login_with_username(client, users):
    # The identifier field accepts the username too, case-insensitively.
    resp = client.post(
        "/auth/token",
        data={"username": "Alice", "password": "alicepass1"},
    )
    assert resp.status_code == 200


def test_wrong_password_401(client, users):
    resp = client.post(
        "/auth/token",
        data={"username": "alice@example.com", "password": "wrong"},
    )
    assert resp.status_code == 401


def test_me_requires_token(client):
    assert client.get("/auth/me").status_code == 401


def test_inactive_user_cannot_login(client, db, users):
    users_service_user = users["alice"]
    users_service_user.is_active = False
    db.commit()
    resp = client.post(
        "/auth/token",
        data={"username": "alice@example.com", "password": "alicepass1"},
    )
    assert resp.status_code == 401


def test_password_change_invalidates_existing_access_tokens(client, db, users):
    # An access token minted before the last password change must stop working, so
    # changing a password logs out every active session.
    token = client.post(
        "/auth/token",
        data={"username": "alice@example.com", "password": "alicepass1"},
    ).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    assert client.get("/auth/me", headers=headers).status_code == 200

    # Changing the password bumps password_changed_at, which postdates the token.
    users_service.set_password(db, users["alice"], "newpass123")
    db.commit()

    assert client.get("/auth/me", headers=headers).status_code == 401


def test_login_email_ignores_case(client, users):
    resp = client.post("/auth/token", data={"username": "Alice@EXAMPLE.com", "password": "alicepass1"})
    assert resp.status_code == 200


def _login_headers(client, email="alice@example.com", password="alicepass1"):
    token = client.post("/auth/token", data={"username": email, "password": password}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_deactivating_a_user_kills_their_existing_token(client, admin_headers, users):
    # Blocking login is not enough: a session opened before the deactivation must end too.
    alice = _login_headers(client)
    assert client.get("/auth/me", headers=alice).status_code == 200

    resp = client.patch(f"/users/{users['alice'].id}", headers=admin_headers, json={"is_active": False})
    assert resp.status_code == 200

    assert client.get("/auth/me", headers=alice).status_code == 401


def test_expired_access_token_is_refused(client, users):
    token = create_access_token(str(users["alice"].id), expires_minutes=-1)
    assert client.get("/auth/me", headers={"Authorization": f"Bearer {token}"}).status_code == 401


def test_token_without_issue_time_is_refused(client, users):
    # Without iat_ms there is nothing to compare against password_changed_at, so it is rejected.
    settings = get_settings()
    payload = {"sub": str(users["alice"].id), "type": "access", "exp": datetime.now(UTC) + timedelta(hours=1)}
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    assert client.get("/auth/me", headers={"Authorization": f"Bearer {token}"}).status_code == 401


@pytest.mark.parametrize("subject", ["999999", "not-a-number", ""])
def test_token_for_unknown_or_malformed_subject_is_refused(client, users, subject):
    token = create_access_token(subject)
    assert client.get("/auth/me", headers={"Authorization": f"Bearer {token}"}).status_code == 401


def test_token_signed_with_another_key_is_refused(client, users):
    settings = get_settings()
    payload = {"sub": str(users["alice"].id), "type": "access", "iat_ms": 9_999_999_999_999}
    token = jwt.encode(payload, "x" * 32, algorithm=settings.JWT_ALGORITHM)
    assert client.get("/auth/me", headers={"Authorization": f"Bearer {token}"}).status_code == 401
