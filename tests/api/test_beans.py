"""Bean CRUD and validation."""


def _make_bean(client, headers, **overrides):
    payload = {"name": "Kenya AA", "roaster": "Nomad"}
    payload.update(overrides)
    return client.post("/beans", headers=headers, json=payload)


def test_create_and_get_bean(client, alice_headers, users):
    resp = _make_bean(
        client, alice_headers, process="washed", roast_level="medium", weight_grams=250
    )
    assert resp.status_code == 201
    bean = resp.json()
    assert bean["user_id"] == users["alice"].id

    got = client.get(f"/beans/{bean['id']}", headers=alice_headers)
    assert got.status_code == 200
    assert got.json()["name"] == "Kenya AA"


def test_beans_are_shared_across_users(client, alice_headers, bob_headers):
    _make_bean(client, alice_headers, name="Alice bean")
    _make_bean(client, bob_headers, name="Bob bean")

    # Beans are shared: every authenticated user sees them all.
    names = {b["name"] for b in client.get("/beans", headers=alice_headers).json()}
    assert names == {"Alice bean", "Bob bean"}


def test_mine_filter_returns_only_own_beans(client, alice_headers, bob_headers):
    _make_bean(client, alice_headers, name="Alice bean")
    _make_bean(client, bob_headers, name="Bob bean")

    mine = {b["name"] for b in client.get("/beans?mine=true", headers=alice_headers).json()}
    assert mine == {"Alice bean"}


def test_non_owner_can_read_but_not_modify_bean(client, alice_headers, bob_headers):
    bean_id = _make_bean(client, alice_headers).json()["id"]
    # A non-owner can read a shared bean...
    assert client.get(f"/beans/{bean_id}", headers=bob_headers).status_code == 200
    # ...but cannot edit or delete it.
    assert (
        client.patch(
            f"/beans/{bean_id}", headers=bob_headers, json={"is_finished": True}
        ).status_code
        == 403
    )
    assert client.delete(f"/beans/{bean_id}", headers=bob_headers).status_code == 403


def test_update_bean(client, alice_headers):
    bean_id = _make_bean(client, alice_headers).json()["id"]
    resp = client.patch(
        f"/beans/{bean_id}", headers=alice_headers, json={"is_finished": True}
    )
    assert resp.status_code == 200
    assert resp.json()["is_finished"] is True


def test_delete_bean(client, alice_headers):
    bean_id = _make_bean(client, alice_headers).json()["id"]
    assert client.delete(f"/beans/{bean_id}", headers=alice_headers).status_code == 204
    assert client.get(f"/beans/{bean_id}", headers=alice_headers).status_code == 404


def test_missing_name_422(client, alice_headers):
    assert client.post("/beans", headers=alice_headers, json={"roaster": "X"}).status_code == 422


def test_invalid_process_422(client, alice_headers):
    assert _make_bean(client, alice_headers, process="rocket-fuel").status_code == 422


def test_nonpositive_weight_422(client, alice_headers):
    assert _make_bean(client, alice_headers, weight_grams=0).status_code == 422
