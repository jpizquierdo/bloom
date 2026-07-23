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


def test_second_tasting_by_same_user_conflicts(client, alice_headers, brew_id):
    # Each user tastes a brew at most once: the first is created, the second is a
    # 409, and the brew keeps exactly one tasting.
    first = client.post(f"/brews/{brew_id}/tastings", headers=alice_headers, json={"overall": 4})
    assert first.status_code == 201

    second = client.post(f"/brews/{brew_id}/tastings", headers=alice_headers, json={"overall": 5})
    assert second.status_code == 409

    listing = client.get(f"/brews/{brew_id}/tastings", headers=alice_headers)
    assert len(listing.json()) == 1

    # The right way to change your score is to edit the existing tasting.
    patched = client.patch(f"/tastings/{first.json()['id']}", headers=alice_headers, json={"overall": 5})
    assert patched.status_code == 200
    assert patched.json()["overall"] == 5


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


def test_null_tasted_at_rejected(client, alice_headers, brew_id):
    tasting = client.post(f"/brews/{brew_id}/tastings", headers=alice_headers, json={"overall": 4}).json()
    # tasted_at is NOT NULL (server default now()): an explicit null is a 422, not a DB error.
    resp = client.patch(f"/tastings/{tasting['id']}", headers=alice_headers, json={"tasted_at": None})
    assert resp.status_code == 422


def test_tasting_notes_cleared_with_null(client, alice_headers, brew_id):
    tasting = client.post(
        f"/brews/{brew_id}/tastings",
        headers=alice_headers,
        json={"overall": 4, "notes": "juicy"},
    ).json()
    resp = client.patch(f"/tastings/{tasting['id']}", headers=alice_headers, json={"notes": None})
    assert resp.status_code == 200
    assert resp.json()["notes"] is None


def test_tasting_on_unknown_brew_404(client, alice_headers):
    assert client.post("/brews/9999/tastings", headers=alice_headers, json={"overall": 4}).status_code == 404
