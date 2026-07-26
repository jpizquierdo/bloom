"""Bean CRUD, validation, duplicate detection and merge."""

import pytest


def _make_bean(client, headers, **overrides):
    payload = {"name": "Kenya AA", "roaster": "Nomad"}
    payload.update(overrides)
    return client.post("/beans", headers=headers, json=payload)


def test_create_and_get_bean(client, alice_headers, users):
    resp = _make_bean(client, alice_headers, process="washed", roast_level="medium")
    assert resp.status_code == 201
    bean = resp.json()
    assert bean["user_id"] == users["alice"].id
    # The owner is embedded as a nested object so the UI can name who added the bag.
    assert bean["owner"] == {"id": users["alice"].id, "username": "alice"}
    # The roaster is returned as a nested object, created on the fly from its name.
    assert bean["roaster"]["name"] == "Nomad"
    # Physical, per-purchase fields moved to bean_lot — the bean is now the coffee concept.
    for moved in ("roast_date", "purchase_date", "weight_grams", "price", "is_finished"):
        assert moved not in bean, f"{moved} should live on the lot now"

    # New descriptive columns default when omitted: unknown roast type, single origin,
    # unrated (null rating), and no website.
    assert bean["roast_type"] == "unknown"
    assert bean["blend"] == "single_origin"
    assert bean["rating"] is None
    assert bean["website"] is None

    got = client.get(f"/beans/{bean['id']}", headers=alice_headers)
    assert got.status_code == 200
    assert got.json()["name"] == "Kenya AA"


def test_create_bean_with_new_fields(client, alice_headers):
    resp = _make_bean(
        client,
        alice_headers,
        roast_type="filter",
        blend="blend",
        rating=4,
        website="https://nomadcoffee.es",
    )
    assert resp.status_code == 201
    bean = resp.json()
    assert bean["roast_type"] == "filter"
    assert bean["blend"] == "blend"
    assert bean["rating"] == 4
    assert bean["website"] == "https://nomadcoffee.es"


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
    assert client.patch(f"/beans/{bean_id}", headers=bob_headers, json={"notes": "mine now"}).status_code == 403
    assert client.delete(f"/beans/{bean_id}", headers=bob_headers).status_code == 403


def test_update_bean(client, alice_headers):
    bean_id = _make_bean(client, alice_headers).json()["id"]
    resp = client.patch(f"/beans/{bean_id}", headers=alice_headers, json={"notes": "Great as filter"})
    assert resp.status_code == 200
    assert resp.json()["notes"] == "Great as filter"


def test_update_bean_roaster_moves_it_to_a_new_roaster(client, alice_headers):
    bean = _make_bean(client, alice_headers, roaster="Nomad").json()
    resp = client.patch(f"/beans/{bean['id']}", headers=alice_headers, json={"roaster": "Right Side"})
    assert resp.status_code == 200
    assert resp.json()["roaster"]["name"] == "Right Side"
    assert resp.json()["roaster"]["id"] != bean["roaster"]["id"]

    # The bean moved to a roaster created on the fly; the one it left held nothing and
    # had no beans left, so it was discarded (see the abandoned-roaster tests below).
    roasters = {r["name"] for r in client.get("/roasters", headers=alice_headers).json()}
    assert roasters == {"Right Side"}


def test_fixing_a_typo_discards_the_abandoned_roaster(client, alice_headers):
    # A roaster auto-created by a typo holds no information, so once its last bean
    # leaves it must not linger in the picker.
    bean = _make_bean(client, alice_headers, roaster="Nomad Coffe").json()
    client.patch(f"/beans/{bean['id']}", headers=alice_headers, json={"roaster": "Nomad Coffee"})

    roasters = {r["name"] for r in client.get("/roasters", headers=alice_headers).json()}
    assert roasters == {"Nomad Coffee"}


def test_an_abandoned_roaster_with_metadata_is_kept(client, alice_headers):
    # Somebody entered this roaster's details on purpose: losing its last bean does not
    # make it garbage.
    client.post("/roasters", headers=alice_headers, json={"name": "Nomad", "country": "Spain"})
    bean = _make_bean(client, alice_headers, roaster="Nomad").json()
    client.patch(f"/beans/{bean['id']}", headers=alice_headers, json={"roaster": "Right Side"})

    roasters = {r["name"] for r in client.get("/roasters", headers=alice_headers).json()}
    assert roasters == {"Nomad", "Right Side"}


