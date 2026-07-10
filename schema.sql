-- ============================================================
-- Bloom — specialty coffee tracking
-- REFERENCE SCHEMA — validated against PostgreSQL 16.
--
-- NOTE: This file is NOT applied at runtime. Alembic owns the live
-- schema (see ARCHITECTURE.md). Keep this as the reference the SQLAlchemy
-- models must reproduce faithfully — every CHECK, FK ON DELETE policy
-- and default here must appear in the models and their migrations.
-- The `user` table is intentionally absent below; it was added when
-- multi-user support was introduced and lives only in the ORM/migrations.
-- ============================================================

-- brew_method as lookup table (3A)
CREATE TABLE brew_method (
    id            SMALLSERIAL PRIMARY KEY,
    name          TEXT NOT NULL UNIQUE,
    category      TEXT NOT NULL CHECK (category IN ('espresso', 'filter', 'immersion')),
    default_ratio NUMERIC(5,2)          -- nullable, e.g. 16.00 for 1:16
);

-- single equipment table with a type discriminator (5A)
CREATE TABLE equipment (
    id         SERIAL PRIMARY KEY,
    type       TEXT NOT NULL CHECK (type IN ('grinder', 'espresso_machine', 'kettle', 'other')),
    name       TEXT NOT NULL,
    brand      TEXT,
    notes      TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- bean = physical bag/lot (1A); process as text + CHECK (4B)
CREATE TABLE bean (
    id                   SERIAL PRIMARY KEY,
    name                 TEXT NOT NULL,
    roaster              TEXT NOT NULL,
    origin_country       TEXT,
    region               TEXT,
    producer             TEXT,
    variety              TEXT,
    process              TEXT CHECK (process IN (
                             'washed', 'natural', 'honey',
                             'anaerobic', 'carbonic_maceration', 'other'
                         )),
    roast_level          TEXT CHECK (roast_level IN ('light', 'medium_light', 'medium', 'medium_dark', 'dark')),
    roast_date           DATE,
    purchase_date        DATE,
    weight_grams         INTEGER CHECK (weight_grams > 0),
    price                NUMERIC(7,2),
    altitude_masl        INTEGER,
    tasting_notes_label  TEXT,           -- what the bag claims
    notes                TEXT,
    is_finished          BOOLEAN NOT NULL DEFAULT FALSE,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Central entity.
-- ratio computed in app (not stored); tds & extraction_yield stored (2C).
-- grind_setting as text (7A).
CREATE TABLE brew (
    id                       SERIAL PRIMARY KEY,
    bean_id                  INTEGER NOT NULL REFERENCES bean(id) ON DELETE CASCADE,
    method_id                SMALLINT NOT NULL REFERENCES brew_method(id) ON DELETE RESTRICT,
    grinder_id               INTEGER REFERENCES equipment(id) ON DELETE SET NULL,
    brewed_at                TIMESTAMPTZ NOT NULL DEFAULT now(),

    -- inputs
    dose_grams               NUMERIC(6,2) NOT NULL CHECK (dose_grams > 0),
    yield_grams              NUMERIC(6,2) CHECK (yield_grams > 0),   -- beverage out
    water_grams              NUMERIC(6,2) CHECK (water_grams > 0),   -- for filter/immersion
    grind_setting            TEXT,
    water_temp_celsius       NUMERIC(4,1),
    brew_time_seconds        INTEGER CHECK (brew_time_seconds > 0),

    -- measured extraction (nullable, only if you have a refractometer)
    tds_percent              NUMERIC(4,2) CHECK (tds_percent >= 0),
    extraction_yield_percent NUMERIC(4,2) CHECK (extraction_yield_percent >= 0),

    notes                    TEXT
);

-- tasting 1:N with brew (6B); scores smallint 1-10 with CHECK (8A);
-- descriptors as text[] (9B).
CREATE TABLE tasting (
    id          SERIAL PRIMARY KEY,
    brew_id     INTEGER NOT NULL REFERENCES brew(id) ON DELETE CASCADE,
    aroma       SMALLINT CHECK (aroma      BETWEEN 1 AND 10),
    acidity     SMALLINT CHECK (acidity    BETWEEN 1 AND 10),
    sweetness   SMALLINT CHECK (sweetness  BETWEEN 1 AND 10),
    body        SMALLINT CHECK (body       BETWEEN 1 AND 10),
    bitterness  SMALLINT CHECK (bitterness BETWEEN 1 AND 10),
    aftertaste  SMALLINT CHECK (aftertaste BETWEEN 1 AND 10),
    overall     SMALLINT CHECK (overall    BETWEEN 1 AND 10),
    descriptors TEXT[] NOT NULL DEFAULT '{}',
    notes       TEXT,
    tasted_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================
-- Indexes for the queries you'll actually run
-- ============================================================
CREATE INDEX idx_brew_bean_id    ON brew(bean_id);
CREATE INDEX idx_brew_method_id  ON brew(method_id);
CREATE INDEX idx_brew_brewed_at  ON brew(brewed_at DESC);
CREATE INDEX idx_tasting_brew_id ON tasting(brew_id);
CREATE INDEX idx_bean_roaster    ON bean(roaster);
