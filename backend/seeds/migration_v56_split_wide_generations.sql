-- Migration v5.6 — split five catch-all generation rows into real windows
--
-- Five rows in `generations` spanned more than 12 years. Ad analysis uses the
-- generation window as the year guard of the live market comparison, so a 2018
-- BMW 530e was priced against every 530 from "1988–now".
--
--   BMW 530            1988–now   -> E34, E39, E60, F10, G30, G60
--   Volkswagen Caddy   2003–2020  -> Caddy III, Caddy III facelift, Caddy IV
--   Fiat 500 (312)     2007–2023  -> 500 (312), 500 (312) facelift
--   Fiat Panda III     2012–now   -> Panda III, Panda III (2020 update)
--   Lexus IS III       2013–now   -> IS III, IS III facelift, IS III 2nd facelift
--
-- Windows, sources and the reasoning are in migration_v56_split_wide_generations.md.
--
-- How a row is split
--   * The existing row keeps its id and becomes the window that holds most of
--     its linked evidence, so reliability_scores_history and the denormalised
--     reliability_* columns stay where they are. New windows are inserted with
--     no score; the monthly reliability run fills them in.
--   * reliability_evidence rows carrying a single model year (NHTSA) move to
--     the window containing that year. Safety Gate rows carry a production
--     range and stay with the window they overlap most (no move needed today).
--   * market_price_stats_history and price_observations have no rows for these
--     generations (checked 2026-11-13), so nothing else references them.
--   * Windows of one model do not overlap. A changeover year goes to the
--     generation on sale for most of it (launch in the second half of the year
--     -> the outgoing generation keeps that year).
--
-- Idempotent: each block looks for the old wide row by brand, model and years
-- and does nothing when it is gone. Models missing from a database are skipped.

BEGIN;

DO $$
DECLARE
    gid     INTEGER;   -- the existing wide row
    mid     INTEGER;   -- its model
    new_gid INTEGER;
