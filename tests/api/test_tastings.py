"""Tasting creation, listing, and score validation."""

import pytest


@pytest.fixture
def brew_id(client, alice_headers, lookups):
    bean_id = client.post("/beans", headers=alice_headers, json={"name": "Kenya AA", "roaster": "Nomad"}).json()["id"]
    return client.post(
        "/brews",
        headers=alice_headers,
        json={"bean_id": bean_id, "method_id": lookups["filter"]["id"], "dose_grams": "15"},
    ).json()["id"]


def test_create_and_list_tasting(client, alice_headers, brew_id):
    resp = client.post(
        f"/brews/{brew_id}/tastings",
        headers=alice_headers,
        json={"aroma": 4, "acidity": 5, "overall": 4, "descriptors": ["floral", "citrus"]},
    )
    assert resp.status_code == 201
    tasting = resp.json()
    assert tasting["descriptors"] == ["floral", "citrus"]

    listing = client.get(f"/brews/{brew_id}/tastings", headers=alice_headers)
    assert listing.status_code == 200
    assert len(listing.json()) == 1


def test_tasting_embeds_taster(client, bob_headers, brew_id):
    # Anyone can taste any brew; the tasting embeds its taster, who need not be
    # the brew's author (here bob tastes alice's brew).
    resp = client.post(f"/brews/{brew_id}/tastings", headers=bob_headers, json={"overall": 4})
    assert resp.status_code == 201
    assert resp.json()["author"]["username"] == "bob"


def test_multiple_tastings_per_brew(client, alice_headers, brew_id):
    client.post(f"/brews/{brew_id}/tastings", headers=alice_headers, json={"overall": 4})
    client.post(f"/brews/{brew_id}/tastings", headers=alice_headers, json={"overall": 5})
    assert len(client.get(f"/brews/{brew_id}/tastings", headers=alice_headers).json()) == 2


def test_score_out_of_range_rejected(client, alice_headers, brew_id):
    # Scores are 1–5; 6 is over the top of the scale.
    assert client.post(f"/brews/{brew_id}/tastings", headers=alice_headers, json={"aroma": 6}).status_code == 422


def test_null_descriptors_rejected_but_scores_are_nullable(client, alice_headers, brew_id):
    tasting = client.post(
        f"/brews/{brew_id}/tastings",
        headers=alice_headers,
        json={"aroma": 4, "descriptors": ["floral"]},
    ).json()

    # descriptors is NOT NULL (empty list, never null) — send [] to clear it.
    assert client.patch(f"/tastings/{tasting['id']}", headers=alice_headers, json={"descriptors": None}).status_code == 422
    assert client.patch(f"/tastings/{tasting['id']}", headers=alice_headers, json={"descriptors": []}).status_code == 200

    # Scores, in contrast, are nullable: an explicit null clears one.
    resp = client.patch(f"/tastings/{tasting['id']}", headers=alice_headers, json={"aroma": None})
    assert resp.status_code == 200
    assert resp.json()["aroma"] is None


def test_tasting_on_unknown_brew_404(client, alice_headers):
    assert client.post("/brews/9999/tastings", headers=alice_headers, json={"overall": 4}).status_code == 404
