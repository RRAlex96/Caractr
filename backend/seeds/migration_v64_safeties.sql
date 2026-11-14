-- Migration v6.4 — the database refuses bad rows; every figure can say where it comes from
--
-- Until now nothing but application code stood between a bad row and a buyer.
-- The catalogue had: a model created twice under two names (BMW 530 / Série 5),
-- two generations of one model claiming the same year (Audi TT 2006), one fuel
-- spelled two ways, engines written by an LLM with no fuel consumption, and a
-- count-based score of 1.4/10 on a Honda CR-V. Each was found by reading the
-- tables, after it had been shown to users.
--
-- This migration makes the rules the audit checks (app/services/data_audit.py)
-- into constraints, so a row that breaks one is rejected when it is written:
--
--   vehicle_models   a brand, and one row per (brand, name) whatever the case
--   generations      a model; years in order and in range; one row per
--                    (model, name); no two generations of a model sharing a
--                    year (an exclusion constraint; rows restricted to one
--                    fuel, like the electric Fiat 500e, are outside it)
--   engines          a model; a known fuel; power, size, consumption, CO2,
--                    reliability and maintenance in possible ranges; years in
--                    order; one row per (model, code)
--   driving_character one row per model; scores from 1 to 10
--   market_price_stats low <= typical <= high; a measured price rests on at
--                    least 6 listings
--   price_observations year and km in range
--
-- And three places to record provenance:
--
--   generations.source_url / verified_on    where the years were checked
--   market_snapshot_runs                    each market snapshot loaded: when it
--                                           was read, how many listings, how many
--                                           matched a catalogue model
--   brand_reliability                       per brand: the anchor score and the
--                                           published studies it rests on
--
-- A CHECK passes when its condition is unknown (a NULL power is "between 30
-- and 1100" as far as SQL is concerned), so each condition is wrapped in
-- COALESCE(..., FALSE): a missing value fails unless the rule itself allows it.
--
-- The no-shared-year rule is checked when a transaction commits, not row by
-- row: a migration that moves one generation's end and the next one's start
-- in the same statement passes through states that break it for a moment.
--
-- Run it after v63 (the generation corrections): the exclusion constraint
-- cannot be created while two generations overlap. Idempotent.

BEGIN;

CREATE EXTENSION IF NOT EXISTS btree_gist;

-- ── provenance ───────────────────────────────────────────────────────────────

ALTER TABLE generations
    ADD COLUMN IF NOT EXISTS source_url  TEXT,
    ADD COLUMN IF NOT EXISTS verified_on DATE;

CREATE TABLE IF NOT EXISTS market_snapshot_runs (
    id               SERIAL PRIMARY KEY,
    source           VARCHAR(50) NOT NULL,
    collected_on     DATE        NOT NULL,
    listings_read    INTEGER     NOT NULL CHECK (listings_read >= 0),
    listings_matched INTEGER     NOT NULL CHECK (listings_matched >= 0),
    listings_loaded  INTEGER     NOT NULL CHECK (listings_loaded >= 0),
    makes            INTEGER,
    notes            JSONB       NOT NULL DEFAULT '{}'::jsonb,
    loaded_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT market_snapshot_runs_matched_le_read CHECK (listings_matched <= listings_read),
    CONSTRAINT uq_market_snapshot_runs UNIQUE (source, collected_on)
);

CREATE TABLE IF NOT EXISTS brand_reliability (
    brand_id   INTEGER PRIMARY KEY REFERENCES brands(id) ON DELETE CASCADE,
    score      NUMERIC(3,1) NOT NULL CHECK (score BETWEEN 1 AND 10),
    studies    INTEGER      NOT NULL CHECK (studies >= 0),
    sources    JSONB        NOT NULL DEFAULT '[]'::jsonb,
    method     TEXT,
    as_of      DATE         NOT NULL
);

-- ── constraints ──────────────────────────────────────────────────────────────

DO $$
DECLARE
    wanted RECORD;
BEGIN
    FOR wanted IN
        SELECT * FROM (VALUES
            ('vehicle_models', 'vehicle_models_brand_required',
             'CHECK (COALESCE((brand_id IS NOT NULL), FALSE))'),
            ('generations', 'generations_model_required',
             'CHECK (COALESCE((model_id IS NOT NULL AND name IS NOT NULL), FALSE))'),
            ('generations', 'generations_years_ordered',
             'CHECK (COALESCE((year_start BETWEEN 1970 AND 2035 AND (year_end IS NULL OR year_end BETWEEN year_start AND 2035)), FALSE))'),
            ('generations', 'uq_generations_model_name',
             'UNIQUE (model_id, name)'),
            ('generations', 'generations_no_shared_year',
             'EXCLUDE USING gist (model_id WITH =, int4range(year_start, COALESCE(year_end, 9999), ''[]'') WITH &&) WHERE (fuel_type IS NULL) DEFERRABLE INITIALLY DEFERRED'),
            ('engines', 'engines_model_required',
             'CHECK (COALESCE((model_id IS NOT NULL AND code IS NOT NULL), FALSE))'),
            ('engines', 'engines_fuel_known',
             'CHECK (COALESCE((fuel_type IN (''gasolina'', ''diesel'', ''hibrido'', ''eletrico'', ''gpl'')), FALSE))'),
            ('engines', 'engines_power_range',
             'CHECK (COALESCE((power_hp BETWEEN 30 AND 1100), FALSE))'),
            ('engines', 'engines_size_fits_fuel',
             'CHECK (COALESCE(((fuel_type = ''eletrico'' AND COALESCE(displacement_cc, 0) = 0) OR (fuel_type <> ''eletrico'' AND displacement_cc BETWEEN 600 AND 8500)), FALSE))'),
            ('engines', 'engines_consumption_range',
             'CHECK (COALESCE((consumption_mixed IS NULL OR (fuel_type = ''eletrico'' AND consumption_mixed BETWEEN 10 AND 35) OR (fuel_type <> ''eletrico'' AND plug_in AND consumption_mixed BETWEEN 0.4 AND 9) OR (fuel_type <> ''eletrico'' AND NOT plug_in AND consumption_mixed BETWEEN 2.8 AND 25)), FALSE))'),
            ('engines', 'engines_co2_range',
             'CHECK (COALESCE((co2_emissions IS NULL OR (fuel_type = ''eletrico'' AND co2_emissions = 0) OR (fuel_type <> ''eletrico'' AND co2_emissions BETWEEN 8 AND 500)), FALSE))'),
            ('engines', 'engines_reliability_range',
             'CHECK (COALESCE((reliability_score BETWEEN 1 AND 10 AND maintenance_cost_year BETWEEN 100 AND 6000), FALSE))'),
            ('engines', 'engines_years_ordered',
             'CHECK (COALESCE((year_from IS NULL OR year_to IS NULL OR (year_from >= 1985 AND year_to BETWEEN year_from AND 2035)), FALSE))'),
            ('engines', 'uq_engines_model_code',
             'UNIQUE (model_id, code)'),
            ('driving_character', 'driving_character_scores_range',
             'CHECK (COALESCE((model_id IS NOT NULL AND comfort_score BETWEEN 1 AND 10 AND driving_fun_score BETWEEN 1 AND 10 AND city_score BETWEEN 1 AND 10 AND highway_score BETWEEN 1 AND 10 AND family_score BETWEEN 1 AND 10), FALSE))'),
            ('driving_character', 'uq_driving_character_model',
             'UNIQUE (model_id)'),
            ('market_price_stats', 'market_price_stats_ordered',
             'CHECK (COALESCE((avg_price BETWEEN 500 AND 500000 AND (min_price IS NULL OR min_price <= avg_price) AND (max_price IS NULL OR max_price >= avg_price)), FALSE))'),
            ('market_price_stats', 'market_price_stats_sample',
             'CHECK (COALESCE((source <> ''aggregated'' OR sample_count >= 6), FALSE))'),
            ('price_observations', 'price_observations_year_km_range',
             'CHECK (COALESCE(((vehicle_year IS NULL OR vehicle_year BETWEEN 1950 AND 2035) AND (km IS NULL OR km BETWEEN 0 AND 1500000)), FALSE))')
        ) AS t(tbl, name, definition)
    LOOP
        IF NOT EXISTS (SELECT 1 FROM pg_constraint c
                       WHERE c.conname = wanted.name AND c.conrelid = wanted.tbl::regclass) THEN
            EXECUTE format('ALTER TABLE %I ADD CONSTRAINT %I %s', wanted.tbl, wanted.name, wanted.definition);
        END IF;
    END LOOP;
END $$;

-- One model per (brand, name), whatever the case or the accents ("Série 5" / "serie 5").
CREATE UNIQUE INDEX IF NOT EXISTS uq_vehicle_models_brand_name
    ON vehicle_models (brand_id, LOWER(TRANSLATE(name, 'áàâãéêíóôõúçÁÀÂÃÉÊÍÓÔÕÚÇ', 'aaaaeeiooucAAAAEEIOOOUC')));

COMMIT;

-- Verify: the constraints now in place.
SELECT conrelid::regclass AS table_name, conname
FROM pg_constraint
WHERE connamespace = 'public'::regnamespace AND contype IN ('c', 'u', 'x')
  AND conrelid::regclass::text IN ('vehicle_models', 'generations', 'engines', 'driving_character',
                                   'market_price_stats', 'price_observations', 'market_snapshot_runs', 'brand_reliability')
ORDER BY 1, 2;
