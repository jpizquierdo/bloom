"""Ownership isolation, admin visibility, and ON DELETE cascade behavior."""

import pytest


@pytest.fixture
def alice_stack(client, alice_headers, lookups):
    """Create a bean -> brew -> tasting owned by alice; return their ids."""
    bean_id = client.post(
        "/beans", headers=alice_headers, json={"name": "Kenya AA", "roaster": "Nomad"}
    ).json()["id"]
    brew_id = client.post(
        "/brews",
        headers=alice_headers,
        json={"bean_id": bean_id, "method_id": lookups["filter"]["id"], "dose_grams": "15"},
    ).json()["id"]
    tasting_id = client.post(
        f"/brews/{brew_id}/tastings", headers=alice_headers, json={"overall": 8}
    ).json()["id"]
    return {"bean": bean_id, "brew": brew_id, "tasting": tasting_id}


def test_other_user_cannot_read_bean(client, bob_headers, alice_stack):
    assert client.get(f"/beans/{alice_stack['bean']}", headers=bob_headers).status_code == 404


def test_other_user_cannot_read_brew_or_tasting(client, bob_headers, alice_stack):
    assert client.get(f"/brews/{alice_stack['brew']}", headers=bob_headers).status_code == 404
    assert (
        client.get(f"/tastings/{alice_stack['tasting']}", headers=bob_headers).status_code
        == 404
    )


def test_other_user_cannot_brew_on_foreign_bean(client, bob_headers, alice_stack, lookups):
    resp = client.post(
        "/brews",
        headers=bob_headers,
        json={"bean_id": alice_stack["bean"], "method_id": lookups["filter"]["id"], "dose_grams": "15"},
    )
    assert resp.status_code == 404


def test_bob_sees_no_brews(client, bob_headers, alice_stack):
    assert client.get("/brews", headers=bob_headers).json() == []


def test_admin_sees_all(client, admin_headers, alice_stack):
    assert client.get(f"/brews/{alice_stack['brew']}", headers=admin_headers).status_code == 200
    assert len(client.get("/brews", headers=admin_headers).json()) == 1


def test_delete_bean_cascades(client, alice_headers, alice_stack):
    assert client.delete(f"/beans/{alice_stack['bean']}", headers=alice_headers).status_code == 204
    # brew and tasting are removed by the DB-level ON DELETE CASCADE
    assert client.get(f"/brews/{alice_stack['brew']}", headers=alice_headers).status_code == 404
    assert client.get(f"/tastings/{alice_stack['tasting']}", headers=alice_headers).status_code == 404


def test_lookups_readable_by_any_user_writable_only_by_admin(client, alice_headers, lookups):
    # Any authenticated user can read.
    assert client.get("/brew-methods", headers=alice_headers).status_code == 200
    assert client.get("/equipment", headers=alice_headers).status_code == 200
    # Only admins can write.
    assert (
        client.post(
            "/brew-methods", headers=alice_headers, json={"name": "Chemex", "category": "filter"}
        ).status_code
        == 403
    )
