"""User management: admin gating, creation, and self-lockout guard."""


def test_admin_creates_user(client, admin_headers):
    resp = client.post(
        "/users",
        headers=admin_headers,
        json={"email": "carol@example.com", "username": "carol", "password": "carolpass1"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == "carol@example.com"
    assert body["username"] == "carol"
    assert body["role"] == "user"
    assert body["is_active"] is True


def test_duplicate_email_conflict(client, admin_headers):
    assert (
        client.post(
            "/users",
            headers=admin_headers,
            json={"email": "alice@example.com", "username": "alice2", "password": "whatever1"},
        ).status_code
        == 409
    )


def test_duplicate_username_conflict(client, admin_headers):
    # "alice" is already seeded, so reusing the handle must 409.
    assert (
        client.post(
            "/users",
            headers=admin_headers,
            json={"email": "alice2@example.com", "username": "alice", "password": "whatever1"},
        ).status_code
        == 409
    )


def test_invalid_username_rejected(client, admin_headers):
    # Spaces / uppercase are outside the handle pattern.
    assert (
        client.post(
            "/users",
            headers=admin_headers,
            json={"email": "eve@example.com", "username": "eve smith", "password": "evepass123"},
        ).status_code
        == 422
    )


def test_weak_password_rejected(client, admin_headers):
    assert (
        client.post(
            "/users",
            headers=admin_headers,
            json={"email": "dave@example.com", "username": "dave", "password": "short"},
        ).status_code
        == 422
    )


def test_admin_renames_user(client, admin_headers, users):
    alice_id = users["alice"].id
    resp = client.patch(f"/users/{alice_id}", headers=admin_headers, json={"username": "alice-v2"})
    assert resp.status_code == 200
    assert resp.json()["username"] == "alice-v2"


def test_rename_to_taken_username_conflict(client, admin_headers, users):
    alice_id = users["alice"].id
    # "bob" is already seeded, so renaming alice to it must 409.
    assert client.patch(f"/users/{alice_id}", headers=admin_headers, json={"username": "bob"}).status_code == 409


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


def test_null_role_or_is_active_rejected(client, admin_headers, users):
    alice_id = users["alice"].id
    # Both columns are NOT NULL: a null is a validation error, not a 500.
    assert client.patch(f"/users/{alice_id}", headers=admin_headers, json={"role": None}).status_code == 422
    assert client.patch(f"/users/{alice_id}", headers=admin_headers, json={"is_active": None}).status_code == 422


def test_patch_missing_user_404(client, admin_headers):
    assert client.patch("/users/9999", headers=admin_headers, json={"is_active": False}).status_code == 404
