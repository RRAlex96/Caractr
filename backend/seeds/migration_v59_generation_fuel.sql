-- Migration v5.9 — mark the Fiat 500e generation as electric-only
--
-- The petrol Fiat 500 (312, built to 2024) and the electric 500e (from 2020)
-- are different cars sold side by side under one model name, so their
-- generation rows overlap from 2020 to 2024. The lookup returned the newest
-- row containing the car's year, which put every 2020-or-later petrol 500 in
-- the 500e generation.
--
-- generations.fuel_type says "this generation exists only with this fuel".
-- NULL (every other row) means no restriction. _pick_generation in
-- ad_analysis_service.py chooses a fuel-specific generation only for a car of
-- that fuel. Values are the canonical ones from known_issues.normalize_fuel
-- (diesel, gasolina, hibrido, gpl, eletrico).
--
-- The app also adds the column at boot (main.py, _run_startup_migrations), so
-- running this first or second makes no difference. Idempotent.

BEGIN;

ALTER TABLE generations
    ADD COLUMN IF NOT EXISTS fuel_type VARCHAR(20);

UPDATE generations g
SET fuel_type = 'eletrico'
FROM vehicle_models vm
JOIN brands b ON b.id = vm.brand_id
WHERE vm.id = g.model_id
  AND b.name = 'Fiat' AND vm.name = '500'
  AND g.name = '500e'
  AND g.fuel_type IS DISTINCT FROM 'eletrico';

COMMIT;

-- Verify: the Fiat 500 generations and every row carrying a fuel restriction.
SELECT b.name AS brand, vm.name AS model, g.id, g.name AS generation,
       g.year_start, g.year_end, g.fuel_type
FROM generations g
JOIN vehicle_models vm ON vm.id = g.model_id
JOIN brands b ON b.id = vm.brand_id
WHERE (b.name = 'Fiat' AND vm.name = '500') OR g.fuel_type IS NOT NULL
ORDER BY b.name, vm.name, g.year_start;
