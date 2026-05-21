-- ═══════════════════════════════════════════════════════════════════════
-- CarroJusto — Seed Data v3 Expansion
-- ═══════════════════════════════════════════════════════════════════════
-- Adds ~55 vehicle models, ~170 engines, engine issues, driving character
-- for all cars commonly found on Standvirtual Portugal.
--
-- Run AFTER seed_data_refined_v2.sql and BEFORE migration_v51_generations.sql
-- IDEMPOTENT: uses WHERE NOT EXISTS checks. Safe to run multiple times.
--
-- Sources: ACAP 2024, Standvirtual trends, TÜV Report 2024/2025,
--          ADAC 2024, Spritmonitor.de, manufacturer specs
-- ═══════════════════════════════════════════════════════════════════════

BEGIN;

-- ═══════════════════════════════════════════════════════════
-- 1. BRAND NAME NORMALIZATION
--    Match v51_generations naming (ASCII, official casing)
-- ═══════════════════════════════════════════════════════════
UPDATE brands SET name = 'SEAT'  WHERE name = 'Seat';
UPDATE brands SET name = 'MINI'  WHERE name = 'Mini';
UPDATE brands SET name = 'Citroen' WHERE name = 'Citroën';

-- Normalize accented model names to ASCII
UPDATE vehicle_models SET name = 'Serie 3' WHERE name = 'Série 3';


-- ═══════════════════════════════════════════════════════════
-- 2. NEW BRANDS (15 brands referenced by v51 generations)
-- ═══════════════════════════════════════════════════════════
INSERT INTO brands (name, country)
SELECT v.name, v.country
FROM (VALUES
  ('Alfa Romeo',  'Italia'),
  ('Alpine',      'Franca'),
  ('BYD',         'China'),
  ('Cupra',       'Espanha'),
  ('DS',          'Franca'),
  ('Jaguar',      'Reino Unido'),
  ('Jeep',        'EUA'),
  ('Land Rover',  'Reino Unido'),
  ('Lexus',       'Japao'),
  ('Maserati',    'Italia'),
  ('MG',          'China'),
  ('Omoda',       'China'),
  ('Porsche',     'Alemanha'),
  ('Smart',       'Alemanha'),
  ('Subaru',      'Japao')
) AS v(name, country)
WHERE NOT EXISTS (SELECT 1 FROM brands b2 WHERE LOWER(b2.name) = LOWER(v.name));


-- ═══════════════════════════════════════════════════════════
-- 3. NEW VEHICLE MODELS (~55 most searched on Standvirtual)
-- ═══════════════════════════════════════════════════════════
INSERT INTO vehicle_models (brand_id, name, body_type, segment)
SELECT b.id, v.model, v.body, v.seg
FROM (VALUES
  -- Citroen
  ('Citroen',      'C3',            'compacto',   'economico'),
  ('Citroen',      'C4',            'compacto',   'medio'),
  ('Citroen',      'C5 Aircross',   'suv',        'medio'),
  ('Citroen',      'C3 Aircross',   'suv',        'economico'),
  ('Citroen',      'Berlingo',      'monovolume', 'economico'),
  -- Renault
  ('Renault',      'Captur',        'suv',        'economico'),
  ('Renault',      'Megane',        'compacto',   'medio'),
  ('Renault',      'Arkana',        'suv',        'medio'),
  ('Renault',      'Kadjar',        'suv',        'medio'),
  ('Renault',      'Austral',       'suv',        'medio'),
  ('Renault',      'Scenic',        'monovolume', 'medio'),
  ('Renault',      'Twingo',        'compacto',   'economico'),
  -- BMW
  ('BMW',          'Serie 1',       'compacto',   'premium'),
  ('BMW',          'Serie 2 Active Tourer', 'monovolume', 'premium'),
  ('BMW',          'Serie 2 Gran Coupe',    'coupe',      'premium'),
  ('BMW',          'Serie 4',       'coupe',      'premium'),
  ('BMW',          'Serie 5',       'berlina',    'premium'),
  ('BMW',          'X1',            'suv',        'premium'),
  ('BMW',          'X3',            'suv',        'premium'),
  ('BMW',          'X5',            'suv',        'luxo'),
  -- Mercedes-Benz
  ('Mercedes-Benz','Classe B',      'monovolume', 'premium'),
  ('Mercedes-Benz','Classe C',      'berlina',    'premium'),
  ('Mercedes-Benz','Classe E',      'berlina',    'luxo'),
  ('Mercedes-Benz','CLA',           'coupe',      'premium'),
  ('Mercedes-Benz','GLA',           'suv',        'premium'),
  ('Mercedes-Benz','GLC',           'suv',        'premium'),
  -- Audi
  ('Audi',         'A1',            'compacto',   'premium'),
  ('Audi',         'A3',            'compacto',   'premium'),
  ('Audi',         'A4',            'berlina',    'premium'),
  ('Audi',         'Q3',            'suv',        'premium'),
  ('Audi',         'Q5',            'suv',        'premium'),
  -- Volkswagen
  ('Volkswagen',   'T-Roc',         'suv',        'medio'),
  ('Volkswagen',   'T-Cross',       'suv',        'economico'),
  ('Volkswagen',   'Tiguan',        'suv',        'medio'),
  ('Volkswagen',   'Passat',        'berlina',    'medio'),
  ('Volkswagen',   'ID.3',          'compacto',   'medio'),
  -- Toyota
  ('Toyota',       'C-HR',          'suv',        'medio'),
  ('Toyota',       'Yaris Cross',   'suv',        'economico'),
  ('Toyota',       'RAV4',          'suv',        'medio'),
  -- Hyundai
  ('Hyundai',      'i20',           'compacto',   'economico'),
  ('Hyundai',      'i30',           'compacto',   'medio'),
  ('Hyundai',      'Kona',          'suv',        'economico'),
  ('Hyundai',      'Ioniq 5',       'suv',        'premium'),
  -- Kia
  ('Kia',          'Ceed',          'compacto',   'medio'),
  ('Kia',          'Niro',          'suv',        'medio'),
  ('Kia',          'EV6',           'suv',        'premium'),
  ('Kia',          'Rio',           'compacto',   'economico'),
  ('Kia',          'Picanto',       'compacto',   'economico'),
  -- Ford
  ('Ford',         'Fiesta',        'compacto',   'economico'),
  ('Ford',         'Puma',          'suv',        'medio'),
  ('Ford',         'Kuga',          'suv',        'medio'),
  -- Skoda
  ('Skoda',        'Fabia',         'compacto',   'economico'),
  ('Skoda',        'Kamiq',         'suv',        'economico'),
  ('Skoda',        'Karoq',         'suv',        'medio'),
  ('Skoda',        'Superb',        'berlina',    'medio'),
  -- SEAT
  ('SEAT',         'Ibiza',         'compacto',   'economico'),
  ('SEAT',         'Arona',         'suv',        'economico'),
  ('SEAT',         'Ateca',         'suv',        'medio'),
  -- Cupra
  ('Cupra',        'Formentor',     'suv',        'premium'),
  -- Opel
  ('Opel',         'Astra',         'compacto',   'medio'),
  ('Opel',         'Mokka',         'suv',        'economico'),
  -- Nissan
  ('Nissan',       'Juke',          'suv',        'economico'),
  ('Nissan',       'Micra',         'compacto',   'economico'),
  -- Fiat
  ('Fiat',         '500',           'compacto',   'economico'),
  ('Fiat',         'Tipo',          'compacto',   'economico'),
  -- Volvo
  ('Volvo',        'XC40',          'suv',        'premium'),
  ('Volvo',        'XC60',          'suv',        'premium'),
  -- Tesla
  ('Tesla',        'Model 3',       'berlina',    'premium'),
  ('Tesla',        'Model Y',       'suv',        'premium'),
  -- Dacia
  ('Dacia',        'Jogger',        'monovolume', 'economico'),
  -- Honda
  ('Honda',        'Civic',         'compacto',   'medio'),
  ('Honda',        'HR-V',          'suv',        'medio'),
  -- Mazda
  ('Mazda',        'CX-30',         'suv',        'medio'),
  ('Mazda',        'CX-5',          'suv',        'medio'),
  ('Mazda',        '3',             'compacto',   'medio'),
  -- Suzuki
  ('Suzuki',       'Swift',         'compacto',   'economico'),
  ('Suzuki',       'Vitara',        'suv',        'economico')
) AS v(brand, model, body, seg)
JOIN brands b ON LOWER(b.name) = LOWER(v.brand)
WHERE NOT EXISTS (
  SELECT 1 FROM vehicle_models vm2
  WHERE vm2.brand_id = b.id AND LOWER(vm2.name) = LOWER(v.model)
);


-- ═══════════════════════════════════════════════════════════
-- 4. ENGINES FOR NEW MODELS
--    Sources: manufacturer specs, TÜV 2024, ADAC 2024,
--    Spritmonitor.de (real consumption), Honest John
-- ═══════════════════════════════════════════════════════════

-- Helper: insert engine only if model exists and engine code not duplicate
-- Pattern: (brand, model, code, fuel, cc, hp, consumption, reliability, maintenance)

-- ── CITROEN C3 ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, consumption_mixed, reliability_score, maintenance_cost_year)
SELECT vm.id, v.code, v.fuel, v.cc, v.hp, v.cons, v.rel, v.maint
FROM (VALUES
  ('1.2 PureTech 83',  'gasolina', 1199,  83, 6.0, 7, 380),
  ('1.2 PureTech 110', 'gasolina', 1199, 110, 6.3, 6, 420),
  ('1.5 BlueHDi 100',  'diesel',   1499, 100, 4.5, 7, 440)
) AS v(code, fuel, cc, hp, cons, rel, maint)
CROSS JOIN (SELECT vm2.id FROM vehicle_models vm2 JOIN brands b ON b.id=vm2.brand_id WHERE LOWER(b.name)='citroen' AND LOWER(vm2.name)='c3') vm
WHERE NOT EXISTS (SELECT 1 FROM engines e2 WHERE e2.model_id=vm.id AND e2.code=v.code);

-- ── CITROEN C4 ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, consumption_mixed, reliability_score, maintenance_cost_year)
SELECT vm.id, v.code, v.fuel, v.cc, v.hp, v.cons, v.rel, v.maint
FROM (VALUES
  ('1.2 PureTech 130', 'gasolina', 1199, 130, 6.8, 6, 480),
  ('1.5 BlueHDi 130',  'diesel',   1499, 130, 5.2, 7, 500),
  ('e-C4 136',         'eletrico', NULL, 136, NULL, 8, 280)
) AS v(code, fuel, cc, hp, cons, rel, maint)
CROSS JOIN (SELECT vm2.id FROM vehicle_models vm2 JOIN brands b ON b.id=vm2.brand_id WHERE LOWER(b.name)='citroen' AND LOWER(vm2.name)='c4') vm
WHERE NOT EXISTS (SELECT 1 FROM engines e2 WHERE e2.model_id=vm.id AND e2.code=v.code);

-- ── CITROEN C5 AIRCROSS ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, consumption_mixed, reliability_score, maintenance_cost_year)
SELECT vm.id, v.code, v.fuel, v.cc, v.hp, v.cons, v.rel, v.maint
FROM (VALUES
  ('1.2 PureTech 130', 'gasolina', 1199, 130, 7.2, 6, 520),
  ('1.5 BlueHDi 130',  'diesel',   1499, 130, 5.5, 7, 550),
  ('1.6 Hybrid 225',   'hibrido',  1598, 225, 2.0, 7, 480)
) AS v(code, fuel, cc, hp, cons, rel, maint)
CROSS JOIN (SELECT vm2.id FROM vehicle_models vm2 JOIN brands b ON b.id=vm2.brand_id WHERE LOWER(b.name)='citroen' AND LOWER(vm2.name)='c5 aircross') vm
WHERE NOT EXISTS (SELECT 1 FROM engines e2 WHERE e2.model_id=vm.id AND e2.code=v.code);

-- ── RENAULT CAPTUR ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, consumption_mixed, reliability_score, maintenance_cost_year)
SELECT vm.id, v.code, v.fuel, v.cc, v.hp, v.cons, v.rel, v.maint
FROM (VALUES
  ('1.0 TCe 100',      'gasolina', 999, 100, 6.5, 7, 420),
  ('1.3 TCe 130',      'gasolina', 1333, 130, 6.8, 7, 450),
  ('1.5 dCi 95',       'diesel',   1461,  95, 4.8, 8, 460),
  ('1.6 E-Tech 145',   'hibrido',  1598, 145, 5.0, 8, 400)
) AS v(code, fuel, cc, hp, cons, rel, maint)
CROSS JOIN (SELECT vm2.id FROM vehicle_models vm2 JOIN brands b ON b.id=vm2.brand_id WHERE b.name='Renault' AND LOWER(vm2.name)='captur') vm
WHERE NOT EXISTS (SELECT 1 FROM engines e2 WHERE e2.model_id=vm.id AND e2.code=v.code);

