-- Migration v6.0 — merge the auto-created "BMW 530" model into "BMW Série 5"
--
-- "530" was created when a 530e listing could not be matched to the
-- catalogue: the matcher compared an accent-stripped "serie 5" with the
-- catalogue's "Série 5" and never found it (fixed in a943622). The stub then
-- captured every 530 listing, and the curator gave it generations and an
-- engine of its own while the real Série 5 had none.
--
-- What moves to Série 5:
--   - the stub's generations Série 5 lacks (E34, E39, E60), with their evidence
--   - its engine (the 3.0 diesel of the 530d) and that engine's issue rows
--   - the analysed listings, their snapshots and price observations
-- What is deleted:
--   - the stub's F10 / G30 / G60 rows: duplicates of Série 5's, no evidence
--   - its market_price_stats rows: pools of one live comparison each, stored
--     under the wrong model; the next analysis or snapshot writes Série 5's
--   - the stub model itself
-- Série 5's F10 starts in 2010, not 2009: the E60 it replaces is now in the
-- catalogue and runs to 2009 (one generation per changeover year, as in v58).
--
-- Second fix, same cause: a BMW 640 Gran Coupé was matched to "Série 2 Gran
-- Coupé" by the old any-word fallback. Its cached listing is detached from
-- that model and the price row its comparison wrote there is removed.
--
-- Models are found by name, not id. Idempotent: a second run finds no stub.

BEGIN;

DO $$
DECLARE
    stub_id  INTEGER;
    real_id  INTEGER;
    gc_id    INTEGER;
    g        RECORD;
    target   INTEGER;
BEGIN
    SELECT vm.id INTO stub_id
    FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
    WHERE b.name = 'BMW' AND vm.name = '530' AND COALESCE(vm.body_type, '') = '';

    SELECT vm.id INTO real_id
    FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
    WHERE b.name = 'BMW' AND vm.name = 'Série 5';

    IF stub_id IS NOT NULL THEN
        IF real_id IS NULL THEN
            RAISE EXCEPTION 'BMW Série 5 not found — nothing to merge into';
        END IF;

        FOR g IN SELECT id, name FROM generations WHERE model_id = stub_id LOOP
            SELECT id INTO target FROM generations WHERE model_id = real_id AND name = g.name;
            IF target IS NULL THEN
                UPDATE generations SET model_id = real_id WHERE id = g.id;
            ELSE
                UPDATE reliability_evidence SET generation_id = target WHERE generation_id = g.id;
                UPDATE price_observations   SET generation_id = target WHERE generation_id = g.id;
                DELETE FROM reliability_scores_history WHERE generation_id = g.id;   -- recomputed by the scorer
                DELETE FROM market_price_stats_history WHERE generation_id = g.id;   -- recomputed by the aggregator
                DELETE FROM generations WHERE id = g.id;
            END IF;
        END LOOP;

        UPDATE generations f10
        SET year_start = 2010
        WHERE f10.model_id = real_id AND f10.name = 'F10' AND f10.year_start = 2009
          AND EXISTS (SELECT 1 FROM generations e60
                      WHERE e60.model_id = real_id AND e60.name = 'E60' AND e60.year_end = 2009);

        UPDATE engines SET model_id = real_id WHERE model_id = stub_id;
        DELETE FROM market_price_stats WHERE model_id = stub_id;
        DELETE FROM driving_character  WHERE model_id = stub_id;
        UPDATE import_cost_estimates SET model_id = real_id WHERE model_id = stub_id;
        UPDATE normalized_listings   SET model_id = real_id WHERE model_id = stub_id;
        UPDATE listing_snapshots     SET model_id = real_id WHERE model_id = stub_id;
        UPDATE price_observations po
        SET model_id = real_id,
            generation_id = (SELECT gen.id FROM generations gen
                             WHERE gen.model_id = real_id
                               AND po.vehicle_year BETWEEN gen.year_start AND COALESCE(gen.year_end, 9999)
                             ORDER BY gen.year_start DESC LIMIT 1)
        WHERE po.model_id = stub_id;

        DELETE FROM vehicle_models WHERE id = stub_id;
        RAISE NOTICE 'BMW 530 (id %) merged into Série 5 (id %)', stub_id, real_id;
    ELSE
        RAISE NOTICE 'no BMW 530 stub — already merged';
    END IF;

    -- The BMW 640 Gran Coupé that was filed under Série 2 Gran Coupé.
    SELECT vm.id INTO gc_id
    FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
    WHERE b.name = 'BMW' AND vm.name = 'Série 2 Gran Coupé';

    IF gc_id IS NOT NULL THEN
        -- The listing is recognised by its URL: the stored model name is the
        -- (wrong) catalogue name it was matched to.
        DELETE FROM market_price_stats mps
        WHERE mps.model_id = gc_id AND mps.source = 'live_scraped'
          AND EXISTS (SELECT 1 FROM normalized_listings n
                      JOIN raw_listings r ON r.id = n.raw_listing_id
                      WHERE n.model_id = gc_id AND r.source_url LIKE '%/bmw-640-%' AND n.year = mps.year);
        UPDATE price_observations SET model_id = NULL, generation_id = NULL
        WHERE model_id = gc_id AND source_url LIKE '%/bmw-640-%';
        UPDATE listing_snapshots SET model_id = NULL
        WHERE model_id = gc_id AND source_url LIKE '%/bmw-640-%';
        UPDATE normalized_listings n SET model_id = NULL
        FROM raw_listings r
        WHERE r.id = n.raw_listing_id AND n.model_id = gc_id AND r.source_url LIKE '%/bmw-640-%';
    END IF;
END $$;

COMMIT;

-- Verify: Série 5 and what hangs off it; no "530" model left.
SELECT vm.id, vm.name, vm.body_type,
       (SELECT string_agg(g.name || ' ' || g.year_start || '–' || COALESCE(g.year_end::text, ''), ', ' ORDER BY g.year_start)
        FROM generations g WHERE g.model_id = vm.id) AS generations,
       (SELECT COUNT(*) FROM engines e WHERE e.model_id = vm.id) AS engines
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE b.name = 'BMW' AND vm.name IN ('530', 'Série 5');
