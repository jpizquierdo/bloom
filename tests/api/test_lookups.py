"""Admin edit/delete of the shared lookup tables (brew_method, equipment)."""


def _bean_id(client, headers):
    return client.post("/beans", headers=headers, json={"name": "Kenya AA", "roaster": "Nomad"}).json()["id"]


# --- Admin gating -----------------------------------------------------------------


def test_non_admin_cannot_update_or_delete_brew_method(client, alice_headers, lookups):
    method_id = lookups["filter"]["id"]
    assert client.patch(f"/brew-methods/{method_id}", headers=alice_headers, json={"name": "X"}).status_code == 403
    assert client.delete(f"/brew-methods/{method_id}", headers=alice_headers).status_code == 403


def test_non_admin_cannot_update_or_delete_equipment(client, alice_headers, lookups):
    equipment_id = lookups["grinder"]["id"]
    assert client.patch(f"/equipment/{equipment_id}", headers=alice_headers, json={"name": "X"}).status_code == 403
    assert client.delete(f"/equipment/{equipment_id}", headers=alice_headers).status_code == 403


# --- Update -----------------------------------------------------------------------


def test_admin_updates_brew_method(client, admin_headers, lookups):
    resp = client.patch(
        f"/brew-methods/{lookups['filter']['id']}",
        headers=admin_headers,
        json={"name": "V60 Switch", "category": "immersion", "default_ratio": "15.00"},
    )
    assert resp.status_code == 200
    method = resp.json()
    assert method["name"] == "V60 Switch"
    assert method["category"] == "immersion"
    assert method["default_ratio"] == "15.00"


def test_admin_updates_equipment(client, admin_headers, lookups):
    resp = client.patch(
        f"/equipment/{lookups['grinder']['id']}",
        headers=admin_headers,
        json={"name": "Niche Zero v2", "brand": "Niche"},
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Niche Zero v2"
    assert resp.json()["brand"] == "Niche"


def test_rename_brew_method_to_existing_name_is_409(client, admin_headers, lookups):
    # brew_method.name is unique: renaming V60 onto the existing Espresso must conflict.
    resp = client.patch(
        f"/brew-methods/{lookups['filter']['id']}",
        headers=admin_headers,
        json={"name": "Espresso"},
    )
    assert resp.status_code == 409


# --- Clearing nullable fields with null --------------------------------------------


def test_clear_brew_method_default_ratio_with_null(client, admin_headers, lookups):
    # default_ratio is nullable: an explicit null clears it (the filter method has one).
    resp = client.patch(
        f"/brew-methods/{lookups['filter']['id']}",
        headers=admin_headers,
        json={"default_ratio": None},
    )
    assert resp.status_code == 200
    assert resp.json()["default_ratio"] is None


def test_clear_equipment_brand_and_notes_with_null(client, admin_headers):
    equipment = client.post(
        "/equipment",
        headers=admin_headers,
        json={"type": "kettle", "name": "Fellow Stagg", "brand": "Fellow", "notes": "gooseneck"},
    ).json()
    resp = client.patch(
        f"/equipment/{equipment['id']}",
        headers=admin_headers,
        json={"brand": None, "notes": None},
    )
    assert resp.status_code == 200
    assert resp.json()["brand"] is None
    assert resp.json()["notes"] is None


# --- Rejecting null on NOT NULL fields ---------------------------------------------


def test_reject_null_on_brew_method_required_fields(client, admin_headers, lookups):
    method_id = lookups["filter"]["id"]
    for field in ["name", "category"]:
        resp = client.patch(f"/brew-methods/{method_id}", headers=admin_headers, json={field: None})
        assert resp.status_code == 422, f"{field} accepted a null"


def test_reject_null_on_equipment_required_fields(client, admin_headers, lookups):
    equipment_id = lookups["grinder"]["id"]
    for field in ["type", "name"]:
        resp = client.patch(f"/equipment/{equipment_id}", headers=admin_headers, json={field: None})
        assert resp.status_code == 422, f"{field} accepted a null"


# --- Delete semantics --------------------------------------------------------------


def test_delete_brew_method_in_use_is_409(client, admin_headers, alice_headers, lookups):
    bean_id = _bean_id(client, alice_headers)
    client.post(
        "/brews",
        headers=alice_headers,
        json={"bean_id": bean_id, "method_id": lookups["filter"]["id"], "dose_grams": "15"},
    )
    # method_id is RESTRICT: a method used by a brew cannot be deleted.
    assert client.delete(f"/brew-methods/{lookups['filter']['id']}", headers=admin_headers).status_code == 409
    # The unused espresso method deletes fine.
    assert client.delete(f"/brew-methods/{lookups['espresso']['id']}", headers=admin_headers).status_code == 204


def test_delete_grinder_in_use_unlinks_the_brew(client, admin_headers, alice_headers, lookups):
    bean_id = _bean_id(client, alice_headers)
    brew = client.post(
        "/brews",
        headers=alice_headers,
        json={
            "bean_id": bean_id,
            "method_id": lookups["filter"]["id"],
            "dose_grams": "15",
            "grinder_id": lookups["grinder"]["id"],
        },
    ).json()
    assert brew["grinder_id"] == lookups["grinder"]["id"]

    # grinder_id is SET NULL: deleting a grinder in use succeeds and unlinks the brew.
    assert client.delete(f"/equipment/{lookups['grinder']['id']}", headers=admin_headers).status_code == 204
    after = client.get(f"/brews/{brew['id']}", headers=alice_headers).json()
    assert after["grinder_id"] is None
