"""Startup database tasks: wait for the DB, apply migrations, bootstrap the admin.

Run from the FastAPI lifespan. Migrating and bootstrapping run under a Postgres advisory
lock, so several workers or replicas starting together take turns: the first migrates and
creates the admin, the rest find both done. The ``db_is_at_head`` guard keeps restarts
cheap: migrations run only when the schema is actually behind.
"""

from __future__ import annotations

import time

from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from alembic import command
from bloom.core.logger import get_logger
from bloom.db.session import SessionLocal, engine
from bloom.services import auth_service

logger = get_logger(__name__)

ALEMBIC_INI = "alembic.ini"
# Any constant shared by every Bloom process; this one spells "bloom".
STARTUP_LOCK_ID = 0x626C6F6F6D


def wait_for_db(max_attempts: int = 10, delay_seconds: float = 1.0) -> None:
    """Block until the database accepts connections, or raise after giving up."""
    for attempt in range(1, max_attempts + 1):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return
        except OperationalError as exc:
            logger.info(
                "Database not ready yet (attempt %d/%d): %s",
                attempt,
                max_attempts,
                exc,
            )
            time.sleep(delay_seconds)
    raise RuntimeError("Database not reachable after waiting")


def db_is_at_head(config: Config) -> bool:
    """Return True if the database is already migrated to the latest revision."""
    script = ScriptDirectory.from_config(config)
    with engine.connect() as conn:
        current = set(MigrationContext.configure(conn).get_current_heads())
    return current == set(script.get_heads())


def migrate_to_head() -> None:
    """Apply Alembic migrations up to head, unless the DB is already there."""
    config = Config(ALEMBIC_INI)
    if db_is_at_head(config):
        logger.info("Database already at head; skipping migrations.")
        return
    logger.info("Applying migrations (alembic upgrade head)...")
    command.upgrade(config, "head")
    logger.info("Migrations applied.")


def bootstrap_admin() -> None:
    """Create the configured first admin if it does not exist yet."""
    db = SessionLocal()
    try:
        auth_service.bootstrap_admin(db)
    finally:
        db.close()


def init_db() -> None:
    """Run all startup DB tasks in order, one process at a time."""
    wait_for_db()
    with engine.connect() as lock_conn:
        lock_conn.execute(text("SELECT pg_advisory_lock(:id)"), {"id": STARTUP_LOCK_ID})
        try:
            migrate_to_head()
            bootstrap_admin()
        finally:
            lock_conn.execute(text("SELECT pg_advisory_unlock(:id)"), {"id": STARTUP_LOCK_ID})
