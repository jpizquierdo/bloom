"""Brew creation, the domain EY calculation, ratio/diagnostics, and validation."""

import pytest


@pytest.fixture
def bean_id(client, alice_headers):
    return client.post(
        "/beans", headers=alice_headers, json={"name": "Kenya AA", "roaster": "Nomad"}
    ).json()["id"]


def test_brew_on_finished_bean_is_allowed(client, alice_headers, lookups, bean_id):
    # Marking a bag as finished does not block logging a brew (retroactive logging);
    # the service only emits a warning.
    client.patch(f"/beans/{bean_id}", headers=alice_headers, json={"is_finished": True})
    resp = client.post(
        "/brews",
        headers=alice_headers,
        json={"bean_id": bean_id, "method_id": lookups["filter"]["id"], "dose_grams": "15"},
    )
    assert resp.status_code == 201


def test_extraction_yield_computed_and_stored(client, alice_headers, lookups, bean_id):
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


def test_explicit_extraction_yield_is_kept(client, alice_headers, lookups, bean_id):
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
    assert resp.json()["extraction_yield_percent"] == "20.00"


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


def test_unknown_method_404(client, alice_headers, bean_id):
    resp = client.post(
        "/brews",
        headers=alice_headers,
        json={"bean_id": bean_id, "method_id": 9999, "dose_grams": "15"},
    )
    assert resp.status_code == 404
