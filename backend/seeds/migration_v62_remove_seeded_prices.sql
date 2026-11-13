-- Migration v6.2 — remove the seeded placeholder prices
--
-- market_price_stats was seeded with 139 rows of source "Standvirtual/OLX
-- 2025": round prices (12 000, 13 500, 19 500), round sample counts (35, 40,
-- 45, 50, 55), nearly all for model year 2022. They were never measured.
--
-- Run AFTER the first market snapshot has been loaded and aggregated
-- (scripts/market_snapshot.py load, then the monthly refresh's aggregate
-- step). The aggregation overwrites a seeded row wherever it measured that
-- model and year; this removes the ones it did not reach. Run before the
-- snapshot, it would leave the recommender without any price.
--
-- The guard below refuses to run when fewer than 50 models have a measured
-- price. Idempotent.

BEGIN;

DO $$
DECLARE
    measured INTEGER;
    removed  INTEGER;
BEGIN
    SELECT COUNT(DISTINCT model_id) INTO measured
    FROM market_price_stats WHERE source = 'aggregated';

    IF measured < 50 THEN
        RAISE EXCEPTION 'only % models have a measured price — load and aggregate a market snapshot first', measured;
    END IF;

    DELETE FROM market_price_stats WHERE source LIKE 'Standvirtual/OLX%';
    GET DIAGNOSTICS removed = ROW_COUNT;
    RAISE NOTICE '% seeded rows removed; % models have measured prices', removed, measured;
END $$;

COMMIT;

-- Verify: what is left, by source.
SELECT source, COUNT(*) AS row_count, COUNT(DISTINCT model_id) AS models,
       MIN(year) AS first_year, MAX(year) AS last_year
FROM market_price_stats
GROUP BY source
ORDER BY 2 DESC;
