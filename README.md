# Bloom ☕

Self-hosted tracking for the specialty coffee you brew — at home or behind the bar.
Bloom records the beans you buy, every brew you pull or pour, and how each one tasted,
so you can find what actually makes a good cup repeatable.

## Screenshots

The shared dashboard — coffees, brews and recent extractions at a glance:

![Bloom dashboard](docs/screenshots/dashboard.png)

| Beans, filterable by roaster | A coffee: its lots and its brews |
| :--: | :--: |
| ![Beans list](docs/screenshots/beans.png) | ![Bean detail](docs/screenshots/bean-detail.png) |

A brew with its recipe, extraction-yield diagnostics and a tasting:

![Brew detail](docs/screenshots/brew-detail.png)

## Quick start

Bloom ships as a **single container** (API + web UI) that runs alongside Postgres via Docker
Compose — the only requirement is Docker:

```bash
# 1. Configure — set BLOOM_ADMIN_EMAIL / BLOOM_ADMIN_PASSWORD and a strong JWT_SECRET
cp .env.example .env

# 2. Start Postgres + Bloom
docker compose -f docker/docker-compose.yml up -d
```

Open **http://localhost:8000** — the web UI, with the API under `/api/v1` and interactive
Swagger docs at **`/docs`**.

On startup Bloom waits for the database, applies any pending migrations, and bootstraps the
first admin — there is no separate migration step. It runs as a **single instance**, which
keeps migrating in-process simple and safe.

> Compose pulls the published `jpizquierdo/bloom` image. To build it yourself, run the app from
> source, or hack on it, see [Development](#development).

## Configuration

Settings come from environment variables or a local `.env` (copy `.env.example`):

| Variable | Purpose |
|----------|---------|
| `POSTGRES_USER` / `POSTGRES_PASSWORD` | Postgres credentials (default `bloom` / `bloom`). |
| `POSTGRES_SERVER` / `POSTGRES_PORT` / `POSTGRES_DB` | Postgres host, port and database (default `localhost` / `5432` / `bloom`). |
| `JWT_SECRET` | Access-token signing key — **set a strong value in production**. |
| `ACCESS_TOKEN_EXPIRE_HOURS` | Access-token lifetime in hours; generous by default for self-hosted use — set it lower for shorter sessions. |
| `RESET_TOKEN_EXPIRE_MINUTES` | Lifetime of a password-reset link (default 30). |
| `SMTP_HOST` / `SMTP_PORT` | Outgoing mail server (default port `587`). Leave the host blank to disable sending — links are written to the log instead. |
| `SMTP_USER` / `SMTP_PASSWORD` | SMTP credentials, if the server needs them. |
| `SMTP_TLS` / `SMTP_SSL` | STARTTLS (default `true`, port 587) or implicit TLS (`SMTP_SSL=true`, port 465). |
| `EMAILS_FROM_EMAIL` / `EMAILS_FROM_NAME` | Sender address and display name (default name `Bloom`). Mail is only sent once the address is set. |
| `LOG_LEVEL` | Logging level for the `bloom` logger (default `INFO`). |
| `FRONTEND_HOST` | Origin of the Vite dev server, allowed by CORS (default `http://localhost:5173`). Also the base of the links in outgoing emails, so set it to your public URL in production. |
| `BACKEND_CORS_ORIGINS` | Comma-separated list of extra browser origins allowed by CORS. |
| `BLOOM_ADMIN_EMAIL` / `BLOOM_ADMIN_PASSWORD` | First admin, bootstrapped on startup if absent. |

## Authentication

There is no public sign-up. The first admin is bootstrapped from the env vars above; admins
create further users (default role `user`) via `POST /users`. New users are emailed a link to
set their own password, so the admin never has to invent one — omit `password` and that link
is the only way in.

Users who forget their password recover it themselves from **Forgot password?** on the login
page (`POST /auth/recover-password` → `POST /auth/reset-password`). Reset links expire after
`RESET_TOKEN_EXPIRE_MINUTES` and work only once. Both need SMTP configured; without it the app
runs fine and logs the links instead of mailing them.

```bash
# Get a token (OAuth2 password flow; the username field takes an email or a handle)
curl -s -X POST http://localhost:8000/api/v1/auth/token \
  -d 'username=admin@example.com&password=your-password'

# Use it
curl http://localhost:8000/api/v1/auth/me -H "Authorization: Bearer <token>"
```

### Email in development

`docker/docker-compose.yml` ships [Mailpit](https://mailpit.axllent.org/): it accepts
everything on port 1025 and delivers nothing, so you can read the real rendered mail at
<http://localhost:8025>. The templates live in `bloom/templates/email/`.

## API overview

Everything is served under `/api/v1` (`/health` stays at the root, for container healthchecks).
For the full list of endpoints and their schemas, use the **interactive Swagger docs at
[`/docs`](http://localhost:8000/docs)** — the fastest way to explore the API.

Bloom is a **shared log**: any authenticated user reads everything and can add beans, brew from
any bean and taste any brew; only a row's creator (or an admin) may edit or delete it. A **bean
is the coffee**, and each bag you buy is a **lot** under it — a brew names its bean and,
optionally, the lot it came from. See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the
data model.

## Development

Run the API and the web UI from source (Postgres still comes from Compose). Needs Python 3.12+
with [`uv`](https://docs.astral.sh/uv/) and Node (via `nvm`):

```bash
# Postgres only
docker compose -f docker/docker-compose.yml up -d db

# API — http://localhost:8000, docs at /docs
uv sync
uv run fastapi dev bloom/main.py

# Web UI — http://localhost:5173, proxies /api to the API
cd frontend && npm install && npm run dev
```

The dev server runs on its own origin, so the API allows it through CORS via `FRONTEND_HOST`;
point the proxy at another API with `BLOOM_API_URL`. `fastapi dev` auto-reloads;
`fastapi run` is the production entrypoint.

- **Tests**: `uv run pytest`. Domain unit tests run without a database; API tests build a
  disposable `bloom_test` database on the running Postgres.
- **Generated client**: the UI's API client is generated from the schema. After changing a
  route or a schema, regenerate both (CI fails on drift):

  ```bash
  uv run python scripts/dump_openapi.py            # writes openapi.json at the repo root
  cd frontend && npm run generate-client           # regenerates src/client from it
  ```

- **Build the image**: `docker build -t bloom:local .`. One image compiles the SPA in a Node
  stage and FastAPI serves it from its own origin, so the UI uses **relative** URLs and the same
  image works at `localhost`, on a LAN IP, or behind a reverse proxy — no rebuild, no CORS setup.
  Point it at any Postgres with `POSTGRES_SERVER`.

## Architecture

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the data model, the
`routes → services → repositories → db` layering rule, and the design decisions;
[`frontend/README.md`](frontend/README.md) for the web stack and how to add a page.

## Status

Backend API and data layer are implemented (users/auth, beans, lots, brews, tastings, lookups),
and the web UI covers all of them. Password reset works over email; sign-up does not exist yet
(the UI shows that screen but leaves it inert), and admins create accounts.

## License

Bloom is licensed under the **GNU Affero General Public License v3.0 or later** — see
[`LICENSE`](LICENSE). You can use, modify and self-host it freely; but if you run a modified
version as a network service, you must offer that version's source to its users.