-- ── RENAULT MEGANE ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, consumption_mixed, reliability_score, maintenance_cost_year)
SELECT vm.id, v.code, v.fuel, v.cc, v.hp, v.cons, v.rel, v.maint
FROM (VALUES
  ('1.3 TCe 140',      'gasolina', 1333, 140, 6.8, 7, 470),
  ('1.5 dCi 115',      'diesel',   1461, 115, 5.0, 8, 500),
  ('1.6 E-Tech 160',   'hibrido',  1598, 160, 4.8, 8, 420)
) AS v(code, fuel, cc, hp, cons, rel, maint)
CROSS JOIN (SELECT vm2.id FROM vehicle_models vm2 JOIN brands b ON b.id=vm2.brand_id WHERE b.name='Renault' AND LOWER(vm2.name)='megane') vm
WHERE NOT EXISTS (SELECT 1 FROM engines e2 WHERE e2.model_id=vm.id AND e2.code=v.code);

-- ── RENAULT ARKANA ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, consumption_mixed, reliability_score, maintenance_cost_year)
SELECT vm.id, v.code, v.fuel, v.cc, v.hp, v.cons, v.rel, v.maint
FROM (VALUES
  ('1.3 TCe 140',      'gasolina', 1333, 140, 7.0, 7, 460),
  ('1.6 E-Tech 145',   'hibrido',  1598, 145, 5.2, 8, 410)
) AS v(code, fuel, cc, hp, cons, rel, maint)
CROSS JOIN (SELECT vm2.id FROM vehicle_models vm2 JOIN brands b ON b.id=vm2.brand_id WHERE b.name='Renault' AND LOWER(vm2.name)='arkana') vm
WHERE NOT EXISTS (SELECT 1 FROM engines e2 WHERE e2.model_id=vm.id AND e2.code=v.code);

-- ── RENAULT KADJAR ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, consumption_mixed, reliability_score, maintenance_cost_year)
SELECT vm.id, v.code, v.fuel, v.cc, v.hp, v.cons, v.rel, v.maint
FROM (VALUES
  ('1.3 TCe 140',      'gasolina', 1333, 140, 7.2, 7, 480),
  ('1.5 dCi 115',      'diesel',   1461, 115, 5.2, 8, 510)
) AS v(code, fuel, cc, hp, cons, rel, maint)
CROSS JOIN (SELECT vm2.id FROM vehicle_models vm2 JOIN brands b ON b.id=vm2.brand_id WHERE b.name='Renault' AND LOWER(vm2.name)='kadjar') vm
WHERE NOT EXISTS (SELECT 1 FROM engines e2 WHERE e2.model_id=vm.id AND e2.code=v.code);

-- ── RENAULT SCENIC ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, consumption_mixed, reliability_score, maintenance_cost_year)
SELECT vm.id, v.code, v.fuel, v.cc, v.hp, v.cons, v.rel, v.maint
FROM (VALUES
  ('1.3 TCe 140',      'gasolina', 1333, 140, 7.0, 7, 490),
  ('1.5 dCi 120',      'diesel',   1461, 120, 5.2, 8, 520),
  ('1.6 E-Tech 160',   'hibrido',  1598, 160, 5.0, 8, 430)
) AS v(code, fuel, cc, hp, cons, rel, maint)
CROSS JOIN (SELECT vm2.id FROM vehicle_models vm2 JOIN brands b ON b.id=vm2.brand_id WHERE b.name='Renault' AND LOWER(vm2.name)='scenic') vm
WHERE NOT EXISTS (SELECT 1 FROM engines e2 WHERE e2.model_id=vm.id AND e2.code=v.code);

-- ── BMW SERIE 1 ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, consumption_mixed, reliability_score, maintenance_cost_year)
SELECT vm.id, v.code, v.fuel, v.cc, v.hp, v.cons, v.rel, v.maint
FROM (VALUES
  ('116d',   'diesel',   1995, 116, 5.0, 7, 700),
  ('118i',   'gasolina', 1499, 140, 6.5, 8, 720),
  ('120d',   'diesel',   1995, 190, 5.5, 7, 750),
  ('120i',   'gasolina', 1998, 184, 7.0, 8, 740)
) AS v(code, fuel, cc, hp, cons, rel, maint)
CROSS JOIN (SELECT vm2.id FROM vehicle_models vm2 JOIN brands b ON b.id=vm2.brand_id WHERE b.name='BMW' AND vm2.name='Serie 1') vm
WHERE NOT EXISTS (SELECT 1 FROM engines e2 WHERE e2.model_id=vm.id AND e2.code=v.code);

-- ── BMW SERIE 5 ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, consumption_mixed, reliability_score, maintenance_cost_year)
SELECT vm.id, v.code, v.fuel, v.cc, v.hp, v.cons, v.rel, v.maint
FROM (VALUES
  ('520d',   'diesel',   1995, 190, 5.8, 8, 900),
  ('530i',   'gasolina', 1998, 252, 7.5, 8, 950),
  ('530e',   'hibrido',  1998, 292, 2.5, 8, 850)
) AS v(code, fuel, cc, hp, cons, rel, maint)
CROSS JOIN (SELECT vm2.id FROM vehicle_models vm2 JOIN brands b ON b.id=vm2.brand_id WHERE b.name='BMW' AND vm2.name='Serie 5') vm
WHERE NOT EXISTS (SELECT 1 FROM engines e2 WHERE e2.model_id=vm.id AND e2.code=v.code);

-- ── BMW X1 ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, consumption_mixed, reliability_score, maintenance_cost_year)
SELECT vm.id, v.code, v.fuel, v.cc, v.hp, v.cons, v.rel, v.maint
FROM (VALUES
  ('sDrive18d', 'diesel',   1995, 150, 5.5, 7, 750),
  ('sDrive20i', 'gasolina', 1998, 192, 7.0, 8, 780),
  ('xDrive20d', 'diesel',   1995, 190, 5.8, 7, 800)
) AS v(code, fuel, cc, hp, cons, rel, maint)
CROSS JOIN (SELECT vm2.id FROM vehicle_models vm2 JOIN brands b ON b.id=vm2.brand_id WHERE b.name='BMW' AND vm2.name='X1') vm
WHERE NOT EXISTS (SELECT 1 FROM engines e2 WHERE e2.model_id=vm.id AND e2.code=v.code);

-- ── BMW X3 ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, consumption_mixed, reliability_score, maintenance_cost_year)
SELECT vm.id, v.code, v.fuel, v.cc, v.hp, v.cons, v.rel, v.maint
FROM (VALUES
  ('xDrive20d', 'diesel',   1995, 190, 6.2, 8, 850),
  ('xDrive30d', 'diesel',   2993, 265, 6.8, 8, 900),
  ('xDrive20i', 'gasolina', 1998, 184, 7.8, 8, 830)
) AS v(code, fuel, cc, hp, cons, rel, maint)
CROSS JOIN (SELECT vm2.id FROM vehicle_models vm2 JOIN brands b ON b.id=vm2.brand_id WHERE b.name='BMW' AND vm2.name='X3') vm
WHERE NOT EXISTS (SELECT 1 FROM engines e2 WHERE e2.model_id=vm.id AND e2.code=v.code);

-- ── MERCEDES CLASSE C ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, consumption_mixed, reliability_score, maintenance_cost_year)
SELECT vm.id, v.code, v.fuel, v.cc, v.hp, v.cons, v.rel, v.maint
FROM (VALUES
  ('C180',   'gasolina', 1595, 156, 7.0, 7, 780),
  ('C200',   'gasolina', 1991, 184, 7.2, 7, 800),
  ('C220d',  'diesel',   2143, 170, 5.5, 7, 820),
  ('C300e',  'hibrido',  1991, 320, 2.5, 7, 750)
) AS v(code, fuel, cc, hp, cons, rel, maint)
CROSS JOIN (SELECT vm2.id FROM vehicle_models vm2 JOIN brands b ON b.id=vm2.brand_id WHERE LOWER(b.name)='mercedes-benz' AND LOWER(vm2.name)='classe c') vm
WHERE NOT EXISTS (SELECT 1 FROM engines e2 WHERE e2.model_id=vm.id AND e2.code=v.code);

-- ── MERCEDES CLASSE E ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, consumption_mixed, reliability_score, maintenance_cost_year)
SELECT vm.id, v.code, v.fuel, v.cc, v.hp, v.cons, v.rel, v.maint
FROM (VALUES
  ('E200',   'gasolina', 1991, 184, 7.5, 7, 900),
  ('E220d',  'diesel',   1950, 194, 5.8, 7, 920),
  ('E300e',  'hibrido',  1991, 320, 2.5, 7, 850)
) AS v(code, fuel, cc, hp, cons, rel, maint)
CROSS JOIN (SELECT vm2.id FROM vehicle_models vm2 JOIN brands b ON b.id=vm2.brand_id WHERE LOWER(b.name)='mercedes-benz' AND LOWER(vm2.name)='classe e') vm
WHERE NOT EXISTS (SELECT 1 FROM engines e2 WHERE e2.model_id=vm.id AND e2.code=v.code);

-- ── MERCEDES CLA ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, consumption_mixed, reliability_score, maintenance_cost_year)
SELECT vm.id, v.code, v.fuel, v.cc, v.hp, v.cons, v.rel, v.maint
FROM (VALUES
  ('CLA180',  'gasolina', 1332, 136, 6.8, 7, 750),
  ('CLA200',  'gasolina', 1332, 163, 7.0, 7, 780),
  ('CLA200d', 'diesel',   1461, 116, 5.0, 7, 720)
) AS v(code, fuel, cc, hp, cons, rel, maint)
CROSS JOIN (SELECT vm2.id FROM vehicle_models vm2 JOIN brands b ON b.id=vm2.brand_id WHERE LOWER(b.name)='mercedes-benz' AND LOWER(vm2.name)='cla') vm
WHERE NOT EXISTS (SELECT 1 FROM engines e2 WHERE e2.model_id=vm.id AND e2.code=v.code);

-- ── MERCEDES GLA ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, consumption_mixed, reliability_score, maintenance_cost_year)
SELECT vm.id, v.code, v.fuel, v.cc, v.hp, v.cons, v.rel, v.maint
FROM (VALUES
  ('GLA180',  'gasolina', 1332, 136, 7.0, 7, 760),
  ('GLA200',  'gasolina', 1332, 163, 7.2, 7, 790),
  ('GLA200d', 'diesel',   1461, 116, 5.2, 7, 730)
) AS v(code, fuel, cc, hp, cons, rel, maint)
CROSS JOIN (SELECT vm2.id FROM vehicle_models vm2 JOIN brands b ON b.id=vm2.brand_id WHERE LOWER(b.name)='mercedes-benz' AND LOWER(vm2.name)='gla') vm
WHERE NOT EXISTS (SELECT 1 FROM engines e2 WHERE e2.model_id=vm.id AND e2.code=v.code);

-- ── MERCEDES GLC ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, consumption_mixed, reliability_score, maintenance_cost_year)
SELECT vm.id, v.code, v.fuel, v.cc, v.hp, v.cons, v.rel, v.maint
FROM (VALUES
  ('GLC200',  'gasolina', 1991, 197, 7.8, 7, 850),
  ('GLC220d', 'diesel',   1950, 194, 6.0, 7, 870),
  ('GLC300e', 'hibrido',  1991, 320, 2.5, 7, 800)
) AS v(code, fuel, cc, hp, cons, rel, maint)
CROSS JOIN (SELECT vm2.id FROM vehicle_models vm2 JOIN brands b ON b.id=vm2.brand_id WHERE LOWER(b.name)='mercedes-benz' AND LOWER(vm2.name)='glc') vm
WHERE NOT EXISTS (SELECT 1 FROM engines e2 WHERE e2.model_id=vm.id AND e2.code=v.code);

-- ── AUDI A1 ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, consumption_mixed, reliability_score, maintenance_cost_year)
SELECT vm.id, v.code, v.fuel, v.cc, v.hp, v.cons, v.rel, v.maint
FROM (VALUES
  ('1.0 TFSI',  'gasolina', 999,  95, 5.8, 7, 550),
  ('1.5 TFSI',  'gasolina', 1498, 150, 6.2, 8, 580),
  ('1.6 TDI',   'diesel',   1598,  90, 4.5, 7, 570)
) AS v(code, fuel, cc, hp, cons, rel, maint)
CROSS JOIN (SELECT vm2.id FROM vehicle_models vm2 JOIN brands b ON b.id=vm2.brand_id WHERE b.name='Audi' AND vm2.name='A1') vm
WHERE NOT EXISTS (SELECT 1 FROM engines e2 WHERE e2.model_id=vm.id AND e2.code=v.code);

