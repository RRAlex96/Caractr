-- Migration v5.7 — close generations that were replaced but still run to "now"
--
-- An open-ended row (year_end NULL) keeps growing after its generation is
-- replaced or discontinued, so a car is priced against its successor: the same
-- failure as the BMW 530 catch-all row fixed in v5.6.
--
--   Part 1  33 open-ended rows get an end year; 26 of them get a successor row.
--   Part 2  four models with wrong years (MINI Cooper, Porsche Macan,
--           Cupra Ateca, Volkswagen Touran).
--
-- Dates, sources and the reasoning are in migration_v57_close_replaced_generations.md.
--
-- Rules (same as v5.6)
--   * Windows of one model do not overlap. A changeover year goes to the
--     generation on sale for most of it: launch in the second half of the year
--     -> the outgoing generation keeps that year.
--   * The existing row keeps its id, its reliability_scores_history and its
--     denormalised reliability_* columns. Successor rows start with no score.
--   * reliability_evidence dated entirely after the old row's new end year
--     moves to the successor. Evidence that starts inside the old window stays.
--   * market_price_stats_history and price_observations have no rows for these
--     generations (checked 2026-11-13).
--
-- Idempotent: Part 1 only matches a row that is still open-ended with its old
-- start year; Part 2 only matches the old values. Missing models are skipped.

BEGIN;

-- Brand / model names without accents ("Citroën" -> "Citroen", "Série 1" -> "Serie 1").
DROP TABLE IF EXISTS _v57_models;
CREATE TEMP TABLE _v57_models AS
SELECT vm.id AS model_id,
       translate(b.name,  'ÀÁÂÃÄÅÈÉÊËÌÍÎÏÒÓÔÕÖÙÚÛÜàáâãäåèéêëìíîïòóôõöùúûü',
                          'AAAAAAEEEEIIIIOOOOOUUUUaaaaaaeeeeiiiiooooouuuu') AS brand,
       translate(vm.name, 'ÀÁÂÃÄÅÈÉÊËÌÍÎÏÒÓÔÕÖÙÚÛÜàáâãäåèéêëìíîïòóôõöùúûü',
                          'AAAAAAEEEEIIIIOOOOOUUUUaaaaaaeeeeiiiiooooouuuu') AS model
FROM vehicle_models vm
JOIN brands b ON b.id = vm.brand_id;

-- ── Part 1 ───────────────────────────────────────────────────────────────────
-- old_start   start year of the open-ended row today (how it is found)
-- new_start   corrected start year, NULL = unchanged
-- new_end     end year to set
-- new_name    corrected name, NULL = unchanged
-- succ_*      successor row to insert, NULL = model discontinued, no successor
DROP TABLE IF EXISTS _v57_close;
CREATE TEMP TABLE _v57_close (
    brand TEXT, model TEXT, old_start INT, new_start INT, new_end INT, new_name TEXT,
    succ_name TEXT, succ_start INT, succ_platform TEXT
);

