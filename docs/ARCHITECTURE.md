# Bloom — Architecture & Design

The design record for Bloom's backend: the data model, the layering rule, and the
rationale behind each decision. This is the "why" document — for how to **run** the
project, see [`README.md`](../README.md).

> Where docs and code disagree, the code and its Alembic migrations win; this file is
> kept in sync with them.

---

## Tech stack

| Layer       | Choice                                    |
|-------------|-------------------------------------------|
| Language    | **Python only** (no Go — decision closed) |
| API         | FastAPI                                   |
| ORM         | SQLAlchemy 2.x (typed, `Mapped[...]`), **sync** |
| Migrations  | Alembic                                   |
| Validation  | Pydantic v2                               |
| Database    | PostgreSQL 16 (`psycopg` 3)               |
| Auth        | JWT (OAuth2 password flow), **argon2id**  |
| Packaging   | `uv` + `pyproject.toml`                   |
| Local dev   | Docker Compose                            |

> **On Go:** an earlier goal was to learn Go by re-implementing this API. That is no
> longer planned — Bloom is Python-only. The domain logic is still kept as framework-free
> pure functions, now purely for testability and clean separation, not portability.

---

## Project structure

Modelled on [Mealie](https://github.com/mealie-recipes/mealie): a single backend package
named after the project, a reserved `frontend/`, tests outside the package, and Alembic
for migrations.

```
bloom/
├── bloom/                     # backend package (the core)
│   ├── main.py                # FastAPI app factory, lifespan (admin bootstrap), /health
│   ├── core/                  # cross-cutting concerns
│   │   ├── config.py          # settings (pydantic-settings, reads env/.env)
│   │   ├── security.py        # argon2 password hashing, JWT create/verify
│   │   └── dependencies.py    # FastAPI deps: get_db, get_current_user, require_admin
│   ├── db/
│   │   ├── base.py            # SQLAlchemy DeclarativeBase
│   │   ├── session.py         # engine + session factory
│   │   └── models/            # ORM models (one concern per file)
│   │       ├── user.py  bean.py  brew.py  brew_method.py  equipment.py  tasting.py
│   ├── schemas/               # Pydantic v2 DTOs (request/response)
│   │   ├── user.py  bean.py  brew.py  tasting.py  lookups.py
│   ├── domain/                # PURE functions — no ORM, no FastAPI imports
│   │   ├── calculations.py    # brew ratio, extraction yield, diagnostics
│   │   └── constants.py       # brew categories + control-chart target ranges
│   ├── repositories/          # DB access layer (queries live here, not in routes)
│   │   ├── users.py  beans.py  brews.py  tastings.py  lookups.py
│   ├── services/              # business logic orchestrating repos + domain
│   │   ├── auth_service.py    users_service.py  bean_service.py
│   │   ├── brew_service.py    tasting_service.py  lookups_service.py
│   │   ├── access.py          # ownership helper (owns_or_admin)
│   │   └── errors.py          # NotFoundError (framework-agnostic)
│   └── routes/                # FastAPI routers (thin — validate, delegate, return)
│       ├── auth.py  users.py  beans.py  brews.py
│       ├── tastings.py  brew_methods.py  equipment.py
├── frontend/                  # React SPA; its API client is generated from openapi.json
├── scripts/                   # dump_openapi.py (schema for the frontend's codegen)
├── alembic/                   # migration environment (env.py, versions/)
├── tests/                     # pytest, outside the package
│   ├── conftest.py
│   ├── domain/                # fast unit tests for the pure functions
│   └── api/                   # endpoint tests against a disposable test DB
├── frontend/                  # reserved — empty for now
├── docker/docker-compose.yml
├── docs/ARCHITECTURE.md       # this file
└── README.md
```

### Layering rule

Requests flow **routes → services → repositories → database**, with **domain** called by
services for any calculation. Dependencies only ever point downward:

- **routes** are thin: parse input, call a service, shape the response. No SQL here.
- **services** hold business logic and orchestrate repositories + domain functions.
- **repositories** are the only place that talks to the database.
- **domain** is pure and imports nothing from the layers above — it never sees a session,
  a request, or an ORM object. This is what keeps `extraction_yield` unit-testable in
  isolation.

---

## Users and roles

Bloom is multi-user with two roles:

| Role       | Capabilities                                                                 |
|------------|------------------------------------------------------------------------------|
| **admin**  | Everything a standard user can do, plus manage users (create, promote/demote, deactivate) and manage shared lookup data (`brew_method`, `equipment`). May edit/delete anyone's data. |
| **user**   | Add beans, brew from any bean, and taste any brew — all shared and readable by everyone. May edit/delete only their own beans, brews and tastings. Read shared lookup data. |

Design points:

- The role is a column on `user` (`role TEXT CHECK (role IN ('admin','user'))`), not a
  separate permissions table — two roles don't justify RBAC machinery yet.
- **On startup** (FastAPI lifespan, see `bloom/db/init_db.py`) the app waits for the DB,
  applies pending migrations (`alembic upgrade head`, guarded by a `db_is_at_head` check so
  restarts are cheap), and bootstraps the admin. Bloom is deployed as a **single instance**,
  so migrating in-process is simple and race-free — no separate migration Job needed.
- The **first admin is bootstrapped from env vars** (`BLOOM_ADMIN_EMAIL` /
  `BLOOM_ADMIN_PASSWORD`), created only if it does not exist. There is **no public sign-up**:
  admins create further accounts, which default to `user`.
- Each account has a unique **`username`** handle (unique on `lower(username)`) alongside its
  email; the login form's single field accepts **either** an email or a handle. Handles are
  set by an admin today and will be supplied by the IdP (Keycloak/Authentik) once automated
  provisioning lands. Brews and tastings embed their author as a nested `{ id, username }`
  object so the UI can name who pulled or scored a cup without reading the admin-only user list.
- **Everything is a shared log** (household/café model, 11). Any authenticated user can
  read all beans, brews and tastings, and can add beans, brew from any bean, and taste any
  brew. Each row records who created it — `bean.user_id` (owner), `brew.user_id` (author),
  `tasting.user_id` (taster) — and **only that creator (or an admin) may edit or delete it**
  (a non-creator write returns `403`). Because tastings carry their taster, several people
  can each score the same brew (realizing 6).
- **Users are soft-deleted** via an `is_active` flag — never hard-deleted — so history is
  always preserved.
- Auth is JWT via the OAuth2 password flow (access token only). Passwords are hashed with
  **argon2id**, never stored in plain text.

---

## Data model

Seven tables. `brew` is the central, highest-volume entity.

```
Entities:
    roaster 1 ──< bean 1 ──< brew >── 1 brew_method
                              │  └─── 1 equipment   (grinder, nullable)
                              │
                              └──< tasting          (1:N)

Ownership (who created each row):
    user 1 ──< bean       (owner)
    user 1 ──< brew       (author)
    user 1 ──< tasting    (taster)
```

Every row carries who created it: `bean.user_id` (owner), `brew.user_id` (author) and
`tasting.user_id` (taster). These are often different people — one member buys a bag
(bean owner), another brews from it (brew author), and several may score that brew
(tasters).

| Table         | Purpose                                                             |
|---------------|---------------------------------------------------------------------|
| `user`        | Accounts with a role (`admin` / `user`) and a unique `username` handle. Owns beans, authors brews, makes tastings. |
| `bean`        | A physical bag/lot of coffee. Shared; `user_id` is the owner.        |
| `roaster`     | Who roasted the bean. User-creatable, unique on `lower(name)` (see 13). |
| `brew_method` | Lookup: V60, Espresso, AeroPress… with a category.                  |
| `equipment`   | Grinders, machines, kettles — one table, `type` discriminator.      |
| `brew`        | A single extraction: the objective parameters. Central entity; `user_id` is the author. |
| `tasting`     | A subjective evaluation of a brew (1:N — several per brew, by different users); `user_id` is the taster. |

The live schema is owned by **Alembic migrations** (`alembic/versions/`); the ORM models in
`bloom/db/models/` are the source of truth for each table's shape. To eyeball the current
schema as plain SQL, dump it straight from the database — always accurate, never drifts:

```bash
docker exec bloom-db pg_dump -U bloom -d bloom --schema-only
```

---

## Design decisions

Each decision was made explicitly.

### 1 — `bean` is a physical lot, not an abstract coffee
One `bean` row = one bag bought, with its own purchase date, price and weight. If needed
later, this splits into `coffee` (concept) + `bean_lot` (physical).

### 2 — Derived vs. measured fields: a hybrid rule
- **`ratio` is computed in the domain layer, never stored.**
- **`tds_percent` and `extraction_yield_percent` are stored** — real refractometer
  measurements, not derivations. When only TDS is measured, EY is computed once at write
  time and stored, so analytics read a single column.

Rule: **per-row math → domain layer; aggregates over many rows → SQL.**

### 3 — `brew_method` as a lookup table, not an enum
New methods without a migration.

### 4 — `process` as `TEXT` + `CHECK`, not a native enum
Specialty processes evolve constantly; `TEXT` + `CHECK` gives integrity with a one-line
change to extend, avoiding the rigidity of Postgres enums.

### 5 — Single `equipment` table with a `type` discriminator
Grinders, machines and kettles share enough shape. `brew` references it as `grinder_id`.

### 6 — `tasting` is 1:N with `brew`
Same extraction can be scored by more than one person, or re-tasted as it cools. Keeping
tasting separate keeps objective parameters clean from subjective scores. Each tasting
records its taster (`tasting.user_id`), so several users can score the same brew (see 11).

### 7 — `grind_setting` as `TEXT`, not numeric
Every grinder has its own scale; a number would lose meaning across grinders.

### 8 — Tasting scores as `SMALLINT` 1–10 with `CHECK`
Enough resolution, no false precision, valid data guaranteed at the DB level.

### 9 — `descriptors` as `TEXT[]`
Flavor notes are a list. A controlled vocabulary (SCA flavor wheel join table) is a
possible future upgrade.

### 10 — Full entity set from day one
`user`, `bean`, `brew`, `tasting`, `brew_method`, `equipment` all present from the start.

### 11 — Shared log, creator-owned rows (household / café model)
The instance is a single shared log — a household, or a café bar with several baristas.
Every authenticated user can **read** all beans, brews and tastings; can **add** beans,
brew from any bean, and taste any brew; and may **edit/delete only what they created**
(a non-creator write returns `403`). Each row records its creator: `bean.user_id` (owner),
`brew.user_id` (author), `tasting.user_id` (taster).

This evolved in two steps:
- Originally `user_id` lived only on `bean` and a brew's owner was derived through it — which
  made "my partner brews from my bag" impossible to attribute. So beans became shared and
  `brew` gained its own author (`brew.user_id`).
- Then, so that several baristas can each score the same pour, brews were opened for reading
  by anyone and `tasting` gained its own `user_id` (the taster), realizing 6.

Alternative considered: a full `household`/`team` grouping entity to isolate one group from
another — deferred as overkill for a small, trusted, self-hosted instance; it is the natural
next step if per-group isolation is ever needed.

### 12 — Brewing from a finished bean is allowed (soft warning)
`bean.is_finished` marks a used-up bag, but it is treated as **informational, not a hard
constraint**. Creating a brew from a finished bean is permitted — you often finish a bag and
only then log a brew you pulled earlier (retroactive logging) — and the brew service emits a
`WARNING` (`Brew N created on a finished bean`) rather than rejecting the request. A hard
block (409) was rejected as too rigid for a personal/café tracking app.

### 13 — `roaster` as its own table, created on demand (not free text, not admin-curated)
`bean.roaster` was free text; it is now `bean.roaster_id` → `roaster`.

Free text made every typo a new roaster ("Nomad" / "Nomad Coffee" / "nomad coffee"), which
silently splits any per-roaster grouping, and it offers nowhere to hang the roaster's own
metadata (country, city, website). But curating the table like `brew_method` / `equipment`
(admin-only writes) was rejected too: those are **small closed sets** — the ~10 brewing
methods, the gear physically in the house — whereas roasters are an **open set that grows with
every bag bought**. Admin-gating them would block a user from logging a bean until an admin
pre-registered the roaster.

So: **any user creates a roaster, implicitly.** `POST /beans` still takes `roaster` as a
*name*; the service resolves it with a get-or-create, matching case-insensitively against a
unique index on `lower(name)` (with whitespace trimmed and collapsed by
`domain/naming.normalize_name`). The first spelling seen becomes canonical. Beans read the
roaster back as a nested object.

**Case folding happens in the database, never in Python.** The index is `lower(name)` under
Postgres' collation, and `str.lower()` does not always agree with it (Turkish `İ`); folding
one side in Python would let a lookup miss a row the index still rejects as a duplicate.

**Every write that can collide with the unique index is savepoint-guarded** (`add_if_absent`,
`try_update`, `try_delete` in the repository): losing a race against a concurrent insert or
rename is a `409`, never an `IntegrityError` escaping as a `500`. The same applies to the FK:
`bean.roaster_id` is `RESTRICT` and `Roaster.beans` is `passive_deletes`, so the database — not
a check-then-delete in the service, which can go stale — is what refuses to strand a bean.

What the table buys, beyond identity:
- **Rename once, every bean follows** (`PATCH /roasters/{id}`, admin) — impossible with free text.
- **Merge duplicates** (`POST /roasters/{id}/merge`, admin): the source's beans are reassigned
  to the target and the source is deleted. The duplicate is often the one somebody filled in
  properly, so the target **adopts the source's metadata for any field it left empty** (its own
  values always win). This is the escape hatch for variants that slipped in before someone
  noticed, and the reason `DELETE` of an in-use roaster is a `409` rather than a cascade —
  beans are never silently detached from their roaster.