def test_a_roaster_still_used_by_another_bean_is_kept(client, alice_headers, bob_headers):
    kept = _make_bean(client, alice_headers, name="Stays", roaster="Nomad").json()
    moving = _make_bean(client, bob_headers, name="Moves", roaster="Nomad").json()
    client.patch(f"/beans/{moving['id']}", headers=bob_headers, json={"roaster": "Right Side"})

    # Alice's bean still points at Nomad, so it survives Bob moving his away.
    assert client.get(f"/beans/{kept['id']}", headers=alice_headers).json()["roaster"]["name"] == "Nomad"
    roasters = {r["name"] for r in client.get("/roasters", headers=alice_headers).json()}
    assert roasters == {"Nomad", "Right Side"}


def test_delete_bean(client, alice_headers):
    bean_id = _make_bean(client, alice_headers).json()["id"]
    assert client.delete(f"/beans/{bean_id}", headers=alice_headers).status_code == 204
    assert client.get(f"/beans/{bean_id}", headers=alice_headers).status_code == 404


def test_missing_name_422(client, alice_headers):
    assert client.post("/beans", headers=alice_headers, json={"roaster": "X"}).status_code == 422


def test_blank_name_or_roaster_422(client, alice_headers):
    # Whitespace-only normalises to an empty string, which is neither a coffee nor a roaster.
    assert _make_bean(client, alice_headers, roaster="   ").status_code == 422
    assert _make_bean(client, alice_headers, name="   ").status_code == 422


def test_bean_name_is_whitespace_normalised(client, alice_headers):
    # Names are normalised on the way in, like roaster names: spacing must never be what
    # decides whether two entries are the same coffee.
    assert _make_bean(client, alice_headers, name="  Kenya   AA ").json()["name"] == "Kenya AA"


def test_explicit_null_on_a_required_field_422(client, alice_headers):
    bean_id = _make_bean(client, alice_headers).json()["id"]
    # These columns are NOT NULL: omitting them leaves them unchanged, but sending an
    # explicit null must be a validation error, not a database failure.
    for field in ["name", "roaster", "roast_type", "blend"]:
        resp = client.patch(f"/beans/{bean_id}", headers=alice_headers, json={field: None})
        assert resp.status_code == 422, f"{field} accepted a null"

    # Nullable fields, in contrast, can still be cleared with an explicit null — including
    # rating (null = unrated), so a bean can be un-rated again.
    for field in ["notes", "rating"]:
        resp = client.patch(f"/beans/{bean_id}", headers=alice_headers, json={field: None})
        assert resp.status_code == 200, f"{field} rejected a null"
        assert resp.json()[field] is None


def test_nullable_bean_fields_cleared_with_null(client, alice_headers):
    # Optional descriptive fields are set on create, then cleared back to null on PATCH.
    bean_id = _make_bean(
        client,
        alice_headers,
        region="Guji",
        website="https://nomadcoffee.es",
        process="washed",
    ).json()["id"]

    resp = client.patch(
        f"/beans/{bean_id}",
        headers=alice_headers,
        json={"region": None, "website": None, "process": None},
    )
    assert resp.status_code == 200
    cleared = resp.json()
    assert cleared["region"] is None
    assert cleared["website"] is None
    assert cleared["process"] is None


def test_invalid_process_422(client, alice_headers):
    assert _make_bean(client, alice_headers, process="rocket-fuel").status_code == 422


def test_invalid_roast_type_422(client, alice_headers):
    assert _make_bean(client, alice_headers, roast_type="turbo").status_code == 422


def test_invalid_blend_422(client, alice_headers):
    assert _make_bean(client, alice_headers, blend="triple_origin").status_code == 422


def test_rating_out_of_range_422(client, alice_headers):
    # Rating is 1–5 (null = unrated); 0 and 6 are out of range.
    assert _make_bean(client, alice_headers, rating=0).status_code == 422
    assert _make_bean(client, alice_headers, rating=6).status_code == 422


# --- Duplicate detection -------------------------------------------------------------


def test_same_name_and_roaster_twice_409(client, alice_headers):
    first = _make_bean(client, alice_headers).json()
    resp = _make_bean(client, alice_headers)
    assert resp.status_code == 409
    # The message must name the bean that already exists, so the UI can point at it.
    detail = resp.json()["detail"]
    assert "Kenya AA" in detail and "Nomad" in detail and str(first["id"]) in detail


