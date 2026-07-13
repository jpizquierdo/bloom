"""User management: admin gating, creation, and self-lockout guard."""


def test_admin_creates_user(client, admin_headers):
    resp = client.post(
        "/users",
        headers=admin_headers,
        json={"email": "carol@example.com", "password": "carolpass1"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == "carol@example.com"
    assert body["role"] == "user"
    assert body["is_active"] is True


def test_duplicate_email_conflict(client, admin_headers):
    assert (
        client.post(
            "/users",
            headers=admin_headers,
            json={"email": "alice@example.com", "password": "whatever1"},
        ).status_code
        == 409
    )


def test_weak_password_rejected(client, admin_headers):
    assert (
        client.post(
            "/users",
            headers=admin_headers,
            json={"email": "dave@example.com", "password": "short"},
        ).status_code
        == 422
    )


def test_non_admin_cannot_list_users(client, alice_headers):
    assert client.get("/users", headers=alice_headers).status_code == 403


def test_admin_can_deactivate_user(client, admin_headers, users):
    alice_id = users["alice"].id
    resp = client.patch(f"/users/{alice_id}", headers=admin_headers, json={"is_active": False})
    assert resp.status_code == 200
    assert resp.json()["is_active"] is False


def test_admin_cannot_self_demote(client, admin_headers, users):
    admin_id = users["admin"].id
    assert client.patch(f"/users/{admin_id}", headers=admin_headers, json={"role": "user"}).status_code == 400


def test_patch_missing_user_404(client, admin_headers):
    assert client.patch("/users/9999", headers=admin_headers, json={"is_active": False}).status_code == 404
