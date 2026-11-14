-- Migration v7.0 — the no-shared-year rule on generations is checked at commit
--
-- v64 created the exclusion constraint generations_no_shared_year checked row
-- by row. A migration that moves one generation's end and the next one's start
-- in a single statement passes through states that break it for a moment, so
-- v63 could not be run a second time once v64 was in place. Checked at commit,
-- the rule is the same and those migrations are idempotent again.
--
-- Recreated only when it is not already deferrable. Idempotent.

BEGIN;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_constraint
               WHERE conname = 'generations_no_shared_year' AND NOT condeferrable) THEN
        ALTER TABLE generations DROP CONSTRAINT generations_no_shared_year;
        ALTER TABLE generations ADD CONSTRAINT generations_no_shared_year
            EXCLUDE USING gist (model_id WITH =, int4range(year_start, COALESCE(year_end, 9999), '[]') WITH &&)
            WHERE (fuel_type IS NULL) DEFERRABLE INITIALLY DEFERRED;
    END IF;
END $$;

COMMIT;

SELECT conname, condeferrable, condeferred FROM pg_constraint WHERE conname = 'generations_no_shared_year';