def test_duplicate_ignores_case_and_spacing(client, alice_headers, bob_headers):
    _make_bean(client, alice_headers)
    # Case folding happens in the database, and both names are whitespace-normalised on
    # the way in — so none of these spellings is a new coffee.
    assert _make_bean(client, alice_headers, name="kenya aa").status_code == 409
    assert _make_bean(client, alice_headers, name="  Kenya   AA ").status_code == 409
    assert _make_bean(client, alice_headers, roaster="nomad").status_code == 409
    # A duplicate is a duplicate for everyone: beans are shared, not per-user.
    assert _make_bean(client, bob_headers).status_code == 409


def test_same_name_under_another_roaster_is_allowed(client, alice_headers):
    _make_bean(client, alice_headers)
    # Two roasters can sell a "Kenya AA": only the pair (roaster, name) must be unique.
    assert _make_bean(client, alice_headers, roaster="Right Side").status_code == 201


def test_allow_duplicate_creates_the_second_bean(client, alice_headers):
    _make_bean(client, alice_headers)
    resp = client.post(
        "/beans?allow_duplicate=true",
        headers=alice_headers,
        json={"name": "Kenya AA", "roaster": "Nomad"},
    )
    assert resp.status_code == 201
    # The guard is a warning, not a constraint: the caller can insist.
    assert len(client.get("/beans", headers=alice_headers).json()) == 2


def test_rename_onto_an_existing_bean_409(client, alice_headers):
    _make_bean(client, alice_headers, name="Kenya AA")
    other_id = _make_bean(client, alice_headers, name="Guji").json()["id"]

    resp = client.patch(f"/beans/{other_id}", headers=alice_headers, json={"name": "Kenya AA"})
    assert resp.status_code == 409
    assert "merge into it instead" in resp.json()["detail"]
    # Nothing was applied: the rejection happens before the bean is touched.
    assert client.get(f"/beans/{other_id}", headers=alice_headers).json()["name"] == "Guji"

    # ...and the caller can still insist.
    forced = client.patch(f"/beans/{other_id}?allow_duplicate=true", headers=alice_headers, json={"name": "Kenya AA"})
    assert forced.status_code == 200


def test_moving_a_bean_onto_a_roaster_that_has_the_name_409(client, alice_headers):
    _make_bean(client, alice_headers, name="Kenya AA", roaster="Nomad")
    moving_id = _make_bean(client, alice_headers, name="Kenya AA", roaster="Right Side").json()["id"]

    assert client.patch(f"/beans/{moving_id}", headers=alice_headers, json={"roaster": "Nomad"}).status_code == 409
    # The rejected move left the bean on its own roaster, which therefore survives.
    assert client.get(f"/beans/{moving_id}", headers=alice_headers).json()["roaster"]["name"] == "Right Side"


def test_saving_a_bean_unchanged_is_not_a_duplicate_of_itself(client, alice_headers):
    bean = _make_bean(client, alice_headers).json()
    resp = client.patch(
        f"/beans/{bean['id']}",
        headers=alice_headers,
        json={"name": "Kenya AA", "roaster": "Nomad", "notes": "Great as filter"},
    )
    assert resp.status_code == 200
    assert resp.json()["notes"] == "Great as filter"


# --- Merge ---------------------------------------------------------------------------


@pytest.fixture
def duplicate_pair(client, alice_headers, lookups):
    """Two beans for the same coffee; the source carries a lot, a brew and a tasting."""
    target = _make_bean(client, alice_headers, name="Kenya AA", roast_type="filter").json()
    source = client.post(
        "/beans?allow_duplicate=true",
        headers=alice_headers,
        json={"name": "Kenya AA", "roaster": "Nomad", "region": "Kirinyaga", "roast_type": "espresso"},
    ).json()

    lot_id = client.post(
        f"/beans/{source['id']}/lots",
        headers=alice_headers,
        json={"weight_grams": 250},
    ).json()["id"]
    brew_id = client.post(
        "/brews",
        headers=alice_headers,
        json={"bean_id": source["id"], "lot_id": lot_id, "method_id": lookups["filter"]["id"], "dose_grams": "15"},
    ).json()["id"]
    tasting_id = client.post(f"/brews/{brew_id}/tastings", headers=alice_headers, json={"overall": 4}).json()["id"]
    return {"target": target, "source": source, "lot": lot_id, "brew": brew_id, "tasting": tasting_id}


