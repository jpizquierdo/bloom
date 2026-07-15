"""Auth flow: token issuance, current user, and rejection paths."""


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