INSERT INTO _v57_close VALUES
    -- Discontinued, no successor under the same model name
    ('Audi',          'A4',                 2015, NULL, 2024, NULL, NULL, NULL, NULL),
    ('Fiat',          'Tipo',               2015, NULL, 2026, NULL, NULL, NULL, NULL),
    ('Ford',          'Focus',              2018, NULL, 2025, NULL, NULL, NULL, NULL),
    ('Jaguar',        'E-Pace',             2017, NULL, 2024, NULL, NULL, NULL, NULL),
    ('Kia',           'Ceed',               2018, NULL, 2025, NULL, NULL, NULL, NULL),
    ('Kia',           'Rio',                2017, NULL, 2023, NULL, NULL, NULL, NULL),
    ('Peugeot',       '508',                2018, NULL, 2025, NULL, NULL, NULL, NULL),
    -- Replaced
    ('Audi',          'A5',                 2016, NULL, 2024, NULL, 'A5 B10',           2025, 'PPC'),
    ('Audi',          'A6',                 2018, NULL, 2024, NULL, 'C9',               2025, 'PPC'),
    ('Audi',          'Q3',                 2018, NULL, 2025, NULL, 'Q3 III',           2026, 'MQB Evo'),
    ('Audi',          'Q5',                 2016, NULL, 2024, NULL, 'Q5 III',           2025, 'PPC'),
    ('BMW',           'Serie 1',            2019, NULL, 2024, NULL, 'F70',              2025, 'FAAR'),
    ('BMW',           'Serie 2 Gran Coupe', 2019, NULL, 2024, NULL, 'F74',              2025, 'FAAR'),
    ('BMW',           'Serie 5',            2016, 2017, 2023, NULL, 'G60',              2024, 'CLAR'),
    ('BMW',           'X3',                 2017, NULL, 2024, NULL, 'X3 G45',           2025, 'CLAR'),
    ('Citroen',       'C3',                 2016, NULL, 2024, NULL, 'C3 IV',            2025, 'Smart Car'),
    ('Citroen',       'C5 Aircross',        2018, NULL, 2025, NULL, 'C5 Aircross II',   2026, 'STLA Medium'),
    ('Jeep',          'Compass',            2017, NULL, 2025, NULL, 'Compass III',      2026, 'STLA Medium'),
    ('Mazda',         'CX-5',               2017, NULL, 2025, NULL, 'CX-5 III',         2026, NULL),
    ('Mercedes-Benz', 'CLA',                2019, NULL, 2025, NULL, 'CLA III',          2026, 'MMA'),
    ('MG',            'HS',                 2018, NULL, 2024, NULL, 'MG HS II',         2025, NULL),
    ('Nissan',        'Micra',              2017, NULL, 2023, NULL, 'Micra EV',         2026, 'AmpR Small'),
    ('Opel',          'Grandland',          2021, NULL, 2024, 'Grandland (facelift)',
                                                                    'Grandland II',     2025, 'STLA Medium'),
    ('Peugeot',       '5008',               2016, NULL, 2024, NULL, '5008 III',         2025, 'STLA Medium'),
    ('Porsche',       'Panamera',           2016, NULL, 2023, NULL, 'Panamera III',     2024, '972'),
    ('Renault',       'Clio',               2019, NULL, 2025, NULL, 'Clio VI',          2026, 'CMF-B'),
    ('Skoda',         'Superb',             2015, NULL, 2023, NULL, 'Superb IV',        2024, 'MQB Evo'),
    ('Skoda',         'Superb Combi',       2015, NULL, 2023, NULL, 'Superb Combi IV',  2024, 'MQB Evo'),
    ('Subaru',        'Forester',           2018, NULL, 2024, NULL, 'Forester VI',      2025, 'SGP'),
    ('Suzuki',        'Swift',              2017, NULL, 2023, NULL, 'Swift VI',         2024, 'Heartect'),
    ('Toyota',        'RAV4',               2018, NULL, 2025, NULL, 'RAV4 VI',          2026, 'TNGA-K'),
    ('Volkswagen',    'T-Roc',              2017, NULL, 2025, NULL, 'T-Roc II',         2026, 'MQB Evo'),
    ('Volkswagen',    'Tiguan',             2016, NULL, 2023, NULL, 'Tiguan III',       2024, 'MQB Evo');

DO $$
DECLARE
    r        RECORD;
    gid      INTEGER;   -- the open-ended row being closed
    mid      INTEGER;   -- its model
    succ_gid INTEGER;
    moved    INTEGER;
BEGIN
    FOR r IN SELECT * FROM _v57_close ORDER BY brand, model LOOP
        gid := NULL;
        SELECT g.id, g.model_id INTO gid, mid
        FROM generations g
        JOIN _v57_models m ON m.model_id = g.model_id
        WHERE m.brand = r.brand AND m.model = r.model
          AND g.year_start = r.old_start AND g.year_end IS NULL;

        IF gid IS NULL THEN
            RAISE NOTICE '% %: no open-ended row starting %, skipped', r.brand, r.model, r.old_start;
            CONTINUE;
        END IF;

        UPDATE generations
        SET year_end   = r.new_end,
            year_start = COALESCE(r.new_start, year_start),
            name       = COALESCE(r.new_name, name)
        WHERE id = gid;

        moved := 0;
        IF r.succ_name IS NOT NULL THEN
            INSERT INTO generations (model_id, name, year_start, year_end, platform)
            VALUES (mid, r.succ_name, r.succ_start, NULL, r.succ_platform)
            RETURNING id INTO succ_gid;

            -- Evidence dated entirely after the old window follows the successor.
            -- NHTSA rows carry one model year; Safety Gate rows a list of years.
            UPDATE reliability_evidence re
            SET generation_id = succ_gid
            WHERE re.generation_id = gid
              AND COALESCE(
                    CASE WHEN re.payload->>'year' ~ '^[0-9]{4}$'
                         THEN (re.payload->>'year')::int END,
                    (SELECT MIN(y::int)
                     FROM jsonb_array_elements_text(
                              CASE WHEN jsonb_typeof(re.payload->'years') = 'array'
                                   THEN re.payload->'years' ELSE '[]'::jsonb END) AS y
                     WHERE y ~ '^[0-9]{4}$')
                  ) > r.new_end;
            GET DIAGNOSTICS moved = ROW_COUNT;
        END IF;

        RAISE NOTICE '% %: generation % closed at %, % evidence rows moved',
            r.brand, r.model, gid, r.new_end, moved;
    END LOOP;
