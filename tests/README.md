# Tests

Two suites:

- **`domain/`** — pure unit tests for `bloom/domain` (brew ratio, extraction yield,
  diagnostics). No database, no FastAPI. Fast and runnable anywhere.
- **`api/`** — endpoint tests via FastAPI's `TestClient` against a disposable
  `bloom_test` database. These require a running Postgres. All DB/auth fixtures live in
  `api/conftest.py`, so only this suite touches the database.

## Requirements

- **Only the API tests need Postgres**, reachable at the configured `POSTGRES_*`
  (defaults: `localhost:5432`, user/password/db `bloom`). The Compose service is enough —
  you don't need Postgres installed on the host:

  ```bash
  docker compose -f docker/docker-compose.yml up -d
  ```

- Install dev dependencies: `uv sync`.

## Running

```bash
uv run pytest                          # everything (needs Postgres)
uv run pytest tests/domain             # domain only — no Postgres needed
uv run pytest tests/api                # API only (needs Postgres)
uv run pytest tests/api/test_brews.py  # a single file
uv run pytest -k ownership             # by keyword
```

## The test database

`api/conftest.py` creates a separate **`bloom_test`** database on the same Postgres and
rebuilds its schema from the ORM models on each session (`drop_all` + `create_all`),
truncating all tables between tests. It never touches your dev `bloom` database. The app's
`get_db` dependency is overridden to use it, and the startup lifespan (migrations + admin
bootstrap) is skipped.
