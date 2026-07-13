"""Ownership isolation, admin visibility, and ON DELETE cascade behavior."""

import pytest


@pytest.fixture
def alice_stack(client, alice_headers, lookups):
    """Create a bean -> brew -> tasting owned by alice; return their ids."""
    bean_id = client.post("/beans", headers=alice_headers, json={"name": "Kenya AA", "roaster": "Nomad"}).json()["id"]
    brew_id = client.post(
        "/brews",
        headers=alice_headers,
        json={"bean_id": bean_id, "method_id": lookups["filter"]["id"], "dose_grams": "15"},
    ).json()["id"]
    tasting_id = client.post(f"/brews/{brew_id}/tastings", headers=alice_headers, json={"overall": 8}).json()["id"]
    return {"bean": bean_id, "brew": brew_id, "tasting": tasting_id}


def test_shared_bean_readable_by_other_user(client, bob_headers, alice_stack):
    # Beans are shared: bob can read alice's bean.
    assert client.get(f"/beans/{alice_stack['bean']}", headers=bob_headers).status_code == 200


def test_shared_brew_and_tasting_readable_by_other_user(client, bob_headers, alice_stack):
    # Brews and their tastings are a shared log: bob can read alice's.
    assert client.get(f"/brews/{alice_stack['brew']}", headers=bob_headers).status_code == 200
    assert client.get(f"/tastings/{alice_stack['tasting']}", headers=bob_headers).status_code == 200


def test_other_user_can_brew_on_shared_bean(client, bob_headers, alice_stack, lookups, users):
    # bob brews from alice's (shared) bean; the brew is authored by bob.
    resp = client.post(
        "/brews",
        headers=bob_headers,
        json={
            "bean_id": alice_stack["bean"],
            "method_id": lookups["filter"]["id"],
            "dose_grams": "15",
        },
    )
    assert resp.status_code == 201
    assert resp.json()["user_id"] == users["bob"].id


def test_brew_log_is_shared(client, alice_headers, bob_headers, alice_stack, lookups):
    bob_brew_id = client.post(
        "/brews",
        headers=bob_headers,
        json={
            "bean_id": alice_stack["bean"],
            "method_id": lookups["filter"]["id"],
            "dose_grams": "15",
        },
    ).json()["id"]

    alice_view = {b["id"] for b in client.get("/brews", headers=alice_headers).json()}
    bob_view = {b["id"] for b in client.get("/brews", headers=bob_headers).json()}

    # Everyone sees the whole shared brew log.
    assert alice_view == bob_view == {alice_stack["brew"], bob_brew_id}


def test_mine_filter_returns_only_own_brews(client, alice_headers, bob_headers, alice_stack, lookups):
    bob_brew_id = client.post(
        "/brews",
        headers=bob_headers,
        json={
            "bean_id": alice_stack["bean"],
            "method_id": lookups["filter"]["id"],
            "dose_grams": "15",
        },
    ).json()["id"]

    # Default: the whole shared log.
    assert len(client.get("/brews", headers=alice_headers).json()) == 2
    # ?mine=true: only the caller's own brews.
    alice_mine = {b["id"] for b in client.get("/brews?mine=true", headers=alice_headers).json()}
    bob_mine = {b["id"] for b in client.get("/brews?mine=true", headers=bob_headers).json()}
    assert alice_mine == {alice_stack["brew"]}
    assert bob_mine == {bob_brew_id}


def test_non_author_cannot_edit_or_delete_brew(client, bob_headers, alice_stack):
    assert client.patch(f"/brews/{alice_stack['brew']}", headers=bob_headers, json={"notes": "hi"}).status_code == 403
    assert client.delete(f"/brews/{alice_stack['brew']}", headers=bob_headers).status_code == 403


def test_multiple_users_can_taste_the_same_brew(client, alice_headers, bob_headers, alice_stack, users):
    # alice_stack already has alice's tasting on the brew; bob adds his own.
    resp = client.post(f"/brews/{alice_stack['brew']}/tastings", headers=bob_headers, json={"overall": 6})
    assert resp.status_code == 201
    assert resp.json()["user_id"] == users["bob"].id

    tastings = client.get(f"/brews/{alice_stack['brew']}/tastings", headers=alice_headers).json()
    authors = {t["user_id"] for t in tastings}
    assert authors == {users["alice"].id, users["bob"].id}


def test_mine_filter_returns_only_own_tastings(client, alice_headers, bob_headers, alice_stack):
    # alice_stack already has alice's tasting; bob adds his own on the same brew.
    bob_tasting_id = client.post(f"/brews/{alice_stack['brew']}/tastings", headers=bob_headers, json={"overall": 5}).json()["id"]

    # Default: the whole shared tasting log.
    assert len(client.get("/tastings", headers=alice_headers).json()) == 2
    # ?mine=true: only the caller's own tastings.
    alice_mine = {t["id"] for t in client.get("/tastings?mine=true", headers=alice_headers).json()}
    bob_mine = {t["id"] for t in client.get("/tastings?mine=true", headers=bob_headers).json()}
    assert alice_mine == {alice_stack["tasting"]}
    assert bob_mine == {bob_tasting_id}


def test_non_author_cannot_edit_or_delete_tasting(client, bob_headers, alice_stack):
    tid = alice_stack["tasting"]
    assert client.patch(f"/tastings/{tid}", headers=bob_headers, json={"overall": 3}).status_code == 403
    assert client.delete(f"/tastings/{tid}", headers=bob_headers).status_code == 403


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
    assert client.post("/brew-methods", headers=alice_headers, json={"name": "Chemex", "category": "filter"}).status_code == 403
