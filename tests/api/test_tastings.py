"""Tasting creation, listing, and score validation."""

import pytest


@pytest.fixture
def brew_id(client, alice_headers, lookups):
    bean_id = client.post(
        "/beans", headers=alice_headers, json={"name": "Kenya AA", "roaster": "Nomad"}
    ).json()["id"]
    return client.post(
        "/brews",
        headers=alice_headers,
        json={"bean_id": bean_id, "method_id": lookups["filter"]["id"], "dose_grams": "15"},
    ).json()["id"]


def test_create_and_list_tasting(client, alice_headers, brew_id):
    resp = client.post(
        f"/brews/{brew_id}/tastings",
        headers=alice_headers,
        json={"aroma": 8, "acidity": 9, "overall": 8, "descriptors": ["floral", "citrus"]},
    )
    assert resp.status_code == 201
    tasting = resp.json()
    assert tasting["descriptors"] == ["floral", "citrus"]

    listing = client.get(f"/brews/{brew_id}/tastings", headers=alice_headers)
    assert listing.status_code == 200
    assert len(listing.json()) == 1


def test_multiple_tastings_per_brew(client, alice_headers, brew_id):
    client.post(f"/brews/{brew_id}/tastings", headers=alice_headers, json={"overall": 7})
    client.post(f"/brews/{brew_id}/tastings", headers=alice_headers, json={"overall": 8})
    assert len(client.get(f"/brews/{brew_id}/tastings", headers=alice_headers).json()) == 2


def test_score_out_of_range_rejected(client, alice_headers, brew_id):
    assert (
        client.post(
            f"/brews/{brew_id}/tastings", headers=alice_headers, json={"aroma": 11}
        ).status_code
        == 422
    )


def test_tasting_on_unknown_brew_404(client, alice_headers):
    assert (
        client.post(
            "/brews/9999/tastings", headers=alice_headers, json={"overall": 8}
        ).status_code
        == 404
    )
