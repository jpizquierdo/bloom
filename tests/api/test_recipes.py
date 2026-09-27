"""Recipe CRUD, ownership, lifecycle, and one-way brew snapshots."""

import pytest


@pytest.fixture
def bean_id(client, alice_headers):
    return client.post("/beans", headers=alice_headers, json={"name": "Brazil", "roaster": "Nomad"}).json()["id"]


def _recipe_payload(lookups, **overrides):
    payload = {
        "name": "Brazil: recipe #1",
        "method_id": lookups["espresso"]["id"],
        "grinder_id": lookups["grinder"]["id"],
        "dose_grams": "18",
        "yield_grams": "42",
        "grind_setting": "14",
        "water_temp_celsius": "94",
        "brew_time_seconds": 30,
        "notes": "Recipe-only guidance",
    }
    payload.update(overrides)
    return payload


def _create_recipe(client, headers, bean_id, lookups, **overrides):
    return client.post(
        f"/beans/{bean_id}/recipes",
        headers=headers,
        json=_recipe_payload(lookups, **overrides),
    )


def test_create_list_and_get_recipe(client, alice_headers, users, lookups, bean_id):
    response = _create_recipe(client, alice_headers, bean_id, lookups)

    assert response.status_code == 201
    recipe = response.json()
    assert recipe["bean_id"] == bean_id
    assert recipe["user_id"] == users["alice"].id
    assert recipe["owner"]["username"] == "alice"
    assert recipe["name"] == "Brazil: recipe #1"
    assert recipe["dose_grams"] == "18.00"
    assert recipe["notes"] == "Recipe-only guidance"

    assert client.get(f"/recipes/{recipe['id']}", headers=alice_headers).json() == recipe
    assert client.get(f"/beans/{bean_id}/recipes", headers=alice_headers).json() == [recipe]


def test_recipes_are_optional(client, alice_headers, bean_id):
    assert client.get(f"/beans/{bean_id}/recipes", headers=alice_headers).json() == []


def test_recipes_are_shared_but_writes_are_creator_owned(
    client,
    alice_headers,
    bob_headers,
    admin_headers,
    lookups,
    bean_id,
):
    recipe = _create_recipe(client, alice_headers, bean_id, lookups).json()

    assert client.get(f"/recipes/{recipe['id']}", headers=bob_headers).status_code == 200
    assert client.patch(f"/recipes/{recipe['id']}", headers=bob_headers, json={"name": "Bob's"}).status_code == 403
    assert client.delete(f"/recipes/{recipe['id']}", headers=bob_headers).status_code == 403

    updated = client.patch(f"/recipes/{recipe['id']}", headers=admin_headers, json={"name": "House espresso"})
    assert updated.status_code == 200
    assert updated.json()["name"] == "House espresso"


def test_any_user_can_create_a_recipe_for_a_shared_bean(client, bob_headers, lookups, bean_id, users):
    recipe = _create_recipe(client, bob_headers, bean_id, lookups).json()
    assert recipe["user_id"] == users["bob"].id


def test_any_user_can_brew_from_a_shared_recipe(client, alice_headers, bob_headers, lookups, bean_id, users):
    recipe = _create_recipe(client, alice_headers, bean_id, lookups).json()
    response = client.post(f"/recipes/{recipe['id']}/brews", headers=bob_headers, json={})
    assert response.status_code == 201
    assert response.json()["user_id"] == users["bob"].id


def test_update_recipe_and_clear_nullable_fields(client, alice_headers, lookups, bean_id):
    recipe = _create_recipe(client, alice_headers, bean_id, lookups).json()

    response = client.patch(
        f"/recipes/{recipe['id']}",
        headers=alice_headers,
        json={"dose_grams": "19", "grinder_id": None, "notes": None},
    )

    assert response.status_code == 200
    assert response.json()["dose_grams"] == "19.00"
    assert response.json()["grinder_id"] is None
    assert response.json()["notes"] is None


@pytest.mark.parametrize("field", ["name", "method_id", "dose_grams"])
def test_required_recipe_fields_reject_null(client, alice_headers, lookups, bean_id, field):
    recipe = _create_recipe(client, alice_headers, bean_id, lookups).json()
    response = client.patch(f"/recipes/{recipe['id']}", headers=alice_headers, json={field: None})
    assert response.status_code == 422


def test_recipe_validates_name_and_references(client, alice_headers, lookups, bean_id):
    assert _create_recipe(client, alice_headers, bean_id, lookups, name="   ").status_code == 422
    assert _create_recipe(client, alice_headers, bean_id, lookups, method_id=9999).status_code == 404
    assert _create_recipe(client, alice_headers, bean_id, lookups, grinder_id=9999).status_code == 404
    assert client.get("/beans/9999/recipes", headers=alice_headers).status_code == 404


@pytest.mark.parametrize("field", ["dose_grams", "brewed_at"])
def test_brew_from_recipe_rejects_null_required_values(client, alice_headers, lookups, bean_id, field):
    recipe = _create_recipe(client, alice_headers, bean_id, lookups).json()
    response = client.post(f"/recipes/{recipe['id']}/brews", headers=alice_headers, json={field: None})
    assert response.status_code == 422