def test_merge_moves_brews_and_lots_and_deletes_the_source(client, alice_headers, duplicate_pair):
    target_id = duplicate_pair["target"]["id"]
    resp = client.post(
        f"/beans/{target_id}/merge",
        headers=alice_headers,
        json={"source_id": duplicate_pair["source"]["id"]},
    )
    assert resp.status_code == 200

    # The brew and the lot moved instead of being cascaded away with the source bean.
    assert client.get(f"/brews/{duplicate_pair['brew']}", headers=alice_headers).json()["bean_id"] == target_id
    lots = client.get(f"/beans/{target_id}/lots", headers=alice_headers).json()
    assert [lot["id"] for lot in lots] == [duplicate_pair["lot"]]
    # The tasting hangs off the brew, so it follows it.
    assert client.get(f"/tastings/{duplicate_pair['tasting']}", headers=alice_headers).status_code == 200

    assert client.get(f"/beans/{duplicate_pair['source']['id']}", headers=alice_headers).status_code == 404


def test_merge_adopts_source_data_only_where_the_target_has_none(client, alice_headers, duplicate_pair):
    resp = client.post(
        f"/beans/{duplicate_pair['target']['id']}/merge",
        headers=alice_headers,
        json={"source_id": duplicate_pair["source"]["id"]},
    )
    merged = resp.json()
    # The target had no region, so it adopts the source's...
    assert merged["region"] == "Kirinyaga"
    # ...but its own roast type wins over the duplicate's.
    assert merged["roast_type"] == "filter"


def test_merge_adopts_a_value_over_unknown(client, alice_headers):
    # "unknown" is the no-information value of the two NOT NULL descriptive columns, so
    # it must not beat a real value coming from the duplicate.
    target = _make_bean(client, alice_headers, name="Kenya AA").json()
    source = client.post(
        "/beans?allow_duplicate=true",
        headers=alice_headers,
        json={"name": "Kenya AA", "roaster": "Nomad", "roast_type": "espresso", "blend": "blend"},
    ).json()

    merged = client.post(f"/beans/{target['id']}/merge", headers=alice_headers, json={"source_id": source["id"]}).json()
    assert merged["roast_type"] == "espresso"
    # blend defaults to single_origin, which is a real answer — the target keeps it.
    assert merged["blend"] == "single_origin"


def test_merge_into_itself_409(client, alice_headers):
    bean_id = _make_bean(client, alice_headers).json()["id"]
    resp = client.post(f"/beans/{bean_id}/merge", headers=alice_headers, json={"source_id": bean_id})
    assert resp.status_code == 409


def test_merge_requires_owning_both_beans(client, alice_headers, bob_headers, admin_headers):
    alice_bean = _make_bean(client, alice_headers, name="Kenya AA").json()["id"]
    bob_bean = _make_bean(client, bob_headers, name="Guji").json()["id"]

    # Bob owns neither the target nor the source outright, so he cannot fold one away.
    assert client.post(f"/beans/{alice_bean}/merge", headers=bob_headers, json={"source_id": bob_bean}).status_code == 403
    assert client.post(f"/beans/{bob_bean}/merge", headers=alice_headers, json={"source_id": alice_bean}).status_code == 403
    # An admin may merge anything.
    assert client.post(f"/beans/{alice_bean}/merge", headers=admin_headers, json={"source_id": bob_bean}).status_code == 200


def test_merge_missing_source_404(client, alice_headers):
    bean_id = _make_bean(client, alice_headers).json()["id"]
    assert client.post(f"/beans/{bean_id}/merge", headers=alice_headers, json={"source_id": 9999}).status_code == 404


def test_merging_away_the_last_bean_of_a_roaster_discards_it(client, alice_headers):
    # Same mess as a typo fixed with PATCH: the duplicate's roaster held nothing and now
    # has no beans, so it must not linger in the picker.
    target = _make_bean(client, alice_headers, name="Kenya AA", roaster="Nomad").json()
    source = _make_bean(client, alice_headers, name="Kenya AA", roaster="Nomad Coffe").json()

    client.post(f"/beans/{target['id']}/merge", headers=alice_headers, json={"source_id": source["id"]})

    roasters = {r["name"] for r in client.get("/roasters", headers=alice_headers).json()}
    assert roasters == {"Nomad"}