-- ── AUDI A3 ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, consumption_mixed, reliability_score, maintenance_cost_year)
SELECT vm.id, v.code, v.fuel, v.cc, v.hp, v.cons, v.rel, v.maint
FROM (VALUES
  ('1.0 TFSI',      'gasolina', 999,  110, 6.0, 7, 560),
  ('1.5 TFSI',      'gasolina', 1498, 150, 6.5, 8, 600),
  ('2.0 TDI',       'diesel',   1968, 150, 5.5, 8, 650),
  ('1.4 TFSI e',    'hibrido',  1395, 204, 2.0, 7, 550)
) AS v(code, fuel, cc, hp, cons, rel, maint)
CROSS JOIN (SELECT vm2.id FROM vehicle_models vm2 JOIN brands b ON b.id=vm2.brand_id WHERE b.name='Audi' AND vm2.name='A3') vm
WHERE NOT EXISTS (SELECT 1 FROM engines e2 WHERE e2.model_id=vm.id AND e2.code=v.code);

-- ── AUDI A4 ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, consumption_mixed, reliability_score, maintenance_cost_year)
SELECT vm.id, v.code, v.fuel, v.cc, v.hp, v.cons, v.rel, v.maint
FROM (VALUES
  ('2.0 TFSI',  'gasolina', 1984, 190, 7.0, 8, 700),
  ('2.0 TDI',   'diesel',   1968, 150, 5.5, 8, 720),
  ('35 TFSI',   'gasolina', 1498, 150, 6.5, 8, 680)
) AS v(code, fuel, cc, hp, cons, rel, maint)
CROSS JOIN (SELECT vm2.id FROM vehicle_models vm2 JOIN brands b ON b.id=vm2.brand_id WHERE b.name='Audi' AND vm2.name='A4') vm
WHERE NOT EXISTS (SELECT 1 FROM engines e2 WHERE e2.model_id=vm.id AND e2.code=v.code);

-- ── AUDI Q3 ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, consumption_mixed, reliability_score, maintenance_cost_year)
SELECT vm.id, v.code, v.fuel, v.cc, v.hp, v.cons, v.rel, v.maint
FROM (VALUES
  ('35 TFSI',  'gasolina', 1498, 150, 6.8, 8, 650),
  ('35 TDI',   'diesel',   1968, 150, 5.8, 8, 680),
  ('1.4 TFSI', 'gasolina', 1395, 150, 6.5, 7, 630)
) AS v(code, fuel, cc, hp, cons, rel, maint)
CROSS JOIN (SELECT vm2.id FROM vehicle_models vm2 JOIN brands b ON b.id=vm2.brand_id WHERE b.name='Audi' AND vm2.name='Q3') vm
WHERE NOT EXISTS (SELECT 1 FROM engines e2 WHERE e2.model_id=vm.id AND e2.code=v.code);

-- ── AUDI Q5 ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, consumption_mixed, reliability_score, maintenance_cost_year)
SELECT vm.id, v.code, v.fuel, v.cc, v.hp, v.cons, v.rel, v.maint
FROM (VALUES
  ('2.0 TFSI',    'gasolina', 1984, 252, 7.8, 8, 780),
  ('2.0 TDI',     'diesel',   1968, 190, 6.2, 8, 800),
  ('55 TFSI e',   'hibrido',  1984, 367, 2.5, 7, 720)
) AS v(code, fuel, cc, hp, cons, rel, maint)
CROSS JOIN (SELECT vm2.id FROM vehicle_models vm2 JOIN brands b ON b.id=vm2.brand_id WHERE b.name='Audi' AND vm2.name='Q5') vm
WHERE NOT EXISTS (SELECT 1 FROM engines e2 WHERE e2.model_id=vm.id AND e2.code=v.code);

-- ── VW T-ROC ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, consumption_mixed, reliability_score, maintenance_cost_year)
SELECT vm.id, v.code, v.fuel, v.cc, v.hp, v.cons, v.rel, v.maint
FROM (VALUES
  ('1.0 TSI',  'gasolina', 999,  110, 6.5, 7, 500),
  ('1.5 TSI',  'gasolina', 1498, 150, 6.8, 8, 540),
  ('2.0 TDI',  'diesel',   1968, 150, 5.8, 8, 580)
) AS v(code, fuel, cc, hp, cons, rel, maint)
CROSS JOIN (SELECT vm2.id FROM vehicle_models vm2 JOIN brands b ON b.id=vm2.brand_id WHERE b.name='Volkswagen' AND vm2.name='T-Roc') vm
WHERE NOT EXISTS (SELECT 1 FROM engines e2 WHERE e2.model_id=vm.id AND e2.code=v.code);

-- ── VW T-CROSS ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, consumption_mixed, reliability_score, maintenance_cost_year)
SELECT vm.id, v.code, v.fuel, v.cc, v.hp, v.cons, v.rel, v.maint
FROM (VALUES
  ('1.0 TSI 95',  'gasolina', 999,  95, 6.2, 7, 470),
  ('1.0 TSI 110', 'gasolina', 999, 110, 6.3, 7, 490)
) AS v(code, fuel, cc, hp, cons, rel, maint)
CROSS JOIN (SELECT vm2.id FROM vehicle_models vm2 JOIN brands b ON b.id=vm2.brand_id WHERE b.name='Volkswagen' AND vm2.name='T-Cross') vm
WHERE NOT EXISTS (SELECT 1 FROM engines e2 WHERE e2.model_id=vm.id AND e2.code=v.code);

-- ── VW TIGUAN ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, consumption_mixed, reliability_score, maintenance_cost_year)
SELECT vm.id, v.code, v.fuel, v.cc, v.hp, v.cons, v.rel, v.maint
FROM (VALUES
  ('1.5 TSI',      'gasolina', 1498, 150, 7.0, 8, 580),
  ('2.0 TDI',      'diesel',   1968, 150, 6.2, 8, 620),
  ('1.4 eHybrid',  'hibrido',  1395, 245, 2.0, 7, 530)
) AS v(code, fuel, cc, hp, cons, rel, maint)
CROSS JOIN (SELECT vm2.id FROM vehicle_models vm2 JOIN brands b ON b.id=vm2.brand_id WHERE b.name='Volkswagen' AND vm2.name='Tiguan') vm
WHERE NOT EXISTS (SELECT 1 FROM engines e2 WHERE e2.model_id=vm.id AND e2.code=v.code);

-- ── VW PASSAT ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, consumption_mixed, reliability_score, maintenance_cost_year)
SELECT vm.id, v.code, v.fuel, v.cc, v.hp, v.cons, v.rel, v.maint
FROM (VALUES
  ('1.5 TSI',   'gasolina', 1498, 150, 6.8, 8, 580),
  ('2.0 TDI',   'diesel',   1968, 150, 5.8, 8, 620),
  ('1.4 GTE',   'hibrido',  1395, 218, 2.0, 7, 540)
) AS v(code, fuel, cc, hp, cons, rel, maint)
CROSS JOIN (SELECT vm2.id FROM vehicle_models vm2 JOIN brands b ON b.id=vm2.brand_id WHERE b.name='Volkswagen' AND vm2.name='Passat') vm
WHERE NOT EXISTS (SELECT 1 FROM engines e2 WHERE e2.model_id=vm.id AND e2.code=v.code);

-- ── VW ID.3 ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, consumption_mixed, reliability_score, maintenance_cost_year)
SELECT vm.id, v.code, v.fuel, v.cc, v.hp, v.cons, v.rel, v.maint
FROM (VALUES
  ('Pro 58kWh',    'eletrico', NULL, 204, NULL, 7, 280),
  ('Pro S 77kWh',  'eletrico', NULL, 204, NULL, 7, 280)
) AS v(code, fuel, cc, hp, cons, rel, maint)
CROSS JOIN (SELECT vm2.id FROM vehicle_models vm2 JOIN brands b ON b.id=vm2.brand_id WHERE b.name='Volkswagen' AND vm2.name='ID.3') vm
WHERE NOT EXISTS (SELECT 1 FROM engines e2 WHERE e2.model_id=vm.id AND e2.code=v.code);

-- ── TOYOTA C-HR ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, consumption_mixed, reliability_score, maintenance_cost_year)
SELECT vm.id, v.code, v.fuel, v.cc, v.hp, v.cons, v.rel, v.maint
FROM (VALUES
  ('1.2 Turbo',   'gasolina', 1197, 116, 7.0, 8, 450),
  ('1.8 Hybrid',  'hibrido',  1798, 122, 4.8, 10, 350),
  ('2.0 Hybrid',  'hibrido',  1987, 184, 5.2, 9, 380)
) AS v(code, fuel, cc, hp, cons, rel, maint)
CROSS JOIN (SELECT vm2.id FROM vehicle_models vm2 JOIN brands b ON b.id=vm2.brand_id WHERE b.name='Toyota' AND vm2.name='C-HR') vm
WHERE NOT EXISTS (SELECT 1 FROM engines e2 WHERE e2.model_id=vm.id AND e2.code=v.code);

-- ── TOYOTA YARIS CROSS ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, consumption_mixed, reliability_score, maintenance_cost_year)
SELECT vm.id, v.code, v.fuel, v.cc, v.hp, v.cons, v.rel, v.maint
FROM (VALUES
  ('1.5 Hybrid', 'hibrido', 1490, 116, 4.4, 10, 300)
) AS v(code, fuel, cc, hp, cons, rel, maint)
CROSS JOIN (SELECT vm2.id FROM vehicle_models vm2 JOIN brands b ON b.id=vm2.brand_id WHERE b.name='Toyota' AND vm2.name='Yaris Cross') vm
WHERE NOT EXISTS (SELECT 1 FROM engines e2 WHERE e2.model_id=vm.id AND e2.code=v.code);

-- ── TOYOTA RAV4 ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, consumption_mixed, reliability_score, maintenance_cost_year)
SELECT vm.id, v.code, v.fuel, v.cc, v.hp, v.cons, v.rel, v.maint
FROM (VALUES
  ('2.5 Hybrid',  'hibrido', 2487, 218, 5.6, 9, 400),
  ('2.5 PHEV',    'hibrido', 2487, 306, 1.5, 9, 420)
) AS v(code, fuel, cc, hp, cons, rel, maint)
CROSS JOIN (SELECT vm2.id FROM vehicle_models vm2 JOIN brands b ON b.id=vm2.brand_id WHERE b.name='Toyota' AND vm2.name='RAV4') vm
WHERE NOT EXISTS (SELECT 1 FROM engines e2 WHERE e2.model_id=vm.id AND e2.code=v.code);

-- ── HYUNDAI i20 ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, consumption_mixed, reliability_score, maintenance_cost_year)
SELECT vm.id, v.code, v.fuel, v.cc, v.hp, v.cons, v.rel, v.maint
FROM (VALUES
  ('1.2 MPI',      'gasolina', 1197, 84, 6.0, 8, 350),
  ('1.0 T-GDi',    'gasolina', 998, 100, 5.8, 8, 380),
  ('1.0 T-GDi 48V','gasolina', 998, 100, 5.5, 8, 390)
) AS v(code, fuel, cc, hp, cons, rel, maint)
CROSS JOIN (SELECT vm2.id FROM vehicle_models vm2 JOIN brands b ON b.id=vm2.brand_id WHERE b.name='Hyundai' AND vm2.name='i20') vm
WHERE NOT EXISTS (SELECT 1 FROM engines e2 WHERE e2.model_id=vm.id AND e2.code=v.code);

-- ── HYUNDAI i30 ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, consumption_mixed, reliability_score, maintenance_cost_year)
SELECT vm.id, v.code, v.fuel, v.cc, v.hp, v.cons, v.rel, v.maint
FROM (VALUES
  ('1.0 T-GDi',  'gasolina', 998,  120, 6.2, 8, 430),
  ('1.5 T-GDi',  'gasolina', 1482, 160, 6.8, 8, 460),
  ('1.6 CRDi',   'diesel',   1598, 136, 5.2, 8, 480)
) AS v(code, fuel, cc, hp, cons, rel, maint)
CROSS JOIN (SELECT vm2.id FROM vehicle_models vm2 JOIN brands b ON b.id=vm2.brand_id WHERE b.name='Hyundai' AND vm2.name='i30') vm
WHERE NOT EXISTS (SELECT 1 FROM engines e2 WHERE e2.model_id=vm.id AND e2.code=v.code);