def test_brew_from_recipe_copies_parameters_and_accepts_overrides(client, alice_headers, lookups, bean_id):
    recipe = _create_recipe(client, alice_headers, bean_id, lookups).json()

    response = client.post(
        f"/recipes/{recipe['id']}/brews",
        headers=alice_headers,
        json={"grind_setting": "15", "water_temp_celsius": "93", "notes": "Brew-only observation"},
    )

    assert response.status_code == 201
    brew = response.json()
    assert brew["recipe_id"] == recipe["id"]
    assert brew["bean_id"] == bean_id
    assert brew["method_id"] == recipe["method_id"]
    assert brew["dose_grams"] == "18.00"
    assert brew["yield_grams"] == "42.00"
    assert brew["grind_setting"] == "15"
    assert brew["water_temp_celsius"] == "93.0"
    assert brew["notes"] == "Brew-only observation"

    unchanged = client.get(f"/recipes/{recipe['id']}", headers=alice_headers).json()
    assert unchanged["grind_setting"] == "14"
    assert unchanged["water_temp_celsius"] == "94.0"
    assert unchanged["notes"] == "Recipe-only guidance"


def test_recipe_notes_do_not_copy_to_brew(client, alice_headers, lookups, bean_id):
    recipe = _create_recipe(client, alice_headers, bean_id, lookups).json()
    brew = client.post(f"/recipes/{recipe['id']}/brews", headers=alice_headers, json={}).json()
    assert brew["notes"] is None


def test_later_recipe_edits_do_not_change_existing_brew(client, alice_headers, lookups, bean_id):
    recipe = _create_recipe(client, alice_headers, bean_id, lookups).json()
    brew = client.post(f"/recipes/{recipe['id']}/brews", headers=alice_headers, json={}).json()

    client.patch(
        f"/recipes/{recipe['id']}",
        headers=alice_headers,
        json={"dose_grams": "20", "grind_setting": "16"},
    )

    stored = client.get(f"/brews/{brew['id']}", headers=alice_headers).json()
    assert stored["dose_grams"] == "18.00"
    assert stored["grind_setting"] == "14"


def test_delete_recipe_clears_provenance_but_keeps_brew(client, alice_headers, lookups, bean_id):
    recipe = _create_recipe(client, alice_headers, bean_id, lookups).json()
    brew = client.post(f"/recipes/{recipe['id']}/brews", headers=alice_headers, json={}).json()

    assert client.delete(f"/recipes/{recipe['id']}", headers=alice_headers).status_code == 204
    assert client.get(f"/recipes/{recipe['id']}", headers=alice_headers).status_code == 404
    stored = client.get(f"/brews/{brew['id']}", headers=alice_headers)
    assert stored.status_code == 200
    assert stored.json()["recipe_id"] is None
    assert stored.json()["dose_grams"] == "18.00"


def test_recipe_restricts_method_delete_and_unlinks_deleted_grinder(
    client,
    alice_headers,
    admin_headers,
    lookups,
    bean_id,
):
    recipe = _create_recipe(client, alice_headers, bean_id, lookups).json()

    method_response = client.delete(f"/brew-methods/{recipe['method_id']}", headers=admin_headers)
    assert method_response.status_code == 409

    assert client.delete(f"/equipment/{recipe['grinder_id']}", headers=admin_headers).status_code == 204
    assert client.get(f"/recipes/{recipe['id']}", headers=alice_headers).json()["grinder_id"] is None


def test_brew_from_recipe_rejects_lot_from_another_bean(client, alice_headers, lookups, bean_id):
    recipe = _create_recipe(client, alice_headers, bean_id, lookups).json()
    other = client.post("/beans", headers=alice_headers, json={"name": "Other", "roaster": "Nomad"}).json()
    lot = client.post(f"/beans/{other['id']}/lots", headers=alice_headers, json={}).json()

    response = client.post(
        f"/recipes/{recipe['id']}/brews",
        headers=alice_headers,
        json={"lot_id": lot["id"]},
    )
    assert response.status_code == 422


def test_bean_merge_moves_recipes(client, alice_headers, lookups):
    target = client.post("/beans", headers=alice_headers, json={"name": "Brazil", "roaster": "Nomad"}).json()
    source = client.post(
        "/beans?allow_duplicate=true",
        headers=alice_headers,
        json={"name": "Brazil", "roaster": "Nomad"},
    ).json()
    recipe = _create_recipe(client, alice_headers, source["id"], lookups).json()

    response = client.post(
        f"/beans/{target['id']}/merge",
        headers=alice_headers,
        json={"source_id": source["id"]},
    )

    assert response.status_code == 200
    assert client.get(f"/recipes/{recipe['id']}", headers=alice_headers).json()["bean_id"] == target["id"]


def test_delete_bean_cascades_to_recipe(client, alice_headers, lookups, bean_id):
    recipe = _create_recipe(client, alice_headers, bean_id, lookups).json()
    assert client.delete(f"/beans/{bean_id}", headers=alice_headers).status_code == 204
    assert client.get(f"/recipes/{recipe['id']}", headers=alice_headers).status_code == 404
