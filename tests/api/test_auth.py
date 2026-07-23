"""Auth flow: token issuance, current user, and rejection paths."""

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