-- ── HYUNDAI KONA ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, consumption_mixed, reliability_score, maintenance_cost_year)
SELECT vm.id, v.code, v.fuel, v.cc, v.hp, v.cons, v.rel, v.maint
FROM (VALUES
  ('1.0 T-GDi',       'gasolina', 998,  120, 6.5, 8, 420),
  ('1.6 GDi Hybrid',  'hibrido',  1580, 141, 4.8, 9, 380),
  ('Kona EV 64kWh',   'eletrico', NULL, 204, NULL, 8, 260)
) AS v(code, fuel, cc, hp, cons, rel, maint)
CROSS JOIN (SELECT vm2.id FROM vehicle_models vm2 JOIN brands b ON b.id=vm2.brand_id WHERE b.name='Hyundai' AND vm2.name='Kona') vm
WHERE NOT EXISTS (SELECT 1 FROM engines e2 WHERE e2.model_id=vm.id AND e2.code=v.code);

-- ── HYUNDAI IONIQ 5 ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, consumption_mixed, reliability_score, maintenance_cost_year)
SELECT vm.id, v.code, v.fuel, v.cc, v.hp, v.cons, v.rel, v.maint
FROM (VALUES
  ('Standard RWD 58kWh', 'eletrico', NULL, 170, NULL, 8, 280),
  ('Long Range RWD 77kWh','eletrico', NULL, 229, NULL, 8, 280),
  ('Long Range AWD',      'eletrico', NULL, 325, NULL, 8, 300)
) AS v(code, fuel, cc, hp, cons, rel, maint)
CROSS JOIN (SELECT vm2.id FROM vehicle_models vm2 JOIN brands b ON b.id=vm2.brand_id WHERE b.name='Hyundai' AND vm2.name='Ioniq 5') vm
WHERE NOT EXISTS (SELECT 1 FROM engines e2 WHERE e2.model_id=vm.id AND e2.code=v.code);

-- ── KIA CEED ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, consumption_mixed, reliability_score, maintenance_cost_year)
SELECT vm.id, v.code, v.fuel, v.cc, v.hp, v.cons, v.rel, v.maint
FROM (VALUES
  ('1.0 T-GDi',  'gasolina', 998,  120, 6.2, 8, 430),
  ('1.5 T-GDi',  'gasolina', 1482, 160, 6.8, 8, 460),
  ('1.6 CRDi',   'diesel',   1598, 136, 5.2, 8, 480)
) AS v(code, fuel, cc, hp, cons, rel, maint)
CROSS JOIN (SELECT vm2.id FROM vehicle_models vm2 JOIN brands b ON b.id=vm2.brand_id WHERE b.name='Kia' AND vm2.name='Ceed') vm
WHERE NOT EXISTS (SELECT 1 FROM engines e2 WHERE e2.model_id=vm.id AND e2.code=v.code);

-- ── KIA NIRO ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, consumption_mixed, reliability_score, maintenance_cost_year)
SELECT vm.id, v.code, v.fuel, v.cc, v.hp, v.cons, v.rel, v.maint
FROM (VALUES
  ('1.6 GDi Hybrid', 'hibrido',  1580, 141, 4.8, 9, 380),
  ('1.6 PHEV',       'hibrido',  1580, 183, 1.5, 9, 400),
  ('Niro EV 64kWh',  'eletrico', NULL, 204, NULL, 8, 270)
) AS v(code, fuel, cc, hp, cons, rel, maint)
CROSS JOIN (SELECT vm2.id FROM vehicle_models vm2 JOIN brands b ON b.id=vm2.brand_id WHERE b.name='Kia' AND vm2.name='Niro') vm
WHERE NOT EXISTS (SELECT 1 FROM engines e2 WHERE e2.model_id=vm.id AND e2.code=v.code);

-- ── KIA EV6 ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, consumption_mixed, reliability_score, maintenance_cost_year)
SELECT vm.id, v.code, v.fuel, v.cc, v.hp, v.cons, v.rel, v.maint
FROM (VALUES
  ('Standard RWD',   'eletrico', NULL, 170, NULL, 8, 300),
  ('Long Range RWD', 'eletrico', NULL, 229, NULL, 8, 300),
  ('GT AWD',         'eletrico', NULL, 585, NULL, 8, 350)
) AS v(code, fuel, cc, hp, cons, rel, maint)
CROSS JOIN (SELECT vm2.id FROM vehicle_models vm2 JOIN brands b ON b.id=vm2.brand_id WHERE b.name='Kia' AND vm2.name='EV6') vm
WHERE NOT EXISTS (SELECT 1 FROM engines e2 WHERE e2.model_id=vm.id AND e2.code=v.code);

-- ── KIA RIO ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, consumption_mixed, reliability_score, maintenance_cost_year)
SELECT vm.id, v.code, v.fuel, v.cc, v.hp, v.cons, v.rel, v.maint
FROM (VALUES
  ('1.0 T-GDi', 'gasolina', 998, 100, 5.8, 8, 370),
  ('1.2 MPI',   'gasolina', 1248, 84, 6.0, 8, 340)
) AS v(code, fuel, cc, hp, cons, rel, maint)
CROSS JOIN (SELECT vm2.id FROM vehicle_models vm2 JOIN brands b ON b.id=vm2.brand_id WHERE b.name='Kia' AND vm2.name='Rio') vm
WHERE NOT EXISTS (SELECT 1 FROM engines e2 WHERE e2.model_id=vm.id AND e2.code=v.code);

-- ── KIA PICANTO ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, consumption_mixed, reliability_score, maintenance_cost_year)
SELECT vm.id, v.code, v.fuel, v.cc, v.hp, v.cons, v.rel, v.maint
FROM (VALUES
  ('1.0 MPI',   'gasolina', 998, 67, 5.5, 9, 280),
  ('1.0 T-GDi', 'gasolina', 998, 100, 5.5, 8, 310)
) AS v(code, fuel, cc, hp, cons, rel, maint)
CROSS JOIN (SELECT vm2.id FROM vehicle_models vm2 JOIN brands b ON b.id=vm2.brand_id WHERE b.name='Kia' AND vm2.name='Picanto') vm
WHERE NOT EXISTS (SELECT 1 FROM engines e2 WHERE e2.model_id=vm.id AND e2.code=v.code);

-- ── FORD FIESTA ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, consumption_mixed, reliability_score, maintenance_cost_year)
SELECT vm.id, v.code, v.fuel, v.cc, v.hp, v.cons, v.rel, v.maint
FROM (VALUES
  ('1.0 EcoBoost 100', 'gasolina', 999, 100, 6.0, 7, 420),
  ('1.0 EcoBoost 125', 'gasolina', 999, 125, 6.2, 7, 440),
  ('1.5 EcoBlue',      'diesel',   1499, 85, 4.5, 7, 460)
) AS v(code, fuel, cc, hp, cons, rel, maint)
CROSS JOIN (SELECT vm2.id FROM vehicle_models vm2 JOIN brands b ON b.id=vm2.brand_id WHERE b.name='Ford' AND vm2.name='Fiesta') vm
WHERE NOT EXISTS (SELECT 1 FROM engines e2 WHERE e2.model_id=vm.id AND e2.code=v.code);

-- ── FORD PUMA ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, consumption_mixed, reliability_score, maintenance_cost_year)
SELECT vm.id, v.code, v.fuel, v.cc, v.hp, v.cons, v.rel, v.maint
FROM (VALUES
  ('1.0 EcoBoost 125',      'gasolina', 999, 125, 6.5, 7, 470),
  ('1.0 EcoBoost mHEV 125', 'gasolina', 999, 125, 6.0, 7, 480),
  ('1.0 EcoBoost mHEV 155', 'gasolina', 999, 155, 6.2, 7, 500)
) AS v(code, fuel, cc, hp, cons, rel, maint)
CROSS JOIN (SELECT vm2.id FROM vehicle_models vm2 JOIN brands b ON b.id=vm2.brand_id WHERE b.name='Ford' AND vm2.name='Puma') vm
WHERE NOT EXISTS (SELECT 1 FROM engines e2 WHERE e2.model_id=vm.id AND e2.code=v.code);

-- ── FORD KUGA ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, consumption_mixed, reliability_score, maintenance_cost_year)
SELECT vm.id, v.code, v.fuel, v.cc, v.hp, v.cons, v.rel, v.maint
FROM (VALUES
  ('1.5 EcoBoost',  'gasolina', 1498, 150, 7.5, 7, 530),
  ('2.5 PHEV',      'hibrido',  2488, 225, 1.5, 7, 500),
  ('1.5 EcoBlue',   'diesel',   1499, 120, 5.5, 7, 560)
) AS v(code, fuel, cc, hp, cons, rel, maint)
CROSS JOIN (SELECT vm2.id FROM vehicle_models vm2 JOIN brands b ON b.id=vm2.brand_id WHERE b.name='Ford' AND vm2.name='Kuga') vm
WHERE NOT EXISTS (SELECT 1 FROM engines e2 WHERE e2.model_id=vm.id AND e2.code=v.code);

-- ── SKODA FABIA ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, consumption_mixed, reliability_score, maintenance_cost_year)
SELECT vm.id, v.code, v.fuel, v.cc, v.hp, v.cons, v.rel, v.maint
FROM (VALUES
  ('1.0 MPI',   'gasolina', 999,  80, 5.8, 9, 360),
  ('1.0 TSI',   'gasolina', 999, 110, 5.8, 7, 400)
) AS v(code, fuel, cc, hp, cons, rel, maint)
CROSS JOIN (SELECT vm2.id FROM vehicle_models vm2 JOIN brands b ON b.id=vm2.brand_id WHERE b.name='Skoda' AND vm2.name='Fabia') vm
WHERE NOT EXISTS (SELECT 1 FROM engines e2 WHERE e2.model_id=vm.id AND e2.code=v.code);

-- ── SKODA KAMIQ ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, consumption_mixed, reliability_score, maintenance_cost_year)
SELECT vm.id, v.code, v.fuel, v.cc, v.hp, v.cons, v.rel, v.maint
FROM (VALUES
  ('1.0 TSI 95',  'gasolina', 999,  95, 6.0, 7, 440),
  ('1.0 TSI 110', 'gasolina', 999, 110, 6.2, 7, 460),
  ('1.5 TSI',     'gasolina', 1498, 150, 6.5, 8, 490)
) AS v(code, fuel, cc, hp, cons, rel, maint)
CROSS JOIN (SELECT vm2.id FROM vehicle_models vm2 JOIN brands b ON b.id=vm2.brand_id WHERE b.name='Skoda' AND vm2.name='Kamiq') vm
WHERE NOT EXISTS (SELECT 1 FROM engines e2 WHERE e2.model_id=vm.id AND e2.code=v.code);

-- ── SKODA KAROQ ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, consumption_mixed, reliability_score, maintenance_cost_year)
SELECT vm.id, v.code, v.fuel, v.cc, v.hp, v.cons, v.rel, v.maint
FROM (VALUES
  ('1.0 TSI',  'gasolina', 999,  110, 6.5, 7, 470),
  ('1.5 TSI',  'gasolina', 1498, 150, 6.8, 8, 510),
  ('2.0 TDI',  'diesel',   1968, 150, 5.8, 8, 550)
) AS v(code, fuel, cc, hp, cons, rel, maint)
CROSS JOIN (SELECT vm2.id FROM vehicle_models vm2 JOIN brands b ON b.id=vm2.brand_id WHERE b.name='Skoda' AND vm2.name='Karoq') vm
WHERE NOT EXISTS (SELECT 1 FROM engines e2 WHERE e2.model_id=vm.id AND e2.code=v.code);

-- ── SKODA SUPERB ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, consumption_mixed, reliability_score, maintenance_cost_year)
SELECT vm.id, v.code, v.fuel, v.cc, v.hp, v.cons, v.rel, v.maint
FROM (VALUES
  ('1.5 TSI',  'gasolina', 1498, 150, 6.8, 8, 530),
  ('2.0 TDI',  'diesel',   1968, 150, 5.5, 8, 580)
) AS v(code, fuel, cc, hp, cons, rel, maint)
CROSS JOIN (SELECT vm2.id FROM vehicle_models vm2 JOIN brands b ON b.id=vm2.brand_id WHERE b.name='Skoda' AND vm2.name='Superb') vm
WHERE NOT EXISTS (SELECT 1 FROM engines e2 WHERE e2.model_id=vm.id AND e2.code=v.code);

