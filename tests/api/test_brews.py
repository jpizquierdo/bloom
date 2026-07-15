"""Brew creation, the domain EY calculation, ratio/diagnostics, and validation."""

import pytest


@pytest.fixture
def bean_id(client, alice_headers):
    return client.post("/beans", headers=alice_headers, json={"name": "Kenya AA", "roaster": "Nomad"}).json()["id"]


def test_brew_on_finished_lot_is_allowed(client, alice_headers, lookups, bean_id):
    # Brewing from a finished lot does not block logging (retroactive logging);
    # the service only emits a warning.
    lot_id = client.post(f"/beans/{bean_id}/lots", headers=alice_headers, json={"is_finished": True}).json()["id"]
    resp = client.post(
        "/brews",
        headers=alice_headers,
        json={"bean_id": bean_id, "lot_id": lot_id, "method_id": lookups["filter"]["id"], "dose_grams": "15"},
    )
    assert resp.status_code == 201
    assert resp.json()["lot_id"] == lot_id


def test_brew_without_a_lot_is_allowed(client, alice_headers, lookups, bean_id):
    # The lot is optional: a brew can name only the coffee.
    resp = client.post(
        "/brews",
        headers=alice_headers,
        json={"bean_id": bean_id, "method_id": lookups["filter"]["id"], "dose_grams": "15"},
    )
    assert resp.status_code == 201
    assert resp.json()["lot_id"] is None


def test_brew_with_lot_from_another_bean_422(client, alice_headers, lookups, bean_id):
    # A lot must belong to the brew's bean, else the reference is unprocessable.
    other_bean = client.post("/beans", headers=alice_headers, json={"name": "Other", "roaster": "Nomad"}).json()["id"]
    other_lot = client.post(f"/beans/{other_bean}/lots", headers=alice_headers, json={}).json()["id"]
    resp = client.post(
        "/brews",
        headers=alice_headers,
        json={"bean_id": bean_id, "lot_id": other_lot, "method_id": lookups["filter"]["id"], "dose_grams": "15"},
    )
    assert resp.status_code == 422


def test_brew_embeds_author(client, alice_headers, lookups, bean_id):
    # The brew carries its author as a nested object so the UI can show who
    # pulled it without resolving the (admin-only) user list.
    resp = client.post(
        "/brews",
        headers=alice_headers,
        json={"bean_id": bean_id, "method_id": lookups["filter"]["id"], "dose_grams": "15"},
    )
    assert resp.status_code == 201
    author = resp.json()["author"]
    assert author["username"] == "alice"
    assert author["id"] == resp.json()["user_id"]


def test_extraction_yield_computed_on_read(client, alice_headers, lookups, bean_id):
    resp = client.post(
        "/brews",
        headers=alice_headers,
        json={
            "bean_id": bean_id,
            "method_id": lookups["filter"]["id"],
            "dose_grams": "15",
            "water_grams": "250",
            "yield_grams": "250",
            "tds_percent": "1.35",
        },
    )
    assert resp.status_code == 201
    brew = resp.json()
    # (1.35 * 250) / 15 = 22.50
    assert brew["extraction_yield_percent"] == "22.50"
    # filter ratio = water / dose = 250 / 15 = 16.67
    assert brew["ratio"] == "16.67"
    assert brew["diagnostics"] == {"strength": "within", "extraction": "above"}


def test_extraction_yield_null_without_yield_mass(client, alice_headers, lookups, bean_id):
    resp = client.post(
        "/brews",
        headers=alice_headers,
        json={
            "bean_id": bean_id,
            "method_id": lookups["filter"]["id"],
            "dose_grams": "18",
            "tds_percent": "1.30",
        },
    )
    assert resp.status_code == 201
    assert resp.json()["extraction_yield_percent"] is None


def test_extraction_yield_recomputed_on_update(client, alice_headers, lookups, bean_id):
    # Regression: EY used to be computed only at create, so adding the
    # measurements afterwards left it null. It is now derived on read, so a later
    # edit that supplies TDS + yield is reflected immediately.
    brew = client.post(
        "/brews",
        headers=alice_headers,
        json={"bean_id": bean_id, "method_id": lookups["filter"]["id"], "dose_grams": "15"},
    ).json()
    assert brew["extraction_yield_percent"] is None

    resp = client.patch(
        f"/brews/{brew['id']}",
        headers=alice_headers,
        json={"yield_grams": "250", "tds_percent": "1.35"},
    )
    assert resp.status_code == 200
    # (1.35 * 250) / 15 = 22.50 — no explicit EY was ever sent.
    assert resp.json()["extraction_yield_percent"] == "22.50"


def test_extraction_yield_field_is_read_only(client, alice_headers, lookups, bean_id):
    # A client-supplied EY is ignored: the value always follows the measurements.
    resp = client.post(
        "/brews",
        headers=alice_headers,
        json={
            "bean_id": bean_id,
            "method_id": lookups["filter"]["id"],
            "dose_grams": "15",
            "yield_grams": "250",
            "tds_percent": "1.35",
            "extraction_yield_percent": "20.00",
        },
    )
    # The bogus 20.00 is dropped; the computed 22.50 wins.
    assert resp.json()["extraction_yield_percent"] == "22.50"


def test_espresso_ratio_uses_yield(client, alice_headers, lookups, bean_id):
    resp = client.post(
        "/brews",
        headers=alice_headers,
        json={
            "bean_id": bean_id,
            "method_id": lookups["espresso"]["id"],
            "dose_grams": "18",
            "yield_grams": "36",
        },
    )
    assert resp.json()["ratio"] == "2.00"


def test_dose_zero_rejected(client, alice_headers, lookups, bean_id):
    resp = client.post(
        "/brews",
        headers=alice_headers,
        json={"bean_id": bean_id, "method_id": lookups["filter"]["id"], "dose_grams": "0"},
    )
    assert resp.status_code == 422


def test_null_dose_rejected(client, alice_headers, lookups, bean_id):
    brew = client.post(
        "/brews",
        headers=alice_headers,
        json={"bean_id": bean_id, "method_id": lookups["filter"]["id"], "dose_grams": "15"},
    ).json()
    # dose_grams is NOT NULL: omit it to leave it alone, never null it out.
    resp = client.patch(f"/brews/{brew['id']}", headers=alice_headers, json={"dose_grams": None})
    assert resp.status_code == 422


def test_unknown_method_404(client, alice_headers, bean_id):
    resp = client.post(
        "/brews",
        headers=alice_headers,
        json={"bean_id": bean_id, "method_id": 9999, "dose_grams": "15"},
    )
    assert resp.status_code == 404