END $$;

-- ── Part 2: wrong years ──────────────────────────────────────────────────────

-- MINI Cooper: the F56 was built until early 2024; its successors (petrol F66,
-- electric J01) reached customers in 2024, not 2023.
UPDATE generations g SET year_end = 2023
FROM _v57_models m
WHERE m.model_id = g.model_id AND m.brand = 'MINI' AND m.model = 'Cooper'
  AND g.year_start = 2013 AND g.year_end = 2022;

UPDATE generations g SET year_start = 2024, name = 'F66 / J01'
FROM _v57_models m
WHERE m.model_id = g.model_id AND m.brand = 'MINI' AND m.model = 'Cooper'
  AND g.year_start = 2023 AND g.year_end IS NULL;

-- Porsche Macan: the petrol Macan was sold in the EU until mid-2024; the
-- electric Macan (PPE platform, not J1) reached customers in the autumn.
UPDATE generations g SET year_end = 2024
FROM _v57_models m
WHERE m.model_id = g.model_id AND m.brand = 'Porsche' AND m.model = 'Macan'
  AND g.year_start = 2014 AND g.year_end = 2023;

UPDATE generations g SET year_start = 2025, name = 'Macan Electric', platform = 'PPE'
FROM _v57_models m
WHERE m.model_id = g.model_id AND m.brand = 'Porsche' AND m.model = 'Macan'
  AND g.year_start = 2023 AND g.year_end IS NULL;

-- Cupra Ateca: Cupra only became a brand in 2018 and the Ateca was its first car.
UPDATE generations g SET year_start = 2018
FROM _v57_models m
WHERE m.model_id = g.model_id AND m.brand = 'Cupra' AND m.model = 'Ateca'
  AND g.year_start = 2016 AND g.year_end IS NULL;

-- Volkswagen Touran: the first generation ran to 2015 (facelift 2010), but the
-- table jumped from 2010 to 2015, leaving 2011–2014 with no generation.
INSERT INTO generations (model_id, name, year_start, year_end, platform)
SELECT m.model_id, 'Touran I facelift', 2011, 2015, 'PQ35'
FROM _v57_models m
WHERE m.brand = 'Volkswagen' AND m.model = 'Touran'
  AND EXISTS (SELECT 1 FROM generations g
              WHERE g.model_id = m.model_id AND g.year_start = 2015 AND g.year_end IS NULL);

UPDATE generations g SET year_start = 2016
FROM _v57_models m
WHERE m.model_id = g.model_id AND m.brand = 'Volkswagen' AND m.model = 'Touran'
  AND g.year_start = 2015 AND g.year_end IS NULL;

COMMIT;

-- Verify: every generation of the models touched, with what each now holds.
-- (The two temp tables last until the session ends.)
SELECT b.name AS brand, vm.name AS model, g.id, g.name AS generation,
       g.year_start, g.year_end, g.platform, g.reliability_score,
       (SELECT COUNT(*) FROM reliability_evidence re WHERE re.generation_id = g.id) AS evidence_rows,
       (SELECT COUNT(*) FROM reliability_scores_history rs WHERE rs.generation_id = g.id) AS score_rows
FROM generations g
JOIN vehicle_models vm ON vm.id = g.model_id
JOIN brands b ON b.id = vm.brand_id
JOIN _v57_models m ON m.model_id = g.model_id
WHERE (m.brand, m.model) IN (SELECT brand, model FROM _v57_close)
   OR (m.brand, m.model) IN (('MINI', 'Cooper'), ('Porsche', 'Macan'), ('Cupra', 'Ateca'),
                             ('Volkswagen', 'Touran'))
ORDER BY b.name, vm.name, g.year_start;