- **Somewhere to put roaster metadata** (country, city, website, notes).

**Abandoned roasters are reaped.** Fixing a typo with `PATCH /beans/{id}` would otherwise leave
the misspelled roaster in the picker forever — the very mess the table exists to prevent. When a
bean moves away and its old roaster has no beans left **and no metadata**, it is deleted: it held
nothing anyone entered. A roaster with metadata is always kept, beans or not — someone typed
those details on purpose.

### 14 — `/api/v1` prefix, and the frontend generates its client from the schema

Every router is mounted under `API_V1_STR` (`/api/v1`) so the API can evolve without breaking
an installed UI. **`/health` deliberately stays at the root**: container healthchecks probe it,
and a liveness check is not part of the versioned contract.

The web UI's API client is *derived* from the backend, never hand-written, so a route or schema
change surfaces as a TypeScript error rather than a runtime 404. Two things make that work:

- **Operation ids are `<tag>-<handler>`** (`generate_unique_id_function`), which is what gives
  the generated client readable names (`beansCreateBean`, not `create_bean_beans_post`).
- **`scripts/dump_openapi.py`** writes `openapi.json` without needing a database, so codegen
  runs offline and in CI.

### 15 — One image serves the UI and the API (like Mealie)

The Docker build compiles the SPA in a Node stage and copies `dist/` into `bloom/static`, which
`app.frontend()` serves (FastAPI ≥ 0.139) with an `index.html` fallback so client-side routes
survive a refresh. API routes, `/docs` and `/health` are matched first; missing assets and
non-GET requests still return a real 404.

