# Bloom ☕

Self-hosted tracking for the specialty coffee you brew — at home or behind the bar.
Bloom records the beans you buy, every brew you pull or pour, and how each one tasted,
so you can find what actually makes a good cup repeatable.

This repository is the **backend REST API and data layer** (FastAPI + PostgreSQL). A
`frontend/` directory is reserved for later. For the design rationale and data model, see
[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

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

# 3. Apply migrations
uv run alembic upgrade head

# 4. Configure the first admin (created on startup if it doesn't exist)
cp .env.example .env
#   then set BLOOM_ADMIN_EMAIL and BLOOM_ADMIN_PASSWORD in .env

# 5. Run the API — docs at http://localhost:8000/docs
uv run uvicorn bloom.main:app --reload
```

## Configuration

Settings come from environment variables or a local `.env` (copy `.env.example`):

| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | Postgres connection string (default `postgresql+psycopg://bloom:bloom@localhost:5432/bloom`). |
| `JWT_SECRET` | Access-token signing key — **set a strong value in production**. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access-token lifetime (default 60). |
| `BLOOM_ADMIN_EMAIL` / `BLOOM_ADMIN_PASSWORD` | First admin, bootstrapped on startup if absent. |

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
| Beans | `POST/GET /beans`, `GET/PATCH/DELETE /beans/{id}` |
| Brews | `POST/GET /brews`, `GET/PATCH/DELETE /brews/{id}` |
| Tastings | `POST/GET /brews/{id}/tastings`, `GET/PATCH/DELETE /tastings/{id}` |
| Lookups | `GET /brew-methods`, `GET /equipment` (create is admin-only) |

Beans are **shared**: any user can see them and brew from any bean, but only a bean's owner
(or an admin) can edit or delete it. Brews and tastings are **private to their author**;
admins see everything. Interactive docs are served at `/docs`.

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
