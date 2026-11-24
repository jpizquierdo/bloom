"""Paging and server-side filtering of the brew and tasting logs."""

from datetime import UTC, datetime, timedelta

import pytest


@pytest.fixture
def log(client, alice_headers, bob_headers, lookups):
    """Seed two roasters, three beans and six brews (newest first: b5 … b0).

    Alice made b0-b3, Bob b4-b5. Kenya (Nomad) gets b0, b1, b4; Guji (Nomad) b2;
    Sidra (La Cabra) b3, b5. Even brews use the filter method, odd ones espresso.
    """
    kenya = client.post("/beans", headers=alice_headers, json={"name": "Kenya AA", "roaster": "Nomad"}).json()
    guji = client.post("/beans", headers=alice_headers, json={"name": "Guji", "roaster": "Nomad"}).json()
    sidra = client.post("/beans", headers=alice_headers, json={"name": "Sidra 100% washed", "roaster": "La Cabra"}).json()
    beans = [kenya, kenya, guji, sidra, kenya, sidra]
    start = datetime(2026, 1, 1, tzinfo=UTC)
    brews = []
    for i, bean in enumerate(beans):
        headers = alice_headers if i < 4 else bob_headers
        method = lookups["filter"] if i % 2 == 0 else lookups["espresso"]
        brew = client.post(
            "/brews",
            headers=headers,
            json={
                "bean_id": bean["id"],
                "method_id": method["id"],
                "dose_grams": "15",
                "brewed_at": (start + timedelta(hours=i)).isoformat(),
            },
        )
        assert brew.status_code == 201, brew.text
        brews.append(brew.json()["id"])
    return {"brews": brews, "kenya": kenya, "guji": guji, "sidra": sidra}


def _ids(client, headers, query=""):
    body = client.get(f"/brews{query}", headers=headers).json()
    return [brew["id"] for brew in body["items"]], body["total"]


def test_pages_are_newest_first_and_do_not_overlap(client, alice_headers, log):
    b = log["brews"]
    first, total = _ids(client, alice_headers, "?limit=4")
    second, _ = _ids(client, alice_headers, "?limit=4&offset=4")
    assert total == 6
    assert first == [b[5], b[4], b[3], b[2]]
    assert second == [b[1], b[0]]


def test_same_timestamp_keeps_a_stable_order(client, alice_headers, lookups, log):
    # Two brews logged in the same instant must not swap places between pages.
    when = datetime(2027, 1, 1, tzinfo=UTC).isoformat()
    payload = {"bean_id": log["guji"]["id"], "method_id": lookups["filter"]["id"], "dose_grams": "15", "brewed_at": when}
    a = client.post("/brews", headers=alice_headers, json=payload).json()["id"]
    b = client.post("/brews", headers=alice_headers, json=payload).json()["id"]
    assert _ids(client, alice_headers, "?limit=1")[0] == [b]
    assert _ids(client, alice_headers, "?limit=1&offset=1")[0] == [a]


@pytest.mark.parametrize(
    ("query", "expected"),
    [
        ("?mine=true", [3, 2, 1, 0]),  # Alice's own
        ("?method_id={espresso}", [5, 3, 1]),
        ("?bean_id={kenya}", [4, 1, 0]),
        ("?roaster_id={la_cabra}", [5, 3]),
        ("?q=guji", [2]),  # bean name, any case
        ("?q=CABRA", [5, 3]),  # roaster name
        ("?q=espresso", [5, 3, 1]),  # method name
        ("?q=bob", [5, 4]),  # author
        ("?q=100%25", [5, 3]),  # a literal %, not a wildcard
        ("?q=_", []),  # a literal _, not a wildcard
        ("?bean_id={kenya}&mine=true&method_id={filter}", [0]),  # filters combine
    ],
)
def test_filters(client, alice_headers, lookups, log, query, expected):
    la_cabra = log["sidra"]["roaster"]["id"]
    query = query.format(espresso=lookups["espresso"]["id"], filter=lookups["filter"]["id"], kenya=log["kenya"]["id"], la_cabra=la_cabra)
    ids, total = _ids(client, alice_headers, query)
    assert ids == [log["brews"][i] for i in expected]
    assert total == len(expected)


def test_total_counts_every_match_not_just_the_page(client, alice_headers, log):
    ids, total = _ids(client, alice_headers, f"?bean_id={log['kenya']['id']}&limit=1")
    assert len(ids) == 1
    assert total == 3


def test_untasted_is_per_viewer_and_my_tasting_is_embedded(client, alice_headers, bob_headers, log):
    b = log["brews"]
    client.post(f"/brews/{b[5]}/tastings", headers=alice_headers, json={"overall": 4})
    client.post(f"/brews/{b[4]}/tastings", headers=bob_headers, json={"overall": 2})

    # Bob's tasting of b4 does not count as Alice's.
    assert _ids(client, alice_headers, "?untasted=true")[0] == [b[4], b[3], b[2], b[1], b[0]]

    items = client.get("/brews?limit=2", headers=alice_headers).json()["items"]
    assert items[0]["my_tasting"]["overall"] == 4
    assert items[1]["my_tasting"] is None  # only Bob tasted b4

    # The single-brew endpoint carries it too.
    assert client.get(f"/brews/{b[5]}", headers=alice_headers).json()["my_tasting"]["overall"] == 4


@pytest.mark.parametrize("query", ["?limit=0", "?limit=201", "?offset=-1", "?q=" + "x" * 101])
def test_out_of_range_paging_is_rejected(client, alice_headers, query):
    assert client.get(f"/brews{query}", headers=alice_headers).status_code == 422


def test_tastings_page_and_embed_their_brew(client, alice_headers, bob_headers, log):
    b = log["brews"]
    for brew_id in b[:3]:
        client.post(f"/brews/{brew_id}/tastings", headers=alice_headers, json={"overall": 3})
    client.post(f"/brews/{b[0]}/tastings", headers=bob_headers, json={"overall": 5})

    body = client.get("/tastings?limit=2", headers=alice_headers).json()
    assert body["total"] == 4
    assert [t["brew_id"] for t in body["items"]] == [b[0], b[2]]  # newest tasting first
    # Enough of the brew to name it, without fetching the brew log.
    brew = body["items"][1]["brew"]
    assert (brew["id"], brew["bean_id"]) == (b[2], log["guji"]["id"])
    assert set(brew) == {"id", "bean_id", "method_id", "brewed_at"}

    mine = client.get("/tastings?mine=true&limit=50&offset=1", headers=alice_headers).json()
    assert mine["total"] == 3
    assert len(mine["items"]) == 2


def test_list_query_count_does_not_grow_with_the_page(client, alice_headers, log, engine):
    # Brew lists embed method, author and the viewer's tasting; that must not cost a query per row.
    from sqlalchemy import event

    for brew_id in log["brews"]:
        client.post(f"/brews/{brew_id}/tastings", headers=alice_headers, json={"overall": 3})

    def count(path):
        seen = []
        listener = lambda *args, **kwargs: seen.append(1)  # noqa: E731
        event.listen(engine, "before_cursor_execute", listener)
        try:
            assert client.get(path, headers=alice_headers).status_code == 200
        finally:
            event.remove(engine, "before_cursor_execute", listener)
        return len(seen)

    assert count("/brews?limit=1") == count("/brews?limit=6")
    assert count("/tastings?limit=1") == count("/tastings?limit=6")