-- ── SEAT IBIZA ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, consumption_mixed, reliability_score, maintenance_cost_year)
SELECT vm.id, v.code, v.fuel, v.cc, v.hp, v.cons, v.rel, v.maint
FROM (VALUES
  ('1.0 TSI 95',  'gasolina', 999,  95, 5.8, 7, 400),
  ('1.0 TSI 110', 'gasolina', 999, 110, 6.0, 7, 420)
) AS v(code, fuel, cc, hp, cons, rel, maint)
CROSS JOIN (SELECT vm2.id FROM vehicle_models vm2 JOIN brands b ON b.id=vm2.brand_id WHERE b.name='SEAT' AND vm2.name='Ibiza') vm
WHERE NOT EXISTS (SELECT 1 FROM engines e2 WHERE e2.model_id=vm.id AND e2.code=v.code);

-- ── SEAT ARONA ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, consumption_mixed, reliability_score, maintenance_cost_year)
SELECT vm.id, v.code, v.fuel, v.cc, v.hp, v.cons, v.rel, v.maint
FROM (VALUES
  ('1.0 TSI 95',  'gasolina', 999,  95, 6.0, 7, 410),
  ('1.0 TSI 110', 'gasolina', 999, 110, 6.2, 7, 430)
) AS v(code, fuel, cc, hp, cons, rel, maint)
CROSS JOIN (SELECT vm2.id FROM vehicle_models vm2 JOIN brands b ON b.id=vm2.brand_id WHERE b.name='SEAT' AND vm2.name='Arona') vm
WHERE NOT EXISTS (SELECT 1 FROM engines e2 WHERE e2.model_id=vm.id AND e2.code=v.code);

-- ── SEAT ATECA ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, consumption_mixed, reliability_score, maintenance_cost_year)
SELECT vm.id, v.code, v.fuel, v.cc, v.hp, v.cons, v.rel, v.maint
FROM (VALUES
  ('1.0 TSI',  'gasolina', 999,  110, 6.5, 7, 470),
  ('1.5 TSI',  'gasolina', 1498, 150, 6.8, 8, 510),
  ('2.0 TDI',  'diesel',   1968, 150, 5.8, 8, 560)
) AS v(code, fuel, cc, hp, cons, rel, maint)
CROSS JOIN (SELECT vm2.id FROM vehicle_models vm2 JOIN brands b ON b.id=vm2.brand_id WHERE b.name='SEAT' AND vm2.name='Ateca') vm
WHERE NOT EXISTS (SELECT 1 FROM engines e2 WHERE e2.model_id=vm.id AND e2.code=v.code);

-- ── CUPRA FORMENTOR ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, consumption_mixed, reliability_score, maintenance_cost_year)
SELECT vm.id, v.code, v.fuel, v.cc, v.hp, v.cons, v.rel, v.maint
FROM (VALUES
  ('1.5 TSI 150',  'gasolina', 1498, 150, 6.8, 8, 540),
  ('2.0 TSI 310',  'gasolina', 1984, 310, 8.5, 7, 620),
  ('2.0 TDI 150',  'diesel',   1968, 150, 5.8, 8, 580)
) AS v(code, fuel, cc, hp, cons, rel, maint)
CROSS JOIN (SELECT vm2.id FROM vehicle_models vm2 JOIN brands b ON b.id=vm2.brand_id WHERE b.name='Cupra' AND vm2.name='Formentor') vm
WHERE NOT EXISTS (SELECT 1 FROM engines e2 WHERE e2.model_id=vm.id AND e2.code=v.code);

-- ── OPEL ASTRA ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, consumption_mixed, reliability_score, maintenance_cost_year)
SELECT vm.id, v.code, v.fuel, v.cc, v.hp, v.cons, v.rel, v.maint
FROM (VALUES
  ('1.2 Turbo 110', 'gasolina', 1199, 110, 6.5, 6, 460),
  ('1.2 Turbo 130', 'gasolina', 1199, 130, 6.8, 6, 480),
  ('1.5 Diesel 105','diesel',   1499, 105, 5.0, 7, 500),
  ('1.6 Turbo 180', 'gasolina', 1598, 180, 7.2, 7, 520)
) AS v(code, fuel, cc, hp, cons, rel, maint)
CROSS JOIN (SELECT vm2.id FROM vehicle_models vm2 JOIN brands b ON b.id=vm2.brand_id WHERE b.name='Opel' AND vm2.name='Astra') vm
WHERE NOT EXISTS (SELECT 1 FROM engines e2 WHERE e2.model_id=vm.id AND e2.code=v.code);

-- ── OPEL MOKKA ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, consumption_mixed, reliability_score, maintenance_cost_year)
SELECT vm.id, v.code, v.fuel, v.cc, v.hp, v.cons, v.rel, v.maint
FROM (VALUES
  ('1.2 Turbo 100', 'gasolina', 1199, 100, 6.5, 6, 440),
  ('1.2 Turbo 130', 'gasolina', 1199, 130, 6.8, 6, 470),
  ('1.5 Diesel 110','diesel',   1499, 110, 5.0, 7, 490),
  ('Mokka-e 136',   'eletrico', NULL, 136, NULL, 8, 270)
) AS v(code, fuel, cc, hp, cons, rel, maint)
CROSS JOIN (SELECT vm2.id FROM vehicle_models vm2 JOIN brands b ON b.id=vm2.brand_id WHERE b.name='Opel' AND vm2.name='Mokka') vm
WHERE NOT EXISTS (SELECT 1 FROM engines e2 WHERE e2.model_id=vm.id AND e2.code=v.code);

-- ── NISSAN JUKE ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, consumption_mixed, reliability_score, maintenance_cost_year)
SELECT vm.id, v.code, v.fuel, v.cc, v.hp, v.cons, v.rel, v.maint
FROM (VALUES
  ('1.0 DIG-T',     'gasolina', 999,  114, 6.5, 7, 470),
  ('1.6 DIG-T',     'gasolina', 1618, 190, 7.2, 6, 520),
  ('1.6 Hybrid 143','hibrido',  1598, 143, 5.2, 8, 430)
) AS v(code, fuel, cc, hp, cons, rel, maint)
CROSS JOIN (SELECT vm2.id FROM vehicle_models vm2 JOIN brands b ON b.id=vm2.brand_id WHERE b.name='Nissan' AND vm2.name='Juke') vm
WHERE NOT EXISTS (SELECT 1 FROM engines e2 WHERE e2.model_id=vm.id AND e2.code=v.code);

-- ── NISSAN MICRA ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, consumption_mixed, reliability_score, maintenance_cost_year)
SELECT vm.id, v.code, v.fuel, v.cc, v.hp, v.cons, v.rel, v.maint
FROM (VALUES
  ('1.0 IG-T 92',  'gasolina', 999, 92, 5.8, 7, 390),
  ('0.9 IG-T',     'gasolina', 898, 90, 5.5, 7, 380)
) AS v(code, fuel, cc, hp, cons, rel, maint)
CROSS JOIN (SELECT vm2.id FROM vehicle_models vm2 JOIN brands b ON b.id=vm2.brand_id WHERE b.name='Nissan' AND vm2.name='Micra') vm
WHERE NOT EXISTS (SELECT 1 FROM engines e2 WHERE e2.model_id=vm.id AND e2.code=v.code);

-- ── FIAT 500 ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, consumption_mixed, reliability_score, maintenance_cost_year)
SELECT vm.id, v.code, v.fuel, v.cc, v.hp, v.cons, v.rel, v.maint
FROM (VALUES
  ('1.2 69cv',      'gasolina', 1242, 69, 5.8, 7, 340),
  ('0.9 TwinAir',   'gasolina', 875,  85, 5.5, 6, 380),
  ('500e 118cv',     'eletrico', NULL, 118, NULL, 8, 230)
) AS v(code, fuel, cc, hp, cons, rel, maint)
CROSS JOIN (SELECT vm2.id FROM vehicle_models vm2 JOIN brands b ON b.id=vm2.brand_id WHERE b.name='Fiat' AND vm2.name='500') vm
WHERE NOT EXISTS (SELECT 1 FROM engines e2 WHERE e2.model_id=vm.id AND e2.code=v.code);

-- ── FIAT TIPO ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, consumption_mixed, reliability_score, maintenance_cost_year)
SELECT vm.id, v.code, v.fuel, v.cc, v.hp, v.cons, v.rel, v.maint
FROM (VALUES
  ('1.4 95cv',       'gasolina', 1368, 95, 6.8, 7, 380),
  ('1.6 Multijet',   'diesel',   1598, 120, 5.0, 7, 420),
  ('1.0 FireFly 100','gasolina', 999,  100, 6.2, 7, 400)
) AS v(code, fuel, cc, hp, cons, rel, maint)
CROSS JOIN (SELECT vm2.id FROM vehicle_models vm2 JOIN brands b ON b.id=vm2.brand_id WHERE b.name='Fiat' AND vm2.name='Tipo') vm
WHERE NOT EXISTS (SELECT 1 FROM engines e2 WHERE e2.model_id=vm.id AND e2.code=v.code);

-- ── VOLVO XC40 ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, consumption_mixed, reliability_score, maintenance_cost_year)
SELECT vm.id, v.code, v.fuel, v.cc, v.hp, v.cons, v.rel, v.maint
FROM (VALUES
  ('T2 129cv',        'gasolina', 1477, 129, 7.0, 8, 600),
  ('D3 163cv',        'diesel',   1969, 163, 5.8, 7, 650),
  ('T5 PHEV 262cv',   'hibrido',  1477, 262, 2.2, 7, 550),
  ('Recharge Pure EV','eletrico', NULL, 231, NULL, 8, 350)
) AS v(code, fuel, cc, hp, cons, rel, maint)
CROSS JOIN (SELECT vm2.id FROM vehicle_models vm2 JOIN brands b ON b.id=vm2.brand_id WHERE b.name='Volvo' AND vm2.name='XC40') vm
WHERE NOT EXISTS (SELECT 1 FROM engines e2 WHERE e2.model_id=vm.id AND e2.code=v.code);

-- ── VOLVO XC60 ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, consumption_mixed, reliability_score, maintenance_cost_year)
SELECT vm.id, v.code, v.fuel, v.cc, v.hp, v.cons, v.rel, v.maint
FROM (VALUES
  ('D4 190cv',     'diesel',  1969, 190, 6.0, 7, 700),
  ('D5 235cv',     'diesel',  2400, 235, 6.8, 7, 750),
  ('T8 PHEV 390cv','hibrido', 1969, 390, 2.5, 7, 650)
) AS v(code, fuel, cc, hp, cons, rel, maint)
CROSS JOIN (SELECT vm2.id FROM vehicle_models vm2 JOIN brands b ON b.id=vm2.brand_id WHERE b.name='Volvo' AND vm2.name='XC60') vm
WHERE NOT EXISTS (SELECT 1 FROM engines e2 WHERE e2.model_id=vm.id AND e2.code=v.code);

-- ── TESLA MODEL 3 ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, consumption_mixed, reliability_score, maintenance_cost_year)
SELECT vm.id, v.code, v.fuel, v.cc, v.hp, v.cons, v.rel, v.maint
FROM (VALUES
  ('Standard Range Plus', 'eletrico', NULL, 283, NULL, 7, 250),
  ('Long Range',          'eletrico', NULL, 351, NULL, 7, 250),
  ('Performance',         'eletrico', NULL, 510, NULL, 7, 280)
) AS v(code, fuel, cc, hp, cons, rel, maint)
CROSS JOIN (SELECT vm2.id FROM vehicle_models vm2 JOIN brands b ON b.id=vm2.brand_id WHERE b.name='Tesla' AND vm2.name='Model 3') vm
WHERE NOT EXISTS (SELECT 1 FROM engines e2 WHERE e2.model_id=vm.id AND e2.code=v.code);

-- ── TESLA MODEL Y ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, consumption_mixed, reliability_score, maintenance_cost_year)
SELECT vm.id, v.code, v.fuel, v.cc, v.hp, v.cons, v.rel, v.maint
FROM (VALUES
  ('Long Range',  'eletrico', NULL, 351, NULL, 7, 260),
  ('Performance', 'eletrico', NULL, 510, NULL, 7, 290)
) AS v(code, fuel, cc, hp, cons, rel, maint)
CROSS JOIN (SELECT vm2.id FROM vehicle_models vm2 JOIN brands b ON b.id=vm2.brand_id WHERE b.name='Tesla' AND vm2.name='Model Y') vm
WHERE NOT EXISTS (SELECT 1 FROM engines e2 WHERE e2.model_id=vm.id AND e2.code=v.code);

