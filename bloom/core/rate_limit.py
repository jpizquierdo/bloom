"""In-memory sliding-window limiter for the public auth endpoints."""

import math
import threading
import time
from collections import deque

from fastapi import HTTPException, Request, status

WINDOW_SECONDS = 15 * 60
_MAX_KEYS = 10_000


class RateLimiter:
    """Allow ``limit`` hits per key within ``window_seconds``.

    shortcut: state is per process, so the effective limit multiplies with the worker count and
    resets on restart. Fine for the single-instance deployment; move to a shared store before scaling out.
    """

    def __init__(self, limit: int, window_seconds: int = WINDOW_SECONDS) -> None:
        self.limit = limit
        self.window = window_seconds
        self._hits: dict[str, deque[float]] = {}
        self._lock = threading.Lock()

    def _live(self, key: str, now: float) -> deque[float]:
        hits = self._hits.get(key)
        if hits is None:
            return deque()
        while hits and hits[0] <= now - self.window:
            hits.popleft()
        if not hits:
            del self._hits[key]
        return hits

    def retry_after(self, key: str) -> int:
        """Seconds until ``key`` may try again, or 0 if it is under the limit."""
        now = time.monotonic()
        with self._lock:
            hits = self._live(key, now)
            if len(hits) < self.limit:
                return 0
            return math.ceil(hits[0] + self.window - now)

    def record(self, key: str) -> None:
        now = time.monotonic()
        with self._lock:
            hits = self._live(key, now)
            if not hits and len(self._hits) >= _MAX_KEYS:
                # Bound memory against a flood of unique keys: evict the oldest-inserted one.
                del self._hits[next(iter(self._hits))]
            hits.append(now)
            self._hits[key] = hits

    def clear(self, key: str) -> None:
        with self._lock:
            self._hits.pop(key, None)

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()


# Wrong passwords: tight per account+client, looser per client to stop one IP spraying many accounts.
login_by_account = RateLimiter(limit=5)
login_by_client = RateLimiter(limit=20)
# Every recovery request counts, known address or not, so the 429 reveals nothing about accounts.
recovery_by_email = RateLimiter(limit=3)
recovery_by_client = RateLimiter(limit=10)

_ALL = (login_by_account, login_by_client, recovery_by_email, recovery_by_client)


def reset_all() -> None:
    for limiter in _ALL:
        limiter.reset()


def client_ip(request: Request) -> str:
    """Peer address; behind a reverse proxy this is the real client only if uvicorn trusts the proxy's headers."""
    return request.client.host if request.client else "unknown"


def enforce(limiter: RateLimiter, key: str) -> None:
    """Raise 429 with ``Retry-After`` if ``key`` is over its limit."""
    wait = limiter.retry_after(key)
    if wait:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many attempts. Try again later.",
            headers={"Retry-After": str(wait)},
        )
