-- Migration v5.0 — market_price_stats upsert support
-- Adds UNIQUE(model_id, year) constraint required for ON CONFLICT upserts
-- when writing back live-scraped market data.
--
-- Run once against the database before deploying v5.0.
-- Safe to run multiple times (uses IF NOT EXISTS / DO NOTHING patterns).

-- NULL year rows (model-level averages from refresh_all_market_data) need their own constraint.
-- We treat (model_id, year) as the unique key where year may be NULL.
-- PostgreSQL treats NULL != NULL in unique constraints, so two NULL year rows for the same
-- model_id would both be allowed. We use a partial index to handle the NULL case.

-- 1. Standard unique constraint for rows where year IS NOT NULL
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'uq_market_model_year'
    ) THEN
        ALTER TABLE market_price_stats
        ADD CONSTRAINT uq_market_model_year UNIQUE (model_id, year);
    END IF;
END $$;

-- 2. Partial unique index for rows where year IS NULL (model-level averages)
CREATE UNIQUE INDEX IF NOT EXISTS uq_market_model_year_null
    ON market_price_stats (model_id)
    WHERE year IS NULL;
