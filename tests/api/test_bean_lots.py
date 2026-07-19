"""Bean-lot CRUD, ownership, and validation."""

import pytest


@pytest.fixture
def bean_id(client, alice_headers):
    return client.post("/beans", headers=alice_headers, json={"name": "Guji", "roaster": "Nomad"}).json()["id"]


def test_create_and_list_lot(client, alice_headers, users, bean_id):
    resp = client.post(
        f"/beans/{bean_id}/lots",
        headers=alice_headers,
        json={"roast_date": "2026-07-01", "purchase_date": "2026-07-05", "weight_grams": 250, "price": "18.50"},
    )
    assert resp.status_code == 201
    lot = resp.json()
    assert lot["bean_id"] == bean_id
    assert lot["weight_grams"] == 250
    assert lot["price"] == "18.50"
    assert lot["is_finished"] is False
    # The buyer is embedded as a nested object, like a bean's owner.
    assert lot["owner"] == {"id": users["alice"].id, "username": "alice"}

    listing = client.get(f"/beans/{bean_id}/lots", headers=alice_headers)
    assert listing.status_code == 200
    assert len(listing.json()) == 1


def test_nullable_lot_fields_cleared_with_null(client, alice_headers, bean_id):
    # All of a lot's fields except is_finished are nullable and can be cleared on PATCH.
    lot = client.post(
        f"/beans/{bean_id}/lots",
        headers=alice_headers,
        json={"roast_date": "2026-07-01", "weight_grams": 250, "price": "18.50"},
    ).json()

    resp = client.patch(
        f"/lots/{lot['id']}",
        headers=alice_headers,
        json={"roast_date": None, "weight_grams": None, "price": None},
    )
    assert resp.status_code == 200
    cleared = resp.json()
    assert cleared["roast_date"] is None
    assert cleared["weight_grams"] is None
    assert cleared["price"] is None


def test_multiple_lots_per_bean(client, alice_headers, bean_id):
    # The same coffee bought twice: two lots under one bean.
    client.post(f"/beans/{bean_id}/lots", headers=alice_headers, json={"purchase_date": "2026-06-01"})
    client.post(f"/beans/{bean_id}/lots", headers=alice_headers, json={"purchase_date": "2026-07-01"})
    assert len(client.get(f"/beans/{bean_id}/lots", headers=alice_headers).json()) == 2


def test_lots_are_shared_but_owner_scoped_for_writes(client, alice_headers, bob_headers, bean_id):
    lot_id = client.post(f"/beans/{bean_id}/lots", headers=alice_headers, json={"weight_grams": 250}).json()["id"]
    # Anyone can read the lot...
    assert client.get(f"/lots/{lot_id}", headers=bob_headers).status_code == 200
    # ...but only its buyer (or an admin) can edit or delete it.
    assert client.patch(f"/lots/{lot_id}", headers=bob_headers, json={"is_finished": True}).status_code == 403
    assert client.delete(f"/lots/{lot_id}", headers=bob_headers).status_code == 403


def test_update_lot_toggle_finished(client, alice_headers, bean_id):
    lot_id = client.post(f"/beans/{bean_id}/lots", headers=alice_headers, json={"weight_grams": 250}).json()["id"]
    resp = client.patch(f"/lots/{lot_id}", headers=alice_headers, json={"is_finished": True})
    assert resp.status_code == 200
    assert resp.json()["is_finished"] is True


def test_delete_lot(client, alice_headers, bean_id):
    lot_id = client.post(f"/beans/{bean_id}/lots", headers=alice_headers, json={}).json()["id"]
    assert client.delete(f"/lots/{lot_id}", headers=alice_headers).status_code == 204
    assert client.get(f"/lots/{lot_id}", headers=alice_headers).status_code == 404


def test_lot_under_missing_bean_404(client, alice_headers):
    assert client.post("/beans/999/lots", headers=alice_headers, json={}).status_code == 404


def test_nonpositive_weight_422(client, alice_headers, bean_id):
    assert client.post(f"/beans/{bean_id}/lots", headers=alice_headers, json={"weight_grams": 0}).status_code == 422


def test_null_is_finished_rejected(client, alice_headers, bean_id):
    # is_finished backs a NOT NULL column: an explicit null is a 422, not a 500.
    lot_id = client.post(f"/beans/{bean_id}/lots", headers=alice_headers, json={}).json()["id"]
    assert client.patch(f"/lots/{lot_id}", headers=alice_headers, json={"is_finished": None}).status_code == 422


def test_deleting_a_bean_cascades_to_its_lots(client, alice_headers, bean_id):
    lot_id = client.post(f"/beans/{bean_id}/lots", headers=alice_headers, json={}).json()["id"]
    assert client.delete(f"/beans/{bean_id}", headers=alice_headers).status_code == 204
    assert client.get(f"/lots/{lot_id}", headers=alice_headers).status_code == 404
