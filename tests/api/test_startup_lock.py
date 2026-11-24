"""Startup migrations and the admin bootstrap run one process at a time."""

import threading
import time

from sqlalchemy import text

from bloom.db import init_db

_LOCK = {"id": init_db.STARTUP_LOCK_ID}


def test_a_second_process_waits_for_the_first(monkeypatch):
    ran: list[str] = []
    monkeypatch.setattr(init_db, "wait_for_db", lambda: None)
    monkeypatch.setattr(init_db, "migrate_to_head", lambda: ran.append("migrate"))
    monkeypatch.setattr(init_db, "bootstrap_admin", lambda: ran.append("admin"))

    with init_db.engine.connect() as other_process:
        # Another worker is mid-migration: it holds the lock.
        other_process.execute(text("SELECT pg_advisory_lock(:id)"), _LOCK)
        starting = threading.Thread(target=init_db.init_db)
        starting.start()
        time.sleep(0.5)
        assert ran == []  # still waiting its turn, not migrating alongside

        other_process.execute(text("SELECT pg_advisory_unlock(:id)"), _LOCK)
        starting.join(timeout=10)

    assert ran == ["migrate", "admin"]


def test_the_lock_is_released_even_when_migrating_fails(monkeypatch):
    monkeypatch.setattr(init_db, "wait_for_db", lambda: None)

    def broken_migration():
        raise RuntimeError("migration failed")

    monkeypatch.setattr(init_db, "migrate_to_head", broken_migration)
    try:
        init_db.init_db()
    except RuntimeError:
        pass

    # A restarted process must not hang behind a lock its failed predecessor kept.
    with init_db.engine.connect() as conn:
        assert conn.scalar(text("SELECT pg_try_advisory_lock(:id)"), _LOCK) is True
        conn.execute(text("SELECT pg_advisory_unlock(:id)"), _LOCK)