-- ── DACIA JOGGER ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, consumption_mixed, reliability_score, maintenance_cost_year)
SELECT vm.id, v.code, v.fuel, v.cc, v.hp, v.cons, v.rel, v.maint
FROM (VALUES
  ('1.0 TCe 110',     'gasolina', 999, 110, 6.8, 7, 380),
  ('1.6 Hybrid 140',  'hibrido', 1598, 140, 5.0, 8, 360)
) AS v(code, fuel, cc, hp, cons, rel, maint)
CROSS JOIN (SELECT vm2.id FROM vehicle_models vm2 JOIN brands b ON b.id=vm2.brand_id WHERE b.name='Dacia' AND vm2.name='Jogger') vm
WHERE NOT EXISTS (SELECT 1 FROM engines e2 WHERE e2.model_id=vm.id AND e2.code=v.code);

-- ── HONDA CIVIC ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, consumption_mixed, reliability_score, maintenance_cost_year)
SELECT vm.id, v.code, v.fuel, v.cc, v.hp, v.cons, v.rel, v.maint
FROM (VALUES
  ('1.0 VTEC Turbo', 'gasolina', 988,  129, 6.5, 8, 450),
  ('1.5 VTEC Turbo', 'gasolina', 1498, 182, 7.0, 8, 480),
  ('2.0 e:HEV',      'hibrido',  1993, 184, 5.0, 9, 400)
) AS v(code, fuel, cc, hp, cons, rel, maint)
CROSS JOIN (SELECT vm2.id FROM vehicle_models vm2 JOIN brands b ON b.id=vm2.brand_id WHERE b.name='Honda' AND vm2.name='Civic') vm
WHERE NOT EXISTS (SELECT 1 FROM engines e2 WHERE e2.model_id=vm.id AND e2.code=v.code);

-- ── HONDA HR-V ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, consumption_mixed, reliability_score, maintenance_cost_year)
SELECT vm.id, v.code, v.fuel, v.cc, v.hp, v.cons, v.rel, v.maint
FROM (VALUES
  ('1.5 VTEC',   'gasolina', 1498, 131, 6.8, 8, 430),
  ('1.5 e:HEV',  'hibrido',  1498, 131, 5.2, 9, 380)
) AS v(code, fuel, cc, hp, cons, rel, maint)
CROSS JOIN (SELECT vm2.id FROM vehicle_models vm2 JOIN brands b ON b.id=vm2.brand_id WHERE b.name='Honda' AND vm2.name='HR-V') vm
WHERE NOT EXISTS (SELECT 1 FROM engines e2 WHERE e2.model_id=vm.id AND e2.code=v.code);

-- ── MAZDA 3 ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, consumption_mixed, reliability_score, maintenance_cost_year)
SELECT vm.id, v.code, v.fuel, v.cc, v.hp, v.cons, v.rel, v.maint
FROM (VALUES
  ('2.0 SkyActiv-G', 'gasolina', 1998, 122, 6.5, 9, 430),
  ('2.0 SkyActiv-X', 'gasolina', 1998, 186, 6.0, 8, 460),
  ('1.8 SkyActiv-D', 'diesel',   1759, 116, 5.2, 8, 470)
) AS v(code, fuel, cc, hp, cons, rel, maint)
CROSS JOIN (SELECT vm2.id FROM vehicle_models vm2 JOIN brands b ON b.id=vm2.brand_id WHERE b.name='Mazda' AND vm2.name='3') vm
WHERE NOT EXISTS (SELECT 1 FROM engines e2 WHERE e2.model_id=vm.id AND e2.code=v.code);

-- ── MAZDA CX-30 ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, consumption_mixed, reliability_score, maintenance_cost_year)
SELECT vm.id, v.code, v.fuel, v.cc, v.hp, v.cons, v.rel, v.maint
FROM (VALUES
  ('2.0 SkyActiv-G', 'gasolina', 1998, 122, 6.8, 9, 450),
  ('2.0 SkyActiv-X', 'gasolina', 1998, 186, 6.2, 8, 480),
  ('1.8 SkyActiv-D', 'diesel',   1759, 116, 5.5, 8, 490)
) AS v(code, fuel, cc, hp, cons, rel, maint)
CROSS JOIN (SELECT vm2.id FROM vehicle_models vm2 JOIN brands b ON b.id=vm2.brand_id WHERE b.name='Mazda' AND vm2.name='CX-30') vm
WHERE NOT EXISTS (SELECT 1 FROM engines e2 WHERE e2.model_id=vm.id AND e2.code=v.code);

-- ── MAZDA CX-5 ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, consumption_mixed, reliability_score, maintenance_cost_year)
SELECT vm.id, v.code, v.fuel, v.cc, v.hp, v.cons, v.rel, v.maint
FROM (VALUES
  ('2.0 SkyActiv-G 165', 'gasolina', 1998, 165, 7.2, 9, 480),
  ('2.5 SkyActiv-G 194', 'gasolina', 2488, 194, 7.8, 8, 510),
  ('2.2 SkyActiv-D 150', 'diesel',   2191, 150, 5.8, 8, 520)
) AS v(code, fuel, cc, hp, cons, rel, maint)
CROSS JOIN (SELECT vm2.id FROM vehicle_models vm2 JOIN brands b ON b.id=vm2.brand_id WHERE b.name='Mazda' AND vm2.name='CX-5') vm
WHERE NOT EXISTS (SELECT 1 FROM engines e2 WHERE e2.model_id=vm.id AND e2.code=v.code);

-- ── SUZUKI SWIFT ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, consumption_mixed, reliability_score, maintenance_cost_year)
SELECT vm.id, v.code, v.fuel, v.cc, v.hp, v.cons, v.rel, v.maint
FROM (VALUES
  ('1.2 DualJet',      'gasolina', 1197, 83, 5.5, 9, 300),
  ('1.0 BoosterJet',   'gasolina', 998, 112, 5.5, 8, 330),
  ('1.4 BoosterJet Sport','gasolina', 1373, 140, 6.0, 8, 350)
) AS v(code, fuel, cc, hp, cons, rel, maint)
CROSS JOIN (SELECT vm2.id FROM vehicle_models vm2 JOIN brands b ON b.id=vm2.brand_id WHERE b.name='Suzuki' AND vm2.name='Swift') vm
WHERE NOT EXISTS (SELECT 1 FROM engines e2 WHERE e2.model_id=vm.id AND e2.code=v.code);

-- ── SUZUKI VITARA ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, consumption_mixed, reliability_score, maintenance_cost_year)
SELECT vm.id, v.code, v.fuel, v.cc, v.hp, v.cons, v.rel, v.maint
FROM (VALUES
  ('1.0 BoosterJet', 'gasolina', 998, 112, 6.2, 8, 370),
  ('1.4 BoosterJet', 'gasolina', 1373, 140, 6.5, 8, 400)
) AS v(code, fuel, cc, hp, cons, rel, maint)
CROSS JOIN (SELECT vm2.id FROM vehicle_models vm2 JOIN brands b ON b.id=vm2.brand_id WHERE b.name='Suzuki' AND vm2.name='Vitara') vm
WHERE NOT EXISTS (SELECT 1 FROM engines e2 WHERE e2.model_id=vm.id AND e2.code=v.code);


-- ═══════════════════════════════════════════════════════════
-- 5. ENGINE ISSUES FOR CRITICAL ENGINES (new models)
-- ═══════════════════════════════════════════════════════════

-- Citroen C3 / C4 / C5 Aircross — PureTech wet belt (same issue as Peugeot)
INSERT INTO engine_issues (engine_id, issue_name, severity, typical_km_start, typical_km_end, repair_cost_estimate, description, alert_level, what_to_ask, if_maintained, preventable)
SELECT e.id,
'Correia humida (wet belt)',
'media', 50000, 120000, 1200,
'Este motor usa uma correia de distribuicao banhada em oleo (wet belt). A PSA emitiu um recall em 2021 sobre este tema.',
'atencao',
'Pergunte se a correia ja foi substituida. Peca comprovativos das trocas de oleo.',
'Com trocas de oleo rigorosas e correia substituida quando indicado, funciona bem. Versoes 2020+ tem correias melhoradas.',
TRUE
FROM engines e
JOIN vehicle_models vm ON vm.id = e.model_id
JOIN brands b ON b.id = vm.brand_id
WHERE LOWER(b.name) = 'citroen'
  AND e.code LIKE '1.2 PureTech%'
  AND CAST(SUBSTRING(e.code FROM '[0-9]+$') AS INTEGER) >= 100
  AND NOT EXISTS (SELECT 1 FROM engine_issues ei WHERE ei.engine_id = e.id AND ei.issue_name LIKE '%wet belt%');

-- Renault 1.3 TCe (H5H) — Oil consumption in some units
INSERT INTO engine_issues (engine_id, issue_name, severity, typical_km_start, typical_km_end, repair_cost_estimate, description, alert_level, what_to_ask, if_maintained, preventable)
SELECT e.id,
'Consumo de oleo (monitorizar)',
'baixa', 60000, NULL, 300,
'O motor 1.3 TCe (H5H, co-desenvolvido com Mercedes M282) pode apresentar consumo de oleo ligeiro em alguns exemplares. Nao e um defeito sistematico.',
'informativo',
'Pergunte sobre consumo de oleo entre revisoes. Verifique o nivel de oleo durante a inspecao.',
'Com trocas de oleo regulares no intervalo correto e oleo de especificacao adequada, a maioria funciona sem problemas.',
TRUE
FROM engines e
JOIN vehicle_models vm ON vm.id = e.model_id
JOIN brands b ON b.id = vm.brand_id
WHERE b.name = 'Renault' AND e.code LIKE '1.3 TCe%'
  AND NOT EXISTS (SELECT 1 FROM engine_issues ei WHERE ei.engine_id = e.id AND ei.issue_name LIKE '%oleo%');

-- Opel Astra / Mokka — PureTech 1.2 turbo (same PSA engine)
INSERT INTO engine_issues (engine_id, issue_name, severity, typical_km_start, typical_km_end, repair_cost_estimate, description, alert_level, what_to_ask, if_maintained, preventable)
SELECT e.id,
'Correia humida (wet belt)',
'media', 50000, 120000, 1200,
'Motor PSA 1.2 Turbo com correia de distribuicao banhada em oleo. Atencao identica ao PureTech dos Peugeot/Citroen.',
'atencao',
'Pergunte se a correia ja foi substituida. Peca comprovativos das trocas de oleo.',
'Com manutencao rigorosa e correia substituida, funciona bem. Versoes mais recentes tem correias melhoradas.',
TRUE
FROM engines e
JOIN vehicle_models vm ON vm.id = e.model_id
JOIN brands b ON b.id = vm.brand_id
WHERE b.name = 'Opel' AND e.code LIKE '1.2 Turbo%' AND CAST(SUBSTRING(e.code FROM '[0-9]+$') AS INTEGER) >= 110
  AND NOT EXISTS (SELECT 1 FROM engine_issues ei WHERE ei.engine_id = e.id AND ei.issue_name LIKE '%wet belt%');

-- Ford 1.0 EcoBoost (Fiesta/Puma) — Cooling system pre-2017
INSERT INTO engine_issues (engine_id, issue_name, severity, typical_km_start, typical_km_end, repair_cost_estimate, description, alert_level, what_to_ask, if_maintained, preventable)
SELECT e.id,
'Sistema de arrefecimento (versoes pre-2017)',
'media', 50000, 150000, 1500,
'As versoes iniciais do 1.0 EcoBoost (2012-2016) tinham um ponto de atencao no sistema de arrefecimento. A Ford melhorou este componente nas versoes 2017+.',
'atencao',
'Verifique o ano de fabrico. Se for 2017+, este ponto ja foi corrigido.',
'Nas versoes a partir de 2017, a Ford resolveu este ponto.',
TRUE
FROM engines e
JOIN vehicle_models vm ON vm.id = e.model_id
JOIN brands b ON b.id = vm.brand_id
WHERE b.name = 'Ford' AND vm.name IN ('Fiesta', 'Puma') AND e.code LIKE '1.0 EcoBoost%'
  AND NOT EXISTS (SELECT 1 FROM engine_issues ei WHERE ei.engine_id = e.id AND ei.issue_name LIKE '%arrefecimento%');

