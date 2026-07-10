# Bloom

Self-hosted tracking for the specialty coffee you brew — whether at home or behind
the bar as a barista. Bloom records the beans you buy, every brew you pull or pour,
and how each one tasted, so you can find what actually makes a good cup repeatable.

This repository currently covers the **backend REST API and data layer**. A `frontend/`
directory is reserved for later and is out of scope for now.

---

## Status

- [x] Data model designed and validated against PostgreSQL 16
- [x] Domain calculation layer specified (see [Domain logic](#domain-logic))
- [x] Local Postgres via Docker
- [ ] Backend implementation (FastAPI + SQLAlchemy + Alembic) — in progress
- [ ] User accounts with roles (admin / standard)
- [ ] Frontend — not started, reserved for the future

---

## Tech stack

| Layer       | Choice                                    |
|-------------|-------------------------------------------|
| Language    | **Python only** (no Go — decision closed) |
| API         | FastAPI                                   |
| ORM         | SQLAlchemy 2.x (typed, `Mapped[...]`)     |
| Migrations  | Alembic                                   |
| Validation  | Pydantic v2                               |
| Database    | PostgreSQL 16                             |
| Auth        | JWT (OAuth2 password flow)                |
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
│   ├── main.py                # FastAPI app factory & entrypoint
│   ├── core/                  # cross-cutting concerns
│   │   ├── config.py          # settings (pydantic-settings, reads env)
│   │   ├── security.py        # password hashing, JWT create/verify
│   │   └── dependencies.py    # FastAPI deps: get_db, get_current_user, require_admin
│   ├── db/
│   │   ├── base.py            # SQLAlchemy DeclarativeBase
│   │   ├── session.py         # engine + session factory
│   │   └── models/            # ORM models (one concern per file)
│   │       ├── user.py
│   │       ├── bean.py
│   │       ├── brew.py
│   │       ├── brew_method.py
│   │       ├── equipment.py
│   │       └── tasting.py
│   ├── schemas/               # Pydantic v2 models (request/response DTOs)
│   │   ├── user.py
│   │   ├── bean.py
│   │   ├── brew.py
│   │   └── tasting.py
│   ├── domain/                # PURE functions — no ORM, no FastAPI imports
│   │   ├── calculations.py    # brew ratio, extraction yield, diagnostics
│   │   └── constants.py       # SCA-style target ranges
│   ├── repositories/          # DB access layer (queries live here, not in routes)
│   │   ├── users.py
│   │   ├── beans.py
│   │   └── brews.py
│   ├── services/              # business logic orchestrating repos + domain
│   │   ├── auth_service.py
│   │   └── brew_service.py
│   └── routes/                # FastAPI routers (thin — validate, delegate, return)
│       ├── auth.py
│       ├── users.py
│       ├── beans.py
│       ├── brews.py
│       └── tastings.py
├── alembic/                   # migration environment
│   ├── env.py
│   └── versions/
├── tests/                     # pytest, outside the package
│   ├── conftest.py
│   ├── domain/                # fast unit tests for pure functions
│   └── api/                   # endpoint tests against a test DB
├── frontend/                  # reserved — empty for now
├── docker/
│   └── docker-compose.yml
├── alembic.ini
├── pyproject.toml
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
- The **first user created is bootstrapped as `admin`** (via env-configured initial
  admin, or a CLI command). Every subsequent sign-up defaults to `user`.
- Ownership: `bean` and `brew` carry a `user_id`. Users see and edit their own data;
  admins can see all.
- Auth is JWT via the OAuth2 password flow. Passwords are hashed (bcrypt/argon2), never
  stored in plain text.

---

## Getting started

Requires Docker (for Postgres) and Python 3.12+ with `uv`.

```bash
# 1. Start Postgres
docker compose -f docker/docker-compose.yml up -d

# 2. Install deps
uv sync

# 3. Apply migrations
uv run alembic upgrade head

# 4. Run the API (http://localhost:8000, docs at /docs)
uv run uvicorn bloom.main:app --reload
```

Connection string:

```
postgresql+psycopg://bloom:bloom@localhost:5432/bloom
```

> The schema is now owned by **Alembic migrations**, not a hand-written `schema.sql`.
> The original `schema.sql` from the design phase is kept only as a reference for the
> initial migration; the database of record is built by `alembic upgrade head`.

---

## Data model

Six tables. `brew` is the central, highest-volume entity; `user` owns the data.

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
| `user`        | Accounts with a role (`admin` / `user`). Owns beans and brews.      |
| `bean`        | A physical bag/lot of coffee.                                       |
| `brew_method` | Lookup: V60, Espresso, AeroPress… with a category.                  |
| `equipment`   | Grinders, machines, kettles — one table, `type` discriminator.      |
| `brew`        | A single extraction: the objective parameters. Central entity.      |
| `tasting`     | A subjective evaluation of a brew (1:N — a brew can have several).   |

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
- **First user is admin**, the rest default to `user`.
- **JWT / OAuth2 password flow**; passwords hashed, never stored plain.
- **Ownership** via `user_id` on `bean` / `brew`.

### Cross-cutting choices
- **`TIMESTAMPTZ` everywhere**, never naive `TIMESTAMP`.
- **`NUMERIC` for all weights and measures**, never floating point.
- **`ON DELETE` policies**:
  - `bean` → `brew` → `tasting`: **CASCADE**.
  - `brew.method_id`: **RESTRICT** (a method in use cannot be deleted).
  - `brew.grinder_id`: **SET NULL** (deleting a grinder preserves brew history).
  - `user` → `bean`: decision pending — likely **RESTRICT** or soft-delete, so deleting
    an account never silently destroys brew history. To be finalised in the user migration.

All constraints, both delete policies, and the aggregate query were executed against
PostgreSQL 16 during design and behaved as documented.

---

## Domain logic

Pure functions, framework-free, in `bloom/domain/`.

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

### Extraction diagnostics (optional)
Classify against the brewing control chart. Ranges below are for **filter**; espresso uses
a different strength scale (TDS ~8–12%), so make the strength band depend on `category`.
```
STRENGTH_RANGE = (1.15, 1.35)   # TDS %, filter
EY_RANGE       = (18.0, 22.0)   # extraction yield %
```

---

## Repository layout (top level)

```
.
├── bloom/            # backend package
├── alembic/          # migrations
├── tests/            # pytest
├── frontend/         # reserved, empty
├── docker/           # docker-compose for Postgres
├── alembic.ini
├── pyproject.toml
└── README.md
```