The alternative — a second nginx image — was rejected because **Vite inlines the API URL at
build time**: a published frontend image would only work for whoever's API happened to sit at
the baked-in URL. Serving both from one origin means the UI calls the API with **relative**
paths, so a single image works at `localhost`, on a LAN IP, or behind a reverse proxy with no
rebuild and no configuration. It also makes CORS unnecessary in production.

CORS therefore exists only for development, where Vite runs the UI on its own origin (`:5173`)
and proxies `/api` to the backend: `FRONTEND_HOST` (plus any `BACKEND_CORS_ORIGINS`) lists the
origins allowed through the middleware. In a source checkout `bloom/static` does not exist and
the app simply serves no UI.

### 16 — shadcn/ui: components are vendored, not a dependency

`frontend/src/components/ui/` holds the actual source of every primitive, copied in rather than
imported from a package. Restyling a button is editing a file in this repo, not fighting a
library's theme API — which is the whole point for a project meant to be easy to pick up later.
The cost is that upstream fixes do not arrive by `npm update`; that trade is deliberate.

The reference (`fastapi/full-stack-fastapi-template`) uses Chakra; its architecture was kept
(Vite, TanStack Router + Query, generated client, route guards) and only the component layer
swapped.

### 17 — One CRUD kit, so a resource is one file