-- Fiat 0.9 TwinAir — Excessive vibration and consumption
INSERT INTO engine_issues (engine_id, issue_name, severity, typical_km_start, typical_km_end, repair_cost_estimate, description, alert_level, what_to_ask, if_maintained, preventable)
SELECT e.id,
'Vibracoes e consumo de oleo (2 cilindros)',
'baixa', 40000, NULL, 250,
'O motor TwinAir de 2 cilindros e inerentemente mais vibrante. Alguns exemplares reportam consumo de oleo. E uma caracteristica do design, nao um defeito.',
'informativo',
'Verifique o nivel de oleo e pergunte sobre consumo entre revisoes. Teste o motor a frio para avaliar vibracoes.',
'Com manutencao adequada, o TwinAir funciona sem problemas graves. As vibracoes sao normais para um 2 cilindros.',
TRUE
FROM engines e
JOIN vehicle_models vm ON vm.id = e.model_id
JOIN brands b ON b.id = vm.brand_id
WHERE b.name = 'Fiat' AND e.code LIKE '0.9 TwinAir%'
  AND NOT EXISTS (SELECT 1 FROM engine_issues ei WHERE ei.engine_id = e.id AND ei.issue_name LIKE '%TwinAir%');

-- Tesla Model 3/Y — Panel gaps and suspension noises (early units)
INSERT INTO engine_issues (engine_id, issue_name, severity, typical_km_start, typical_km_end, repair_cost_estimate, description, alert_level, what_to_ask, if_maintained, preventable)
SELECT e.id,
'Qualidade de construcao (unidades iniciais)',
'baixa', 0, 100000, 500,
'Unidades dos primeiros anos podem ter folgas nos paineis e ruidos de suspensao. As versoes mais recentes (2021+) melhoraram significativamente.',
'informativo',
'Verifique folgas nos paineis, ruidos na suspensao e estado geral da pintura. Peca historico de intervencoes na garantia.',
'Nao e um problema mecanico grave. Versoes mais recentes tem melhor controlo de qualidade.',
FALSE
FROM engines e
JOIN vehicle_models vm ON vm.id = e.model_id
JOIN brands b ON b.id = vm.brand_id
WHERE b.name = 'Tesla' AND vm.name IN ('Model 3', 'Model Y')
  AND NOT EXISTS (SELECT 1 FROM engine_issues ei WHERE ei.engine_id = e.id AND ei.issue_name LIKE '%construcao%');

-- VW/Audi/Skoda/SEAT 1.0 TSI — Timing chain (early versions, already exists for Golf/Octavia/Leon)
-- Add for new models: T-Cross, T-Roc, Fabia, Kamiq, Ibiza, Arona, A1
INSERT INTO engine_issues (engine_id, issue_name, severity, typical_km_start, typical_km_end, repair_cost_estimate, description, alert_level, what_to_ask, if_maintained, preventable)
SELECT e.id,
'Corrente de distribuicao (versoes iniciais)',
'baixa', 60000, 150000, 1200,
'As primeiras versoes deste motor (EA211 EVO, pre-2019) tinham uma corrente mais fragil. As versoes mais recentes ja foram melhoradas.',
'informativo',
'Verifique o ano de fabrico. Se for 2019+, este ponto ja foi corrigido.',
'Versoes a partir de 2019 ja tem a corrente melhorada de fabrica.',
TRUE
FROM engines e
JOIN vehicle_models vm ON vm.id = e.model_id
JOIN brands b ON b.id = vm.brand_id
WHERE e.code = '1.0 TSI'
  AND NOT EXISTS (SELECT 1 FROM engine_issues ei WHERE ei.engine_id = e.id AND ei.issue_name LIKE '%Corrente%');


-- ═══════════════════════════════════════════════════════════
-- 6. DRIVING CHARACTER FOR NEW MODELS
-- ═══════════════════════════════════════════════════════════

INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, v.comfort, v.fun, v.city, v.highway, v.family, v.noise, v.descr
FROM (VALUES
  -- Citroen C3
  ('Citroen', 'C3', 6, 4, 9, 5, 5, 'medio',
   'Compacto citadino simpatico, com suspensao confortavel. Ideal para cidade. Interior funcional mas sem pretensoes premium.'),
  -- Citroen C5 Aircross
  ('Citroen', 'C5 Aircross', 8, 5, 7, 7, 8, 'baixo',
   'SUV familiar muito confortavel gracas a suspensao com amortecedores progressivos. Excelente espaco traseiro. Nao entusiasma na conducao mas e relaxante.'),
  -- Renault Captur
  ('Renault', 'Captur', 7, 5, 8, 6, 6, 'medio',
   'SUV compacto versatil com bom espaco interior para o segmento. E-Tech Hybrid muito eficiente em cidade. Posicao de conducao elevada agrada.'),
  -- Renault Megane
  ('Renault', 'Megane', 7, 6, 7, 7, 6, 'medio',
   'Compacto equilibrado com bom espaco e equipamento. A versao E-Tech e particularmente suave. Concorre bem com o Golf.'),
  -- Renault Arkana
  ('Renault', 'Arkana', 7, 6, 7, 7, 6, 'medio',
   'SUV coupe com linhas desportivas mas caracter confortavel. A versao E-Tech Hybrid e o melhor compromisso. Bom espaco para um coupe.'),
  -- BMW Serie 1
  ('BMW', 'Serie 1', 7, 8, 7, 7, 5, 'baixo',
   'Compacto premium com dinamica BMW. F40 (2019+) e tracao dianteira, menos puro que o F20 mas mais pratico. Bom equipamento tecnologico.'),
  -- BMW Serie 5
  ('BMW', 'Serie 5', 9, 8, 6, 10, 7, 'baixo',
   'Berlina executiva de referencia. Conforto excepcional em autoestrada, conducao envolvente para o segmento. Envelhecimento elegante.'),
  -- BMW X1
  ('BMW', 'X1', 7, 7, 7, 8, 7, 'baixo',
   'SUV compacto premium muito pratico. Espaco interior surpreendente, especialmente na geracao U11. Conducao tipica BMW.'),
  -- BMW X3
  ('BMW', 'X3', 8, 7, 6, 9, 8, 'baixo',
   'SUV medio premium. Equilibrio entre conforto e dinamismo. Espaco generoso, qualidade premium. Dos melhores do segmento.'),
  -- Mercedes Classe C
  ('Mercedes-Benz', 'Classe C', 9, 7, 6, 9, 6, 'baixo',
   'Berlina premium com interior refinado e tecnologico. Sistema MBUX excelente. Confortavel e silenciosa. Rival direto do Serie 3.'),
  -- Mercedes CLA
  ('Mercedes-Benz', 'CLA', 8, 6, 7, 8, 5, 'baixo',
   'Coupe de 4 portas com design marcante. Interior premium com MBUX. Menos pratico que o Classe A mas mais elegante. Imagem forte.'),
  -- Mercedes GLA
  ('Mercedes-Benz', 'GLA', 7, 6, 8, 7, 6, 'baixo',
   'SUV compacto premium com boa posicao de conducao. Interior identico ao Classe A. Menos espaco que os rivais mas mais premium.'),
  -- Mercedes GLC
  ('Mercedes-Benz', 'GLC', 9, 6, 6, 9, 8, 'baixo',
   'SUV medio premium de referencia. Excelente conforto, espaco generoso, qualidade interior topo. Rival do X3 e Q5.'),
  -- Audi A3
  ('Audi', 'A3', 8, 7, 8, 8, 6, 'baixo',
   'Compacto premium com qualidade Audi. Interior tecnologico com Virtual Cockpit. Conducao refinada, mas menos dinamico que o Serie 1.'),
  -- Audi A4
  ('Audi', 'A4', 8, 7, 6, 9, 7, 'baixo',
   'Berlina premium com construcao solida. Interior minimalista e tecnologico. Confortavel e refinada. Quattro excelente para quem precisa.'),
  -- Audi Q3
  ('Audi', 'Q3', 7, 6, 7, 7, 7, 'medio',
   'SUV compacto premium com interior de qualidade. Virtual Cockpit distintivo. Pratico para familias que querem premium.'),
  -- VW T-Roc
  ('Volkswagen', 'T-Roc', 7, 6, 7, 7, 7, 'medio',
   'SUV compacto com estilo mais arrojado que o Tiguan. Boa qualidade VW, pratico e versatil. Conducao solida sem ser excitante.'),
  -- VW Tiguan
  ('Volkswagen', 'Tiguan', 8, 6, 7, 8, 9, 'baixo',
   'SUV familiar VW por excelencia. Espaco generoso, qualidade solida, conducao competente. A escolha racional do segmento.'),
  -- VW Passat
  ('Volkswagen', 'Passat', 8, 6, 6, 9, 8, 'baixo',
   'Familiar de referencia. Bagageira enorme, muito confortavel em viagem. Qualidade premium a preco VW. Versao Variant e imbativel.'),
  -- Toyota C-HR
  ('Toyota', 'C-HR', 7, 6, 8, 7, 5, 'medio',
   'SUV coupe com design ousado. Hibrido excelente para cidade. Visibilidade traseira limitada pelo design. Fiabilidade Toyota.'),
  -- Toyota Yaris Cross
  ('Toyota', 'Yaris Cross', 7, 5, 9, 6, 6, 'medio',
   'SUV citadino baseado no Yaris. Hibrido muito eficiente em cidade. Compacto mas com boa altura ao solo. Fiabilidade Toyota.'),
  -- Toyota RAV4
  ('Toyota', 'RAV4', 8, 5, 7, 8, 9, 'baixo',
   'SUV familiar hibrido de referencia. Muito eficiente, fiavel, espaco generoso. PHEV com autonomia eletrica util. Escolha segura.'),
  -- Hyundai i20
  ('Hyundai', 'i20', 6, 5, 9, 5, 4, 'medio',
   'Compacto citadino bem equipado para o preco. Design moderno, garantia 7 anos. Bom para cidade, basico em autoestrada.'),
  -- Hyundai i30
  ('Hyundai', 'i30', 7, 6, 7, 7, 7, 'medio',
   'Alternativa coreana ao Golf. Muito bem equipado, garantia 7 anos, qualidade em alta. Conducao competente, sem excitacao.'),
  -- Hyundai Kona
  ('Hyundai', 'Kona', 7, 5, 8, 6, 6, 'medio',
   'SUV compacto versatil. Versao EV muito competitiva. Design arrojado, equipamento generoso, garantia 7 anos.'),
  -- Kia Ceed
  ('Kia', 'Ceed', 7, 6, 7, 7, 7, 'medio',
   'Alternativa coreana ao Golf e Focus. Muito bem equipado, garantia 7 anos, design moderno. Pratico e sem surpresas.'),
  -- Kia Niro
  ('Kia', 'Niro', 7, 5, 8, 7, 7, 'medio',
   'SUV compacto eletrificado. Disponivel em hibrido, PHEV e EV. Muito pratico, eficiente e bem equipado. Garantia 7 anos.'),
  -- Kia EV6
  ('Kia', 'EV6', 8, 8, 7, 9, 7, 'baixo',
   'Eletrico de referencia com plataforma E-GMP. Carregamento ultra-rapido 800V, autonomia generosa, conducao surpreendentemente divertida.'),
  -- Ford Fiesta
  ('Ford', 'Fiesta', 6, 8, 9, 5, 4, 'medio',
   'Compacto de referencia em prazer de conducao. Chassis fantastico. Interior menos refinado que rivais mas compensado pela dinamica.'),
  -- Ford Puma
  ('Ford', 'Puma', 7, 7, 8, 7, 6, 'medio',
   'SUV compacto com chassis do Fiesta — divertido de conduzir. MegaBox pratica, bom espaco. Uma das melhores opcoes do segmento.'),
  -- Ford Kuga
  ('Ford', 'Kuga', 7, 6, 7, 8, 8, 'medio',
   'SUV familiar versatil. PHEV com boa autonomia eletrica. Espaco generoso, conducao competente. Bom custo-beneficio.'),
  -- Skoda Fabia
  ('Skoda', 'Fabia', 7, 5, 8, 6, 5, 'medio',
   'Compacto com espaco de classe superior. Bagageira enorme para o segmento. Qualidade VW a preco mais acessivel. Simply Clever.'),
  -- SEAT Ibiza
  ('SEAT', 'Ibiza', 6, 7, 9, 6, 4, 'medio',
   'Primo espanhol do Polo. Mais dinamico e com design mais arrojado. Bom equipamento, preco competitivo. Ideal para cidade.'),
  -- Cupra Formentor
  ('Cupra', 'Formentor', 7, 9, 6, 8, 6, 'medio',
   'SUV coupe desportivo. Design marcante, conducao envolvente, motorizacoes potentes. A alternativa espanhola ao BMW X2.'),
  -- Opel Astra
  ('Opel', 'Astra', 7, 6, 7, 7, 6, 'medio',
   'Geracao mais recente deu um salto de qualidade. Design moderno, interior premium para a marca. Versao PHEV muito eficiente.'),
  -- Nissan Juke
  ('Nissan', 'Juke', 6, 5, 8, 6, 5, 'medio',
   'SUV compacto com design polarizante. Pratico para cidade, equipamento decente. Segunda geracao (2019+) muito melhor que a primeira.'),
  -- Fiat 500
  ('Fiat', '500', 5, 6, 10, 3, 2, 'alto',
   'Icone de estilo citadino. Perfeito para cidade com o seu tamanho mini. Versao eletrica 500e e silenciosa e moderna. Pouco pratico para familia.'),
  -- Fiat Tipo
  ('Fiat', 'Tipo', 6, 4, 7, 6, 6, 'medio',
   'Carro honesto com muito espaco pelo preco. Interior basico mas pratico. Bom para quem quer espaco com orcamento limitado.'),
  -- Volvo XC40
  ('Volvo', 'XC40', 8, 6, 7, 8, 7, 'baixo',
   'SUV compacto premium com design escandinavo. Interior minimalista mas de qualidade. Seguranca referencia. Versao Recharge competitiva.'),
  -- Volvo XC60
  ('Volvo', 'XC60', 9, 6, 6, 9, 8, 'baixo',
   'SUV medio premium com conforto excepcional. Interior sofisticado, seguranca maxima. T8 PHEV muito potente e eficiente.'),
  -- Tesla Model 3
  ('Tesla', 'Model 3', 7, 8, 7, 9, 5, 'baixo',
   'Berlina eletrica de referencia. Aceleracao fulminante, autonomia generosa, rede de Superchargers. Interior minimalista polariza.'),
  -- Tesla Model Y
  ('Tesla', 'Model Y', 7, 7, 7, 9, 7, 'baixo',
   'SUV eletrico mais vendido da Europa. Espaco familiar, autonomia generosa. Mesmo powertrain do Model 3 com mais praticabilidade.'),
  -- Dacia Jogger
  ('Dacia', 'Jogger', 5, 3, 6, 5, 8, 'alto',
   'Carro de 7 lugares mais acessivel do mercado. Espaco enorme pelo preco. Acabamento basico mas honesto. Versao Hybrid surpreendente.'),
  -- Honda Civic
  ('Honda', 'Civic', 7, 7, 7, 8, 6, 'medio',
   'Compacto com motores VTEC de referencia. Geracao XI e madura e refinada. e:HEV muito eficiente. Fiabilidade Honda.'),
  -- Honda HR-V
  ('Honda', 'HR-V', 7, 5, 8, 7, 7, 'medio',
   'SUV compacto com Magic Seats versateis. e:HEV muito eficiente. Espaco generoso para o segmento. Fiabilidade Honda.'),
  -- Mazda CX-30
  ('Mazda', 'CX-30', 7, 7, 7, 7, 6, 'medio',
   'SUV compacto com qualidade de construcao premium. Conducao envolvente para o segmento. Interior elegante. Motores SkyActiv eficientes.'),
  -- Mazda CX-5
  ('Mazda', 'CX-5', 8, 7, 6, 8, 8, 'baixo',
   'SUV familiar com qualidade premium a preco acessivel. Conducao refinada, interior elegante, motores eficientes. Alternativa ao Tiguan.'),
  -- Mazda 3
  ('Mazda', '3', 7, 8, 7, 7, 5, 'medio',
   'Compacto premium com design elegante e conducao envolvente. SkyActiv-X inovador. Interior de qualidade superior ao preco.'),
  -- Suzuki Swift
  ('Suzuki', 'Swift', 5, 6, 9, 4, 3, 'medio',
   'Compacto leve e agil. Muito divertido de conduzir para o segmento. Consumos baixos, fiavel e economico de manter.'),
  -- Suzuki Vitara
  ('Suzuki', 'Vitara', 6, 5, 7, 6, 6, 'medio',
   'SUV compacto acessivel com opcao 4x4. Pratico e fiavel. Sem pretensoes premium mas honesto e capaz.')
) AS v(brand, model, comfort, fun, city, highway, family, noise, descr)
JOIN brands b ON LOWER(b.name) = LOWER(v.brand)
JOIN vehicle_models vm ON vm.brand_id = b.id AND LOWER(vm.name) = LOWER(v.model)
WHERE NOT EXISTS (
  SELECT 1 FROM driving_character dc2 WHERE dc2.model_id = vm.id
);


