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
- **Everything is a shared log** (household/café model, 11A). Any authenticated user can
  read all beans, brews and tastings, and can add beans, brew from any bean, and taste any
  brew. Each row records who created it — `bean.user_id` (owner), `brew.user_id` (author),
  `tasting.user_id` (taster) — and **only that creator (or an admin) may edit or delete it**
  (a non-creator write returns `403`). Because tastings carry their taster, several people
  can each score the same brew (realizing 6B).
- **Users are soft-deleted** via an `is_active` flag — never hard-deleted — so history is
  always preserved.
- Auth is JWT via the OAuth2 password flow (access token only). Passwords are hashed with
  **argon2id**, never stored in plain text.

---

## Data model

Six tables. `brew` is the central, highest-volume entity.

```
Entities:
    bean 1 ──< brew >── 1 brew_method
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
| `user`        | Accounts with a role (`admin` / `user`). Owns beans, authors brews, makes tastings. |
| `bean`        | A physical bag/lot of coffee. Shared; `user_id` is the owner.        |
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

Each decision was made explicitly. Letter codes match the options weighed during design.

### 1A — `bean` is a physical lot, not an abstract coffee
One `bean` row = one bag bought, with its own purchase date, price and weight. If needed
later, this splits into `coffee` (concept) + `bean_lot` (physical).

### 2C — Derived vs. measured fields: a hybrid rule
- **`ratio` is computed in the domain layer, never stored.**
- **`tds_percent` and `extraction_yield_percent` are stored** — real refractometer
  measurements, not derivations. When only TDS is measured, EY is computed once at write
  time and stored, so analytics read a single column.

Rule: **per-row math → domain layer; aggregates over many rows → SQL.**

### 3A — `brew_method` as a lookup table, not an enum
New methods without a migration.

### 4B — `process` as `TEXT` + `CHECK`, not a native enum
Specialty processes evolve constantly; `TEXT` + `CHECK` gives integrity with a one-line
change to extend, avoiding the rigidity of Postgres enums.

### 5A — Single `equipment` table with a `type` discriminator
Grinders, machines and kettles share enough shape. `brew` references it as `grinder_id`.

### 6B — `tasting` is 1:N with `brew`
Same extraction can be scored by more than one person, or re-tasted as it cools. Keeping
tasting separate keeps objective parameters clean from subjective scores. Each tasting
records its taster (`tasting.user_id`), so several users can score the same brew (see 11A).

### 7A — `grind_setting` as `TEXT`, not numeric
Every grinder has its own scale; a number would lose meaning across grinders.

### 8A — Tasting scores as `SMALLINT` 1–10 with `CHECK`
Enough resolution, no false precision, valid data guaranteed at the DB level.

### 9B — `descriptors` as `TEXT[]`
Flavor notes are a list. A controlled vocabulary (SCA flavor wheel join table) is a
possible future upgrade.

### 10A — Full entity set from day one
`user`, `bean`, `brew`, `tasting`, `brew_method`, `equipment` all present from the start.

### 11A — Shared log, creator-owned rows (household / café model)
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
  by anyone and `tasting` gained its own `user_id` (the taster), realizing 6B.

Alternative considered: a full `household`/`team` grouping entity to isolate one group from
another — deferred as overkill for a small, trusted, self-hosted instance; it is the natural
next step if per-group isolation is ever needed.

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
