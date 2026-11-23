"""Brute-force protection on login and password recovery."""

import pytest

from bloom.core import rate_limit
from bloom.core.rate_limit import RateLimiter
from bloom.services import auth_service, email_service


def _login(client, username="alice@example.com", password="wrong"):
    return client.post("/auth/token", data={"username": username, "password": password})


def test_sixth_wrong_password_is_blocked(client, users):
    # Five failures are answered normally...
    assert [_login(client).status_code for _ in range(5)] == [401] * 5

    # ...then even the *correct* password is refused until the window passes.
    blocked = _login(client, password="alicepass1")
    assert blocked.status_code == 429
    assert int(blocked.headers["Retry-After"]) > 0


def test_success_resets_the_account_counter(client, users):
    for _ in range(4):
        assert _login(client).status_code == 401
    assert _login(client, password="alicepass1").status_code == 200
    # The four earlier failures no longer count: four more still fit under the limit.
    assert [_login(client).status_code for _ in range(4)] == [401] * 4


def test_lockout_is_per_account(client, users):
    for _ in range(5):
        _login(client)
    assert _login(client).status_code == 429
    # Bob, from the same client, is not locked out by attempts on Alice.
    assert _login(client, "bob@example.com", "bobpass123").status_code == 200


def test_account_key_ignores_case_and_whitespace(client, users):
    for name in ("alice@example.com", "ALICE@example.com", " alice@example.com ", "Alice@Example.com", "alice@EXAMPLE.com"):
        assert _login(client, name).status_code == 401
    assert _login(client, "alice@example.com").status_code == 429


def test_one_client_spraying_many_accounts_is_blocked(client, users):
    # Each username stays under its own limit, but the client as a whole does not.
    statuses = [_login(client, f"ghost{i}").status_code for i in range(21)]
    assert statuses[:20] == [401] * 20
    assert statuses[20] == 429


def test_recovery_is_limited_per_address_even_for_unknown_emails(client, users, monkeypatch):
    sent = []
    monkeypatch.setattr(email_service, "send_email", lambda **kw: sent.append(kw))

    codes = [client.post("/auth/recover-password", json={"email": "alice@example.com"}).status_code for _ in range(4)]
    assert codes == [202, 202, 202, 429]
    assert len(sent) == 3  # the blocked request sent nothing

    # An address with no account is throttled exactly the same way, so the 429 leaks nothing.
    codes = [client.post("/auth/recover-password", json={"email": "nobody@example.com"}).status_code for _ in range(4)]
    assert codes == [202, 202, 202, 429]


def test_unknown_account_still_costs_a_password_check(db, monkeypatch):
    # Without this, response time reveals which usernames exist.
    calls = []
    monkeypatch.setattr(auth_service, "verify_password", lambda password, hashed: calls.append(hashed) or False)

    assert auth_service.authenticate(db, "ghost", "whatever") is None
    assert calls == [auth_service._DUMMY_HASH]


def test_limiter_window_expires(monkeypatch):
    now = [1000.0]
    monkeypatch.setattr(rate_limit.time, "monotonic", lambda: now[0])
    limiter = RateLimiter(limit=2, window_seconds=60)

    limiter.record("k")
    limiter.record("k")
    assert limiter.retry_after("k") == 60

    now[0] += 59
    assert limiter.retry_after("k") == 1
    now[0] += 1
    assert limiter.retry_after("k") == 0


def test_limiter_memory_is_bounded(monkeypatch):
    monkeypatch.setattr(rate_limit, "_MAX_KEYS", 3)
    limiter = RateLimiter(limit=1)
    for i in range(10):
        limiter.record(f"key{i}")
    assert len(limiter._hits) == 3
    assert limiter.retry_after("key9") > 0  # the newest key survives; the oldest were evicted


@pytest.mark.parametrize("limit", [1, 3])
def test_limiter_blocks_exactly_at_the_limit(limit):
    limiter = RateLimiter(limit=limit)
    for _ in range(limit - 1):
        limiter.record("k")
    assert limiter.retry_after("k") == 0
    limiter.record("k")
    assert limiter.retry_after("k") > 0
