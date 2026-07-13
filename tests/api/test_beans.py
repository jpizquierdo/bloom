"""Bean CRUD and validation."""


def _make_bean(client, headers, **overrides):
    payload = {"name": "Kenya AA", "roaster": "Nomad"}
    payload.update(overrides)
    return client.post("/beans", headers=headers, json=payload)


def test_create_and_get_bean(client, alice_headers, users):
    resp = _make_bean(client, alice_headers, process="washed", roast_level="medium", weight_grams=250)
    assert resp.status_code == 201
    bean = resp.json()
    assert bean["user_id"] == users["alice"].id
    # The roaster is returned as a nested object, created on the fly from its name.
    assert bean["roaster"]["name"] == "Nomad"

    got = client.get(f"/beans/{bean['id']}", headers=alice_headers)
    assert got.status_code == 200
    assert got.json()["name"] == "Kenya AA"


def test_creating_a_bean_creates_its_roaster_once(client, alice_headers, bob_headers):
    # Same roaster spelled three ways: one roaster row, shared by all three beans.
    first = _make_bean(client, alice_headers, name="Bag 1", roaster="Nomad Coffee").json()
    second = _make_bean(client, bob_headers, name="Bag 2", roaster="nomad coffee").json()
    third = _make_bean(client, alice_headers, name="Bag 3", roaster="  Nomad   Coffee ").json()

    assert first["roaster"]["id"] == second["roaster"]["id"] == third["roaster"]["id"]
    # The first spelling seen wins as the canonical one.
    assert third["roaster"]["name"] == "Nomad Coffee"
    assert len(client.get("/roasters", headers=alice_headers).json()) == 1


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
    assert client.patch(f"/beans/{bean_id}", headers=bob_headers, json={"is_finished": True}).status_code == 403
    assert client.delete(f"/beans/{bean_id}", headers=bob_headers).status_code == 403


def test_update_bean(client, alice_headers):
    bean_id = _make_bean(client, alice_headers).json()["id"]
    resp = client.patch(f"/beans/{bean_id}", headers=alice_headers, json={"is_finished": True})
    assert resp.status_code == 200
    assert resp.json()["is_finished"] is True


def test_update_bean_roaster_moves_it_to_a_new_roaster(client, alice_headers):
    bean = _make_bean(client, alice_headers, roaster="Nomad").json()
    resp = client.patch(f"/beans/{bean['id']}", headers=alice_headers, json={"roaster": "Right Side"})
    assert resp.status_code == 200
    assert resp.json()["roaster"]["name"] == "Right Side"
    assert resp.json()["roaster"]["id"] != bean["roaster"]["id"]

    # The bean moved; the roaster it was patched onto was created on the fly.
    roasters = {r["name"] for r in client.get("/roasters", headers=alice_headers).json()}
    assert roasters == {"Nomad", "Right Side"}


def test_delete_bean(client, alice_headers):
    bean_id = _make_bean(client, alice_headers).json()["id"]
    assert client.delete(f"/beans/{bean_id}", headers=alice_headers).status_code == 204
    assert client.get(f"/beans/{bean_id}", headers=alice_headers).status_code == 404


def test_missing_name_422(client, alice_headers):
    assert client.post("/beans", headers=alice_headers, json={"roaster": "X"}).status_code == 422


def test_blank_roaster_422(client, alice_headers):
    # Whitespace-only normalises to an empty name, which is not a roaster.
    assert _make_bean(client, alice_headers, roaster="   ").status_code == 422


def test_invalid_process_422(client, alice_headers):
    assert _make_bean(client, alice_headers, process="rocket-fuel").status_code == 422


def test_nonpositive_weight_422(client, alice_headers):
    assert _make_bean(client, alice_headers, weight_grams=0).status_code == 422
