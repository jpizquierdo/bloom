# Bloom ☕

Self-hosted tracking for the specialty coffee you brew — at home or behind the bar.
Bloom records the beans you buy, every brew you pull or pour, and how each one tasted,
so you can find what actually makes a good cup repeatable.


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

# 5. Run the web UI — http://localhost:5173
cd frontend && npm install && npm run dev
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
| `FRONTEND_HOST` | Origin of the Vite dev server, allowed by CORS (default `http://localhost:5173`). Not needed in production: the image serves the UI from the API's own origin. |
| `BACKEND_CORS_ORIGINS` | Comma-separated list of extra browser origins allowed by CORS. |
| `BLOOM_ADMIN_EMAIL` / `BLOOM_ADMIN_PASSWORD` | First admin, bootstrapped on startup if absent. |


## Docker

Bloom ships a **single image containing both the API and the web UI** — one container, one
port. The build compiles the SPA in a Node stage and FastAPI serves it, so the UI talks to the
API on its own origin: the same image works at `localhost`, on a LAN IP, or behind a reverse
proxy, with no rebuild and no CORS setup.

Point `POSTGRES_SERVER` at your Postgres (the Compose service is reachable as `db`):

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
`fastapi run`: the UI at `http://localhost:8000/`, the API under `/api/v1`, docs at `/docs`.

## Authentication

There is no public sign-up. The first admin is bootstrapped from the env vars above;
admins create further users (who default to the `user` role) via `POST /users`.

```bash
# Get a token (OAuth2 password flow; the username field takes an email or a handle)
curl -s -X POST http://localhost:8000/api/v1/auth/token \
  -d 'username=admin@example.com&password=your-password'

# Use it
curl http://localhost:8000/api/v1/auth/me -H "Authorization: Bearer <token>"
```

## API overview

Every route below is served under the `/api/v1` prefix (`API_V1_STR`); `/health` is the
only exception and stays at the root, for container healthchecks.

| Area | Endpoints |
|------|-----------|
| Auth | `POST /auth/token`, `GET /auth/me` |
| Users (admin) | `POST /users`, `GET /users`, `PATCH /users/{id}` |
| Beans | `POST/GET /beans` (`?mine=true`), `GET/PATCH/DELETE /beans/{id}` |
| Lots | `POST/GET /beans/{id}/lots`, `GET/PATCH/DELETE /lots/{id}` |
| Roasters | `POST/GET /roasters`, `GET /roasters/{id}`; `PATCH/DELETE /roasters/{id}` and `POST /roasters/{id}/merge` are admin-only |
| Brews | `POST/GET /brews` (`?mine=true`), `GET/PATCH/DELETE /brews/{id}` |
| Tastings | `POST/GET /brews/{id}/tastings`, `GET /tastings` (`?mine=true`), `GET/PATCH/DELETE /tastings/{id}` |
| Lookups | `GET /brew-methods`, `GET /equipment` (create is admin-only) |

Bloom is a **shared log**: any authenticated user can read all beans, brews and tastings,
add beans, brew from any bean, and taste any brew. Each row records who created it, and only
that creator (or an admin) can edit or delete it. Interactive docs are served at `/docs`.

A bean carries its **roaster** as a name (`"roaster": "Nomad Coffee"`): the API matches it
case-insensitively and creates the roaster if it is new, so nobody has to pre-register one.
Beans read back with the roaster as a nested object. Admins can rename a roaster — every bean
follows — or merge a duplicate into another with `POST /roasters/{id}/merge`.

A **bean is the coffee** (name, roaster, origin, variety…); each bag you buy is a **lot** under
it (roast/purchase date, weight, price, finished flag), so buying the same coffee again just
adds a lot instead of a duplicate bean. A brew always names its bean and may optionally name the
lot it came from.

## OpenAPI schema

The web UI generates its API client from the schema, so regenerate both whenever routes or
schemas change (no database needed). CI fails if either is out of date:

```bash
uv run python scripts/dump_openapi.py            # writes openapi.json at the repo root
cd frontend && npm run generate-client           # regenerates src/client from it
```

## Tests

```bash
uv run pytest
```

Domain unit tests run without a database; API tests build a disposable `bloom_test`
database on the running Postgres.

## Web UI

A React SPA lives in [`frontend/`](frontend/), with its API client generated from
`openapi.json`. It has a login screen, a sidebar, and CRUD for every resource, with drill-down
detail pages (a roaster's beans, a bean's brews) and client-side filtering.

In production it is **built into the API image** and served from the same origin (see Docker
below) — there is nothing separate to deploy. For development, run it against a local API:

```bash
cd frontend
npm install
npm run dev             # http://localhost:5173, proxying /api to http://localhost:8000
```

Vite proxies `/api` to the backend, so the app talks to a relative URL in development exactly
as it does in production. Point the proxy elsewhere with `BLOOM_API_URL`. The dev server has
its own origin, which is why the API allows it through CORS via `FRONTEND_HOST`.

See [`frontend/README.md`](frontend/README.md) for the stack and how to add a page.

## Project layout

```
bloom/        backend package (routes → services → repositories → db, with a pure domain/)
frontend/     React + TypeScript web UI (Vite, Tailwind, shadcn/ui)
alembic/      migrations
tests/        pytest (domain/ + api/)
scripts/      dump_openapi.py
docker/       docker-compose for Postgres, the API and the UI
```

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the full layering rule, data model,
and design decisions.

## Status

Backend API and data layer are implemented (users/auth, beans, brews, tastings, lookups),
and the web UI covers all of them. Sign-up and password reset do not exist yet: the UI shows
those screens but leaves them inert, and admins create accounts.
