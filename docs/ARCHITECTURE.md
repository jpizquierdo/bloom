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
├── schema.sql                 # reference schema (not applied at runtime)
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
| **admin**  | Everything a standard user can do, plus manage users (create, promote/demote, deactivate) and manage shared lookup data (`brew_method`, `equipment`). |
| **user**   | Manage their own beans, brews and tastings. Read shared lookup data.         |

Design points:

- The role is a column on `user` (`role TEXT CHECK (role IN ('admin','user'))`), not a
  separate permissions table — two roles don't justify RBAC machinery yet.
- The **first admin is bootstrapped on startup from env vars**
  (`BLOOM_ADMIN_EMAIL` / `BLOOM_ADMIN_PASSWORD`), created only if it does not exist.
  There is **no public sign-up**: admins create further accounts, which default to `user`.
- **Ownership lives on `bean`** (`bean.user_id`). A brew's owner is derived through its
  bean (`brew → bean.user_id`); a tasting's through its brew. Non-admins only see and edit
  their own data; admins see all. Cross-user access returns `404` (existence is not leaked).
- **Users are soft-deleted** via an `is_active` flag — never hard-deleted — so brew
  history is always preserved.
- Auth is JWT via the OAuth2 password flow (access token only). Passwords are hashed with
  **argon2id**, never stored in plain text.

---

## Data model

Six tables. `brew` is the central, highest-volume entity; `user` owns the data (via `bean`).

```
user  1 ──< bean  1 ──< brew >── 1  brew_method
                          │
                          │  (grinder, nullable)
                   equipment ──1
                          │
                   brew  1 ──< tasting
```

| Table         | Purpose                                                             |
|---------------|---------------------------------------------------------------------|
| `user`        | Accounts with a role (`admin` / `user`). Owns beans (and brews via bean). |
| `bean`        | A physical bag/lot of coffee. Carries `user_id`.                    |
| `brew_method` | Lookup: V60, Espresso, AeroPress… with a category.                  |
| `equipment`   | Grinders, machines, kettles — one table, `type` discriminator.      |
| `brew`        | A single extraction: the objective parameters. Central entity.      |
| `tasting`     | A subjective evaluation of a brew (1:N — a brew can have several).   |

The live schema is owned by **Alembic migrations**. `schema.sql` is the reference from the
design phase (pre-`user`) that the ORM models reproduce faithfully; it is **not** applied at
runtime.

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
tasting separate keeps objective parameters clean from subjective scores.

### 7A — `grind_setting` as `TEXT`, not numeric
Every grinder has its own scale; a number would lose meaning across grinders.

### 8A — Tasting scores as `SMALLINT` 1–10 with `CHECK`
Enough resolution, no false precision, valid data guaranteed at the DB level.

### 9B — `descriptors` as `TEXT[]`
Flavor notes are a list. A controlled vocabulary (SCA flavor wheel join table) is a
possible future upgrade.

### 10A — Full entity set from day one
`user`, `bean`, `brew`, `tasting`, `brew_method`, `equipment` all present from the start.

### Users & auth
- **Two roles only** (`admin` / `user`) as a column on `user`; no RBAC tables yet.
- **First admin via env vars on startup**; further accounts are admin-created and default
  to `user` (no public registration).
- **JWT / OAuth2 password flow**, access token only; passwords hashed with argon2id.
- **Ownership** via `user_id` on `bean`; brew/tasting ownership derives through the bean.
- **Soft-delete** of users (`is_active`) instead of hard deletion.

### Cross-cutting choices
- **`TIMESTAMPTZ` everywhere**, never naive `TIMESTAMP`.
- **`NUMERIC` for all weights and measures**, never floating point (the domain layer uses
  `Decimal` end to end for the same reason).
- **`ON DELETE` policies**:
  - `bean` → `brew` → `tasting`: **CASCADE**.
  - `brew.method_id`: **RESTRICT** (a method in use cannot be deleted).
  - `brew.grinder_id`: **SET NULL** (deleting a grinder preserves brew history).
  - `user` → `bean`: **RESTRICT**, paired with **soft-delete** of users (an
    `is_active` flag). Accounts are never hard-deleted, so brew history is never
    silently destroyed.

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
