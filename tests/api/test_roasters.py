"""Roaster CRUD: open creation, admin-only edit/merge/delete."""


def _make_bean(client, headers, roaster, name="Kenya AA"):
    return client.post("/beans", headers=headers, json={"name": name, "roaster": roaster})


def test_any_user_can_create_a_roaster_with_metadata(client, alice_headers):
    resp = client.post(
        "/roasters",
        headers=alice_headers,
        json={"name": "Nomad Coffee", "country": "Spain", "city": "Barcelona"},
    )
    assert resp.status_code == 201
    assert resp.json()["city"] == "Barcelona"


def test_duplicate_roaster_name_409(client, alice_headers, bob_headers):
    client.post("/roasters", headers=alice_headers, json={"name": "Nomad Coffee"})
    # Same name in a different case is the same roaster, so it conflicts.
    resp = client.post("/roasters", headers=bob_headers, json={"name": "nomad COFFEE"})
    assert resp.status_code == 409


def test_bean_reuses_an_existing_roaster_and_keeps_its_metadata(client, alice_headers):
    roaster = client.post("/roasters", headers=alice_headers, json={"name": "Nomad", "country": "Spain"}).json()
    bean = _make_bean(client, alice_headers, roaster="nomad").json()

    # The bean attaches to the existing roaster rather than creating a second one.
    assert bean["roaster"]["id"] == roaster["id"]
    assert bean["roaster"]["country"] == "Spain"


def test_roasters_are_listed_alphabetically(client, alice_headers):
    for name in ["Right Side", "Nomad", "artesa"]:
        client.post("/roasters", headers=alice_headers, json={"name": name})

    names = [r["name"] for r in client.get("/roasters", headers=alice_headers).json()]
    assert names == ["artesa", "Nomad", "Right Side"]  # case-insensitive ordering


def test_admin_can_rename_and_every_bean_follows(client, admin_headers, alice_headers):
    bean = _make_bean(client, alice_headers, roaster="Nomad").json()
    roaster_id = bean["roaster"]["id"]

    resp = client.patch(f"/roasters/{roaster_id}", headers=admin_headers, json={"name": "Nomad Coffee Roasters"})
    assert resp.status_code == 200

    # The bean was never touched, yet it now reports the new name.
    refreshed = client.get(f"/beans/{bean['id']}", headers=alice_headers).json()
    assert refreshed["roaster"]["name"] == "Nomad Coffee Roasters"


def test_admin_can_clear_roaster_metadata_with_null(client, admin_headers, alice_headers):
    roaster_id = client.post(
        "/roasters",
        headers=alice_headers,
        json={"name": "Nomad", "country": "Spain", "notes": "great subs"},
    ).json()["id"]

    resp = client.patch(f"/roasters/{roaster_id}", headers=admin_headers, json={"country": None, "notes": None})
    assert resp.status_code == 200
    assert resp.json()["country"] is None
    assert resp.json()["notes"] is None


def test_null_roaster_name_rejected(client, admin_headers, alice_headers):
    roaster_id = client.post("/roasters", headers=alice_headers, json={"name": "Nomad"}).json()["id"]
    # name is NOT NULL: an explicit null is a 422, not a rename.
    assert client.patch(f"/roasters/{roaster_id}", headers=admin_headers, json={"name": None}).status_code == 422


def test_non_admin_cannot_rename_or_delete_a_roaster(client, alice_headers):
    roaster_id = client.post("/roasters", headers=alice_headers, json={"name": "Nomad"}).json()["id"]

    assert client.patch(f"/roasters/{roaster_id}", headers=alice_headers, json={"name": "X"}).status_code == 403
    assert client.delete(f"/roasters/{roaster_id}", headers=alice_headers).status_code == 403


def test_renaming_onto_an_existing_roaster_409(client, admin_headers, alice_headers):
    client.post("/roasters", headers=alice_headers, json={"name": "Nomad"})
    other_id = client.post("/roasters", headers=alice_headers, json={"name": "Right Side"}).json()["id"]

    # Renaming into a name that is taken must be a merge, not a rename.
    resp = client.patch(f"/roasters/{other_id}", headers=admin_headers, json={"name": "nomad"})
    assert resp.status_code == 409


def test_merge_moves_beans_and_deletes_the_source(client, admin_headers, alice_headers):
    # Two spellings that slipped in as separate roasters (e.g. created before a fix).
    keeper = client.post("/roasters", headers=alice_headers, json={"name": "Nomad Coffee"}).json()
    duplicate = client.post("/roasters", headers=alice_headers, json={"name": "Nomad Coffe"}).json()
    bean = _make_bean(client, alice_headers, roaster="Nomad Coffe", name="Typo bag").json()
    assert bean["roaster"]["id"] == duplicate["id"]

    resp = client.post(
        f"/roasters/{keeper['id']}/merge",
        headers=admin_headers,
        json={"source_id": duplicate["id"]},
    )
    assert resp.status_code == 200
    assert resp.json()["id"] == keeper["id"]

    # The bean now belongs to the survivor, and the duplicate is gone.
    moved = client.get(f"/beans/{bean['id']}", headers=alice_headers).json()
    assert moved["roaster"]["id"] == keeper["id"]
    assert client.get(f"/roasters/{duplicate['id']}", headers=alice_headers).status_code == 404


def test_merge_adopts_the_source_metadata_where_the_target_is_empty(client, admin_headers, alice_headers):
    # The duplicate is often the one somebody filled in properly; its data must survive.
    keeper = client.post("/roasters", headers=alice_headers, json={"name": "Nomad", "city": "BCN"}).json()
    duplicate = client.post(
        "/roasters",
        headers=alice_headers,
        json={"name": "Nomad Coffe", "city": "Barcelona", "country": "Spain"},
    ).json()

    merged = client.post(
        f"/roasters/{keeper['id']}/merge",
        headers=admin_headers,
        json={"source_id": duplicate["id"]},
    ).json()

    assert merged["country"] == "Spain"  # target had none: adopted from the source
    assert merged["city"] == "BCN"  # target had its own: kept, not overwritten


def test_merge_into_itself_409(client, admin_headers, alice_headers):
    roaster_id = client.post("/roasters", headers=alice_headers, json={"name": "Nomad"}).json()["id"]
    resp = client.post(f"/roasters/{roaster_id}/merge", headers=admin_headers, json={"source_id": roaster_id})
    assert resp.status_code == 409


def test_delete_unused_roaster(client, admin_headers, alice_headers):
    roaster_id = client.post("/roasters", headers=alice_headers, json={"name": "Nomad"}).json()["id"]
    assert client.delete(f"/roasters/{roaster_id}", headers=admin_headers).status_code == 204
    assert client.get(f"/roasters/{roaster_id}", headers=alice_headers).status_code == 404


def test_delete_roaster_in_use_409(client, admin_headers, alice_headers):
    bean = _make_bean(client, alice_headers, roaster="Nomad").json()
    # A roaster with beans must be merged away, never deleted from under them.
    resp = client.delete(f"/roasters/{bean['roaster']['id']}", headers=admin_headers)
    assert resp.status_code == 409


def test_deleting_the_last_bean_frees_its_roaster(client, admin_headers, alice_headers):
    bean = _make_bean(client, alice_headers, roaster="Nomad").json()
    client.delete(f"/beans/{bean['id']}", headers=alice_headers)
    # The roaster survives the bean (it is not cascaded away) but is now deletable.
    assert client.delete(f"/roasters/{bean['roaster']['id']}", headers=admin_headers).status_code == 204