`DataTable`, `ResourceDialog`, `DeleteAlert` and `RowActions` (`src/components/data/`) are
shared, and a page supplies only three things: column definitions, a zod form schema, and the
generated query/mutation hooks. `routes/_app/roasters.tsx` is the smallest complete example.

Two API rules are centralised rather than re-derived per page, because getting either wrong is
silent:

- **Ownership** — `canEdit(row, user)` (`src/lib/auth.ts`) mirrors `services/access.py`. The UI
  hides what it must, and the API enforces it regardless.
- **PATCH omits, never nulls** — `stripEmpty()` (`src/lib/format.ts`), because `reject_null`
  turns an explicit `null` on a NOT NULL-backed field into a 422.

### 18 — Bearer token in `localStorage`, no refresh flow

The API issues a 60-minute JWT and has no refresh endpoint, so the UI stores the token in
`localStorage`, attaches it on every request, and on a `401` clears it and returns to `/login`.
An expired session means logging in again.

`localStorage` is readable by any script on the origin, so this leans on the app shipping no
third-party JavaScript (the CSP-free, self-hosted, single-origin setup makes that tractable).
If the threat model ever widens, the fix is a refresh flow with an httpOnly cookie — a backend
change, not a UI one.

### 19 — Mutations invalidate everything

Deletes cascade server-side (a bean takes its brews and its tastings with it) and rows
cross-reference each other, so a blanket `invalidateQueries()` after any write is both the
simplest and the most correct refresh. It is affordable precisely because the lists are small
and unpaginated — see 20. Revisit together with pagination, not before.

