# Bloom ☕

Self-hosted tracking for the specialty coffee you brew — at home or behind the bar.
Bloom records the beans you buy, every brew you pull or pour, and how each one tasted,
so you can find what actually makes a good cup repeatable.


## Stack

FastAPI · SQLAlchemy 2.x (sync) · Alembic · Pydantic v2 · PostgreSQL 16 (`psycopg` 3) ·
JWT auth (argon2id) · packaged with `uv` · Postgres via Docker Compose.

## Requirements

- Docker (for PostgreSQL)
- Python 3.12+ and [`uv`](https://docs.astral.sh/uv/)

## Quick start

```bash
# 1. Start Postgres
docker compose -f docker/docker-compose.yml up -d

# 2. Install dependencies
uv sync

# 3. Configure (copy and edit; set BLOOM_ADMIN_EMAIL / BLOOM_ADMIN_PASSWORD)
cp .env.example .env

# 4. Run the API — docs at http://localhost:8000/docs
uv run fastapi dev bloom/main.py     # or: uv run uvicorn bloom.main:app --reload
```

On startup Bloom waits for the database, applies any pending migrations
(`alembic upgrade head`), and bootstraps the first admin — so there is no separate
migration step. Bloom runs as a **single instance**, which makes migrating in-process
simple and safe. To run migrations by hand you can still use `uv run alembic upgrade head`.

> `fastapi[standard]` ships the FastAPI CLI: `fastapi dev` (auto-reload) for development
> and `fastapi run` for production. `uvicorn` is still available if you prefer it.

## Configuration

Settings come from environment variables or a local `.env` (copy `.env.example`):

| Variable | Purpose |
|----------|---------|
| `POSTGRES_USER` / `POSTGRES_PASSWORD` | Postgres credentials (default `bloom` / `bloom`). |
| `POSTGRES_SERVER` / `POSTGRES_PORT` / `POSTGRES_DB` | Postgres host, port and database (default `localhost` / `5432` / `bloom`). |
| `JWT_SECRET` | Access-token signing key — **set a strong value in production**. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access-token lifetime (default 60). |
| `LOG_LEVEL` | Logging level for the `bloom` logger (default `INFO`). |
| `BLOOM_ADMIN_EMAIL` / `BLOOM_ADMIN_PASSWORD` | First admin, bootstrapped on startup if absent. |


## Docker

Bloom ships a minimal single-instance image. Point `POSTGRES_SERVER` at your Postgres
(the Compose service is reachable as `db`):

```bash
docker build -t bloom:latest .

docker run --rm -p 8000:8000 \
  --network docker_default \
  -e POSTGRES_SERVER=db \
  -e JWT_SECRET=change-me \
  -e BLOOM_ADMIN_EMAIL=admin@example.com -e BLOOM_ADMIN_PASSWORD=change-me \
  bloom:latest
```

The container applies migrations and bootstraps the admin on startup, then serves with
`fastapi run`.

## Authentication

There is no public sign-up. The first admin is bootstrapped from the env vars above;
admins create further users (who default to the `user` role) via `POST /users`.

```bash
# Get a token (OAuth2 password flow; username = email)
curl -s -X POST http://localhost:8000/auth/token \
  -d 'username=admin@example.com&password=your-password'

# Use it
curl http://localhost:8000/auth/me -H "Authorization: Bearer <token>"
```

## API overview

| Area | Endpoints |
|------|-----------|
| Auth | `POST /auth/token`, `GET /auth/me` |
| Users (admin) | `POST /users`, `GET /users`, `PATCH /users/{id}` |
| Beans | `POST/GET /beans` (`?mine=true`), `GET/PATCH/DELETE /beans/{id}` |
| Brews | `POST/GET /brews` (`?mine=true`), `GET/PATCH/DELETE /brews/{id}` |
| Tastings | `POST/GET /brews/{id}/tastings`, `GET /tastings` (`?mine=true`), `GET/PATCH/DELETE /tastings/{id}` |
| Lookups | `GET /brew-methods`, `GET /equipment` (create is admin-only) |

Bloom is a **shared log**: any authenticated user can read all beans, brews and tastings,
add beans, brew from any bean, and taste any brew. Each row records who created it, and only
that creator (or an admin) can edit or delete it. Interactive docs are served at `/docs`.

## Tests

```bash
uv run pytest
```

Domain unit tests run without a database; API tests build a disposable `bloom_test`
database on the running Postgres.

## Project layout

```
bloom/        backend package (routes → services → repositories → db, with a pure domain/)
alembic/      migrations
tests/        pytest (domain/ + api/)
docker/       docker-compose for Postgres
```

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the full layering rule, data model,
and design decisions.

## Status

Backend API and data layer are implemented (users/auth, beans, brews, tastings, lookups).
The frontend is not started — reserved for the future.
