"""Startup database tasks: wait for the DB, apply migrations, bootstrap the admin.

Run from the FastAPI lifespan. Bloom is deployed as a single instance, so doing
this in-process is simple and safe — there is no second worker to race with. The
``db_is_at_head`` guard keeps restarts cheap: migrations run only when the schema
is actually behind.
"""

from __future__ import annotations

import logging
import time

from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from bloom.db.session import SessionLocal, engine
from bloom.services import auth_service

logger = logging.getLogger("bloom.db.init_db")

ALEMBIC_INI = "alembic.ini"


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
    """Run all startup DB tasks in order."""
    wait_for_db()
    migrate_to_head()
    bootstrap_admin()