BEGIN

    -- ── BMW 530: 1988–now ────────────────────────────────────────────────────
    SELECT g.id, g.model_id INTO gid, mid
    FROM generations g
    JOIN vehicle_models vm ON vm.id = g.model_id
    JOIN brands b ON b.id = vm.brand_id
    WHERE b.name = 'BMW' AND vm.name = '530'
      AND g.year_start = 1988 AND g.year_end IS NULL;

    IF gid IS NULL THEN
        RAISE NOTICE 'BMW 530: no 1988-now row, skipped';
    ELSE
        -- Existing row -> E39: 7 of its 9 evidence rows are model years 1997–2001.
        UPDATE generations
        SET name = 'E39', year_start = 1996, year_end = 2003, platform = 'E39'
        WHERE id = gid;

        INSERT INTO generations (model_id, name, year_start, year_end, platform) VALUES
            (mid, 'E34', 1988, 1995, 'E34'),
            (mid, 'E60', 2004, 2009, 'E60'),
            (mid, 'F10', 2010, 2016, 'F10'),
            (mid, 'G30', 2017, 2023, 'CLAR'),
            (mid, 'G60', 2024, NULL, 'CLAR');

        -- Evidence follows its model year (today: two rows, 1994 and 1995 -> E34).
        UPDATE reliability_evidence re
        SET generation_id = g2.id
        FROM generations g2
        WHERE re.generation_id = gid
          AND g2.model_id = mid AND g2.id <> gid
          AND (CASE WHEN re.payload->>'year' ~ '^[0-9]{4}$'
                    THEN (re.payload->>'year')::int END)
              BETWEEN g2.year_start AND COALESCE(g2.year_end, 9999);

        RAISE NOTICE 'BMW 530: split (generation id %)', gid;
    END IF;

    -- ── Volkswagen Caddy: 2003–2020 ──────────────────────────────────────────
    gid := NULL;
    SELECT g.id, g.model_id INTO gid, mid
    FROM generations g
    JOIN vehicle_models vm ON vm.id = g.model_id
    JOIN brands b ON b.id = vm.brand_id
    WHERE b.name = 'Volkswagen' AND vm.name = 'Caddy'
      AND g.year_start = 2003 AND g.year_end = 2020;

    IF gid IS NULL THEN
        RAISE NOTICE 'Volkswagen Caddy: no 2003-2020 row, skipped';
    ELSE
        -- Existing row -> Caddy IV: its one Safety Gate recall covers 2013–2024,
        -- and 2016–2020 is the largest part of that range.
        UPDATE generations
        SET name = 'Caddy IV', year_start = 2016, year_end = 2020
        WHERE id = gid;

        INSERT INTO generations (model_id, name, year_start, year_end, platform) VALUES
            (mid, 'Caddy III',          2003, 2010, 'PQ35'),
            (mid, 'Caddy III facelift', 2011, 2015, 'PQ35');

        -- Caddy V reached dealers at the very end of 2020; "2020–now" overlapped
        -- Caddy IV and, being the newer row, claimed every 2020 car.
        UPDATE generations
        SET year_start = 2021
        WHERE model_id = mid AND year_start = 2020 AND year_end IS NULL;

        RAISE NOTICE 'Volkswagen Caddy: split (generation id %)', gid;
    END IF;

    -- ── Fiat 500 (312): 2007–2023 ────────────────────────────────────────────
    gid := NULL;
    SELECT g.id, g.model_id INTO gid, mid
    FROM generations g
    JOIN vehicle_models vm ON vm.id = g.model_id
    JOIN brands b ON b.id = vm.brand_id
    WHERE b.name = 'Fiat' AND vm.name = '500'
      AND g.year_start = 2007 AND g.year_end = 2023;

    IF gid IS NULL THEN
        RAISE NOTICE 'Fiat 500: no 2007-2023 row, skipped';
    ELSE
        -- Existing row keeps the pre-facelift years: 76 of its 85 evidence rows
        -- are model years 2011–2015.
        UPDATE generations
        SET year_end = 2015
        WHERE id = gid;

        INSERT INTO generations (model_id, name, year_start, year_end, platform)
        VALUES (mid, '500 (312) facelift', 2016, 2024, '188/312')
        RETURNING id INTO new_gid;

        -- Evidence follows its model year (today: nine rows, 2016–2018).
        UPDATE reliability_evidence re
        SET generation_id = new_gid
        WHERE re.generation_id = gid
          AND (CASE WHEN re.payload->>'year' ~ '^[0-9]{4}$'
                    THEN (re.payload->>'year')::int END) >= 2016;

        RAISE NOTICE 'Fiat 500: split (generation id %)', gid;
    END IF;

    -- ── Fiat Panda III: 2012–now ─────────────────────────────────────────────
    gid := NULL;
    SELECT g.id, g.model_id INTO gid, mid
    FROM generations g
    JOIN vehicle_models vm ON vm.id = g.model_id
    JOIN brands b ON b.id = vm.brand_id
    WHERE b.name = 'Fiat' AND vm.name = 'Panda'
      AND g.year_start = 2012 AND g.year_end IS NULL;

    IF gid IS NULL THEN
        RAISE NOTICE 'Fiat Panda: no 2012-now row, skipped';
    ELSE
        -- Existing row -> 2020 onwards: all four evidence rows are 2024–2026
        -- recalls and its scored engine is the 1.0 mild hybrid (2020+).
        UPDATE generations
        SET name = 'Panda III (2020 update)', year_start = 2020
        WHERE id = gid;

        INSERT INTO generations (model_id, name, year_start, year_end, platform)
        VALUES (mid, 'Panda III', 2012, 2019, '188');

        RAISE NOTICE 'Fiat Panda: split (generation id %)', gid;
    END IF;

    -- ── Lexus IS III (XE30): 2013–now ────────────────────────────────────────
    gid := NULL;
    SELECT g.id, g.model_id INTO gid, mid
    FROM generations g
    JOIN vehicle_models vm ON vm.id = g.model_id
    JOIN brands b ON b.id = vm.brand_id
    WHERE b.name = 'Lexus' AND vm.name = 'IS'
      AND g.year_start = 2013 AND g.year_end IS NULL;

    IF gid IS NULL THEN
        RAISE NOTICE 'Lexus IS: no 2013-now row, skipped';
    ELSE
        -- No evidence is linked to this row; it keeps the launch years.
        UPDATE generations
        SET year_end = 2016
        WHERE id = gid;

        INSERT INTO generations (model_id, name, year_start, year_end, platform) VALUES
            (mid, 'IS III facelift',     2017, 2020, 'GA-L'),
            (mid, 'IS III 2nd facelift', 2021, NULL, 'GA-L');

        RAISE NOTICE 'Lexus IS: split (generation id %)', gid;
    END IF;

END $$;

COMMIT;

-- Verify: the five models, their windows and the evidence each now holds.
SELECT b.name AS brand, vm.name AS model, g.id, g.name AS generation,
       g.year_start, g.year_end, g.platform, g.reliability_score,
       (SELECT COUNT(*) FROM reliability_evidence re WHERE re.generation_id = g.id) AS evidence_rows,
       (SELECT COUNT(*) FROM reliability_scores_history rs WHERE rs.generation_id = g.id) AS score_rows
FROM generations g
JOIN vehicle_models vm ON vm.id = g.model_id
JOIN brands b ON b.id = vm.brand_id
WHERE (b.name, vm.name) IN (('BMW', '530'), ('Volkswagen', 'Caddy'), ('Fiat', '500'),
                            ('Fiat', 'Panda'), ('Lexus', 'IS'))
ORDER BY b.name, vm.name, g.year_start;
