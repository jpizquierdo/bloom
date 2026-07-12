"""Logging setup: a single stdout handler on the ``bloom`` logger.

Use ``get_logger(__name__)`` anywhere in the package. Logs go to stdout only
(12-factor); the container/orchestrator collects them.
"""

import logging
import sys

from bloom.core.config import get_settings

_configured = False


def configure_logging() -> None:
    global _configured
    if _configured:
        return

    logger = logging.getLogger("bloom")
    logger.setLevel(get_settings().LOG_LEVEL.upper())

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s %(levelname)-8s %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    logger.addHandler(handler)
    # Own handler, independent of uvicorn/alembic root config.
    logger.propagate = False

    _configured = True


def get_logger(name: str | None = None) -> logging.Logger:
    configure_logging()
    return logging.getLogger(name or "bloom")