-- ═══════════════════════════════════════════════════════════
-- 7. ADDITIONAL MARKET PRICE STATS (most popular new models)
-- ═══════════════════════════════════════════════════════════

-- Renault Captur 1.5 dCi
INSERT INTO market_price_stats (model_id, engine_id, year, price_context, avg_price, min_price, max_price, sample_count, confidence)
SELECT vm.id, e.id, v.yr, 'particular', v.avg, v.mn, v.mx, v.cnt, 'alta'
FROM (VALUES
  (2019, 14500, 12000, 17000, 30),
  (2020, 16000, 13500, 18500, 25),
  (2021, 17500, 15000, 20000, 20)
) AS v(yr, avg, mn, mx, cnt)
CROSS JOIN (SELECT vm2.id FROM vehicle_models vm2 JOIN brands b ON b.id=vm2.brand_id WHERE b.name='Renault' AND vm2.name='Captur') vm
CROSS JOIN (SELECT e2.id FROM engines e2 JOIN vehicle_models vm3 ON vm3.id=e2.model_id JOIN brands b2 ON b2.id=vm3.brand_id WHERE b2.name='Renault' AND vm3.name='Captur' AND e2.code='1.5 dCi 95') e
WHERE NOT EXISTS (SELECT 1 FROM market_price_stats m WHERE m.model_id=vm.id AND m.engine_id=e.id AND m.year=v.yr);

-- Audi A3 2.0 TDI
INSERT INTO market_price_stats (model_id, engine_id, year, price_context, avg_price, min_price, max_price, sample_count, confidence)
SELECT vm.id, e.id, v.yr, 'particular', v.avg, v.mn, v.mx, v.cnt, 'alta'
FROM (VALUES
  (2017, 19000, 16000, 22000, 35),
  (2018, 21000, 18000, 24000, 30),
  (2019, 23000, 20000, 26000, 25)
) AS v(yr, avg, mn, mx, cnt)
CROSS JOIN (SELECT vm2.id FROM vehicle_models vm2 JOIN brands b ON b.id=vm2.brand_id WHERE b.name='Audi' AND vm2.name='A3') vm
CROSS JOIN (SELECT e2.id FROM engines e2 JOIN vehicle_models vm3 ON vm3.id=e2.model_id JOIN brands b2 ON b2.id=vm3.brand_id WHERE b2.name='Audi' AND vm3.name='A3' AND e2.code='2.0 TDI') e
WHERE NOT EXISTS (SELECT 1 FROM market_price_stats m WHERE m.model_id=vm.id AND m.engine_id=e.id AND m.year=v.yr);

-- Mercedes Classe C C220d
INSERT INTO market_price_stats (model_id, engine_id, year, price_context, avg_price, min_price, max_price, sample_count, confidence)
SELECT vm.id, e.id, v.yr, 'particular', v.avg, v.mn, v.mx, v.cnt, 'alta'
FROM (VALUES
  (2018, 26000, 22000, 30000, 30),
  (2019, 29000, 25000, 33000, 25),
  (2020, 32000, 28000, 36000, 20)
) AS v(yr, avg, mn, mx, cnt)
CROSS JOIN (SELECT vm2.id FROM vehicle_models vm2 JOIN brands b ON b.id=vm2.brand_id WHERE LOWER(b.name)='mercedes-benz' AND LOWER(vm2.name)='classe c') vm
CROSS JOIN (SELECT e2.id FROM engines e2 WHERE e2.model_id=vm.id AND e2.code='C220d' LIMIT 1) e
WHERE NOT EXISTS (SELECT 1 FROM market_price_stats m WHERE m.model_id=vm.id AND m.engine_id=e.id AND m.year=v.yr);

-- VW Tiguan 2.0 TDI
INSERT INTO market_price_stats (model_id, engine_id, year, price_context, avg_price, min_price, max_price, sample_count, confidence)
SELECT vm.id, e.id, v.yr, 'particular', v.avg, v.mn, v.mx, v.cnt, 'alta'
FROM (VALUES
  (2018, 22000, 19000, 25000, 30),
  (2019, 24000, 21000, 27000, 25),
  (2020, 27000, 23000, 31000, 20)
) AS v(yr, avg, mn, mx, cnt)
CROSS JOIN (SELECT vm2.id FROM vehicle_models vm2 JOIN brands b ON b.id=vm2.brand_id WHERE b.name='Volkswagen' AND vm2.name='Tiguan') vm
CROSS JOIN (SELECT e2.id FROM engines e2 WHERE e2.model_id=vm.id AND e2.code='2.0 TDI' LIMIT 1) e
WHERE NOT EXISTS (SELECT 1 FROM market_price_stats m WHERE m.model_id=vm.id AND m.engine_id=e.id AND m.year=v.yr);

-- Toyota C-HR 1.8 Hybrid
INSERT INTO market_price_stats (model_id, engine_id, year, price_context, avg_price, min_price, max_price, sample_count, confidence)
SELECT vm.id, e.id, v.yr, 'particular', v.avg, v.mn, v.mx, v.cnt, 'alta'
FROM (VALUES
  (2019, 20000, 17000, 23000, 25),
  (2020, 22000, 19000, 25000, 20),
  (2021, 24000, 21000, 27000, 15)
) AS v(yr, avg, mn, mx, cnt)
CROSS JOIN (SELECT vm2.id FROM vehicle_models vm2 JOIN brands b ON b.id=vm2.brand_id WHERE b.name='Toyota' AND vm2.name='C-HR') vm
CROSS JOIN (SELECT e2.id FROM engines e2 WHERE e2.model_id=vm.id AND e2.code='1.8 Hybrid' LIMIT 1) e
WHERE NOT EXISTS (SELECT 1 FROM market_price_stats m WHERE m.model_id=vm.id AND m.engine_id=e.id AND m.year=v.yr);

-- Peugeot 2008 1.2 PureTech 130
INSERT INTO market_price_stats (model_id, engine_id, year, price_context, avg_price, min_price, max_price, sample_count, confidence)
SELECT vm.id, e.id, v.yr, 'particular', v.avg, v.mn, v.mx, v.cnt, 'alta'
FROM (VALUES
  (2020, 18500, 16000, 21000, 30),
  (2021, 20000, 17500, 22500, 25),
  (2022, 22000, 19000, 25000, 20)
) AS v(yr, avg, mn, mx, cnt)
CROSS JOIN (SELECT vm2.id FROM vehicle_models vm2 JOIN brands b ON b.id=vm2.brand_id WHERE b.name='Peugeot' AND vm2.name='2008') vm
CROSS JOIN (SELECT e2.id FROM engines e2 WHERE e2.model_id=vm.id AND e2.code='1.2 PureTech 130' LIMIT 1) e
WHERE NOT EXISTS (SELECT 1 FROM market_price_stats m WHERE m.model_id=vm.id AND m.engine_id=e.id AND m.year=v.yr);

-- Hyundai Tucson 1.6 T-GDi Hybrid
INSERT INTO market_price_stats (model_id, engine_id, year, price_context, avg_price, min_price, max_price, sample_count, confidence)
SELECT vm.id, e.id, v.yr, 'particular', v.avg, v.mn, v.mx, v.cnt, 'alta'
FROM (VALUES
  (2021, 28000, 24000, 32000, 20),
  (2022, 30000, 26000, 34000, 15)
) AS v(yr, avg, mn, mx, cnt)
CROSS JOIN (SELECT vm2.id FROM vehicle_models vm2 JOIN brands b ON b.id=vm2.brand_id WHERE b.name='Hyundai' AND vm2.name='Tucson') vm
CROSS JOIN (SELECT e2.id FROM engines e2 WHERE e2.model_id=vm.id AND e2.code='1.6 T-GDi Hybrid' LIMIT 1) e
WHERE NOT EXISTS (SELECT 1 FROM market_price_stats m WHERE m.model_id=vm.id AND m.engine_id=e.id AND m.year=v.yr);


COMMIT;

-- Verify counts
SELECT 'brands' AS entity, COUNT(*) AS total FROM brands
UNION ALL SELECT 'models', COUNT(*) FROM vehicle_models
UNION ALL SELECT 'engines', COUNT(*) FROM engines
UNION ALL SELECT 'engine_issues', COUNT(*) FROM engine_issues
UNION ALL SELECT 'driving_character', COUNT(*) FROM driving_character
UNION ALL SELECT 'market_price_stats', COUNT(*) FROM market_price_stats
ORDER BY entity;