### 20 — Sorting and filtering are client-side

The API returns whole tables (no `limit`/`offset` anywhere), so the UI sorts and filters what it
already has. This is honest for a household-sized log and wrong at scale; the day a list gets
long, pagination is a backend change first and the tables follow.

### Users & auth
- **Two roles only** (`admin` / `user`) as a column on `user`; no RBAC tables yet.
- **First admin via env vars on startup**; further accounts are admin-created and default
  to `user` (no public registration).
- **JWT / OAuth2 password flow**, access token only; passwords hashed with argon2id.
- **Shared read across the instance**; **each row edited/deleted only by its creator** (or an
  admin), tracked by `bean.user_id` / `brew.user_id` / `tasting.user_id`.
- **Soft-delete** of users (`is_active`) instead of hard deletion.

### Cross-cutting choices
- **`TIMESTAMPTZ` everywhere**, never naive `TIMESTAMP`.
- **`NUMERIC` for all weights and measures**, never floating point (the domain layer uses
  `Decimal` end to end for the same reason).
- **`ON DELETE` policies**:
  - `bean` → `brew` → `tasting`: **CASCADE**. Note: because beans are shared, deleting a
    bean removes *every* user's brews on it (only the owner can trigger this).
  - `brew.method_id`: **RESTRICT** (a method in use cannot be deleted).
  - `bean.roaster_id`: **RESTRICT** (a roaster with beans is merged away, never deleted — see 13).
  - `brew.grinder_id`: **SET NULL** (deleting a grinder preserves brew history).
  - `user` → `bean` (owner), `user` → `brew` (author), `user` → `tasting` (taster): all
    **RESTRICT**, paired with **soft-delete** of users (an `is_active` flag). Accounts are
    never hard-deleted, so history is never silently destroyed.

All constraints and delete policies were executed against PostgreSQL 16 during design and
behave as documented.

---

## Domain logic

Pure functions, framework-free, in `bloom/domain/`. Inputs and outputs are `Decimal`
(ints accepted); floats are intentionally unsupported to avoid silent precision loss.

### Brew ratio (computed, not stored)
```
brew_ratio(dose, yield, water, category):
    reference = yield if category == 'espresso' else (water or yield)
    return reference / dose        # None if dose <= 0 or reference missing
```

### Extraction yield %
```
extraction_yield = (tds_percent * yield_grams) / dose_grams
```
`yield_grams` is beverage mass in the cup. Stored at write time when only TDS was measured.

### Extraction diagnostics
Classify a brew against the brewing control chart. The strength (TDS %) band depends on the
category — espresso is far more concentrated than filter — while the extraction-yield band
is shared. Each axis is reported as `below` / `within` / `above` (or `None` when the
measurement is missing). Ranges live in `domain/constants.py`:
```
STRENGTH_RANGE_FILTER   = (1.15, 1.35)   # TDS %, filter / immersion
STRENGTH_RANGE_ESPRESSO = (8.0, 12.0)    # TDS %, espresso
EY_RANGE                = (18.0, 22.0)   # extraction yield %, all categories
```
