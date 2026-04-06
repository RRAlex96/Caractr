-- ============================================================
-- CARACTR DATABASE v3.0 — COMPLETE REBUILD
-- ~200 modelos, ~500 motorizações, mercado PT
-- ============================================================

-- Drop everything
DROP TABLE IF EXISTS import_cost_estimates CASCADE;
DROP TABLE IF EXISTS normalized_listings CASCADE;
DROP TABLE IF EXISTS raw_listings CASCADE;
DROP TABLE IF EXISTS market_price_stats CASCADE;
DROP TABLE IF EXISTS engine_issues CASCADE;
DROP TABLE IF EXISTS driving_character CASCADE;
DROP TABLE IF EXISTS engines CASCADE;
DROP TABLE IF EXISTS generations CASCADE;
DROP TABLE IF EXISTS vehicle_models CASCADE;
DROP TABLE IF EXISTS brands CASCADE;

-- ============================================================
-- SCHEMA
-- ============================================================

CREATE TABLE brands (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    country VARCHAR(50),
    segment VARCHAR(30),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE vehicle_models (
    id SERIAL PRIMARY KEY,
    brand_id INTEGER REFERENCES brands(id),
    name VARCHAR(100) NOT NULL,
    body_type VARCHAR(30),
    segment VARCHAR(30),
    years_produced VARCHAR(30),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE generations (
    id SERIAL PRIMARY KEY,
    model_id INTEGER REFERENCES vehicle_models(id),
    name VARCHAR(50),
    year_start INTEGER,
    year_end INTEGER,
    platform VARCHAR(50)
);

CREATE TABLE engines (
    id SERIAL PRIMARY KEY,
    model_id INTEGER REFERENCES vehicle_models(id),
    code VARCHAR(80),
    fuel_type VARCHAR(20),
    displacement_cc INTEGER,
    power_hp INTEGER,
    torque_nm INTEGER,
    transmission VARCHAR(30),
    consumption_mixed DECIMAL(4,1),
    co2_emissions INTEGER,
    reliability_score DECIMAL(3,1),
    maintenance_cost_year INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE engine_issues (
    id SERIAL PRIMARY KEY,
    engine_id INTEGER REFERENCES engines(id),
    severity VARCHAR(20),
    description TEXT,
    affected_years VARCHAR(50),
    fix_cost_estimate VARCHAR(50),
    source VARCHAR(100)
);

CREATE TABLE driving_character (
    id SERIAL PRIMARY KEY,
    model_id INTEGER REFERENCES vehicle_models(id),
    comfort_score INTEGER,
    driving_fun_score INTEGER,
    city_score INTEGER,
    highway_score INTEGER,
    family_score INTEGER,
    noise_level VARCHAR(20),
    description TEXT
);

CREATE TABLE market_price_stats (
    id SERIAL PRIMARY KEY,
    model_id INTEGER REFERENCES vehicle_models(id),
    engine_id INTEGER REFERENCES engines(id),
    price_context VARCHAR(20),
    year INTEGER,
    avg_price INTEGER,
    min_price INTEGER,
    max_price INTEGER,
    sample_count INTEGER,
    source VARCHAR(50),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE raw_listings (
    id SERIAL PRIMARY KEY,
    source VARCHAR(30),
    external_id VARCHAR(100),
    url TEXT,
    raw_data JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE normalized_listings (
    id SERIAL PRIMARY KEY,
    raw_listing_id INTEGER REFERENCES raw_listings(id),
    model_id INTEGER REFERENCES vehicle_models(id),
    engine_id INTEGER REFERENCES engines(id),
    year INTEGER,
    mileage_km INTEGER,
    price INTEGER,
    location VARCHAR(100),
    seller_type VARCHAR(20),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE import_cost_estimates (
    id SERIAL PRIMARY KEY,
    model_id INTEGER REFERENCES vehicle_models(id),
    engine_id INTEGER REFERENCES engines(id),
    origin_country VARCHAR(50),
    base_price_origin INTEGER,
    isv_estimate INTEGER,
    iuc_annual INTEGER,
    transport_cost INTEGER,
    total_estimate INTEGER,
    notes TEXT
);

-- ============================================================
-- BRANDS (40)
-- ============================================================

INSERT INTO brands (name, country, segment) VALUES
('Renault', 'França', 'generalista'),
('Peugeot', 'França', 'generalista'),
('Citroën', 'França', 'generalista'),
('Dacia', 'Roménia', 'economico'),
('Opel', 'Alemanha', 'generalista'),
('Toyota', 'Japão', 'generalista'),
('Volkswagen', 'Alemanha', 'generalista'),
('SEAT', 'Espanha', 'generalista'),
('Skoda', 'Chéquia', 'generalista'),
('Hyundai', 'Coreia do Sul', 'generalista'),
('Kia', 'Coreia do Sul', 'generalista'),
('Ford', 'EUA', 'generalista'),
('Nissan', 'Japão', 'generalista'),
('Mazda', 'Japão', 'generalista'),
('Honda', 'Japão', 'generalista'),
('Fiat', 'Itália', 'generalista'),
('BMW', 'Alemanha', 'premium'),
('Mercedes-Benz', 'Alemanha', 'premium'),
('Audi', 'Alemanha', 'premium'),
('Volvo', 'Suécia', 'premium'),
('Alfa Romeo', 'Itália', 'premium'),
('Cupra', 'Espanha', 'premium'),
('DS', 'França', 'premium'),
('Lexus', 'Japão', 'premium'),
('Jaguar', 'Reino Unido', 'premium'),
('Land Rover', 'Reino Unido', 'premium'),
('Porsche', 'Alemanha', 'luxo'),
('Maserati', 'Itália', 'luxo'),
('MINI', 'Reino Unido', 'premium'),
('Tesla', 'EUA', 'premium'),
('BYD', 'China', 'generalista'),
('MG', 'China', 'generalista'),
('Omoda', 'China', 'generalista'),
('Smart', 'Alemanha', 'premium'),
('Jeep', 'EUA', 'generalista'),
('Subaru', 'Japão', 'generalista'),
('Suzuki', 'Japão', 'generalista'),
('Alpine', 'França', 'premium')
ON CONFLICT (name) DO NOTHING;

-- ============================================================
-- VEHICLE MODELS — CATEGORY 1: CITADINOS (25)
-- ============================================================

INSERT INTO vehicle_models (brand_id, name, body_type, segment, years_produced) VALUES
((SELECT id FROM brands WHERE name='Renault'), 'Clio', 'citadino', 'economico', '2019-presente'),
((SELECT id FROM brands WHERE name='Peugeot'), '208', 'citadino', 'economico', '2019-presente'),
((SELECT id FROM brands WHERE name='Citroën'), 'C3', 'citadino', 'economico', '2016-presente'),
((SELECT id FROM brands WHERE name='Dacia'), 'Sandero', 'citadino', 'economico', '2020-presente'),
((SELECT id FROM brands WHERE name='Opel'), 'Corsa', 'citadino', 'economico', '2019-presente'),
((SELECT id FROM brands WHERE name='Toyota'), 'Yaris', 'citadino', 'economico', '2020-presente'),
((SELECT id FROM brands WHERE name='Volkswagen'), 'Polo', 'citadino', 'medio', '2017-presente'),
((SELECT id FROM brands WHERE name='SEAT'), 'Ibiza', 'citadino', 'economico', '2017-presente'),
((SELECT id FROM brands WHERE name='Skoda'), 'Fabia', 'citadino', 'economico', '2021-presente'),
((SELECT id FROM brands WHERE name='Hyundai'), 'i20', 'citadino', 'economico', '2020-presente'),
((SELECT id FROM brands WHERE name='Kia'), 'Rio', 'citadino', 'economico', '2017-presente'),
((SELECT id FROM brands WHERE name='Ford'), 'Fiesta', 'citadino', 'economico', '2017-2023'),
((SELECT id FROM brands WHERE name='Nissan'), 'Micra', 'citadino', 'economico', '2017-2024'),
((SELECT id FROM brands WHERE name='Mazda'), '2', 'citadino', 'economico', '2014-presente'),
((SELECT id FROM brands WHERE name='Honda'), 'Jazz', 'citadino', 'economico', '2020-presente'),
((SELECT id FROM brands WHERE name='Fiat'), '500', 'citadino', 'economico', '2007-presente'),
((SELECT id FROM brands WHERE name='Fiat'), 'Panda', 'citadino', 'economico', '2011-presente'),
((SELECT id FROM brands WHERE name='Toyota'), 'Aygo X', 'citadino', 'economico', '2022-presente'),
((SELECT id FROM brands WHERE name='Hyundai'), 'i10', 'citadino', 'economico', '2019-presente'),
((SELECT id FROM brands WHERE name='Kia'), 'Picanto', 'citadino', 'economico', '2017-presente'),
((SELECT id FROM brands WHERE name='Volkswagen'), 'up!', 'citadino', 'economico', '2011-2023'),
((SELECT id FROM brands WHERE name='Renault'), 'Twingo', 'citadino', 'economico', '2014-2024'),
((SELECT id FROM brands WHERE name='Citroën'), 'C1', 'citadino', 'economico', '2014-2022'),
((SELECT id FROM brands WHERE name='Peugeot'), '108', 'citadino', 'economico', '2014-2022'),
((SELECT id FROM brands WHERE name='Opel'), 'Adam', 'citadino', 'economico', '2012-2019');

-- ============================================================
-- VEHICLE MODELS — CATEGORY 2: COMPACTOS (35)
-- ============================================================

INSERT INTO vehicle_models (brand_id, name, body_type, segment, years_produced) VALUES
((SELECT id FROM brands WHERE name='Volkswagen'), 'Golf', 'compacto', 'medio', '2019-presente'),
((SELECT id FROM brands WHERE name='Peugeot'), '308', 'compacto', 'medio', '2021-presente'),
((SELECT id FROM brands WHERE name='Renault'), 'Mégane', 'compacto', 'medio', '2016-2023'),
((SELECT id FROM brands WHERE name='Toyota'), 'Corolla', 'compacto', 'medio', '2019-presente'),
((SELECT id FROM brands WHERE name='SEAT'), 'Leon', 'compacto', 'medio', '2020-presente'),
((SELECT id FROM brands WHERE name='Skoda'), 'Octavia', 'compacto', 'medio', '2020-presente'),
((SELECT id FROM brands WHERE name='Ford'), 'Focus', 'compacto', 'medio', '2018-2025'),
((SELECT id FROM brands WHERE name='Opel'), 'Astra', 'compacto', 'medio', '2021-presente'),
((SELECT id FROM brands WHERE name='Hyundai'), 'i30', 'compacto', 'medio', '2017-presente'),
((SELECT id FROM brands WHERE name='Kia'), 'Ceed', 'compacto', 'medio', '2018-presente'),
((SELECT id FROM brands WHERE name='Mazda'), '3', 'compacto', 'medio', '2019-presente'),
((SELECT id FROM brands WHERE name='Honda'), 'Civic', 'compacto', 'medio', '2022-presente'),
((SELECT id FROM brands WHERE name='Audi'), 'A3', 'compacto', 'premium', '2020-presente'),
((SELECT id FROM brands WHERE name='BMW'), 'Série 1', 'compacto', 'premium', '2019-presente'),
((SELECT id FROM brands WHERE name='Mercedes-Benz'), 'Classe A', 'compacto', 'premium', '2018-presente'),
((SELECT id FROM brands WHERE name='Volvo'), 'V40', 'compacto', 'premium', '2012-2019'),
((SELECT id FROM brands WHERE name='Cupra'), 'Leon', 'compacto', 'premium', '2020-presente'),
((SELECT id FROM brands WHERE name='DS'), '4', 'compacto', 'premium', '2021-presente'),
((SELECT id FROM brands WHERE name='Citroën'), 'C4', 'compacto', 'medio', '2020-presente'),
((SELECT id FROM brands WHERE name='Fiat'), 'Tipo', 'compacto', 'economico', '2015-presente'),
((SELECT id FROM brands WHERE name='Skoda'), 'Scala', 'compacto', 'medio', '2019-presente'),
((SELECT id FROM brands WHERE name='Volkswagen'), 'ID.3', 'compacto', 'medio', '2020-presente'),
((SELECT id FROM brands WHERE name='MG'), '4', 'compacto', 'economico', '2022-presente'),
((SELECT id FROM brands WHERE name='Renault'), '5 E-Tech', 'citadino', 'medio', '2024-presente'),
((SELECT id FROM brands WHERE name='Peugeot'), 'E-308', 'compacto', 'medio', '2023-presente'),
((SELECT id FROM brands WHERE name='Toyota'), 'Prius', 'compacto', 'medio', '2023-presente'),
((SELECT id FROM brands WHERE name='Hyundai'), 'Ioniq', 'compacto', 'medio', '2016-2022'),
((SELECT id FROM brands WHERE name='Honda'), 'e:Ny1', 'compacto', 'medio', '2023-presente'),
((SELECT id FROM brands WHERE name='MINI'), 'Cooper', 'compacto', 'premium', '2014-presente'),
((SELECT id FROM brands WHERE name='Audi'), 'A1', 'citadino', 'premium', '2018-presente'),
((SELECT id FROM brands WHERE name='Mercedes-Benz'), 'CLA', 'compacto', 'premium', '2019-presente'),
((SELECT id FROM brands WHERE name='BMW'), 'Série 2 Gran Coupé', 'compacto', 'premium', '2020-presente'),
((SELECT id FROM brands WHERE name='Skoda'), 'Superb', 'berlina', 'medio', '2019-presente'),
((SELECT id FROM brands WHERE name='Volkswagen'), 'Passat', 'berlina', 'medio', '2019-presente'),
((SELECT id FROM brands WHERE name='Peugeot'), '508', 'berlina', 'medio', '2018-presente');

-- ============================================================
-- VEHICLE MODELS — CATEGORY 3: SUVs PEQUENOS E MÉDIOS (40)
-- ============================================================

INSERT INTO vehicle_models (brand_id, name, body_type, segment, years_produced) VALUES
((SELECT id FROM brands WHERE name='Peugeot'), '2008', 'suv', 'economico', '2019-presente'),
((SELECT id FROM brands WHERE name='Renault'), 'Captur', 'suv', 'economico', '2019-presente'),
((SELECT id FROM brands WHERE name='Dacia'), 'Duster', 'suv', 'economico', '2018-presente'),
((SELECT id FROM brands WHERE name='Nissan'), 'Qashqai', 'suv', 'medio', '2021-presente'),
((SELECT id FROM brands WHERE name='Peugeot'), '3008', 'suv', 'medio', '2020-presente'),
((SELECT id FROM brands WHERE name='Hyundai'), 'Tucson', 'suv', 'medio', '2020-presente'),
((SELECT id FROM brands WHERE name='Kia'), 'Sportage', 'suv', 'medio', '2021-presente'),
((SELECT id FROM brands WHERE name='Volkswagen'), 'T-Roc', 'suv', 'medio', '2017-presente'),
((SELECT id FROM brands WHERE name='Volkswagen'), 'Tiguan', 'suv', 'medio', '2020-presente'),
((SELECT id FROM brands WHERE name='Toyota'), 'C-HR', 'suv', 'medio', '2016-presente'),
((SELECT id FROM brands WHERE name='Toyota'), 'RAV4', 'suv', 'medio', '2018-presente'),
((SELECT id FROM brands WHERE name='SEAT'), 'Arona', 'suv', 'economico', '2017-presente'),
((SELECT id FROM brands WHERE name='SEAT'), 'Ateca', 'suv', 'medio', '2016-presente'),
((SELECT id FROM brands WHERE name='Skoda'), 'Kamiq', 'suv', 'economico', '2019-presente'),
((SELECT id FROM brands WHERE name='Skoda'), 'Karoq', 'suv', 'medio', '2017-presente'),
((SELECT id FROM brands WHERE name='Skoda'), 'Kodiaq', 'suv', 'medio', '2016-presente'),
((SELECT id FROM brands WHERE name='Ford'), 'Puma', 'suv', 'economico', '2019-presente'),
((SELECT id FROM brands WHERE name='Ford'), 'Kuga', 'suv', 'medio', '2020-presente'),
((SELECT id FROM brands WHERE name='Nissan'), 'Juke', 'suv', 'economico', '2019-presente'),
((SELECT id FROM brands WHERE name='Hyundai'), 'Kona', 'suv', 'economico', '2017-presente'),
((SELECT id FROM brands WHERE name='Hyundai'), 'Bayon', 'suv', 'economico', '2021-presente'),
((SELECT id FROM brands WHERE name='Kia'), 'Stonic', 'suv', 'economico', '2017-presente'),
((SELECT id FROM brands WHERE name='Kia'), 'Niro', 'suv', 'medio', '2022-presente'),
((SELECT id FROM brands WHERE name='Mazda'), 'CX-3', 'suv', 'economico', '2015-presente'),
((SELECT id FROM brands WHERE name='Mazda'), 'CX-30', 'suv', 'medio', '2019-presente'),
((SELECT id FROM brands WHERE name='Mazda'), 'CX-5', 'suv', 'medio', '2017-presente'),
((SELECT id FROM brands WHERE name='Honda'), 'HR-V', 'suv', 'economico', '2021-presente'),
((SELECT id FROM brands WHERE name='Honda'), 'CR-V', 'suv', 'medio', '2018-presente'),
((SELECT id FROM brands WHERE name='Opel'), 'Mokka', 'suv', 'economico', '2020-presente'),
((SELECT id FROM brands WHERE name='Opel'), 'Grandland', 'suv', 'medio', '2021-presente'),
((SELECT id FROM brands WHERE name='Citroën'), 'C3 Aircross', 'suv', 'economico', '2017-presente'),
((SELECT id FROM brands WHERE name='Citroën'), 'C5 Aircross', 'suv', 'medio', '2018-presente'),
((SELECT id FROM brands WHERE name='Renault'), 'Kadjar', 'suv', 'medio', '2015-2022'),
((SELECT id FROM brands WHERE name='Renault'), 'Austral', 'suv', 'medio', '2022-presente'),
((SELECT id FROM brands WHERE name='Renault'), 'Arkana', 'suv', 'medio', '2021-presente'),
((SELECT id FROM brands WHERE name='Volkswagen'), 'T-Cross', 'suv', 'economico', '2019-presente'),
((SELECT id FROM brands WHERE name='Toyota'), 'Yaris Cross', 'suv', 'economico', '2021-presente'),
((SELECT id FROM brands WHERE name='BMW'), 'X1', 'suv', 'premium', '2022-presente'),
((SELECT id FROM brands WHERE name='Mercedes-Benz'), 'GLA', 'suv', 'premium', '2020-presente'),
((SELECT id FROM brands WHERE name='Audi'), 'Q2', 'suv', 'premium', '2016-presente');

-- ============================================================
-- VEHICLE MODELS — CATEGORY 4: BERLINAS E PREMIUM MÉDIO (25)
-- ============================================================

INSERT INTO vehicle_models (brand_id, name, body_type, segment, years_produced) VALUES
((SELECT id FROM brands WHERE name='BMW'), 'Série 3', 'berlina', 'premium', '2018-presente'),
((SELECT id FROM brands WHERE name='Mercedes-Benz'), 'Classe C', 'berlina', 'premium', '2021-presente'),
((SELECT id FROM brands WHERE name='Audi'), 'A4', 'berlina', 'premium', '2019-presente'),
((SELECT id FROM brands WHERE name='Volvo'), 'S60', 'berlina', 'premium', '2019-presente'),
((SELECT id FROM brands WHERE name='Volvo'), 'V60', 'carrinha', 'premium', '2018-presente'),
((SELECT id FROM brands WHERE name='Alfa Romeo'), 'Giulia', 'berlina', 'premium', '2016-presente'),
((SELECT id FROM brands WHERE name='Skoda'), 'Superb Combi', 'carrinha', 'medio', '2019-presente'),
((SELECT id FROM brands WHERE name='BMW'), 'Série 5', 'berlina', 'premium', '2023-presente'),
((SELECT id FROM brands WHERE name='Mercedes-Benz'), 'Classe E', 'berlina', 'premium', '2023-presente'),
((SELECT id FROM brands WHERE name='Audi'), 'A6', 'berlina', 'premium', '2018-presente'),
((SELECT id FROM brands WHERE name='Volvo'), 'S90', 'berlina', 'premium', '2016-presente'),
((SELECT id FROM brands WHERE name='Volvo'), 'V90', 'carrinha', 'premium', '2016-presente'),
((SELECT id FROM brands WHERE name='Tesla'), 'Model 3', 'berlina', 'premium', '2019-presente'),
((SELECT id FROM brands WHERE name='Tesla'), 'Model Y', 'suv', 'premium', '2021-presente'),
((SELECT id FROM brands WHERE name='Mercedes-Benz'), 'Classe B', 'compacto', 'premium', '2018-presente'),
((SELECT id FROM brands WHERE name='Audi'), 'Q3', 'suv', 'premium', '2019-presente'),
((SELECT id FROM brands WHERE name='BMW'), 'X3', 'suv', 'premium', '2022-presente'),
((SELECT id FROM brands WHERE name='Mercedes-Benz'), 'GLC', 'suv', 'premium', '2022-presente'),
((SELECT id FROM brands WHERE name='Audi'), 'Q5', 'suv', 'premium', '2020-presente'),
((SELECT id FROM brands WHERE name='Volvo'), 'XC40', 'suv', 'premium', '2018-presente'),
((SELECT id FROM brands WHERE name='Volvo'), 'XC60', 'suv', 'premium', '2017-presente'),
((SELECT id FROM brands WHERE name='Cupra'), 'Formentor', 'suv', 'premium', '2020-presente'),
((SELECT id FROM brands WHERE name='Cupra'), 'Ateca', 'suv', 'premium', '2020-presente'),
((SELECT id FROM brands WHERE name='Lexus'), 'UX', 'suv', 'premium', '2018-presente'),
((SELECT id FROM brands WHERE name='Lexus'), 'NX', 'suv', 'premium', '2021-presente');

-- ============================================================
-- VEHICLE MODELS — CATEGORY 5: PREMIUM E LUXO (20)
-- ============================================================

INSERT INTO vehicle_models (brand_id, name, body_type, segment, years_produced) VALUES
((SELECT id FROM brands WHERE name='Land Rover'), 'Range Rover Evoque', 'suv', 'premium', '2019-presente'),
((SELECT id FROM brands WHERE name='Land Rover'), 'Range Rover Velar', 'suv', 'premium', '2017-presente'),
((SELECT id FROM brands WHERE name='Land Rover'), 'Range Rover Sport', 'suv', 'luxo', '2022-presente'),
((SELECT id FROM brands WHERE name='Land Rover'), 'Discovery Sport', 'suv', 'premium', '2019-presente'),
((SELECT id FROM brands WHERE name='Land Rover'), 'Defender', 'suv', 'premium', '2020-presente'),
((SELECT id FROM brands WHERE name='Porsche'), 'Macan', 'suv', 'luxo', '2019-presente'),
((SELECT id FROM brands WHERE name='Porsche'), 'Cayenne', 'suv', 'luxo', '2018-presente'),
((SELECT id FROM brands WHERE name='BMW'), 'X5', 'suv', 'premium', '2019-presente'),
((SELECT id FROM brands WHERE name='BMW'), 'X6', 'suv', 'luxo', '2019-presente'),
((SELECT id FROM brands WHERE name='Mercedes-Benz'), 'GLE', 'suv', 'premium', '2019-presente'),
((SELECT id FROM brands WHERE name='Mercedes-Benz'), 'GLS', 'suv', 'luxo', '2019-presente'),
((SELECT id FROM brands WHERE name='Audi'), 'Q7', 'suv', 'premium', '2019-presente'),
((SELECT id FROM brands WHERE name='Audi'), 'Q8', 'suv', 'luxo', '2018-presente'),
((SELECT id FROM brands WHERE name='Volvo'), 'XC90', 'suv', 'premium', '2015-presente'),
((SELECT id FROM brands WHERE name='Alfa Romeo'), 'Stelvio', 'suv', 'premium', '2017-presente'),
((SELECT id FROM brands WHERE name='Jaguar'), 'F-Pace', 'suv', 'premium', '2016-presente'),
((SELECT id FROM brands WHERE name='Jaguar'), 'E-Pace', 'suv', 'premium', '2017-presente'),
((SELECT id FROM brands WHERE name='Maserati'), 'Grecale', 'suv', 'luxo', '2022-presente'),
((SELECT id FROM brands WHERE name='Lexus'), 'RX', 'suv', 'premium', '2022-presente'),
((SELECT id FROM brands WHERE name='Porsche'), 'Panamera', 'berlina', 'luxo', '2016-presente');

-- ============================================================
-- VEHICLE MODELS — CATEGORY 6: MPV E FAMILIAR (15)
-- ============================================================

INSERT INTO vehicle_models (brand_id, name, body_type, segment, years_produced) VALUES
((SELECT id FROM brands WHERE name='Dacia'), 'Jogger', 'mpv', 'economico', '2022-presente'),
((SELECT id FROM brands WHERE name='Renault'), 'Scénic', 'mpv', 'medio', '2024-presente'),
((SELECT id FROM brands WHERE name='Citroën'), 'Berlingo', 'mpv', 'economico', '2018-presente'),
((SELECT id FROM brands WHERE name='Peugeot'), 'Rifter', 'mpv', 'economico', '2018-presente'),
((SELECT id FROM brands WHERE name='Opel'), 'Combo Life', 'mpv', 'economico', '2018-presente'),
((SELECT id FROM brands WHERE name='Volkswagen'), 'Touran', 'mpv', 'medio', '2015-presente'),
((SELECT id FROM brands WHERE name='Volkswagen'), 'Caddy', 'mpv', 'economico', '2020-presente'),
((SELECT id FROM brands WHERE name='Ford'), 'Tourneo Connect', 'mpv', 'economico', '2022-presente'),
((SELECT id FROM brands WHERE name='Ford'), 'S-Max', 'mpv', 'medio', '2015-2023'),
((SELECT id FROM brands WHERE name='SEAT'), 'Alhambra', 'mpv', 'medio', '2010-2020'),
((SELECT id FROM brands WHERE name='Volkswagen'), 'Sharan', 'mpv', 'medio', '2010-2022'),
((SELECT id FROM brands WHERE name='Mercedes-Benz'), 'Classe V', 'mpv', 'premium', '2014-presente'),
((SELECT id FROM brands WHERE name='Toyota'), 'Proace City Verso', 'mpv', 'economico', '2019-presente'),
((SELECT id FROM brands WHERE name='Peugeot'), '5008', 'suv', 'medio', '2020-presente'),
((SELECT id FROM brands WHERE name='BMW'), 'Série 2 Active Tourer', 'mpv', 'premium', '2022-presente');

-- ============================================================
-- VEHICLE MODELS — CATEGORY 7: ELÉTRICOS E EMERGENTES (15)
-- ============================================================

INSERT INTO vehicle_models (brand_id, name, body_type, segment, years_produced) VALUES
((SELECT id FROM brands WHERE name='BYD'), 'Dolphin', 'compacto', 'economico', '2023-presente'),
((SELECT id FROM brands WHERE name='BYD'), 'Atto 3', 'suv', 'medio', '2022-presente'),
((SELECT id FROM brands WHERE name='BYD'), 'Seal', 'berlina', 'medio', '2023-presente'),
((SELECT id FROM brands WHERE name='MG'), 'ZS EV', 'suv', 'economico', '2019-presente'),
((SELECT id FROM brands WHERE name='MG'), 'HS', 'suv', 'medio', '2020-presente'),
((SELECT id FROM brands WHERE name='MG'), '5', 'carrinha', 'economico', '2022-presente'),
((SELECT id FROM brands WHERE name='Omoda'), '5', 'suv', 'medio', '2024-presente'),
((SELECT id FROM brands WHERE name='Smart'), '#1', 'suv', 'premium', '2023-presente'),
((SELECT id FROM brands WHERE name='Smart'), '#3', 'compacto', 'premium', '2024-presente'),
((SELECT id FROM brands WHERE name='Volvo'), 'EX30', 'suv', 'premium', '2024-presente'),
((SELECT id FROM brands WHERE name='Kia'), 'EV3', 'suv', 'medio', '2024-presente'),
((SELECT id FROM brands WHERE name='Kia'), 'EV6', 'compacto', 'premium', '2021-presente'),
((SELECT id FROM brands WHERE name='Hyundai'), 'Ioniq 5', 'suv', 'premium', '2021-presente'),
((SELECT id FROM brands WHERE name='Hyundai'), 'Ioniq 6', 'berlina', 'premium', '2023-presente'),
((SELECT id FROM brands WHERE name='Tesla'), 'Model S', 'berlina', 'luxo', '2012-presente');

-- ============================================================
-- VEHICLE MODELS — CATEGORY 8: ENTUSIASTA E NICHO (25)
-- ============================================================

INSERT INTO vehicle_models (brand_id, name, body_type, segment, years_produced) VALUES
((SELECT id FROM brands WHERE name='BMW'), 'Série 4', 'compacto', 'premium', '2020-presente'),
((SELECT id FROM brands WHERE name='BMW'), 'Z4', 'compacto', 'premium', '2018-presente'),
((SELECT id FROM brands WHERE name='Toyota'), 'GR Yaris', 'citadino', 'premium', '2020-presente'),
((SELECT id FROM brands WHERE name='Toyota'), 'GR86', 'compacto', 'premium', '2022-presente'),
((SELECT id FROM brands WHERE name='Mazda'), 'MX-5', 'compacto', 'medio', '2015-presente'),
((SELECT id FROM brands WHERE name='Audi'), 'TT', 'compacto', 'premium', '2014-presente'),
((SELECT id FROM brands WHERE name='Audi'), 'A5', 'berlina', 'premium', '2019-presente'),
((SELECT id FROM brands WHERE name='Mercedes-Benz'), 'CLE', 'compacto', 'premium', '2024-presente'),
((SELECT id FROM brands WHERE name='Ford'), 'Mustang', 'compacto', 'premium', '2015-presente'),
((SELECT id FROM brands WHERE name='Alpine'), 'A110', 'compacto', 'premium', '2017-presente'),
((SELECT id FROM brands WHERE name='MINI'), 'Clubman', 'compacto', 'premium', '2015-presente'),
((SELECT id FROM brands WHERE name='MINI'), 'Countryman', 'suv', 'premium', '2023-presente'),
((SELECT id FROM brands WHERE name='Jeep'), 'Avenger', 'suv', 'medio', '2023-presente'),
((SELECT id FROM brands WHERE name='Jeep'), 'Compass', 'suv', 'medio', '2017-presente'),
((SELECT id FROM brands WHERE name='Fiat'), '500X', 'suv', 'economico', '2014-presente'),
((SELECT id FROM brands WHERE name='DS'), '7', 'suv', 'premium', '2018-presente'),
((SELECT id FROM brands WHERE name='Lexus'), 'IS', 'berlina', 'premium', '2013-presente'),
((SELECT id FROM brands WHERE name='Lexus'), 'ES', 'berlina', 'premium', '2018-presente'),
((SELECT id FROM brands WHERE name='Subaru'), 'Outback', 'carrinha', 'medio', '2021-presente'),
((SELECT id FROM brands WHERE name='Subaru'), 'Forester', 'suv', 'medio', '2019-presente'),
((SELECT id FROM brands WHERE name='Subaru'), 'BRZ', 'compacto', 'medio', '2022-presente'),
((SELECT id FROM brands WHERE name='Suzuki'), 'Swift', 'citadino', 'economico', '2017-presente'),
((SELECT id FROM brands WHERE name='Suzuki'), 'Vitara', 'suv', 'economico', '2018-presente'),
((SELECT id FROM brands WHERE name='Suzuki'), 'S-Cross', 'suv', 'economico', '2022-presente');

-- Falta Mercedes E Coupé — adicionado como variante
INSERT INTO vehicle_models (brand_id, name, body_type, segment, years_produced) VALUES
((SELECT id FROM brands WHERE name='Mercedes-Benz'), 'E Coupé', 'compacto', 'luxo', '2017-2023');
-- ============================================================
-- CARACTR DATABASE v3.0 — AUTO-GENERATED SEED
-- 128 modelos
-- ============================================================


-- ── Renault Clio ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.0 TCe 90', 'gasolina', 999, 90, 160, 'manual 5', 5.8, 131, 7.0, 380
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Clio' AND b.name = 'Renault';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.0 TCe 100 LPG', 'gpl', 999, 100, 160, 'manual 5', 6.5, 120, 7.0, 350
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Clio' AND b.name = 'Renault';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.6 E-Tech 145 Híbrido', 'hibrido', 1598, 145, 205, 'auto', 4.3, 98, 7.5, 350
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Clio' AND b.name = 'Renault';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 7, 5, 8, 6, 5, 'baixo', 'Polivalente e confortável para a classe. Bom compromisso para uso diário em cidade e estrada.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Clio' AND b.name = 'Renault';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 15500, 12000, 19000, 45, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Clio' AND b.name = 'Renault';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2021, 13500, 10500, 17000, 52, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Clio' AND b.name = 'Renault';

-- ── Peugeot 208 ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.2 PureTech 100', 'gasolina', 1199, 100, 205, 'manual 6', 5.5, 125, 6.5, 420
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = '208' AND b.name = 'Peugeot';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.2 PureTech 130 EAT8', 'gasolina', 1199, 130, 230, 'auto 8', 5.8, 132, 6.0, 450
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = '208' AND b.name = 'Peugeot';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, 'e-208 136cv', 'eletrico', 0, 136, 260, 'auto', 15.0, 0, 8.0, 200
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = '208' AND b.name = 'Peugeot';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 7, 6, 9, 6, 4, 'baixo', 'Interior premium para o segmento. i-Cockpit polariza mas é moderno. Ágil na cidade.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = '208' AND b.name = 'Peugeot';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 17000, 13500, 21000, 40, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = '208' AND b.name = 'Peugeot';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2021, 14500, 11000, 18500, 48, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = '208' AND b.name = 'Peugeot';
INSERT INTO engine_issues (engine_id, severity, description, affected_years, fix_cost_estimate, source)
SELECT e.id, 'medio', 'Motor 1.2 PureTech com correia húmida — verificar manutenção. Recall aplicado em 2021.', '2019-2021', '600-1200€', 'PSA/Stellantis recall'
FROM engines e JOIN vehicle_models vm ON e.model_id = vm.id JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = '208' AND b.name = 'Peugeot' LIMIT 1;

-- ── Citroën C3 ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.2 PureTech 83', 'gasolina', 1199, 83, 205, 'manual 5', 5.4, 123, 7.0, 380
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'C3' AND b.name = 'Citroën';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.2 PureTech 110', 'gasolina', 1199, 110, 205, 'manual 6', 5.6, 127, 6.5, 400
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'C3' AND b.name = 'Citroën';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 7, 4, 8, 5, 5, 'baixo', 'Confortável com suspensão macia. Design simpático. Pouco entusiasmante mas agradável.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'C3' AND b.name = 'Citroën';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 13000, 10000, 16500, 38, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'C3' AND b.name = 'Citroën';

-- ── Dacia Sandero ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.0 TCe 90', 'gasolina', 999, 90, 160, 'manual 5', 5.7, 129, 7.0, 300
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Sandero' AND b.name = 'Dacia';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.0 TCe 100 Bi-Fuel', 'gpl', 999, 100, 170, 'manual 6', 6.3, 115, 7.0, 280
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Sandero' AND b.name = 'Dacia';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.0 TCe 90 CVT', 'gasolina', 999, 90, 160, 'auto cvt', 6.0, 136, 6.5, 320
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Sandero' AND b.name = 'Dacia';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 5, 4, 7, 6, 6, 'medio', 'Relação qualidade-preço imbatível. Espaço surpreendente. Sem luxos mas honesto.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Sandero' AND b.name = 'Dacia';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 12000, 9500, 15000, 55, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Sandero' AND b.name = 'Dacia';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2023, 13500, 11000, 16500, 35, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Sandero' AND b.name = 'Dacia';

-- ── Opel Corsa ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.2 PureTech 75', 'gasolina', 1199, 75, 118, 'manual 5', 5.5, 125, 7.0, 380
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Corsa' AND b.name = 'Opel';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.2 PureTech 100', 'gasolina', 1199, 100, 205, 'manual 6', 5.6, 127, 6.5, 400
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Corsa' AND b.name = 'Opel';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, 'Corsa-e 136cv', 'eletrico', 0, 136, 260, 'auto', 15.5, 0, 8.0, 200
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Corsa' AND b.name = 'Opel';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 6, 5, 8, 6, 4, 'baixo', 'Base Peugeot 208 com personalidade mais discreta. Ergonomia alemã, plataforma francesa.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Corsa' AND b.name = 'Opel';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 15000, 12000, 18500, 35, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Corsa' AND b.name = 'Opel';

-- ── Toyota Yaris ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.5 Híbrido 116cv', 'hibrido', 1490, 116, 120, 'auto cvt', 3.8, 87, 9.5, 280
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Yaris' AND b.name = 'Toyota';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.5 VVT-i 125cv', 'gasolina', 1490, 125, 153, 'manual 6', 5.6, 127, 8.5, 300
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Yaris' AND b.name = 'Toyota';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 7, 5, 9, 6, 4, 'baixo', 'Híbrido exemplar para cidade. Consumos reais impressionantes. Fiabilidade Toyota.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Yaris' AND b.name = 'Toyota';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 17500, 14500, 21000, 42, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Yaris' AND b.name = 'Toyota';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2021, 15500, 12500, 19000, 50, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Yaris' AND b.name = 'Toyota';

-- ── Volkswagen Polo ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.0 TSI 95', 'gasolina', 999, 95, 175, 'manual 5', 5.4, 123, 7.5, 400
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Polo' AND b.name = 'Volkswagen';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.0 TSI 110 DSG', 'gasolina', 999, 110, 200, 'auto 7', 5.6, 128, 7.0, 450
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Polo' AND b.name = 'Volkswagen';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 7, 5, 8, 7, 5, 'baixo', 'Mini Golf. Qualidade de construção acima da média do segmento. Discreto mas sólido.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Polo' AND b.name = 'Volkswagen';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 16500, 13000, 20000, 40, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Polo' AND b.name = 'Volkswagen';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2020, 13000, 10000, 16500, 55, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Polo' AND b.name = 'Volkswagen';

-- ── SEAT Ibiza ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.0 TSI 95', 'gasolina', 999, 95, 175, 'manual 5', 5.3, 121, 7.5, 380
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Ibiza' AND b.name = 'SEAT';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.0 TSI 110', 'gasolina', 999, 110, 200, 'manual 6', 5.5, 125, 7.0, 400
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Ibiza' AND b.name = 'SEAT';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 6, 6, 8, 7, 5, 'baixo', 'Versão ibérica do Polo. Mais dinâmico, suspensão mais firme. Bom para quem gosta de conduzir.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Ibiza' AND b.name = 'SEAT';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 14500, 11500, 18000, 38, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Ibiza' AND b.name = 'SEAT';

-- ── Skoda Fabia ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.0 TSI 95', 'gasolina', 999, 95, 175, 'manual 5', 5.2, 119, 7.5, 370
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Fabia' AND b.name = 'Skoda';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.0 TSI 110', 'gasolina', 999, 110, 200, 'manual 6', 5.4, 123, 7.0, 390
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Fabia' AND b.name = 'Skoda';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 7, 5, 8, 7, 6, 'baixo', 'O maior do segmento. Espaço de compacto num citadino. Prático, racional, sem fitas.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Fabia' AND b.name = 'Skoda';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 15000, 12000, 18500, 32, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Fabia' AND b.name = 'Skoda';

-- ── Hyundai i20 ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.0 T-GDi 100', 'gasolina', 998, 100, 172, 'manual 5', 5.5, 125, 8.0, 350
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'i20' AND b.name = 'Hyundai';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.2 MPI 84', 'gasolina', 1197, 84, 118, 'manual 5', 5.8, 132, 8.5, 320
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'i20' AND b.name = 'Hyundai';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 7, 5, 8, 6, 5, 'baixo', 'Bem equipado e bem construído. 5 anos de garantia. Opção segura e sem surpresas.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'i20' AND b.name = 'Hyundai';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 14000, 11000, 17500, 30, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'i20' AND b.name = 'Hyundai';

-- ── Kia Rio ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.0 T-GDi 100', 'gasolina', 998, 100, 172, 'manual 6', 5.4, 123, 8.0, 350
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Rio' AND b.name = 'Kia';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.0 T-GDi 120 DCT', 'gasolina', 998, 120, 172, 'auto 7', 5.7, 130, 7.5, 380
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Rio' AND b.name = 'Kia';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 6, 5, 8, 6, 5, 'baixo', 'Gémeo do i20 com design diferente. 7 anos de garantia de fábrica. Imbatível em tranquilidade.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Rio' AND b.name = 'Kia';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 13500, 10500, 17000, 28, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Rio' AND b.name = 'Kia';

-- ── Ford Fiesta ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.0 EcoBoost 100', 'gasolina', 999, 100, 170, 'manual 6', 5.5, 125, 7.0, 400
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Fiesta' AND b.name = 'Ford';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.0 EcoBoost 125', 'gasolina', 999, 125, 170, 'manual 6', 5.7, 130, 7.0, 420
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Fiesta' AND b.name = 'Ford';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.5 EcoBoost 200 ST', 'gasolina', 1497, 200, 290, 'manual 6', 7.2, 164, 7.0, 500
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Fiesta' AND b.name = 'Ford';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 6, 8, 8, 7, 4, 'baixo', 'Referência de condução no segmento. Chassis brilhante. Descontinuado mas ainda muito relevante em usados.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Fiesta' AND b.name = 'Ford';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 14500, 11000, 18000, 45, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Fiesta' AND b.name = 'Ford';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2020, 11500, 8500, 15000, 60, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Fiesta' AND b.name = 'Ford';
INSERT INTO engine_issues (engine_id, severity, description, affected_years, fix_cost_estimate, source)
SELECT e.id, 'baixo', 'Motor 1.0 EcoBoost pré-2017: problema de arrefecimento. Versões 2017+ corrigidas.', '2014-2017', '800-1500€', 'Ford TSB'
FROM engines e JOIN vehicle_models vm ON e.model_id = vm.id JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Fiesta' AND b.name = 'Ford' LIMIT 1;

-- ── Nissan Micra ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.0 IG-T 92', 'gasolina', 999, 92, 160, 'manual 5', 5.4, 123, 7.5, 350
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Micra' AND b.name = 'Nissan';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '0.9 IG-T 90', 'gasolina', 898, 90, 140, 'manual 5', 5.0, 114, 7.0, 340
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Micra' AND b.name = 'Nissan';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 6, 5, 8, 5, 4, 'medio', 'Compacto e bem desenhado. Posição de condução agradável. Motor 0.9 um pouco justo.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Micra' AND b.name = 'Nissan';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 12500, 9500, 16000, 25, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Micra' AND b.name = 'Nissan';

-- ── Mazda 2 ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.5 Skyactiv-G 90', 'gasolina', 1496, 90, 148, 'manual 6', 5.4, 123, 8.5, 350
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = '2' AND b.name = 'Mazda';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.5 Híbrido 116', 'hibrido', 1490, 116, 120, 'auto cvt', 3.8, 87, 9.5, 280
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = '2' AND b.name = 'Mazda';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 7, 6, 8, 6, 4, 'baixo', 'Versão rebadged do Yaris com identidade Mazda. Híbrido Toyota debaixo do capô. Fiável e refinado.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = '2' AND b.name = 'Mazda';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2024, 19000, 17000, 22000, 15, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = '2' AND b.name = 'Mazda';

-- ── Honda Jazz ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.5 e:HEV 109', 'hibrido', 1498, 109, 253, 'auto cvt', 4.5, 102, 9.0, 300
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Jazz' AND b.name = 'Honda';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 7, 4, 9, 6, 6, 'baixo', 'Mestre do espaço interior. Bancos Magic Seats geniais. Híbrido eficiente. Aborrecido mas brilhante.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Jazz' AND b.name = 'Honda';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 19000, 16000, 23000, 20, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Jazz' AND b.name = 'Honda';

-- ── Fiat 500 ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.0 Mild Hybrid 70', 'hibrido', 999, 70, 92, 'manual 6', 4.9, 112, 7.0, 350
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = '500' AND b.name = 'Fiat';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '500e 118cv', 'eletrico', 0, 118, 220, 'auto', 14.5, 0, 7.5, 220
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = '500' AND b.name = 'Fiat';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 5, 5, 9, 4, 3, 'medio', 'Ícone de estilo urbano. Perfeito para a cidade, limitado fora dela. O elétrico é o futuro do modelo.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = '500' AND b.name = 'Fiat';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 12000, 8500, 16000, 35, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = '500' AND b.name = 'Fiat';

-- ── Fiat Panda ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.0 Mild Hybrid 70', 'hibrido', 999, 70, 92, 'manual 6', 5.0, 114, 7.0, 300
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Panda' AND b.name = 'Fiat';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 5, 3, 8, 4, 5, 'medio', 'Utilitário puro. Simples, barato, funcional. Surpreendente em espaço. Zero pretensões.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Panda' AND b.name = 'Fiat';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 10500, 8000, 13500, 30, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Panda' AND b.name = 'Fiat';

-- ── Toyota Aygo X ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.0 VVT-i 72', 'gasolina', 998, 72, 93, 'manual 5', 4.9, 112, 9.0, 250
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Aygo X' AND b.name = 'Toyota';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 5, 4, 9, 4, 3, 'medio', 'Citadino puro com estilo crossover. Motor pequeno mas fiável. Perfeito para cidade e estacionar.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Aygo X' AND b.name = 'Toyota';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2023, 14500, 12000, 17000, 18, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Aygo X' AND b.name = 'Toyota';

-- ── Hyundai i10 ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.0 MPI 67', 'gasolina', 998, 67, 96, 'manual 5', 5.0, 114, 8.5, 280
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'i10' AND b.name = 'Hyundai';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.2 MPI 84', 'gasolina', 1197, 84, 118, 'manual 5', 5.3, 121, 8.5, 290
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'i10' AND b.name = 'Hyundai';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 5, 4, 9, 4, 3, 'medio', 'Pequeno mas surpreendentemente bem feito. Ideal para primeiros carros e cidade pura.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'i10' AND b.name = 'Hyundai';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 11000, 8500, 14000, 22, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'i10' AND b.name = 'Hyundai';

-- ── Kia Picanto ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.0 MPI 67', 'gasolina', 998, 67, 96, 'manual 5', 4.8, 109, 8.5, 270
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Picanto' AND b.name = 'Kia';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.0 T-GDi 100', 'gasolina', 998, 100, 172, 'manual 5', 5.2, 118, 8.0, 300
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Picanto' AND b.name = 'Kia';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 5, 5, 9, 4, 3, 'medio', 'Versão T-GDi surpreendentemente animada. Garantia 7 anos. Boa opção de primeiro carro com carácter.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Picanto' AND b.name = 'Kia';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 10500, 8000, 13500, 25, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Picanto' AND b.name = 'Kia';

-- ── Volkswagen up! ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.0 MPI 65', 'gasolina', 999, 65, 95, 'manual 5', 4.9, 112, 8.0, 300
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'up!' AND b.name = 'Volkswagen';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 5, 5, 9, 4, 3, 'baixo', 'Citadino alemão com qualidade sólida. Descontinuado mas excelente em usados. Económico e fiável.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'up!' AND b.name = 'Volkswagen';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2020, 8500, 6000, 11500, 40, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'up!' AND b.name = 'Volkswagen';

-- ── Renault Twingo ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.0 SCe 65', 'gasolina', 999, 65, 95, 'manual 5', 5.2, 118, 6.5, 320
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Twingo' AND b.name = 'Renault';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 5, 5, 9, 3, 3, 'medio', 'Motor traseiro, tração traseira — único no segmento. Raio de viragem minúsculo. Puro citadino.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Twingo' AND b.name = 'Renault';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2021, 9500, 7000, 12500, 28, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Twingo' AND b.name = 'Renault';

-- ── Citroën C1 ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.0 VTi 72', 'gasolina', 998, 72, 93, 'manual 5', 4.6, 105, 8.5, 250
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'C1' AND b.name = 'Citroën';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 4, 4, 9, 3, 3, 'medio', 'Gémeo do Aygo/108. Motor Toyota fiável. Minimalista mas funcional na cidade.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'C1' AND b.name = 'Citroën';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2020, 7500, 5500, 10000, 35, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'C1' AND b.name = 'Citroën';

-- ── Peugeot 108 ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.0 VTi 72', 'gasolina', 998, 72, 93, 'manual 5', 4.6, 105, 8.5, 250
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = '108' AND b.name = 'Peugeot';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 4, 4, 9, 3, 3, 'medio', 'Variante mais estilosa do trio Toyota/Citroën/Peugeot. Motor Toyota, fiabilidade assegurada.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = '108' AND b.name = 'Peugeot';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2020, 7500, 5500, 10500, 30, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = '108' AND b.name = 'Peugeot';

-- ── Opel Adam ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.2 70cv', 'gasolina', 1229, 70, 115, 'manual 5', 5.5, 125, 7.0, 350
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Adam' AND b.name = 'Opel';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 5, 4, 8, 4, 3, 'medio', 'Citadino estiloso descontinuado. Personalização era o forte. Bons preços em usados.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Adam' AND b.name = 'Opel';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2018, 7000, 5000, 9500, 20, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Adam' AND b.name = 'Opel';

-- ── Volkswagen Golf ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.0 TSI 110', 'gasolina', 999, 110, 200, 'manual 6', 5.6, 128, 7.5, 450
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Golf' AND b.name = 'Volkswagen';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.5 TSI 130', 'gasolina', 1498, 130, 200, 'manual 6', 5.8, 132, 7.5, 470
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Golf' AND b.name = 'Volkswagen';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.5 TSI 150 DSG', 'gasolina', 1498, 150, 250, 'auto 7', 6.0, 137, 7.0, 500
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Golf' AND b.name = 'Volkswagen';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '2.0 TDI 115', 'diesel', 1968, 115, 300, 'manual 6', 4.5, 119, 7.5, 480
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Golf' AND b.name = 'Volkswagen';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.4 eHybrid 204', 'hibrido', 1395, 204, 350, 'auto 6', 1.4, 32, 7.0, 520
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Golf' AND b.name = 'Volkswagen';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 8, 7, 7, 8, 6, 'baixo', 'A referência do segmento. Equilibrado em tudo. Tecnologia de topo. Nunca empolga mas nunca desilude.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Golf' AND b.name = 'Volkswagen';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 22000, 17500, 27000, 50, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Golf' AND b.name = 'Volkswagen';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2021, 19500, 15000, 24500, 60, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Golf' AND b.name = 'Volkswagen';
INSERT INTO engine_issues (engine_id, severity, description, affected_years, fix_cost_estimate, source)
SELECT e.id, 'baixo', 'DSG 7 velocidades: trocar óleo a cada 60.000km. Importante para longevidade.', '2019+', '300-400€', 'VW manutenção'
FROM engines e JOIN vehicle_models vm ON e.model_id = vm.id JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Golf' AND b.name = 'Volkswagen' LIMIT 1;

-- ── Peugeot 308 ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.2 PureTech 130', 'gasolina', 1199, 130, 230, 'manual 6', 5.8, 132, 6.5, 440
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = '308' AND b.name = 'Peugeot';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.2 PureTech 130 EAT8', 'gasolina', 1199, 130, 230, 'auto 8', 6.1, 139, 6.0, 470
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = '308' AND b.name = 'Peugeot';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.5 BlueHDi 130', 'diesel', 1499, 130, 300, 'manual 6', 4.3, 113, 7.5, 420
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = '308' AND b.name = 'Peugeot';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 7, 6, 7, 7, 6, 'baixo', 'Nova geração muito bem desenhada. Interior premium para o segmento. i-Cockpit divide opiniões.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = '308' AND b.name = 'Peugeot';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 21000, 17000, 26000, 35, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = '308' AND b.name = 'Peugeot';
INSERT INTO engine_issues (engine_id, severity, description, affected_years, fix_cost_estimate, source)
SELECT e.id, 'medio', 'Motor 1.2 PureTech: correia húmida — verificar manutenção rigorosamente.', '2021+', '600-1200€', 'Stellantis'
FROM engines e JOIN vehicle_models vm ON e.model_id = vm.id JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = '308' AND b.name = 'Peugeot' LIMIT 1;

-- ── Renault Mégane ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.3 TCe 140', 'gasolina', 1332, 140, 240, 'manual 6', 6.2, 141, 7.0, 420
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Mégane' AND b.name = 'Renault';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.3 TCe 140 EDC', 'gasolina', 1332, 140, 240, 'auto 7', 6.4, 146, 6.5, 450
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Mégane' AND b.name = 'Renault';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.5 Blue dCi 115', 'diesel', 1461, 115, 260, 'manual 6', 4.2, 111, 7.5, 400
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Mégane' AND b.name = 'Renault';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 7, 5, 7, 7, 6, 'baixo', 'Bom espaço e conforto. Motor 1.3 TCe é parceria Mercedes. Sólido mas sem brilho.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Mégane' AND b.name = 'Renault';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 18000, 14000, 22500, 40, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Mégane' AND b.name = 'Renault';

-- ── Toyota Corolla ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.8 Híbrido 122cv', 'hibrido', 1798, 122, 142, 'auto cvt', 4.5, 101, 9.5, 320
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Corolla' AND b.name = 'Toyota';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '2.0 Híbrido 196cv', 'hibrido', 1987, 196, 190, 'auto cvt', 5.0, 112, 9.0, 350
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Corolla' AND b.name = 'Toyota';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 8, 6, 8, 8, 7, 'baixo', 'Híbrido de referência. Silencioso, económico, fiável como um relógio. O 2.0 surpreende na potência.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Corolla' AND b.name = 'Toyota';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 23000, 19000, 27500, 45, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Corolla' AND b.name = 'Toyota';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2021, 20500, 17000, 24500, 55, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Corolla' AND b.name = 'Toyota';

-- ── SEAT Leon ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.0 TSI 110', 'gasolina', 999, 110, 200, 'manual 6', 5.5, 125, 7.5, 420
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Leon' AND b.name = 'SEAT';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.5 TSI 150', 'gasolina', 1498, 150, 250, 'manual 6', 5.9, 134, 7.0, 450
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Leon' AND b.name = 'SEAT';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '2.0 TDI 115', 'diesel', 1968, 115, 300, 'manual 6', 4.4, 116, 7.5, 440
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Leon' AND b.name = 'SEAT';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 7, 7, 7, 8, 6, 'baixo', 'Golf ibérico com mais carácter na condução. Suspensão mais firme, mais divertido. Mesmo nível técnico.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Leon' AND b.name = 'SEAT';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 19500, 15500, 24000, 35, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Leon' AND b.name = 'SEAT';

-- ── Skoda Octavia ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.0 TSI 110', 'gasolina', 999, 110, 200, 'manual 6', 5.4, 123, 7.5, 400
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Octavia' AND b.name = 'Skoda';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.5 TSI 150', 'gasolina', 1498, 150, 250, 'manual 6', 5.7, 130, 7.5, 430
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Octavia' AND b.name = 'Skoda';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '2.0 TDI 115', 'diesel', 1968, 115, 300, 'manual 6', 4.2, 111, 7.5, 420
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Octavia' AND b.name = 'Skoda';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '2.0 TDI 150 DSG', 'diesel', 1968, 150, 360, 'auto 7', 4.5, 119, 7.5, 460
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Octavia' AND b.name = 'Skoda';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 8, 5, 7, 9, 8, 'baixo', 'Rei do espaço-preço. Interior de berlina num compacto. Pragmático, racional, excelente em estrada.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Octavia' AND b.name = 'Skoda';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 22000, 17500, 27000, 38, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Octavia' AND b.name = 'Skoda';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2021, 19000, 15000, 23500, 45, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Octavia' AND b.name = 'Skoda';

-- ── Ford Focus ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.0 EcoBoost 125', 'gasolina', 999, 125, 170, 'manual 6', 5.7, 130, 7.0, 420
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Focus' AND b.name = 'Ford';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.5 EcoBoost 150', 'gasolina', 1497, 150, 240, 'manual 6', 6.0, 137, 7.0, 450
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Focus' AND b.name = 'Ford';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.5 EcoBlue 120', 'diesel', 1499, 120, 300, 'manual 6', 4.3, 113, 7.5, 430
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Focus' AND b.name = 'Ford';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 7, 8, 7, 8, 6, 'baixo', 'Melhor chassis do segmento. Prazer de condução genuíno. Descontinuado mas rei dos usados.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Focus' AND b.name = 'Ford';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 18500, 14500, 23000, 42, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Focus' AND b.name = 'Ford';

-- ── Opel Astra ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.2 PureTech 130', 'gasolina', 1199, 130, 230, 'manual 6', 5.8, 132, 6.5, 430
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Astra' AND b.name = 'Opel';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.5 Diesel 130', 'diesel', 1499, 130, 300, 'manual 6', 4.3, 113, 7.5, 420
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Astra' AND b.name = 'Opel';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 7, 5, 7, 7, 6, 'baixo', 'Nova geração sobre plataforma Stellantis. Design ousado. Interior moderno. Falta emoção na condução.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Astra' AND b.name = 'Opel';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2023, 22000, 18000, 26500, 20, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Astra' AND b.name = 'Opel';

-- ── Hyundai i30 ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.0 T-GDi 120', 'gasolina', 998, 120, 172, 'manual 6', 5.8, 132, 8.0, 380
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'i30' AND b.name = 'Hyundai';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.5 T-GDi 160 DCT', 'gasolina', 1482, 160, 253, 'auto 7', 6.2, 141, 7.5, 420
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'i30' AND b.name = 'Hyundai';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.6 CRDi 115', 'diesel', 1598, 115, 280, 'manual 6', 4.5, 119, 8.0, 400
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'i30' AND b.name = 'Hyundai';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 7, 6, 7, 7, 6, 'baixo', 'Bem construído e bem equipado. Design discreto. 5 anos de garantia. Escolha sensata.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'i30' AND b.name = 'Hyundai';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 18000, 14000, 22500, 32, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'i30' AND b.name = 'Hyundai';

-- ── Kia Ceed ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.0 T-GDi 120', 'gasolina', 998, 120, 172, 'manual 6', 5.7, 130, 8.0, 380
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Ceed' AND b.name = 'Kia';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.5 T-GDi 160 DCT', 'gasolina', 1482, 160, 253, 'auto 7', 6.1, 139, 7.5, 410
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Ceed' AND b.name = 'Kia';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 7, 6, 7, 7, 6, 'baixo', 'Gémeo do i30 com design mais europeu. 7 anos de garantia. Versão SW é excelente para famílias.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Ceed' AND b.name = 'Kia';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 17500, 13500, 22000, 28, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Ceed' AND b.name = 'Kia';

-- ── Mazda 3 ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '2.0 Skyactiv-G 122', 'gasolina', 1998, 122, 213, 'manual 6', 6.0, 137, 8.5, 400
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = '3' AND b.name = 'Mazda';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '2.0 Skyactiv-X 186', 'gasolina', 1998, 186, 240, 'manual 6', 5.8, 132, 8.0, 450
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = '3' AND b.name = 'Mazda';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 8, 8, 7, 8, 5, 'baixo', 'Premium disfarçado de generalista. Interior requintado. Condução envolvente. Falta espaço traseiro.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = '3' AND b.name = 'Mazda';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 21000, 17000, 26000, 22, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = '3' AND b.name = 'Mazda';

-- ── Honda Civic ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '2.0 e:HEV 184', 'hibrido', 1993, 184, 315, 'auto cvt', 4.7, 107, 9.0, 380
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Civic' AND b.name = 'Honda';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.5 VTEC Turbo 182', 'gasolina', 1498, 182, 240, 'auto cvt', 6.5, 148, 8.0, 400
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Civic' AND b.name = 'Honda';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 8, 7, 7, 8, 6, 'baixo', 'Nova geração madura e premium. Híbrido brilhante. Condução refinada. Design elegante e sóbrio.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Civic' AND b.name = 'Honda';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2023, 28000, 24000, 33000, 15, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Civic' AND b.name = 'Honda';

-- ── Audi A3 ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '30 TFSI 110', 'gasolina', 999, 110, 200, 'manual 6', 5.6, 128, 7.5, 520
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'A3' AND b.name = 'Audi';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '35 TFSI 150 S-tronic', 'gasolina', 1498, 150, 250, 'auto 7', 5.9, 134, 7.0, 580
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'A3' AND b.name = 'Audi';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '30 TDI 116', 'diesel', 1968, 116, 300, 'manual 6', 4.2, 111, 7.5, 530
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'A3' AND b.name = 'Audi';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '35 TDI 150 S-tronic', 'diesel', 1968, 150, 360, 'auto 7', 4.5, 119, 7.0, 580
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'A3' AND b.name = 'Audi';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 8, 6, 7, 8, 5, 'baixo', 'Premium compacto de referência. Qualidade interior excelente. Virtual Cockpit. Condução refinada.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'A3' AND b.name = 'Audi';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 27000, 22000, 33000, 35, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'A3' AND b.name = 'Audi';

-- ── BMW Série 1 ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '116i 109cv', 'gasolina', 1499, 109, 190, 'manual 6', 5.9, 134, 7.5, 550
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Série 1' AND b.name = 'BMW';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '118i 136cv', 'gasolina', 1499, 136, 220, 'auto 7', 6.0, 137, 7.0, 580
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Série 1' AND b.name = 'BMW';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '116d 116cv', 'diesel', 1995, 116, 280, 'manual 6', 4.3, 113, 7.5, 530
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Série 1' AND b.name = 'BMW';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '120d xDrive 190cv', 'diesel', 1995, 190, 400, 'auto 8', 5.2, 137, 7.0, 620
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Série 1' AND b.name = 'BMW';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 7, 8, 7, 8, 4, 'baixo', 'Tração dianteira mas condução BMW. Mais divertido que A3. Interior orientado ao condutor.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Série 1' AND b.name = 'BMW';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 26000, 21000, 32000, 30, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Série 1' AND b.name = 'BMW';

-- ── Mercedes-Benz Classe A ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, 'A 180 136cv', 'gasolina', 1332, 136, 200, 'auto 7', 6.2, 141, 7.0, 580
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Classe A' AND b.name = 'Mercedes-Benz';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, 'A 200 163cv', 'gasolina', 1332, 163, 250, 'auto 7', 6.3, 143, 7.0, 600
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Classe A' AND b.name = 'Mercedes-Benz';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, 'A 180d 116cv', 'diesel', 1461, 116, 260, 'auto 7', 4.5, 119, 7.5, 550
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Classe A' AND b.name = 'Mercedes-Benz';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, 'A 250 224cv', 'gasolina', 1991, 224, 350, 'auto 7', 6.8, 155, 7.0, 650
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Classe A' AND b.name = 'Mercedes-Benz';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 8, 6, 7, 7, 4, 'baixo', 'MBUX revolucionou o interior. Conforto de topo para o segmento. Motor Renault 1.3 nos base.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Classe A' AND b.name = 'Mercedes-Benz';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 27500, 22000, 34000, 32, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Classe A' AND b.name = 'Mercedes-Benz';

-- ── Volvo V40 ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, 'T2 122cv', 'gasolina', 1969, 122, 220, 'manual 6', 6.0, 137, 7.0, 500
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'V40' AND b.name = 'Volvo';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, 'D2 120cv', 'diesel', 1969, 120, 280, 'manual 6', 4.0, 105, 7.5, 480
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'V40' AND b.name = 'Volvo';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 8, 5, 7, 7, 5, 'baixo', 'Segurança Volvo num compacto premium. Descontinuado mas bons preços em usados. Confortável.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'V40' AND b.name = 'Volvo';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2019, 16000, 12000, 20000, 35, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'V40' AND b.name = 'Volvo';

-- ── Cupra Leon ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.5 TSI 150 DSG', 'gasolina', 1498, 150, 250, 'auto 7', 6.0, 137, 7.0, 480
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Leon' AND b.name = 'Cupra';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '2.0 TSI 245 DSG', 'gasolina', 1984, 245, 370, 'auto 7', 7.2, 164, 7.0, 550
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Leon' AND b.name = 'Cupra';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.4 e-Hybrid 245', 'hibrido', 1395, 245, 400, 'auto 6', 1.5, 33, 7.0, 500
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Leon' AND b.name = 'Cupra';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 7, 9, 7, 9, 5, 'medio', 'SEAT Leon com esteroides. Condução empolgante. O 2.0 TSI é sério. Híbrido impressionante.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Leon' AND b.name = 'Cupra';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 28000, 23000, 34000, 22, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Leon' AND b.name = 'Cupra';

-- ── DS 4 ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.2 PureTech 130 EAT8', 'gasolina', 1199, 130, 230, 'auto 8', 6.1, 139, 6.0, 500
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = '4' AND b.name = 'DS';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.6 E-Tense 225 PHEV', 'hibrido', 1598, 225, 360, 'auto 8', 1.3, 30, 6.5, 520
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = '4' AND b.name = 'DS';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 8, 4, 7, 7, 5, 'baixo', 'Interior luxuoso e diferente. Design ousado. Conforto acima da média. Condução anódina.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = '4' AND b.name = 'DS';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 25000, 20000, 31000, 12, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = '4' AND b.name = 'DS';

-- ── Citroën C4 ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.2 PureTech 130', 'gasolina', 1199, 130, 230, 'auto 8', 5.8, 132, 6.5, 420
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'C4' AND b.name = 'Citroën';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.5 BlueHDi 130', 'diesel', 1499, 130, 300, 'auto 8', 4.3, 113, 7.5, 430
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'C4' AND b.name = 'Citroën';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, 'ë-C4 136cv', 'eletrico', 0, 136, 260, 'auto', 15.5, 0, 7.5, 220
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'C4' AND b.name = 'Citroën';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 8, 4, 7, 7, 6, 'baixo', 'Suspensão com batentes hidráulicos — conforto excecional. Design crossover. Zero desportividade, todo o conforto.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'C4' AND b.name = 'Citroën';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 19000, 15000, 24000, 28, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'C4' AND b.name = 'Citroën';

-- ── Fiat Tipo ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.0 100cv', 'gasolina', 999, 100, 190, 'manual 6', 5.8, 132, 6.5, 380
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Tipo' AND b.name = 'Fiat';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.6 Multijet 130', 'diesel', 1598, 130, 320, 'manual 6', 4.5, 119, 7.0, 400
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Tipo' AND b.name = 'Fiat';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 6, 4, 6, 7, 7, 'medio', 'Máximo espaço pelo mínimo preço. Interior básico mas funcional. Berlina de família acessível.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Tipo' AND b.name = 'Fiat';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 13000, 10000, 17000, 25, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Tipo' AND b.name = 'Fiat';

-- ── Skoda Scala ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.0 TSI 110', 'gasolina', 999, 110, 200, 'manual 6', 5.5, 125, 7.5, 390
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Scala' AND b.name = 'Skoda';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.5 TSI 150 DSG', 'gasolina', 1498, 150, 250, 'auto 7', 5.9, 134, 7.0, 430
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Scala' AND b.name = 'Skoda';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 7, 5, 7, 7, 6, 'baixo', 'Alternativa ao Octavia mais acessível. Bom espaço. Pragmática como um Skoda deve ser.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Scala' AND b.name = 'Skoda';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 17000, 13500, 21000, 22, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Scala' AND b.name = 'Skoda';

-- ── Volkswagen ID.3 ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, 'ID.3 Pro 204cv 58kWh', 'eletrico', 0, 204, 310, 'auto', 15.5, 0, 7.5, 250
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'ID.3' AND b.name = 'Volkswagen';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, 'ID.3 Pro S 204cv 77kWh', 'eletrico', 0, 204, 310, 'auto', 16.0, 0, 7.5, 250
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'ID.3' AND b.name = 'Volkswagen';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 7, 5, 8, 7, 5, 'baixo', 'Golf elétrico. Espaçoso, silencioso, prático. Software melhorou muito. Autonomia real ~350-450km.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'ID.3' AND b.name = 'Volkswagen';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 27000, 22000, 33000, 25, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'ID.3' AND b.name = 'Volkswagen';

-- ── MG 4 ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, 'MG4 Standard 170cv 51kWh', 'eletrico', 0, 170, 250, 'auto', 15.0, 0, 7.0, 220
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = '4' AND b.name = 'MG';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, 'MG4 Long Range 204cv 64kWh', 'eletrico', 0, 204, 250, 'auto', 15.5, 0, 7.0, 220
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = '4' AND b.name = 'MG';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 6, 6, 8, 7, 5, 'baixo', 'Relação preço-autonomia imbatível. Condução surpreendentemente divertida. Interior básico.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = '4' AND b.name = 'MG';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2023, 22000, 18000, 27000, 18, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = '4' AND b.name = 'MG';

-- ── Toyota Prius ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '2.0 Híbrido 196cv', 'hibrido', 1987, 196, 190, 'auto cvt', 4.2, 95, 9.0, 350
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Prius' AND b.name = 'Toyota';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 8, 6, 8, 8, 5, 'baixo', 'Renascimento do ícone híbrido. Agora bonito e rápido. Consumos incríveis. Tecnologia Toyota.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Prius' AND b.name = 'Toyota';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2024, 32000, 28000, 37000, 10, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Prius' AND b.name = 'Toyota';

-- ── MINI Cooper ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, 'Cooper 136cv', 'gasolina', 1499, 136, 220, 'manual 6', 5.9, 134, 7.0, 520
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Cooper' AND b.name = 'MINI';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, 'Cooper S 178cv', 'gasolina', 1998, 178, 280, 'auto 7', 6.5, 148, 7.0, 580
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Cooper' AND b.name = 'MINI';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, 'Cooper SE 184cv', 'eletrico', 0, 184, 290, 'auto', 14.0, 0, 7.5, 250
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Cooper' AND b.name = 'MINI';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 6, 8, 8, 6, 3, 'medio', 'Go-kart feeling. Divertido como poucos. Interior único com personalidade. Custos premium.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Cooper' AND b.name = 'MINI';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 22000, 17000, 28000, 25, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Cooper' AND b.name = 'MINI';

-- ── Audi A1 ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '25 TFSI 95', 'gasolina', 999, 95, 175, 'manual 5', 5.4, 123, 7.5, 480
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'A1' AND b.name = 'Audi';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '30 TFSI 110', 'gasolina', 999, 110, 200, 'manual 6', 5.5, 125, 7.0, 500
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'A1' AND b.name = 'Audi';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 7, 5, 8, 6, 4, 'baixo', 'Mini A3. Qualidade premium num formato compacto. Virtual Cockpit disponível. Preço premium.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'A1' AND b.name = 'Audi';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 21000, 17000, 26000, 20, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'A1' AND b.name = 'Audi';

-- ── Mercedes-Benz CLA ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, 'CLA 180 136cv', 'gasolina', 1332, 136, 200, 'auto 7', 6.2, 141, 7.0, 580
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'CLA' AND b.name = 'Mercedes-Benz';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, 'CLA 200 163cv', 'gasolina', 1332, 163, 250, 'auto 7', 6.3, 143, 7.0, 600
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'CLA' AND b.name = 'Mercedes-Benz';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, 'CLA 250 224cv', 'gasolina', 1991, 224, 350, 'auto 7', 6.8, 155, 7.0, 650
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'CLA' AND b.name = 'Mercedes-Benz';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 7, 6, 7, 8, 4, 'baixo', 'Coupé 4 portas elegante. Linha de cintura baixa. MBUX de topo. Banco traseiro apertado.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'CLA' AND b.name = 'Mercedes-Benz';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 30000, 25000, 36000, 22, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'CLA' AND b.name = 'Mercedes-Benz';

-- ── BMW Série 2 Gran Coupé ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '218i 136cv', 'gasolina', 1499, 136, 220, 'auto 7', 6.0, 137, 7.0, 560
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Série 2 Gran Coupé' AND b.name = 'BMW';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '220d 190cv', 'diesel', 1995, 190, 400, 'auto 8', 4.8, 126, 7.0, 580
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Série 2 Gran Coupé' AND b.name = 'BMW';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 7, 7, 7, 8, 4, 'baixo', 'Entrada na gama BMW com estilo coupé. Condução dinâmica. Banco traseiro justo.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Série 2 Gran Coupé' AND b.name = 'BMW';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 28000, 23000, 34000, 18, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Série 2 Gran Coupé' AND b.name = 'BMW';

-- ── Skoda Superb ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.5 TSI 150', 'gasolina', 1498, 150, 250, 'manual 6', 5.9, 134, 7.5, 430
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Superb' AND b.name = 'Skoda';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '2.0 TDI 150 DSG', 'diesel', 1968, 150, 360, 'auto 7', 4.5, 119, 7.5, 470
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Superb' AND b.name = 'Skoda';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '2.0 TSI 190 DSG 4x4', 'gasolina', 1984, 190, 320, 'auto 7', 6.8, 155, 7.0, 520
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Superb' AND b.name = 'Skoda';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 9, 5, 6, 9, 9, 'baixo', 'Berlina disfarçada de compacto. Espaço de Classe E por preço de Golf. Conforto e espaço enormes.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Superb' AND b.name = 'Skoda';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 25000, 20000, 31000, 25, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Superb' AND b.name = 'Skoda';

-- ── Volkswagen Passat ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.5 TSI 150 DSG', 'gasolina', 1498, 150, 250, 'auto 7', 5.9, 134, 7.5, 470
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Passat' AND b.name = 'Volkswagen';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '2.0 TDI 150 DSG', 'diesel', 1968, 150, 360, 'auto 7', 4.5, 119, 7.5, 490
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Passat' AND b.name = 'Volkswagen';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 8, 5, 6, 9, 8, 'baixo', 'Carrinha/berlina sólida e refinada. Excelente para estrada. Espaço generoso. Fiável.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Passat' AND b.name = 'Volkswagen';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 26000, 21000, 32000, 30, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Passat' AND b.name = 'Volkswagen';

-- ── Peugeot 508 ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.2 PureTech 130 EAT8', 'gasolina', 1199, 130, 230, 'auto 8', 6.0, 137, 6.5, 460
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = '508' AND b.name = 'Peugeot';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.5 BlueHDi 130 EAT8', 'diesel', 1499, 130, 300, 'auto 8', 4.3, 113, 7.5, 440
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = '508' AND b.name = 'Peugeot';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.6 PureTech 225 EAT8', 'gasolina', 1598, 225, 300, 'auto 8', 6.5, 148, 6.5, 500
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = '508' AND b.name = 'Peugeot';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 8, 6, 6, 8, 6, 'baixo', 'A mais bonita do segmento. Interior espetacular. Conforto soberbo. Alternativa séria aos alemães.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = '508' AND b.name = 'Peugeot';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 24000, 19000, 30000, 22, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = '508' AND b.name = 'Peugeot';

-- ── Peugeot 2008 ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.2 PureTech 100', 'gasolina', 1199, 100, 205, 'manual 6', 5.8, 132, 6.5, 420
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = '2008' AND b.name = 'Peugeot';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.2 PureTech 130 EAT8', 'gasolina', 1199, 130, 230, 'auto 8', 6.1, 139, 6.0, 450
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = '2008' AND b.name = 'Peugeot';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.5 BlueHDi 110', 'diesel', 1499, 110, 250, 'manual 6', 4.5, 119, 7.5, 420
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = '2008' AND b.name = 'Peugeot';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, 'e-2008 136cv', 'eletrico', 0, 136, 260, 'auto', 16.0, 0, 7.5, 220
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = '2008' AND b.name = 'Peugeot';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 7, 5, 8, 7, 6, 'baixo', 'SUV urbano elegante. Interior premium com i-Cockpit. Referência no segmento B-SUV em Portugal.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = '2008' AND b.name = 'Peugeot';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 20000, 16000, 25000, 42, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = '2008' AND b.name = 'Peugeot';
INSERT INTO engine_issues (engine_id, severity, description, affected_years, fix_cost_estimate, source)
SELECT e.id, 'medio', 'Motor 1.2 PureTech: correia húmida — confirmar manutenção.', '2019-2021', '600-1200€', 'Stellantis'
FROM engines e JOIN vehicle_models vm ON e.model_id = vm.id JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = '2008' AND b.name = 'Peugeot' LIMIT 1;

-- ── Renault Captur ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.0 TCe 90', 'gasolina', 999, 90, 160, 'manual 5', 5.9, 134, 7.0, 380
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Captur' AND b.name = 'Renault';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.3 TCe 140 EDC', 'gasolina', 1332, 140, 240, 'auto 7', 6.3, 143, 7.0, 430
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Captur' AND b.name = 'Renault';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.6 E-Tech 145 Híbrido', 'hibrido', 1598, 145, 205, 'auto', 4.7, 107, 7.5, 380
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Captur' AND b.name = 'Renault';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 7, 4, 8, 6, 6, 'baixo', 'Crossover bem-sucedido. Banco traseiro deslizante inteligente. Híbrido convincente.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Captur' AND b.name = 'Renault';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 18500, 14500, 23000, 40, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Captur' AND b.name = 'Renault';

-- ── Dacia Duster ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.0 TCe 90', 'gasolina', 999, 90, 160, 'manual 5', 6.5, 148, 7.0, 320
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Duster' AND b.name = 'Dacia';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.3 TCe 130', 'gasolina', 1332, 130, 240, 'manual 6', 6.7, 152, 7.0, 350
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Duster' AND b.name = 'Dacia';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.5 Blue dCi 115', 'diesel', 1461, 115, 260, 'manual 6', 5.2, 137, 7.5, 350
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Duster' AND b.name = 'Dacia';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.5 Blue dCi 115 4x4', 'diesel', 1461, 115, 260, 'manual 6', 5.8, 152, 7.5, 380
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Duster' AND b.name = 'Dacia';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 5, 4, 6, 6, 7, 'medio', 'SUV mais acessível. Verdadeiro 4x4 disponível. Interior simples mas espaçoso. Relação preço-capacidade única.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Duster' AND b.name = 'Dacia';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 15500, 12000, 19500, 55, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Duster' AND b.name = 'Dacia';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2021, 13000, 10000, 17000, 65, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Duster' AND b.name = 'Dacia';

-- ── Nissan Qashqai ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.3 DIG-T 140', 'gasolina', 1332, 140, 240, 'manual 6', 6.5, 148, 7.0, 430
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Qashqai' AND b.name = 'Nissan';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.3 DIG-T 158 Xtronic', 'gasolina', 1332, 158, 270, 'auto cvt', 6.7, 152, 7.0, 460
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Qashqai' AND b.name = 'Nissan';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.5 e-Power 190 Híbrido', 'hibrido', 1497, 190, 330, 'auto', 5.3, 120, 7.5, 400
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Qashqai' AND b.name = 'Nissan';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 7, 5, 7, 7, 7, 'baixo', 'Inventor do segmento C-SUV. e-Power é uma solução inteligente. Confortável e bem equipado.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Qashqai' AND b.name = 'Nissan';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 24000, 19500, 29000, 35, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Qashqai' AND b.name = 'Nissan';

-- ── Peugeot 3008 ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.2 PureTech 130 EAT8', 'gasolina', 1199, 130, 230, 'auto 8', 6.3, 143, 6.0, 460
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = '3008' AND b.name = 'Peugeot';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.5 BlueHDi 130 EAT8', 'diesel', 1499, 130, 300, 'auto 8', 4.7, 124, 7.5, 440
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = '3008' AND b.name = 'Peugeot';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.6 Hybrid 225 PHEV', 'hibrido', 1598, 225, 360, 'auto 8', 1.4, 32, 7.0, 480
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = '3008' AND b.name = 'Peugeot';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 8, 5, 7, 7, 7, 'baixo', 'Interior espetacular. Conforto de topo no segmento. Design forte. Referência em Portugal.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = '3008' AND b.name = 'Peugeot';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 26000, 21000, 32000, 38, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = '3008' AND b.name = 'Peugeot';

-- ── Hyundai Tucson ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.6 T-GDi 150', 'gasolina', 1598, 150, 250, 'manual 6', 6.8, 155, 7.5, 420
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Tucson' AND b.name = 'Hyundai';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.6 T-GDi 230 HEV', 'hibrido', 1598, 230, 350, 'auto 6', 5.5, 125, 8.0, 400
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Tucson' AND b.name = 'Hyundai';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.6 CRDi 115', 'diesel', 1598, 115, 280, 'manual 6', 5.0, 132, 8.0, 420
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Tucson' AND b.name = 'Hyundai';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 7, 5, 7, 7, 8, 'baixo', 'Design radical que divide. Muito espaço interior. Híbrido é a melhor escolha. Garantia 5 anos.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Tucson' AND b.name = 'Hyundai';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 26000, 21000, 32000, 35, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Tucson' AND b.name = 'Hyundai';

-- ── Kia Sportage ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.6 T-GDi 150', 'gasolina', 1598, 150, 250, 'manual 6', 6.8, 155, 7.5, 420
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Sportage' AND b.name = 'Kia';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.6 T-GDi 230 HEV', 'hibrido', 1598, 230, 350, 'auto 6', 5.5, 125, 8.0, 400
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Sportage' AND b.name = 'Kia';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.6 CRDi 115', 'diesel', 1598, 115, 280, 'manual 6', 5.0, 132, 8.0, 420
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Sportage' AND b.name = 'Kia';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 7, 5, 7, 8, 8, 'baixo', 'Gémeo do Tucson com mais espaço e design arrojado. 7 anos de garantia. Excelente para famílias.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Sportage' AND b.name = 'Kia';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 27000, 22000, 33000, 32, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Sportage' AND b.name = 'Kia';

-- ── Volkswagen T-Roc ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.0 TSI 110', 'gasolina', 999, 110, 200, 'manual 6', 5.8, 132, 7.5, 430
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'T-Roc' AND b.name = 'Volkswagen';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.5 TSI 150 DSG', 'gasolina', 1498, 150, 250, 'auto 7', 6.2, 141, 7.0, 480
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'T-Roc' AND b.name = 'Volkswagen';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '2.0 TDI 115', 'diesel', 1968, 115, 300, 'manual 6', 4.7, 124, 7.5, 460
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'T-Roc' AND b.name = 'Volkswagen';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 7, 6, 7, 7, 6, 'baixo', 'Golf elevado. Qualidade VW num formato SUV. Condução segura. Um pouco caro para o que oferece.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'T-Roc' AND b.name = 'Volkswagen';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 23000, 18500, 28000, 38, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'T-Roc' AND b.name = 'Volkswagen';

-- ── Volkswagen Tiguan ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.5 TSI 150 DSG', 'gasolina', 1498, 150, 250, 'auto 7', 6.5, 148, 7.5, 500
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Tiguan' AND b.name = 'Volkswagen';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '2.0 TDI 150 DSG', 'diesel', 1968, 150, 360, 'auto 7', 5.0, 132, 7.5, 520
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Tiguan' AND b.name = 'Volkswagen';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '2.0 TDI 200 DSG 4Motion', 'diesel', 1968, 200, 400, 'auto 7', 5.8, 152, 7.0, 580
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Tiguan' AND b.name = 'Volkswagen';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 8, 6, 7, 8, 8, 'baixo', 'SUV familiar de referência. Espaço, qualidade e versátilidade. Preço elevado mas justificado.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Tiguan' AND b.name = 'Volkswagen';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 30000, 24000, 37000, 32, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Tiguan' AND b.name = 'Volkswagen';

-- ── Toyota C-HR ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.8 Híbrido 122cv', 'hibrido', 1798, 122, 142, 'auto cvt', 4.8, 109, 9.0, 320
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'C-HR' AND b.name = 'Toyota';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '2.0 Híbrido 184cv', 'hibrido', 1987, 184, 190, 'auto cvt', 5.0, 114, 9.0, 350
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'C-HR' AND b.name = 'Toyota';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 7, 6, 8, 7, 5, 'baixo', 'Coupé-SUV com design radical. Visibilidade traseira limitada. Híbrido fiável. Condução agradável.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'C-HR' AND b.name = 'Toyota';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 23000, 19000, 28000, 30, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'C-HR' AND b.name = 'Toyota';

-- ── Toyota RAV4 ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '2.5 Híbrido 218cv', 'hibrido', 2487, 218, 221, 'auto cvt', 5.0, 114, 9.5, 350
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'RAV4' AND b.name = 'Toyota';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '2.5 Híbrido 222cv AWD', 'hibrido', 2487, 222, 221, 'auto cvt', 5.3, 120, 9.5, 380
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'RAV4' AND b.name = 'Toyota';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '2.5 PHEV 306cv', 'hibrido', 2487, 306, 227, 'auto cvt', 1.0, 22, 9.0, 400
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'RAV4' AND b.name = 'Toyota';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 8, 5, 7, 8, 8, 'baixo', 'SUV híbrido campeão. Espaço familiar generoso. Fiabilidade Toyota legendária. PHEV com autonomia real ~60km.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'RAV4' AND b.name = 'Toyota';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 30000, 25000, 36000, 35, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'RAV4' AND b.name = 'Toyota';

-- ── SEAT Arona ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.0 TSI 95', 'gasolina', 999, 95, 175, 'manual 5', 5.5, 125, 7.5, 380
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Arona' AND b.name = 'SEAT';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.0 TSI 110', 'gasolina', 999, 110, 200, 'manual 6', 5.6, 128, 7.0, 400
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Arona' AND b.name = 'SEAT';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 6, 5, 8, 6, 5, 'baixo', 'Ibiza elevado. Bom para cidade. Espaço justo. Preço competitivo. Simpático mas sem destaque.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Arona' AND b.name = 'SEAT';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 16500, 13000, 20500, 30, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Arona' AND b.name = 'SEAT';

-- ── SEAT Ateca ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.0 TSI 110', 'gasolina', 999, 110, 200, 'manual 6', 5.9, 134, 7.5, 420
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Ateca' AND b.name = 'SEAT';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.5 TSI 150 DSG', 'gasolina', 1498, 150, 250, 'auto 7', 6.2, 141, 7.0, 460
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Ateca' AND b.name = 'SEAT';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '2.0 TDI 115', 'diesel', 1968, 115, 300, 'manual 6', 4.8, 126, 7.5, 440
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Ateca' AND b.name = 'SEAT';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 7, 7, 7, 8, 7, 'baixo', 'T-Roc com mais espaço e melhor relação preço. Condução dinâmica para SUV. Escolha inteligente.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Ateca' AND b.name = 'SEAT';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 22000, 17500, 27000, 28, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Ateca' AND b.name = 'SEAT';

-- ── Skoda Kamiq ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.0 TSI 95', 'gasolina', 999, 95, 175, 'manual 5', 5.4, 123, 7.5, 380
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Kamiq' AND b.name = 'Skoda';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.0 TSI 110', 'gasolina', 999, 110, 200, 'manual 6', 5.5, 125, 7.0, 400
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Kamiq' AND b.name = 'Skoda';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.5 TSI 150 DSG', 'gasolina', 1498, 150, 250, 'auto 7', 5.9, 134, 7.0, 440
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Kamiq' AND b.name = 'Skoda';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 7, 5, 8, 7, 6, 'baixo', 'SUV urbano com espaço de compacto. Simply Clever Skoda. Prático e racional como sempre.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Kamiq' AND b.name = 'Skoda';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 18000, 14500, 22500, 25, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Kamiq' AND b.name = 'Skoda';

-- ── Skoda Karoq ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.0 TSI 110', 'gasolina', 999, 110, 200, 'manual 6', 5.8, 132, 7.5, 410
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Karoq' AND b.name = 'Skoda';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.5 TSI 150 DSG', 'gasolina', 1498, 150, 250, 'auto 7', 6.2, 141, 7.0, 450
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Karoq' AND b.name = 'Skoda';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '2.0 TDI 115', 'diesel', 1968, 115, 300, 'manual 6', 4.7, 124, 7.5, 440
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Karoq' AND b.name = 'Skoda';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 7, 5, 7, 7, 7, 'baixo', 'Tiguan checo. Mesmo nível técnico, preço mais competitivo. Bancos traseiros VarioFlex geniais.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Karoq' AND b.name = 'Skoda';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 22500, 18000, 28000, 25, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Karoq' AND b.name = 'Skoda';

-- ── Skoda Kodiaq ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.5 TSI 150 DSG', 'gasolina', 1498, 150, 250, 'auto 7', 6.5, 148, 7.5, 460
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Kodiaq' AND b.name = 'Skoda';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '2.0 TDI 150 DSG', 'diesel', 1968, 150, 360, 'auto 7', 5.2, 137, 7.5, 480
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Kodiaq' AND b.name = 'Skoda';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '2.0 TDI 200 DSG 4x4', 'diesel', 1968, 200, 400, 'auto 7', 6.0, 158, 7.0, 520
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Kodiaq' AND b.name = 'Skoda';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 8, 4, 6, 8, 9, 'baixo', 'SUV 7 lugares acessível. Espaço enorme. Conforto de estrada. O mais prático da família VW.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Kodiaq' AND b.name = 'Skoda';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 28000, 23000, 34000, 22, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Kodiaq' AND b.name = 'Skoda';

-- ── Ford Puma ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.0 EcoBoost 125', 'gasolina', 999, 125, 170, 'manual 6', 5.7, 130, 7.0, 400
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Puma' AND b.name = 'Ford';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.0 EcoBoost 125 mHEV', 'hibrido', 999, 125, 210, 'manual 6', 5.5, 125, 7.0, 410
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Puma' AND b.name = 'Ford';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.0 EcoBoost 155 mHEV', 'hibrido', 999, 155, 240, 'manual 6', 5.7, 130, 7.0, 430
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Puma' AND b.name = 'Ford';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 6, 7, 8, 7, 5, 'baixo', 'Chassis Fiesta num SUV. Divertido de conduzir. MegaBox na bagageira genial. Compacto com alma.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Puma' AND b.name = 'Ford';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 19000, 15000, 24000, 30, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Puma' AND b.name = 'Ford';

-- ── Ford Kuga ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.5 EcoBoost 150', 'gasolina', 1497, 150, 240, 'manual 6', 6.5, 148, 7.0, 440
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Kuga' AND b.name = 'Ford';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '2.5 FHEV 190', 'hibrido', 2488, 190, 200, 'auto cvt', 5.5, 125, 7.5, 420
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Kuga' AND b.name = 'Ford';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '2.5 PHEV 225', 'hibrido', 2488, 225, 200, 'auto cvt', 1.4, 32, 7.0, 460
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Kuga' AND b.name = 'Ford';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 7, 5, 7, 7, 7, 'baixo', 'SUV familiar competente. PHEV com boa autonomia elétrica. Espaço generoso. Ligeiramente anónimo.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Kuga' AND b.name = 'Ford';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 24000, 19000, 30000, 28, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Kuga' AND b.name = 'Ford';

-- ── Nissan Juke ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.0 DIG-T 114', 'gasolina', 999, 114, 200, 'manual 6', 5.8, 132, 7.0, 400
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Juke' AND b.name = 'Nissan';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.6 Hybrid 143', 'hibrido', 1598, 143, 205, 'auto', 5.0, 114, 7.5, 380
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Juke' AND b.name = 'Nissan';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 6, 5, 8, 6, 4, 'baixo', 'Design polarizante. Compacto e ágil na cidade. Híbrido é a melhor opção. Espaço traseiro justo.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Juke' AND b.name = 'Nissan';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 18000, 14000, 22500, 25, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Juke' AND b.name = 'Nissan';

-- ── Hyundai Kona ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.0 T-GDi 120', 'gasolina', 998, 120, 172, 'manual 6', 5.8, 132, 8.0, 380
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Kona' AND b.name = 'Hyundai';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.6 GDi HEV 141', 'hibrido', 1580, 141, 265, 'auto 6', 4.5, 102, 8.0, 370
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Kona' AND b.name = 'Hyundai';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, 'Kona EV 204cv 65kWh', 'eletrico', 0, 204, 255, 'auto', 15.0, 0, 8.0, 200
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Kona' AND b.name = 'Hyundai';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 6, 5, 8, 6, 5, 'baixo', 'Versátil e fiável. EV com excelente autonomia. Híbrido eficiente. Garantia 5 anos. Seguro.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Kona' AND b.name = 'Hyundai';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 20000, 16000, 25000, 30, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Kona' AND b.name = 'Hyundai';

-- ── Hyundai Bayon ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.0 T-GDi 100', 'gasolina', 998, 100, 172, 'manual 5', 5.6, 128, 8.0, 350
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Bayon' AND b.name = 'Hyundai';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.0 T-GDi 100 48V', 'hibrido', 998, 100, 172, 'manual 6', 5.4, 123, 8.0, 360
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Bayon' AND b.name = 'Hyundai';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 6, 4, 8, 6, 5, 'baixo', 'i20 com roupa de SUV. Prático e acessível. Ideal para quem quer SUV sem gastar muito.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Bayon' AND b.name = 'Hyundai';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 16500, 13000, 20500, 22, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Bayon' AND b.name = 'Hyundai';

-- ── Kia Stonic ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.0 T-GDi 100', 'gasolina', 998, 100, 172, 'manual 6', 5.5, 125, 8.0, 350
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Stonic' AND b.name = 'Kia';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.0 T-GDi 120 DCT', 'gasolina', 998, 120, 172, 'auto 7', 5.8, 132, 7.5, 380
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Stonic' AND b.name = 'Kia';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 6, 5, 8, 6, 5, 'baixo', 'Rio em versão SUV. 7 anos de garantia. Bom para cidade. Simples e eficaz.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Stonic' AND b.name = 'Kia';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 16000, 12500, 20000, 22, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Stonic' AND b.name = 'Kia';

-- ── Kia Niro ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.6 HEV 141', 'hibrido', 1580, 141, 265, 'auto 6', 4.4, 100, 8.5, 370
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Niro' AND b.name = 'Kia';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.6 PHEV 183', 'hibrido', 1580, 183, 265, 'auto 6', 1.3, 29, 8.0, 400
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Niro' AND b.name = 'Kia';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, 'Niro EV 204cv 65kWh', 'eletrico', 0, 204, 255, 'auto', 15.0, 0, 8.0, 220
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Niro' AND b.name = 'Kia';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 7, 4, 8, 7, 7, 'baixo', 'Multienergias: híbrido, PHEV ou elétrico. Prático e bem equipado. Garantia 7 anos. Família moderna.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Niro' AND b.name = 'Kia';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2023, 28000, 23000, 34000, 18, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Niro' AND b.name = 'Kia';

-- ── Mazda CX-30 ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '2.0 Skyactiv-G 122', 'gasolina', 1998, 122, 213, 'manual 6', 6.2, 141, 8.5, 400
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'CX-30' AND b.name = 'Mazda';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '2.0 Skyactiv-X 186', 'gasolina', 1998, 186, 240, 'manual 6', 6.0, 137, 8.0, 450
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'CX-30' AND b.name = 'Mazda';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 8, 7, 7, 7, 6, 'baixo', 'Mazda 3 elevado. Interior requintado. Condução envolvente para SUV. Qualidade de acabamento excecional.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'CX-30' AND b.name = 'Mazda';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 23000, 19000, 28000, 20, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'CX-30' AND b.name = 'Mazda';

-- ── Mazda CX-5 ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '2.0 Skyactiv-G 165', 'gasolina', 1998, 165, 213, 'manual 6', 6.8, 155, 8.5, 430
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'CX-5' AND b.name = 'Mazda';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '2.2 Skyactiv-D 150', 'diesel', 2191, 150, 380, 'manual 6', 5.5, 145, 8.0, 450
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'CX-5' AND b.name = 'Mazda';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '2.2 Skyactiv-D 184 AWD', 'diesel', 2191, 184, 445, 'auto 6', 6.0, 158, 8.0, 480
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'CX-5' AND b.name = 'Mazda';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 8, 7, 6, 8, 7, 'baixo', 'SUV premium disfarçado. Condução genuína, interior sofisticado. Fiável e durável. Subvalorizado.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'CX-5' AND b.name = 'Mazda';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 25000, 20000, 31000, 25, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'CX-5' AND b.name = 'Mazda';

-- ── Mazda CX-3 ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '2.0 Skyactiv-G 121', 'gasolina', 1998, 121, 213, 'manual 6', 6.0, 137, 8.5, 380
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'CX-3' AND b.name = 'Mazda';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 7, 6, 8, 6, 4, 'baixo', 'Pequeno mas premium. Condução Mazda típica. Espaço traseiro limitado. Qualidade acima da concorrência.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'CX-3' AND b.name = 'Mazda';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 17500, 14000, 21500, 18, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'CX-3' AND b.name = 'Mazda';

-- ── Honda HR-V ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.5 e:HEV 131', 'hibrido', 1498, 131, 253, 'auto cvt', 5.0, 114, 9.0, 350
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'HR-V' AND b.name = 'Honda';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 7, 5, 8, 7, 6, 'baixo', 'Híbrido Honda eficiente. Magic Seats do Jazz. Espaço surpreendente. Design clean. Fiável.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'HR-V' AND b.name = 'Honda';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 25000, 21000, 30000, 15, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'HR-V' AND b.name = 'Honda';

-- ── Honda CR-V ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.5 VTEC Turbo 193', 'gasolina', 1498, 193, 243, 'auto cvt', 7.0, 159, 8.5, 420
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'CR-V' AND b.name = 'Honda';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '2.0 i-MMD Híbrido 184', 'hibrido', 1993, 184, 315, 'auto cvt', 5.3, 120, 9.0, 380
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'CR-V' AND b.name = 'Honda';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 8, 5, 7, 8, 8, 'baixo', 'SUV familiar de referência. Espaço generoso. Híbrido muito eficiente. Fiabilidade Honda legendária.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'CR-V' AND b.name = 'Honda';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 28000, 23000, 34000, 20, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'CR-V' AND b.name = 'Honda';

-- ── Opel Mokka ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.2 PureTech 100', 'gasolina', 1199, 100, 205, 'manual 6', 5.7, 130, 6.5, 400
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Mokka' AND b.name = 'Opel';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.2 PureTech 130 EAT8', 'gasolina', 1199, 130, 230, 'auto 8', 6.0, 137, 6.0, 440
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Mokka' AND b.name = 'Opel';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, 'Mokka-e 136cv', 'eletrico', 0, 136, 260, 'auto', 16.0, 0, 7.5, 220
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Mokka' AND b.name = 'Opel';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 6, 5, 8, 6, 4, 'baixo', 'Design Vizor marcante. Compacto e ágil. Base Peugeot 2008 com identidade alemã. Elétrico interessante.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Mokka' AND b.name = 'Opel';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 19500, 15500, 24000, 22, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Mokka' AND b.name = 'Opel';

-- ── Opel Grandland ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.2 PureTech 130 EAT8', 'gasolina', 1199, 130, 230, 'auto 8', 6.3, 143, 6.5, 440
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Grandland' AND b.name = 'Opel';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.5 BlueHDi 130 EAT8', 'diesel', 1499, 130, 300, 'auto 8', 4.8, 126, 7.5, 440
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Grandland' AND b.name = 'Opel';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.6 Hybrid 225 PHEV', 'hibrido', 1598, 225, 360, 'auto 8', 1.5, 34, 7.0, 480
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Grandland' AND b.name = 'Opel';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 7, 4, 7, 7, 7, 'baixo', 'SUV familiar Opel. Plataforma Peugeot 3008. Confortável e espaçoso. Design mais conservador.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Grandland' AND b.name = 'Opel';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 24000, 19000, 30000, 20, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Grandland' AND b.name = 'Opel';

-- ── Citroën C3 Aircross ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.2 PureTech 110', 'gasolina', 1199, 110, 205, 'manual 6', 5.8, 132, 6.5, 400
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'C3 Aircross' AND b.name = 'Citroën';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.2 PureTech 130 EAT6', 'gasolina', 1199, 130, 230, 'auto 6', 6.1, 139, 6.0, 430
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'C3 Aircross' AND b.name = 'Citroën';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 7, 4, 8, 6, 6, 'baixo', 'SUV simpático e confortável. Suspensão macia. Ideal para cidade e família. Ar descontraído.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'C3 Aircross' AND b.name = 'Citroën';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 16500, 13000, 20500, 25, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'C3 Aircross' AND b.name = 'Citroën';

-- ── Citroën C5 Aircross ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.2 PureTech 130 EAT8', 'gasolina', 1199, 130, 230, 'auto 8', 6.2, 141, 6.5, 440
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'C5 Aircross' AND b.name = 'Citroën';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.5 BlueHDi 130 EAT8', 'diesel', 1499, 130, 300, 'auto 8', 4.8, 126, 7.5, 430
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'C5 Aircross' AND b.name = 'Citroën';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.6 Hybrid 225 PHEV', 'hibrido', 1598, 225, 360, 'auto 8', 1.5, 34, 7.0, 470
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'C5 Aircross' AND b.name = 'Citroën';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 8, 4, 7, 7, 7, 'baixo', 'Conforto de referência com batentes hidráulicos. Macio como um sofá. Ignora buracos. Zero desportividade.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'C5 Aircross' AND b.name = 'Citroën';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 23000, 18000, 28500, 22, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'C5 Aircross' AND b.name = 'Citroën';

-- ── Renault Kadjar ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.3 TCe 140', 'gasolina', 1332, 140, 240, 'manual 6', 6.5, 148, 7.0, 420
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Kadjar' AND b.name = 'Renault';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.5 Blue dCi 115', 'diesel', 1461, 115, 260, 'manual 6', 4.8, 126, 7.5, 400
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Kadjar' AND b.name = 'Renault';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 7, 4, 7, 7, 7, 'medio', 'Qashqai francês. Confortável e espaçoso. Descontinuado — bons preços em usados.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Kadjar' AND b.name = 'Renault';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2021, 17000, 13000, 21500, 35, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Kadjar' AND b.name = 'Renault';

-- ── Renault Austral ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.2 E-Tech Híbrido 200', 'hibrido', 1199, 200, 205, 'auto', 4.7, 107, 7.0, 430
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Austral' AND b.name = 'Renault';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.3 TCe 160 EDC', 'gasolina', 1332, 160, 270, 'auto 7', 6.5, 148, 7.0, 450
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Austral' AND b.name = 'Renault';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 8, 5, 7, 7, 7, 'baixo', 'Substituto do Kadjar. Interior premium surpreendente. Híbrido eficiente. Salto de qualidade enorme.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Austral' AND b.name = 'Renault';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2023, 28000, 23000, 34000, 15, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Austral' AND b.name = 'Renault';

-- ── Renault Arkana ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.3 TCe 140', 'gasolina', 1332, 140, 240, 'manual 6', 6.3, 143, 7.0, 420
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Arkana' AND b.name = 'Renault';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.6 E-Tech 145 Híbrido', 'hibrido', 1598, 145, 205, 'auto', 4.8, 109, 7.5, 400
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Arkana' AND b.name = 'Renault';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 7, 5, 7, 7, 6, 'baixo', 'Coupé-SUV acessível. Design dinâmico. Híbrido eficiente. Alternativa interessante ao Captur para quem quer mais estilo.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Arkana' AND b.name = 'Renault';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 22000, 18000, 27000, 20, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Arkana' AND b.name = 'Renault';

-- ── Volkswagen T-Cross ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.0 TSI 95', 'gasolina', 999, 95, 175, 'manual 5', 5.5, 125, 7.5, 400
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'T-Cross' AND b.name = 'Volkswagen';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.0 TSI 110', 'gasolina', 999, 110, 200, 'manual 6', 5.6, 128, 7.0, 420
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'T-Cross' AND b.name = 'Volkswagen';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 6, 4, 8, 6, 5, 'baixo', 'Polo com visual de SUV. Compacto e urbano. Qualidade VW. Banco traseiro deslizante.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'T-Cross' AND b.name = 'Volkswagen';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 18500, 14500, 23000, 28, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'T-Cross' AND b.name = 'Volkswagen';

-- ── Toyota Yaris Cross ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.5 Híbrido 116cv', 'hibrido', 1490, 116, 120, 'auto cvt', 4.4, 100, 9.5, 300
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Yaris Cross' AND b.name = 'Toyota';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.5 Híbrido 116cv AWD', 'hibrido', 1490, 116, 120, 'auto cvt', 5.0, 114, 9.5, 330
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Yaris Cross' AND b.name = 'Toyota';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 7, 4, 9, 6, 6, 'baixo', 'Yaris com formato SUV. Híbrido referência em consumos. Fiabilidade Toyota. Compacto e eficiente.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Yaris Cross' AND b.name = 'Toyota';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 22500, 19000, 27000, 30, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Yaris Cross' AND b.name = 'Toyota';

-- ── BMW X1 ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, 'sDrive18i 136cv', 'gasolina', 1499, 136, 230, 'auto 7', 6.3, 143, 7.5, 580
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'X1' AND b.name = 'BMW';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, 'sDrive18d 150cv', 'diesel', 1995, 150, 360, 'auto 7', 4.8, 126, 7.5, 570
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'X1' AND b.name = 'BMW';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, 'xDrive23i 218cv', 'gasolina', 1998, 218, 360, 'auto 7', 6.8, 155, 7.0, 620
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'X1' AND b.name = 'BMW';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, 'iX1 xDrive30 313cv', 'eletrico', 0, 313, 494, 'auto', 16.5, 0, 7.5, 280
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'X1' AND b.name = 'BMW';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 8, 7, 7, 8, 7, 'baixo', 'SUV premium acessível. Nova geração muito mais espaçosa. Condução BMW típica. Elétrico impressionante.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'X1' AND b.name = 'BMW';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2023, 35000, 29000, 42000, 20, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'X1' AND b.name = 'BMW';

-- ── Mercedes-Benz GLA ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, 'GLA 180 136cv', 'gasolina', 1332, 136, 200, 'auto 7', 6.3, 143, 7.0, 580
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'GLA' AND b.name = 'Mercedes-Benz';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, 'GLA 200 163cv', 'gasolina', 1332, 163, 250, 'auto 7', 6.5, 148, 7.0, 600
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'GLA' AND b.name = 'Mercedes-Benz';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, 'GLA 200d 150cv', 'diesel', 1950, 150, 320, 'auto 8', 4.8, 126, 7.5, 570
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'GLA' AND b.name = 'Mercedes-Benz';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 8, 5, 7, 7, 6, 'baixo', 'Classe A elevado. Interior MBUX de topo. Conforto premium. Espaço adequado para o segmento.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'GLA' AND b.name = 'Mercedes-Benz';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 32000, 26000, 39000, 22, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'GLA' AND b.name = 'Mercedes-Benz';

-- ── Audi Q2 ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '25 TFSI 95', 'gasolina', 999, 95, 175, 'manual 5', 5.6, 128, 7.5, 500
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Q2' AND b.name = 'Audi';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '30 TFSI 110', 'gasolina', 999, 110, 200, 'manual 6', 5.7, 130, 7.0, 520
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Q2' AND b.name = 'Audi';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '35 TFSI 150 S-tronic', 'gasolina', 1498, 150, 250, 'auto 7', 6.0, 137, 7.0, 560
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Q2' AND b.name = 'Audi';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 7, 5, 8, 7, 4, 'baixo', 'Mini Q3. Premium compacto com cara de Audi. Qualidade interior boa. Preço premium pelo tamanho.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Q2' AND b.name = 'Audi';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 24000, 19000, 30000, 20, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Q2' AND b.name = 'Audi';

-- ── BMW Série 3 ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '318i 156cv', 'gasolina', 1998, 156, 250, 'auto 8', 6.2, 141, 7.5, 600
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Série 3' AND b.name = 'BMW';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '320i 184cv', 'gasolina', 1998, 184, 300, 'auto 8', 6.5, 148, 7.5, 620
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Série 3' AND b.name = 'BMW';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '320d 190cv', 'diesel', 1995, 190, 400, 'auto 8', 4.8, 126, 7.5, 600
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Série 3' AND b.name = 'BMW';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '330i 258cv', 'gasolina', 1998, 258, 400, 'auto 8', 6.8, 155, 7.0, 680
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Série 3' AND b.name = 'BMW';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '330e PHEV 292cv', 'hibrido', 1998, 292, 420, 'auto 8', 1.6, 37, 7.0, 650
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Série 3' AND b.name = 'BMW';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 8, 9, 6, 9, 5, 'baixo', 'A referência das berlinas desportivas. Condução excepcional. Prazer genuíno ao volante. O 330i é doce.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Série 3' AND b.name = 'BMW';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 34000, 27000, 42000, 40, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Série 3' AND b.name = 'BMW';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2021, 30000, 24000, 38000, 50, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Série 3' AND b.name = 'BMW';

-- ── Mercedes-Benz Classe C ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, 'C 180 170cv', 'gasolina', 1496, 170, 250, 'auto 9', 6.3, 143, 7.5, 620
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Classe C' AND b.name = 'Mercedes-Benz';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, 'C 200 204cv', 'gasolina', 1496, 204, 300, 'auto 9', 6.5, 148, 7.5, 650
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Classe C' AND b.name = 'Mercedes-Benz';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, 'C 220d 200cv', 'diesel', 1993, 200, 440, 'auto 9', 4.5, 119, 7.5, 620
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Classe C' AND b.name = 'Mercedes-Benz';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, 'C 300 258cv', 'gasolina', 1999, 258, 400, 'auto 9', 6.8, 155, 7.0, 700
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Classe C' AND b.name = 'Mercedes-Benz';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 9, 7, 7, 9, 5, 'baixo', 'Mini Classe S. Interior luxuoso com MBUX de nova geração. Conforto supremo. Suspensão refinada.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Classe C' AND b.name = 'Mercedes-Benz';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 38000, 31000, 46000, 35, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Classe C' AND b.name = 'Mercedes-Benz';

-- ── Audi A4 ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '35 TFSI 150', 'gasolina', 1984, 150, 270, 'auto 7', 6.0, 137, 7.5, 600
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'A4' AND b.name = 'Audi';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '40 TFSI 204', 'gasolina', 1984, 204, 320, 'auto 7', 6.3, 143, 7.5, 640
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'A4' AND b.name = 'Audi';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '35 TDI 163', 'diesel', 1968, 163, 380, 'auto 7', 4.5, 119, 7.5, 600
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'A4' AND b.name = 'Audi';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '40 TDI 204 quattro', 'diesel', 1968, 204, 400, 'auto 7', 5.2, 137, 7.0, 660
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'A4' AND b.name = 'Audi';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 8, 7, 6, 9, 5, 'baixo', 'Qualidade de construção impecável. Virtual Cockpit de referência. Equilibrado e refinado. Avant é excelente.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'A4' AND b.name = 'Audi';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 33000, 27000, 41000, 35, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'A4' AND b.name = 'Audi';

-- ── Volvo S60 ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, 'B4 197cv', 'gasolina', 1969, 197, 300, 'auto 8', 6.5, 148, 7.5, 560
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'S60' AND b.name = 'Volvo';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, 'B5 250cv', 'gasolina', 1969, 250, 350, 'auto 8', 6.8, 155, 7.5, 600
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'S60' AND b.name = 'Volvo';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, 'T8 PHEV 390cv', 'hibrido', 1969, 390, 640, 'auto 8', 2.0, 46, 7.0, 650
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'S60' AND b.name = 'Volvo';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 9, 6, 6, 9, 5, 'baixo', 'Segurança Volvo numa berlina elegante. Design escandinavo sóbrio. Conforto soberbo. Subvalorizada.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'S60' AND b.name = 'Volvo';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 32000, 26000, 39000, 15, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'S60' AND b.name = 'Volvo';

-- ── Volvo V60 ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, 'B4 197cv', 'gasolina', 1969, 197, 300, 'auto 8', 6.5, 148, 7.5, 560
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'V60' AND b.name = 'Volvo';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, 'B4D 197cv', 'diesel', 1969, 197, 420, 'auto 8', 5.0, 132, 7.5, 560
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'V60' AND b.name = 'Volvo';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, 'T8 PHEV 390cv', 'hibrido', 1969, 390, 640, 'auto 8', 2.0, 46, 7.0, 650
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'V60' AND b.name = 'Volvo';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 9, 6, 6, 9, 7, 'baixo', 'A carrinha mais bonita do segmento. Segurança, conforto, espaço. Escolha de quem sabe o que quer.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'V60' AND b.name = 'Volvo';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 33000, 27000, 40000, 18, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'V60' AND b.name = 'Volvo';

-- ── Alfa Romeo Giulia ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '2.0 Turbo 200cv', 'gasolina', 1995, 200, 330, 'auto 8', 6.8, 155, 6.0, 650
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Giulia' AND b.name = 'Alfa Romeo';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '2.2 JTDm 160cv', 'diesel', 2143, 160, 450, 'auto 8', 4.8, 126, 6.5, 600
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Giulia' AND b.name = 'Alfa Romeo';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '2.2 JTDm 190cv', 'diesel', 2143, 190, 450, 'auto 8', 5.0, 132, 6.5, 620
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Giulia' AND b.name = 'Alfa Romeo';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '2.9 V6 Quadrifoglio 510cv', 'gasolina', 2891, 510, 600, 'auto 8', 9.5, 216, 5.5, 1200
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Giulia' AND b.name = 'Alfa Romeo';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 7, 10, 5, 9, 4, 'medio', 'Pura emoção italiana. Chassis de referência — melhor que BMW. Motor Quadrifoglio é Ferrari. Fiabilidade é o preço da paixão.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Giulia' AND b.name = 'Alfa Romeo';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 28000, 22000, 35000, 18, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Giulia' AND b.name = 'Alfa Romeo';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2020, 22000, 17000, 28000, 25, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Giulia' AND b.name = 'Alfa Romeo';
INSERT INTO engine_issues (engine_id, severity, description, affected_years, fix_cost_estimate, source)
SELECT e.id, 'medio', 'Eletrónica e sensores podem dar problemas. Manutenção mais cara que alemães. Vale cada cêntimo se gostas de conduzir.', '2016+', 'variável', 'Alfa Romeo forums'
FROM engines e JOIN vehicle_models vm ON e.model_id = vm.id JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Giulia' AND b.name = 'Alfa Romeo' LIMIT 1;

-- ── Tesla Model 3 ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, 'Model 3 RWD 283cv', 'eletrico', 0, 283, 420, 'auto', 14.5, 0, 7.5, 250
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Model 3' AND b.name = 'Tesla';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, 'Model 3 Long Range AWD 366cv', 'eletrico', 0, 366, 493, 'auto', 15.0, 0, 7.5, 280
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Model 3' AND b.name = 'Tesla';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, 'Model 3 Performance 460cv', 'eletrico', 0, 460, 639, 'auto', 15.5, 0, 7.5, 300
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Model 3' AND b.name = 'Tesla';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 7, 7, 8, 8, 5, 'baixo', 'Elétrico que mudou tudo. Autonomia real 400-500km. Performance brutal. Interior minimalista polarizante. Autopilot.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Model 3' AND b.name = 'Tesla';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 32000, 26000, 40000, 35, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Model 3' AND b.name = 'Tesla';

-- ── Tesla Model Y ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, 'Model Y RWD 283cv', 'eletrico', 0, 283, 420, 'auto', 15.5, 0, 7.5, 260
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Model Y' AND b.name = 'Tesla';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, 'Model Y Long Range AWD 366cv', 'eletrico', 0, 366, 493, 'auto', 16.0, 0, 7.5, 290
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Model Y' AND b.name = 'Tesla';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 7, 6, 7, 8, 7, 'baixo', 'Model 3 com mais espaço. Prático para família. Mesma tecnologia. Carro mais vendido do mundo em 2023.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Model Y' AND b.name = 'Tesla';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2023, 37000, 31000, 44000, 28, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Model Y' AND b.name = 'Tesla';

-- ── Volvo XC40 ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, 'B3 163cv', 'gasolina', 1477, 163, 265, 'auto 7', 6.5, 148, 7.5, 520
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'XC40' AND b.name = 'Volvo';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, 'B4 197cv', 'gasolina', 1969, 197, 300, 'auto 8', 6.8, 155, 7.5, 550
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'XC40' AND b.name = 'Volvo';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, 'B4D 197cv', 'diesel', 1969, 197, 420, 'auto 8', 5.5, 145, 7.5, 540
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'XC40' AND b.name = 'Volvo';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, 'Recharge Pure Electric 231cv', 'eletrico', 0, 231, 330, 'auto', 17.0, 0, 7.5, 260
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'XC40' AND b.name = 'Volvo';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 8, 6, 8, 7, 6, 'baixo', 'SUV premium compacto. Segurança Volvo. Design nórdico. Interior requintado. Elétrico com boa autonomia.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'XC40' AND b.name = 'Volvo';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 30000, 24000, 37000, 25, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'XC40' AND b.name = 'Volvo';

-- ── Volvo XC60 ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, 'B4 197cv', 'gasolina', 1969, 197, 300, 'auto 8', 7.2, 164, 7.5, 580
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'XC60' AND b.name = 'Volvo';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, 'B4D 197cv', 'diesel', 1969, 197, 420, 'auto 8', 5.5, 145, 7.5, 570
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'XC60' AND b.name = 'Volvo';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, 'T8 PHEV 390cv', 'hibrido', 1969, 390, 640, 'auto 8', 2.5, 57, 7.0, 650
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'XC60' AND b.name = 'Volvo';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 9, 5, 6, 8, 7, 'baixo', 'SUV de referência em segurança e conforto. Interior sublime. O PHEV é espetacular. Design intemporal.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'XC60' AND b.name = 'Volvo';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 38000, 31000, 46000, 22, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'XC60' AND b.name = 'Volvo';

-- ── Cupra Formentor ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.5 TSI 150 DSG', 'gasolina', 1498, 150, 250, 'auto 7', 6.3, 143, 7.0, 480
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Formentor' AND b.name = 'Cupra';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '2.0 TSI 245 DSG 4Drive', 'gasolina', 1984, 245, 370, 'auto 7', 7.5, 171, 7.0, 560
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Formentor' AND b.name = 'Cupra';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.4 e-Hybrid 245', 'hibrido', 1395, 245, 400, 'auto 6', 1.5, 33, 7.0, 520
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Formentor' AND b.name = 'Cupra';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 7, 8, 7, 8, 6, 'medio', 'SUV-coupé com alma desportiva. Design espetacular. O 2.0 TSI 245cv é sério. Marca em ascensão.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Formentor' AND b.name = 'Cupra';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 28000, 23000, 35000, 22, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Formentor' AND b.name = 'Cupra';

-- ── Lexus NX ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '350h Híbrido 244cv', 'hibrido', 2487, 244, 239, 'auto cvt', 5.5, 125, 9.0, 400
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'NX' AND b.name = 'Lexus';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '450h+ PHEV 309cv', 'hibrido', 2487, 309, 227, 'auto cvt', 1.2, 27, 8.5, 450
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'NX' AND b.name = 'Lexus';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 8, 5, 7, 8, 7, 'baixo', 'Premium japonês alternativo. Fiabilidade Toyota. Interior luxuoso. Híbrido eficiente. Silencioso e refinado.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'NX' AND b.name = 'Lexus';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2023, 42000, 36000, 50000, 12, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'NX' AND b.name = 'Lexus';

-- ── Land Rover Defender ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, 'D200 200cv', 'diesel', 1997, 200, 430, 'auto 8', 7.5, 197, 6.5, 700
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Defender' AND b.name = 'Land Rover';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, 'P300 300cv', 'gasolina', 1997, 300, 400, 'auto 8', 9.0, 205, 6.5, 720
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Defender' AND b.name = 'Land Rover';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, 'P400e PHEV 404cv', 'hibrido', 1997, 404, 640, 'auto 8', 3.0, 68, 6.0, 750
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Defender' AND b.name = 'Land Rover';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 7, 7, 5, 7, 8, 'medio', 'Ícone reinventado. Off-road sério com luxo moderno. Presença inigualável. Manutenção cara mas experiência única.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Defender' AND b.name = 'Land Rover';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 55000, 45000, 68000, 18, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Defender' AND b.name = 'Land Rover';
INSERT INTO engine_issues (engine_id, severity, description, affected_years, fix_cost_estimate, source)
SELECT e.id, 'medio', 'Eletrónica pode ter falhas em primeiros anos. Sensores e sistemas complexos. Garantia 3 anos.', '2020+', 'variável', 'JLR forums'
FROM engines e JOIN vehicle_models vm ON e.model_id = vm.id JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Defender' AND b.name = 'Land Rover' LIMIT 1;

-- ── Porsche Macan ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, 'Macan 265cv', 'gasolina', 1984, 265, 400, 'auto 7', 8.0, 182, 7.5, 800
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Macan' AND b.name = 'Porsche';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, 'Macan S 380cv', 'gasolina', 2894, 380, 520, 'auto 7', 9.0, 205, 7.5, 900
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Macan' AND b.name = 'Porsche';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, 'Macan GTS 440cv', 'gasolina', 2894, 440, 550, 'auto 7', 9.5, 216, 7.5, 1000
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Macan' AND b.name = 'Porsche';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 8, 9, 6, 9, 5, 'baixo', 'SUV desportivo por excelência. Condução de carro desportivo em formato SUV. O GTS é sensacional.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Macan' AND b.name = 'Porsche';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 52000, 42000, 65000, 15, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Macan' AND b.name = 'Porsche';

-- ── Porsche Cayenne ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, 'Cayenne 340cv', 'gasolina', 2995, 340, 450, 'auto 8', 9.5, 216, 7.5, 900
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Cayenne' AND b.name = 'Porsche';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, 'Cayenne S 474cv', 'gasolina', 2894, 474, 600, 'auto 8', 10.0, 227, 7.5, 1100
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Cayenne' AND b.name = 'Porsche';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, 'Cayenne E-Hybrid 462cv', 'hibrido', 2995, 462, 700, 'auto 8', 3.5, 80, 7.0, 950
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Cayenne' AND b.name = 'Porsche';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 9, 9, 5, 9, 6, 'baixo', 'Grand turismo com formato SUV. Conduz como um desportivo, conforta como um sedan de luxo. Impressionante.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Cayenne' AND b.name = 'Porsche';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 65000, 52000, 82000, 12, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Cayenne' AND b.name = 'Porsche';

-- ── BMW X3 ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, 'xDrive20i 184cv', 'gasolina', 1998, 184, 300, 'auto 8', 7.0, 159, 7.5, 620
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'X3' AND b.name = 'BMW';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, 'xDrive20d 190cv', 'diesel', 1995, 190, 400, 'auto 8', 5.5, 145, 7.5, 600
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'X3' AND b.name = 'BMW';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, 'xDrive30e PHEV 292cv', 'hibrido', 1998, 292, 420, 'auto 8', 2.0, 46, 7.0, 650
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'X3' AND b.name = 'BMW';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 8, 7, 6, 9, 7, 'baixo', 'SUV premium equilibrado. Condução BMW sem compromissos. Espaço familiar. PHEV com boa autonomia.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'X3' AND b.name = 'BMW';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2023, 42000, 35000, 50000, 18, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'X3' AND b.name = 'BMW';

-- ── Mercedes-Benz GLC ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, 'GLC 200 204cv', 'gasolina', 1999, 204, 320, 'auto 9', 7.0, 159, 7.5, 640
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'GLC' AND b.name = 'Mercedes-Benz';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, 'GLC 220d 197cv', 'diesel', 1993, 197, 440, 'auto 9', 5.3, 139, 7.5, 620
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'GLC' AND b.name = 'Mercedes-Benz';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, 'GLC 300e PHEV 313cv', 'hibrido', 1999, 313, 550, 'auto 9', 0.8, 18, 7.0, 680
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'GLC' AND b.name = 'Mercedes-Benz';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 9, 6, 6, 8, 7, 'baixo', 'Mini GLE. Interior de luxo. Conforto extraordinário. PHEV com 100km de autonomia elétrica real. Premium total.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'GLC' AND b.name = 'Mercedes-Benz';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2023, 48000, 40000, 58000, 15, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'GLC' AND b.name = 'Mercedes-Benz';

-- ── Audi Q5 ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '40 TFSI 204cv', 'gasolina', 1984, 204, 320, 'auto 7', 7.2, 164, 7.5, 620
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Q5' AND b.name = 'Audi';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '35 TDI 163cv', 'diesel', 1968, 163, 380, 'auto 7', 5.3, 139, 7.5, 600
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Q5' AND b.name = 'Audi';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '50 TFSIe PHEV 299cv', 'hibrido', 1984, 299, 450, 'auto 7', 1.8, 41, 7.0, 650
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Q5' AND b.name = 'Audi';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 8, 6, 6, 8, 7, 'baixo', 'SUV premium equilibrado. Qualidade Audi impecável. quattro de referência. Virtual Cockpit. Refinado em tudo.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Q5' AND b.name = 'Audi';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 40000, 33000, 49000, 20, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Q5' AND b.name = 'Audi';

-- ── Dacia Jogger ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.0 TCe 110', 'gasolina', 999, 110, 200, 'manual 6', 6.3, 143, 7.0, 320
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Jogger' AND b.name = 'Dacia';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.6 Hybrid 140', 'hibrido', 1598, 140, 205, 'auto', 4.8, 109, 7.5, 350
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Jogger' AND b.name = 'Dacia';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 6, 3, 6, 6, 9, 'medio', '7 lugares pelo preço de um citadino. Melhor relação espaço-preço do mercado. Sem luxos mas com espaço para tudo.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Jogger' AND b.name = 'Dacia';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2023, 17000, 14000, 21000, 25, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Jogger' AND b.name = 'Dacia';

-- ── Peugeot 5008 ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.2 PureTech 130 EAT8', 'gasolina', 1199, 130, 230, 'auto 8', 6.5, 148, 6.0, 460
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = '5008' AND b.name = 'Peugeot';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.5 BlueHDi 130 EAT8', 'diesel', 1499, 130, 300, 'auto 8', 5.0, 132, 7.5, 450
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = '5008' AND b.name = 'Peugeot';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.6 Hybrid 225 PHEV', 'hibrido', 1598, 225, 360, 'auto 8', 1.5, 34, 7.0, 490
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = '5008' AND b.name = 'Peugeot';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 8, 4, 6, 7, 9, 'baixo', '7 lugares com estilo. Interior premium para a classe. Confortável e espaçoso. Alternativa elegante aos MPV.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = '5008' AND b.name = 'Peugeot';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 27000, 22000, 33000, 22, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = '5008' AND b.name = 'Peugeot';

-- ── Hyundai Ioniq 5 ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, 'RWD 228cv 77kWh', 'eletrico', 0, 228, 350, 'auto', 17.0, 0, 8.0, 250
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Ioniq 5' AND b.name = 'Hyundai';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, 'AWD 325cv 77kWh', 'eletrico', 0, 325, 605, 'auto', 18.0, 0, 8.0, 270
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Ioniq 5' AND b.name = 'Hyundai';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 8, 7, 7, 8, 7, 'baixo', 'Design retro-futurista. Interior lounge. Carregamento 800V ultra-rápido. Um dos melhores EVs do mercado.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Ioniq 5' AND b.name = 'Hyundai';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2023, 38000, 32000, 46000, 18, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Ioniq 5' AND b.name = 'Hyundai';

-- ── Kia EV6 ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, 'RWD 229cv 77kWh', 'eletrico', 0, 229, 350, 'auto', 16.5, 0, 8.0, 250
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'EV6' AND b.name = 'Kia';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, 'AWD 325cv 77kWh', 'eletrico', 0, 325, 605, 'auto', 17.5, 0, 8.0, 270
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'EV6' AND b.name = 'Kia';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, 'GT 585cv', 'eletrico', 0, 585, 740, 'auto', 19.0, 0, 7.5, 300
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'EV6' AND b.name = 'Kia';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 7, 8, 7, 8, 6, 'baixo', 'Plataforma Ioniq 5, personalidade desportiva. GT é brutal. Design de coupé. 800V. Premiado mundialmente.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'EV6' AND b.name = 'Kia';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2023, 40000, 34000, 48000, 15, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'EV6' AND b.name = 'Kia';

-- ── Volvo EX30 ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, 'Single Motor 272cv', 'eletrico', 0, 272, 343, 'auto', 15.5, 0, 7.5, 230
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'EX30' AND b.name = 'Volvo';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 7, 6, 8, 7, 4, 'baixo', 'O Volvo mais acessível. Interior minimalista radical. Compacto e ágil. Segurança Volvo. Entrada no mundo premium EV.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'EX30' AND b.name = 'Volvo';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2024, 33000, 29000, 38000, 10, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'EX30' AND b.name = 'Volvo';

-- ── Toyota GR Yaris ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.6 Turbo 261cv AWD', 'gasolina', 1618, 261, 360, 'manual 6', 7.5, 171, 8.0, 450
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'GR Yaris' AND b.name = 'Toyota';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 5, 10, 6, 7, 3, 'medio', 'Homologação de rali para a estrada. AWD, 261cv, 1.2 toneladas. Provavelmente o hot hatch mais puro à venda hoje. Lendário.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'GR Yaris' AND b.name = 'Toyota';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2023, 38000, 33000, 45000, 8, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'GR Yaris' AND b.name = 'Toyota';

-- ── Toyota GR86 ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '2.4 Boxer 234cv', 'gasolina', 2387, 234, 250, 'manual 6', 8.5, 193, 8.0, 400
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'GR86' AND b.name = 'Toyota';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 5, 10, 5, 7, 2, 'medio', 'Coupé puro como já não se fazem. Leve, equilibrado, motor boxer. Diversão analógica. Nenhuma eletrónica entre ti e a estrada.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'GR86' AND b.name = 'Toyota';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2023, 32000, 28000, 37000, 6, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'GR86' AND b.name = 'Toyota';

-- ── Mazda MX-5 ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.5 Skyactiv-G 132cv', 'gasolina', 1496, 132, 152, 'manual 6', 6.5, 148, 9.0, 350
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'MX-5' AND b.name = 'Mazda';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '2.0 Skyactiv-G 184cv', 'gasolina', 1998, 184, 205, 'manual 6', 7.0, 159, 8.5, 380
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'MX-5' AND b.name = 'Mazda';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 5, 10, 6, 7, 1, 'medio', 'O roadster perfeito. Leve, equilibrado, capota manual satisfatória. Sorrisos por quilómetro é a métrica que interessa.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'MX-5' AND b.name = 'Mazda';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 25000, 20000, 31000, 12, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'MX-5' AND b.name = 'Mazda';

-- ── Alpine A110 ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.8 Turbo 252cv', 'gasolina', 1798, 252, 320, 'auto 7', 6.5, 148, 7.0, 700
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'A110' AND b.name = 'Alpine';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.8 Turbo S 300cv', 'gasolina', 1798, 300, 340, 'auto 7', 6.8, 155, 7.0, 750
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'A110' AND b.name = 'Alpine';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 5, 10, 4, 8, 1, 'medio', 'Escultura automóvel francesa. Chassis de mid-engine, 1100kg, alumínio. Condução transcendente. Obra de arte.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'A110' AND b.name = 'Alpine';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 48000, 40000, 58000, 6, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'A110' AND b.name = 'Alpine';

-- ── Ford Mustang ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '2.3 EcoBoost 290cv', 'gasolina', 2261, 290, 440, 'auto 10', 9.0, 205, 7.0, 600
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Mustang' AND b.name = 'Ford';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '5.0 V8 GT 450cv', 'gasolina', 4951, 450, 529, 'manual 6', 12.5, 284, 7.0, 800
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Mustang' AND b.name = 'Ford';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 6, 9, 4, 7, 3, 'alto', 'Muscle car americano. V8 inconfundível. Presença na estrada impossível de ignorar. Consumos e tamanho americanos.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Mustang' AND b.name = 'Ford';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 38000, 30000, 48000, 10, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Mustang' AND b.name = 'Ford';

-- ── Subaru BRZ ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '2.4 Boxer 234cv', 'gasolina', 2387, 234, 250, 'manual 6', 8.5, 193, 8.0, 400
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'BRZ' AND b.name = 'Subaru';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 5, 10, 5, 7, 2, 'medio', 'Gémeo do GR86 com identidade Subaru. Motor boxer puro. AWD ausente — é RWD puro. Diversão analógica.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'BRZ' AND b.name = 'Subaru';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2023, 31000, 27000, 36000, 5, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'BRZ' AND b.name = 'Subaru';

-- ── Suzuki Swift ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.2 Hybrid 83cv', 'hibrido', 1197, 83, 107, 'manual 5', 4.6, 105, 8.5, 300
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Swift' AND b.name = 'Suzuki';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.4 Boosterjet Sport 129cv', 'gasolina', 1373, 129, 235, 'manual 6', 5.8, 132, 8.0, 350
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Swift' AND b.name = 'Suzuki';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 5, 7, 9, 5, 4, 'baixo', 'Leve e divertido. Sport é um pocket rocket. Fiável como tudo da Suzuki. Preço justo, diversão garantida.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Swift' AND b.name = 'Suzuki';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 12000, 9000, 15500, 20, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Swift' AND b.name = 'Suzuki';

-- ── Suzuki Vitara ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.4 Boosterjet Hybrid 129cv', 'hibrido', 1373, 129, 235, 'manual 6', 5.8, 132, 8.5, 350
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Vitara' AND b.name = 'Suzuki';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.4 Boosterjet AllGrip 129cv', 'hibrido', 1373, 129, 235, 'manual 6', 6.2, 141, 8.5, 370
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Vitara' AND b.name = 'Suzuki';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 6, 5, 7, 6, 6, 'medio', 'SUV compacto fiável e com verdadeiro 4x4. AllGrip competente em terra. Japão no melhor: simples e durável.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Vitara' AND b.name = 'Suzuki';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 17000, 13500, 21000, 18, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Vitara' AND b.name = 'Suzuki';

-- ── Suzuki S-Cross ──
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.4 Boosterjet Hybrid 129cv', 'hibrido', 1373, 129, 235, 'manual 6', 5.8, 132, 8.5, 360
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'S-Cross' AND b.name = 'Suzuki';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.4 Boosterjet AllGrip Hybrid', 'hibrido', 1373, 129, 235, 'auto 6', 6.2, 141, 8.5, 380
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'S-Cross' AND b.name = 'Suzuki';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 7, 5, 7, 7, 6, 'baixo', 'Evolução do Vitara com mais refinamento. Interior melhorado. Fiabilidade Suzuki. Surpreendente valor.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'S-Cross' AND b.name = 'Suzuki';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2023, 22000, 18000, 27000, 12, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'S-Cross' AND b.name = 'Suzuki';
-- CARACTR v3.1 — Logging & Feedback tables
-- Run after the main seed: psql -U postgres -d carrojusto_dev -f migration_v31_logging.sql

-- Session logging: every /recommend call
CREATE TABLE IF NOT EXISTS recommendation_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMP DEFAULT NOW(),
    answers_raw JSONB NOT NULL,
    profile_computed JSONB NOT NULL,
    models_shown JSONB NOT NULL,
    models_pool_size INTEGER,
    budget_range JSONB,
    had_stretch BOOLEAN DEFAULT FALSE,
    had_wildcard BOOLEAN DEFAULT FALSE
);

-- User feedback: optional, post-results
CREATE TABLE IF NOT EXISTS user_feedback (
    id SERIAL PRIMARY KEY,
    session_id UUID REFERENCES recommendation_sessions(id),
    created_at TIMESTAMP DEFAULT NOW(),
    satisfaction VARCHAR(20),
    preferred_model_id INTEGER,
    email VARCHAR(255)
);

-- Index for fast feedback lookups by session
CREATE INDEX IF NOT EXISTS idx_feedback_session ON user_feedback(session_id);

-- Index for analytics queries
CREATE INDEX IF NOT EXISTS idx_sessions_created ON recommendation_sessions(created_at);
-- Caractr v4.0 — Analytics events table
-- Run once against the production / dev database.

CREATE TABLE IF NOT EXISTS analytics_events (
    id          SERIAL PRIMARY KEY,
    session_id  UUID,                           -- links to recommendation_sessions (optional)
    event_name  TEXT        NOT NULL,
    properties  JSONB       DEFAULT '{}',
    created_at  TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_analytics_events_session  ON analytics_events (session_id);
CREATE INDEX IF NOT EXISTS idx_analytics_events_name     ON analytics_events (event_name);
CREATE INDEX IF NOT EXISTS idx_analytics_events_created  ON analytics_events (created_at DESC);
-- Caractr v4.1 — Extended listings schema for deal scoring + LLM analysis
-- Run once against dev/prod database.

-- Extend raw_listings with seller context and photo count
ALTER TABLE raw_listings
    ADD COLUMN IF NOT EXISTS seller_type    VARCHAR(20),          -- privado | stand
    ADD COLUMN IF NOT EXISTS photo_count    INTEGER,
    ADD COLUMN IF NOT EXISTS listing_age    INTEGER,              -- days since listed
    ADD COLUMN IF NOT EXISTS description    TEXT,
    ADD COLUMN IF NOT EXISTS scraped_at     TIMESTAMPTZ DEFAULT NOW();

-- Extend normalized_listings with deal scoring and LLM analysis
ALTER TABLE normalized_listings
    ADD COLUMN IF NOT EXISTS price_vs_market    FLOAT,            -- (listing_price - avg_price) / avg_price
    ADD COLUMN IF NOT EXISTS price_delta        FLOAT,            -- (avg - listing) / avg: +1 = 20% under, -1 = 20% over
    ADD COLUMN IF NOT EXISTS km_per_year        FLOAT,
    ADD COLUMN IF NOT EXISTS seller_type        VARCHAR(20),      -- privado | stand
    ADD COLUMN IF NOT EXISTS listing_age_days   INTEGER,
    ADD COLUMN IF NOT EXISTS photo_count        INTEGER,
    ADD COLUMN IF NOT EXISTS deal_tier          VARCHAR(20),      -- forte | razoavel | cuidado | evitar
    ADD COLUMN IF NOT EXISTS deal_score         FLOAT,            -- 0.0 – 1.0
    ADD COLUMN IF NOT EXISTS llm_analysis       JSONB,
    ADD COLUMN IF NOT EXISTS analysis_cached_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS description        TEXT;

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_normalized_model_price  ON normalized_listings (model_id, price);
CREATE INDEX IF NOT EXISTS idx_normalized_deal_tier    ON normalized_listings (deal_tier);
CREATE INDEX IF NOT EXISTS idx_normalized_cached_at    ON normalized_listings (analysis_cached_at DESC NULLS LAST);
-- Caractr v4.2 — Concierge requests table
-- Phase 1: intent capture only, no Stripe, manual delivery by founder.

CREATE TABLE IF NOT EXISTS concierge_requests (
    id              SERIAL PRIMARY KEY,
    session_id      UUID,                           -- links to recommendation_sessions
    name            VARCHAR(200),
    email           VARCHAR(200)    NOT NULL,
    phone           VARCHAR(50),
    model_interest  VARCHAR(200),                   -- preferred model name
    budget_max      INTEGER,
    timeline        VARCHAR(50),                    -- "imediato" | "1-3 meses" | "3-6 meses" | "a ver"
    notes           TEXT,                           -- free text from user
    tier            VARCHAR(20)     DEFAULT 'basico',  -- basico | completo
    status          VARCHAR(30)     DEFAULT 'new',  -- new | contacted | delivered | closed
    created_at      TIMESTAMPTZ     DEFAULT now(),
    delivered_at    TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_concierge_status  ON concierge_requests (status);
CREATE INDEX IF NOT EXISTS idx_concierge_created ON concierge_requests (created_at DESC);
-- Caractr migration v4.3 — Concierge v2 schema
-- Adds consent flags and feedback_tags, removes tier dependency

ALTER TABLE concierge_requests
  ADD COLUMN IF NOT EXISTS consent_caractr BOOLEAN NOT NULL DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS consent_dealer  BOOLEAN NOT NULL DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS feedback_tags   JSONB   NOT NULL DEFAULT '[]'::jsonb;

-- Index for dealer consent queries (lead gen pipeline)
CREATE INDEX IF NOT EXISTS idx_concierge_consent_dealer
  ON concierge_requests (consent_dealer)
  WHERE consent_dealer = TRUE;

COMMENT ON COLUMN concierge_requests.consent_caractr IS 'User consented to Caractr contact — required';
COMMENT ON COLUMN concierge_requests.consent_dealer  IS 'User consented to dealer partner referral — optional, lead gen';
COMMENT ON COLUMN concierge_requests.feedback_tags   IS 'Quick feedback reasons from results page (e.g. wrong brand, too sporty)';
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
-- Migration v5.1 — Full generations table population
-- Covers all 200 vehicle models in the Caractr database.
-- Each generation has: name (e.g. 'Mk7', 'E90', 'F30'), year_start, year_end (NULL = still in production), platform/chassis code.
-- year_end is NULL for the current production generation.
--
-- Idempotent: clears existing rows and repopulates.
-- Run once after migration_v50_market_upsert.sql.

TRUNCATE TABLE generations RESTART IDENTITY;

WITH gen_data (brand, model, name, year_start, year_end, platform) AS (VALUES

  -- ── CITADINOS ─────────────────────────────────────────────────────────────

  -- Renault Clio
  ('Renault',    'Clio',       'Clio III',   2005, 2012, 'B/C'),
  ('Renault',    'Clio',       'Clio IV',    2012, 2019, 'B98'),
  ('Renault',    'Clio',       'Clio V',     2019, NULL, 'CMF-B'),

  -- Peugeot 208
  ('Peugeot',    '208',        '208 I',      2012, 2019, 'PF1'),
  ('Peugeot',    '208',        '208 II',     2019, NULL, 'CMP'),

  -- Citroën C3
  ('Citroen',    'C3',         'C3 II',      2009, 2016, 'PF1'),
  ('Citroen',    'C3',         'C3 III',     2016, NULL, 'CMP'),

  -- Dacia Sandero
  ('Dacia',      'Sandero',    'Sandero I',  2008, 2012, 'B0'),
  ('Dacia',      'Sandero',    'Sandero II', 2012, 2020, 'B0'),
  ('Dacia',      'Sandero',    'Sandero III',2021, NULL, 'CMF-B'),

  -- Opel Corsa
  ('Opel',       'Corsa',      'Corsa D',    2006, 2014, 'Gamma'),
  ('Opel',       'Corsa',      'Corsa E',    2014, 2019, 'Gamma 2'),
  ('Opel',       'Corsa',      'Corsa F',    2019, NULL, 'CMP'),

  -- Toyota Yaris
  ('Toyota',     'Yaris',      'Yaris III',  2011, 2020, 'B'),
  ('Toyota',     'Yaris',      'Yaris IV',   2020, NULL, 'GR'),

  -- Volkswagen Polo
  ('Volkswagen', 'Polo',       'Polo V',     2009, 2017, 'PQ25'),
  ('Volkswagen', 'Polo',       'Polo VI',    2017, NULL, 'MQB A0'),

  -- SEAT Ibiza
  ('SEAT',       'Ibiza',      'Ibiza IV',   2008, 2017, 'PQ25'),
  ('SEAT',       'Ibiza',      'Ibiza V',    2017, NULL, 'MQB A0'),

  -- Skoda Fabia
  ('Skoda',      'Fabia',      'Fabia II',   2007, 2014, 'PQ25'),
  ('Skoda',      'Fabia',      'Fabia III',  2014, 2021, 'PQ25'),
  ('Skoda',      'Fabia',      'Fabia IV',   2021, NULL, 'MQB A0'),

  -- Hyundai i20
  ('Hyundai',    'i20',        'i20 I',      2008, 2014, 'PB'),
  ('Hyundai',    'i20',        'i20 II',     2014, 2020, 'GB'),
  ('Hyundai',    'i20',        'i20 III',    2020, NULL, 'BC3'),

  -- Kia Rio
  ('Kia',        'Rio',        'Rio III',    2011, 2017, 'UB'),
  ('Kia',        'Rio',        'Rio IV',     2017, NULL, 'YB'),

  -- Ford Fiesta
  ('Ford',       'Fiesta',     'Fiesta VI',  2008, 2017, 'B299'),
  ('Ford',       'Fiesta',     'Fiesta VII', 2017, 2023, 'B516'),

  -- Nissan Micra
  ('Nissan',     'Micra',      'Micra K13',  2010, 2017, 'V-platform'),
  ('Nissan',     'Micra',      'Micra K14',  2017, NULL, 'CMF-B'),

  -- Mazda 2
  ('Mazda',      '2',          'Mazda 2 III',2014, NULL, 'SkyActiv'),

  -- Honda Jazz
  ('Honda',      'Jazz',       'Jazz III',   2015, 2020, 'GK'),
  ('Honda',      'Jazz',       'Jazz IV',    2020, NULL, 'GR'),

  -- Fiat 500
  ('Fiat',       '500',        '500 (312)',  2007, 2023, '188/312'),
  ('Fiat',       '500',        '500e',       2020, NULL, 'STLA Small'),

  -- Fiat Panda
  ('Fiat',       'Panda',      'Panda III',  2012, NULL, '188'),

  -- Toyota Aygo X
  ('Toyota',     'Aygo X',     'Aygo X',     2022, NULL, 'GNA'),

  -- Hyundai i10
  ('Hyundai',    'i10',        'i10 I',      2007, 2013, 'PA'),
  ('Hyundai',    'i10',        'i10 II',     2013, 2019, 'BA'),
  ('Hyundai',    'i10',        'i10 III',    2019, NULL, 'AC3'),

  -- Kia Picanto
  ('Kia',        'Picanto',    'Picanto II', 2011, 2017, 'TA'),
  ('Kia',        'Picanto',    'Picanto III',2017, NULL, 'JA'),

  -- Volkswagen up!
  ('Volkswagen', 'up!',        'up! I',      2011, 2023, 'NSF'),

  -- Renault Twingo
  ('Renault',    'Twingo',     'Twingo II',  2007, 2014, 'X44'),
  ('Renault',    'Twingo',     'Twingo III', 2014, 2022, 'X07'),

  -- Citroën C1
  ('Citroen',    'C1',         'C1 I',       2005, 2014, 'A'),
  ('Citroen',    'C1',         'C1 II',      2014, 2022, 'B'),

  -- Peugeot 108
  ('Peugeot',    '108',        '108',        2014, 2021, 'B'),

  -- Opel Adam
  ('Opel',       'Adam',       'Adam',       2012, 2019, 'Gamma 2'),

  -- ── COMPACTOS (C-segment) ────────────────────────────────────────────────

  -- Volkswagen Golf
  ('Volkswagen', 'Golf',       'Mk6',        2008, 2012, 'PQ35'),
  ('Volkswagen', 'Golf',       'Mk7',        2012, 2019, 'MQB'),
  ('Volkswagen', 'Golf',       'Mk8',        2020, NULL, 'MQB Evo'),

  -- Peugeot 308
  ('Peugeot',    '308',        '308 I',      2007, 2013, 'PF2'),
  ('Peugeot',    '308',        '308 II',     2013, 2021, 'EMP2'),
  ('Peugeot',    '308',        '308 III',    2021, NULL, 'EMP2'),

  -- Renault Mégane
  ('Renault',    'Megane',     'Mégane III', 2008, 2015, 'C'),
  ('Renault',    'Megane',     'Mégane IV',  2015, 2022, 'CMF-CD'),

  -- Toyota Corolla
  ('Toyota',     'Corolla',    'E170',       2013, 2018, 'MC'),
  ('Toyota',     'Corolla',    'E210',       2018, NULL, 'TNGA-C'),

  -- SEAT Leon
  ('SEAT',       'Leon',       'Leon III',   2012, 2020, 'MQB'),
  ('SEAT',       'Leon',       'Leon IV',    2020, NULL, 'MQB Evo'),

  -- Skoda Octavia
  ('Skoda',      'Octavia',    'Octavia III',2012, 2019, 'MQB'),
  ('Skoda',      'Octavia',    'Octavia IV', 2020, NULL, 'MQB Evo'),

  -- Ford Focus
  ('Ford',       'Focus',      'Focus III',  2010, 2018, 'C1'),
  ('Ford',       'Focus',      'Focus IV',   2018, NULL, 'C2'),

  -- Opel Astra
  ('Opel',       'Astra',      'Astra J',    2009, 2015, 'Delta II'),
  ('Opel',       'Astra',      'Astra K',    2015, 2021, 'D2XX'),
  ('Opel',       'Astra',      'Astra L',    2021, NULL, 'STL-A'),

  -- Hyundai i30
  ('Hyundai',    'i30',        'i30 II',     2011, 2017, 'GD'),
  ('Hyundai',    'i30',        'i30 III',    2017, NULL, 'PD'),

  -- Kia Ceed
  ('Kia',        'Ceed',       'Ceed II',    2012, 2018, 'JD'),
  ('Kia',        'Ceed',       'Ceed III',   2018, NULL, 'CD'),

  -- Mazda 3
  ('Mazda',      '3',          'Mazda 3 III',2013, 2018, 'SkyActiv'),
  ('Mazda',      '3',          'Mazda 3 IV', 2018, NULL, 'SKY-VA'),

  -- Honda Civic
  ('Honda',      'Civic',      'Civic IX',   2011, 2015, 'FB/FG'),
  ('Honda',      'Civic',      'Civic X',    2015, 2021, 'FC/FK'),
  ('Honda',      'Civic',      'Civic XI',   2021, NULL, 'FL'),

  -- Audi A3
  ('Audi',       'A3',         'A3 8P',      2003, 2012, 'PQ35'),
  ('Audi',       'A3',         'A3 8V',      2012, 2020, 'MQB'),
  ('Audi',       'A3',         'A3 8Y',      2020, NULL, 'MQB Evo'),

  -- BMW Série 1
  ('BMW',        'Serie 1',    'E87',        2004, 2011, 'E87'),
  ('BMW',        'Serie 1',    'F20',        2011, 2019, 'UKL1'),
  ('BMW',        'Serie 1',    'F40',        2019, NULL, 'UKL3/FAAR'),

  -- Mercedes-Benz Classe A
  ('Mercedes-Benz','Classe A', 'W168',       1997, 2004, 'W168'),
  ('Mercedes-Benz','Classe A', 'W169',       2004, 2012, 'W169'),
  ('Mercedes-Benz','Classe A', 'W176',       2012, 2018, 'MFA'),
  ('Mercedes-Benz','Classe A', 'W177',       2018, NULL, 'MFA2'),

  -- Volvo V40
  ('Volvo',      'V40',        'V40 II',     2012, 2019, '525/526'),

  -- Cupra Leon
  ('Cupra',      'Leon',       'Leon I',     2014, 2020, 'MQB'),
  ('Cupra',      'Leon',       'Leon II',    2020, NULL, 'MQB Evo'),

  -- DS 4
  ('DS',         '4',          'DS 4',       2021, NULL, 'EMP2'),

  -- Citroën C4
  ('Citroen',    'C4',         'C4 II',      2010, 2018, 'PF2'),
  ('Citroen',    'C4',         'C4 III',     2020, NULL, 'EMP2'),

  -- Fiat Tipo
  ('Fiat',       'Tipo',       'Tipo',       2015, NULL, '356'),

  -- Skoda Scala
  ('Skoda',      'Scala',      'Scala I',    2018, NULL, 'MQB A0'),

  -- Volkswagen ID.3
  ('Volkswagen', 'ID.3',       'ID.3 I',     2020, NULL, 'MEB'),

  -- MG 4
  ('MG',         '4',          'MG 4 I',     2022, NULL, 'MSP'),

  -- Renault 5 E-Tech
  ('Renault',    '5 E-Tech',   'R5 E-Tech',  2024, NULL, 'AmpR Small'),

  -- Peugeot E-308
  ('Peugeot',    'E-308',      'E-308 I',    2023, NULL, 'STLA Medium'),

  -- Toyota Prius
  ('Toyota',     'Prius',      'Prius IV',   2015, 2022, 'TNGA-C'),
  ('Toyota',     'Prius',      'Prius V',    2022, NULL, 'TNGA-C'),

  -- Hyundai Ioniq
  ('Hyundai',    'Ioniq',      'Ioniq I',    2016, 2022, 'AE'),

  -- Honda e:Ny1
  ('Honda',      'e:Ny1',      'e:Ny1',      2023, NULL, 'e:N'),

  -- MINI Cooper
  ('MINI',       'Cooper',     'R56',        2006, 2013, 'R56'),
  ('MINI',       'Cooper',     'F56',        2013, 2022, 'UKL2'),
  ('MINI',       'Cooper',     'J01',        2023, NULL, 'FAAR'),

  -- ── PREMIUM COMPACTOS ────────────────────────────────────────────────────

  -- Audi A1
  ('Audi',       'A1',         'A1 8X',      2010, 2018, 'PQ25'),
  ('Audi',       'A1',         'A1 GB',      2018, NULL, 'MQB A0'),

  -- Mercedes-Benz CLA
  ('Mercedes-Benz','CLA',      'C117',       2013, 2019, 'MFA'),
  ('Mercedes-Benz','CLA',      'C118',       2019, NULL, 'MFA2'),

  -- BMW Série 2 Gran Coupé
  ('BMW',        'Serie 2 Gran Coupe','F44', 2019, NULL, 'UKL3'),

  -- ── BERLINAS MÉDIAS (D-segment) ──────────────────────────────────────────

  -- Skoda Superb
  ('Skoda',      'Superb',     'Superb II',  2008, 2015, 'PQ46'),
  ('Skoda',      'Superb',     'Superb III', 2015, NULL, 'MQB'),

  -- Skoda Superb Combi
  ('Skoda',      'Superb Combi','Superb Combi II', 2009, 2015, 'PQ46'),
  ('Skoda',      'Superb Combi','Superb Combi III',2015, NULL, 'MQB'),

  -- Volkswagen Passat
  ('Volkswagen', 'Passat',     'B7',         2010, 2014, 'PQ46'),
  ('Volkswagen', 'Passat',     'B8',         2014, 2023, 'MQB'),
  ('Volkswagen', 'Passat',     'B9',         2023, NULL, 'MEB hybrid'),

  -- Peugeot 508
  ('Peugeot',    '508',        '508 I',      2010, 2018, 'EMP2'),
  ('Peugeot',    '508',        '508 II',     2018, NULL, 'EMP2'),

  -- ── BERLINAS PREMIUM (D-segment) ─────────────────────────────────────────

  -- BMW Série 3
  ('BMW',        'Serie 3',    'E90',        2005, 2011, 'E9x'),
  ('BMW',        'Serie 3',    'F30',        2012, 2018, 'F3x'),
  ('BMW',        'Serie 3',    'G20',        2019, NULL, 'CLAR'),

  -- Mercedes-Benz Classe C
  ('Mercedes-Benz','Classe C', 'W203',       2000, 2007, 'W203'),
  ('Mercedes-Benz','Classe C', 'W204',       2007, 2014, 'W204'),
  ('Mercedes-Benz','Classe C', 'W205',       2014, 2021, 'W205'),
  ('Mercedes-Benz','Classe C', 'W206',       2021, NULL, 'W206'),

  -- Audi A4
  ('Audi',       'A4',         'B8',         2007, 2015, 'MLB'),
  ('Audi',       'A4',         'B9',         2015, NULL, 'MLB Evo'),

  -- Volvo S60
  ('Volvo',      'S60',        'S60 II',     2010, 2018, 'P24'),
  ('Volvo',      'S60',        'S60 III',    2018, NULL, 'SPA'),

  -- Volvo V60
  ('Volvo',      'V60',        'V60 I',      2010, 2018, 'P3'),
  ('Volvo',      'V60',        'V60 II',     2018, NULL, 'SPA'),

  -- Alfa Romeo Giulia
  ('Alfa Romeo', 'Giulia',     'Giulia I',   2016, NULL, 'Giorgio'),

  -- ── BERLINAS GRANDES (E-segment) ─────────────────────────────────────────

  -- BMW Série 5
  ('BMW',        'Serie 5',    'F10',        2009, 2016, 'F10'),
  ('BMW',        'Serie 5',    'G30',        2016, NULL, 'CLAR'),

  -- Mercedes-Benz Classe E
  ('Mercedes-Benz','Classe E', 'W211',       2002, 2009, 'W211'),
  ('Mercedes-Benz','Classe E', 'W212',       2009, 2016, 'W212'),
  ('Mercedes-Benz','Classe E', 'W213',       2016, 2023, 'W213'),
  ('Mercedes-Benz','Classe E', 'W214',       2023, NULL, 'W214'),

  -- Audi A6
  ('Audi',       'A6',         'C7',         2011, 2018, 'MLB'),
  ('Audi',       'A6',         'C8',         2018, NULL, 'MLB Evo'),

  -- Volvo S90
  ('Volvo',      'S90',        'S90 II',     2016, NULL, 'SPA'),

  -- Volvo V90
  ('Volvo',      'V90',        'V90 II',     2016, NULL, 'SPA'),

  -- ── ELÉTRICOS ────────────────────────────────────────────────────────────

  -- Tesla Model 3
  ('Tesla',      'Model 3',    'Model 3',    2017, 2023, 'E3'),
  ('Tesla',      'Model 3',    'Model 3 Highland',2023, NULL, 'E3 refresh'),

  -- Tesla Model Y
  ('Tesla',      'Model Y',    'Model Y',    2020, NULL, 'E4'),

  -- Tesla Model S
  ('Tesla',      'Model S',    'Model S',    2012, 2020, 'S'),
  ('Tesla',      'Model S',    'Model S Plaid',2021, NULL, 'S refresh'),

  -- Kia EV6
  ('Kia',        'EV6',        'EV6 I',      2021, NULL, 'E-GMP'),

  -- Kia EV3
  ('Kia',        'EV3',        'EV3 I',      2024, NULL, 'E-GMP'),

  -- Hyundai Ioniq 5
  ('Hyundai',    'Ioniq 5',    'Ioniq 5 I',  2021, NULL, 'E-GMP'),

  -- Hyundai Ioniq 6
  ('Hyundai',    'Ioniq 6',    'Ioniq 6 I',  2022, NULL, 'E-GMP'),

  -- Volkswagen ID.3 (already listed above)

  -- BYD Dolphin
  ('BYD',        'Dolphin',    'Dolphin I',  2021, NULL, 'e-Platform 3.0'),

  -- BYD Atto 3
  ('BYD',        'Atto 3',     'Atto 3 I',   2021, NULL, 'e-Platform 3.0'),

  -- BYD Seal
  ('BYD',        'Seal',       'Seal I',     2022, NULL, 'e-Platform 3.0'),

  -- MG ZS EV
  ('MG',         'ZS EV',      'ZS EV I',    2018, 2021, 'MSP'),
  ('MG',         'ZS EV',      'ZS EV II',   2022, NULL, 'MSP'),

  -- Volvo EX30
  ('Volvo',      'EX30',       'EX30 I',     2023, NULL, 'SEA'),

  -- Smart #1
  ('Smart',      '#1',         'Smart #1',   2022, NULL, 'SEA'),

  -- Smart #3
  ('Smart',      '#3',         'Smart #3',   2023, NULL, 'SEA'),

  -- ── PREMIUM / BERLINAS MÉDIAS-GRANDES ────────────────────────────────────

  -- Mercedes-Benz Classe B
  ('Mercedes-Benz','Classe B', 'W245',       2005, 2011, 'W245'),
  ('Mercedes-Benz','Classe B', 'W246',       2011, 2018, 'MFA'),
  ('Mercedes-Benz','Classe B', 'W247',       2018, NULL, 'MFA2'),

  -- Audi Q3
  ('Audi',       'Q3',         'Q3 8U',      2011, 2018, 'MQB'),
  ('Audi',       'Q3',         'Q3 F3',      2018, NULL, 'MQB'),

  -- Audi Q2
  ('Audi',       'Q2',         'Q2 GA',      2016, NULL, 'MQB A0'),

  -- BMW Série 4
  ('BMW',        'Serie 4',    'F32',        2013, 2020, 'F32'),
  ('BMW',        'Serie 4',    'G22',        2020, NULL, 'CLAR'),

  -- BMW Série 2 Active Tourer
  ('BMW',        'Serie 2 Active Tourer','F45',2014, 2021, 'UKL2'),
  ('BMW',        'Serie 2 Active Tourer','U06',2021, NULL, 'FAAR'),

  -- Mercedes-Benz CLE
  ('Mercedes-Benz','CLE',      'C236',       2023, NULL, 'W206'),

  -- Mercedes-Benz E Coupé
  ('Mercedes-Benz','E Coupe',  'C207',       2009, 2017, 'W212'),
  ('Mercedes-Benz','E Coupe',  'C238',       2017, 2023, 'W213'),

  -- Audi A5
  ('Audi',       'A5',         'A5 8T',      2007, 2016, 'MLB'),
  ('Audi',       'A5',         'A5 F5',      2016, NULL, 'MLB Evo'),

  -- Audi TT
  ('Audi',       'TT',         'TT 8N',      1998, 2006, '8N'),
  ('Audi',       'TT',         'TT 8J',      2006, 2014, 'PQ35'),
  ('Audi',       'TT',         'TT 8S',      2014, 2023, 'MQB'),

  -- MINI Clubman
  ('MINI',       'Clubman',    'R55',        2007, 2015, 'R55'),
  ('MINI',       'Clubman',    'F54',        2015, 2024, 'UKL2'),

  -- MINI Countryman
  ('MINI',       'Countryman', 'R60',        2010, 2016, 'R60'),
  ('MINI',       'Countryman', 'F60',        2016, 2023, 'UKL2'),
  ('MINI',       'Countryman', 'U25',        2023, NULL, 'FAAR'),

  -- Alfa Romeo Stelvio
  ('Alfa Romeo', 'Stelvio',    'Stelvio I',  2016, NULL, 'Giorgio'),

  -- Lexus IS
  ('Lexus',      'IS',         'IS III',     2013, NULL, 'GA-L'),

  -- Lexus ES
  ('Lexus',      'ES',         'ES VII',     2018, NULL, 'TNGA-K'),

  -- Lexus UX
  ('Lexus',      'UX',         'UX I',       2018, NULL, 'GA-C'),

  -- Lexus NX
  ('Lexus',      'NX',         'NX I',       2014, 2021, 'GA-K'),
  ('Lexus',      'NX',         'NX II',      2021, NULL, 'TNGA-K'),

  -- Lexus RX
  ('Lexus',      'RX',         'RX IV',      2015, 2022, 'GA-L'),
  ('Lexus',      'RX',         'RX V',       2022, NULL, 'GA-L'),

  -- BMW Z4
  ('BMW',        'Z4',         'Z4 E85',     2002, 2008, 'E85'),
  ('BMW',        'Z4',         'Z4 E89',     2009, 2016, 'E89'),
  ('BMW',        'Z4',         'Z4 G29',     2018, NULL, 'CLAR'),

  -- Porsche Panamera
  ('Porsche',    'Panamera',   'Panamera I', 2009, 2016, '970'),
  ('Porsche',    'Panamera',   'Panamera II',2016, NULL, '971'),

  -- Alpine A110
  ('Alpine',     'A110',       'A110 I',     2017, NULL, 'B10'),

  -- Ford Mustang
  ('Ford',       'Mustang',    'Mustang VI', 2015, 2023, 'S550'),
  ('Ford',       'Mustang',    'Mustang VII',2023, NULL, 'S650'),

  -- Mazda MX-5
  ('Mazda',      'MX-5',       'MX-5 NC',    2005, 2015, 'NC'),
  ('Mazda',      'MX-5',       'MX-5 ND',    2015, NULL, 'ND'),

  -- Toyota GR Yaris
  ('Toyota',     'GR Yaris',   'GR Yaris I', 2020, NULL, 'GR-Four'),

  -- Toyota GR86
  ('Toyota',     'GR86',       'GR86 II',    2021, NULL, 'ZN8'),

  -- Subaru BRZ
  ('Subaru',     'BRZ',        'BRZ I',      2012, 2021, 'ZC6'),
  ('Subaru',     'BRZ',        'BRZ II',     2021, NULL, 'ZD8'),

  -- ── SUVs URBANOS / COMPACTOS ─────────────────────────────────────────────

  -- Peugeot 2008
  ('Peugeot',    '2008',       '2008 I',     2013, 2019, 'PF1'),
  ('Peugeot',    '2008',       '2008 II',    2019, NULL, 'CMP'),

  -- Renault Captur
  ('Renault',    'Captur',     'Captur I',   2013, 2019, 'B'),
  ('Renault',    'Captur',     'Captur II',  2019, NULL, 'CMF-B'),

  -- Dacia Duster
  ('Dacia',      'Duster',     'Duster I',   2010, 2017, 'B0'),
  ('Dacia',      'Duster',     'Duster II',  2017, 2023, 'B0'),
  ('Dacia',      'Duster',     'Duster III', 2024, NULL, 'CMF-B'),

  -- Nissan Qashqai
  ('Nissan',     'Qashqai',    'Qashqai I',  2006, 2013, 'J10'),
  ('Nissan',     'Qashqai',    'Qashqai II', 2013, 2021, 'CMF-C'),
  ('Nissan',     'Qashqai',    'Qashqai III',2021, NULL, 'CMF-CD'),

  -- Volkswagen T-Cross
  ('Volkswagen', 'T-Cross',    'T-Cross I',  2018, NULL, 'MQB A0'),

  -- Volkswagen T-Roc
  ('Volkswagen', 'T-Roc',      'T-Roc I',   2017, NULL, 'MQB'),

  -- Toyota Yaris Cross
  ('Toyota',     'Yaris Cross','Yaris Cross I',2021, NULL, 'TNGA-B'),

  -- Toyota C-HR
  ('Toyota',     'C-HR',       'C-HR I',     2016, 2023, 'TNGA-C'),
  ('Toyota',     'C-HR',       'C-HR II',    2023, NULL, 'TNGA-C'),

  -- SEAT Arona
  ('SEAT',       'Arona',      'Arona I',    2017, NULL, 'MQB A0'),

  -- SEAT Ateca
  ('SEAT',       'Ateca',      'Ateca I',    2016, NULL, 'MQB'),

  -- Skoda Kamiq
  ('Skoda',      'Kamiq',      'Kamiq I',    2019, NULL, 'MQB A0'),

  -- Skoda Karoq
  ('Skoda',      'Karoq',      'Karoq I',    2017, NULL, 'MQB'),

  -- Skoda Kodiaq
  ('Skoda',      'Kodiaq',     'Kodiaq I',   2016, 2024, 'MQB'),
  ('Skoda',      'Kodiaq',     'Kodiaq II',  2024, NULL, 'MQB Evo'),

  -- Ford Puma
  ('Ford',       'Puma',       'Puma II',    2019, NULL, 'C2'),

  -- Nissan Juke
  ('Nissan',     'Juke',       'Juke I',     2010, 2019, 'F15'),
  ('Nissan',     'Juke',       'Juke II',    2019, NULL, 'CMF-B'),

  -- Hyundai Kona
  ('Hyundai',    'Kona',       'Kona I',     2017, 2022, 'OS'),
  ('Hyundai',    'Kona',       'Kona II',    2023, NULL, 'SX2'),

  -- Hyundai Bayon
  ('Hyundai',    'Bayon',      'Bayon I',    2021, NULL, 'BC3'),

  -- Kia Stonic
  ('Kia',        'Stonic',     'Stonic I',   2017, NULL, 'YB'),

  -- Kia Niro
  ('Kia',        'Niro',       'Niro I',     2016, 2022, 'DE'),
  ('Kia',        'Niro',       'Niro II',    2022, NULL, 'SG2'),

  -- Mazda CX-3
  ('Mazda',      'CX-3',       'CX-3 I',     2015, 2023, 'DK'),

  -- Mazda CX-30
  ('Mazda',      'CX-30',      'CX-30 I',    2019, NULL, 'DM'),

  -- Honda HR-V
  ('Honda',      'HR-V',       'HR-V I',     2015, 2021, 'RU'),
  ('Honda',      'HR-V',       'HR-V II',    2021, NULL, 'RS'),

  -- Opel Mokka
  ('Opel',       'Mokka',      'Mokka A',    2012, 2019, 'J13'),
  ('Opel',       'Mokka',      'Mokka B',    2020, NULL, 'CMP'),

  -- Citroën C3 Aircross
  ('Citroen',    'C3 Aircross','C3 Aircross I', 2017, 2023, 'EMP2'),
  ('Citroen',    'C3 Aircross','C3 Aircross II',2024, NULL, 'STLA Small'),

  -- Renault Arkana
  ('Renault',    'Arkana',     'Arkana I',   2019, NULL, 'CMF-B'),

  -- BMW X1
  ('BMW',        'X1',         'X1 E84',     2009, 2015, 'E84'),
  ('BMW',        'X1',         'X1 F48',     2015, 2022, 'UKL2'),
  ('BMW',        'X1',         'X1 U11',     2022, NULL, 'FAAR'),

  -- Mercedes-Benz GLA
  ('Mercedes-Benz','GLA',      'GLA X156',   2013, 2019, 'MFA'),
  ('Mercedes-Benz','GLA',      'GLA H247',   2020, NULL, 'MFA2'),

  -- Cupra Formentor
  ('Cupra',      'Formentor',  'Formentor I',2020, NULL, 'MQB'),

  -- Cupra Ateca
  ('Cupra',      'Ateca',      'Ateca I',    2016, NULL, 'MQB'),

  -- Jeep Avenger
  ('Jeep',       'Avenger',    'Avenger I',  2022, NULL, 'CMP'),

  -- Jeep Compass
  ('Jeep',       'Compass',    'Compass II', 2017, NULL, 'small-wide 4x4'),

  -- Fiat 500X
  ('Fiat',       '500X',       '500X I',     2014, NULL, '334'),

  -- DS 7
  ('DS',         '7',          'DS 7 I',     2017, NULL, 'EMP2'),

  -- MG HS
  ('MG',         'HS',         'MG HS I',    2018, NULL, 'MSP'),

  -- MG 5
  ('MG',         '5',          'MG 5 I',     2021, NULL, 'MSP'),

  -- Omoda 5
  ('Omoda',      '5',          'Omoda 5 I',  2022, NULL, 'CHERY'),

  -- ── SUVs MÉDIOS ──────────────────────────────────────────────────────────

  -- Peugeot 3008
  ('Peugeot',    '3008',       '3008 I',     2008, 2016, 'PF2'),
  ('Peugeot',    '3008',       '3008 II',    2016, 2023, 'EMP2'),
  ('Peugeot',    '3008',       '3008 III',   2023, NULL, 'STLA Medium'),

  -- Hyundai Tucson
  ('Hyundai',    'Tucson',     'Tucson III', 2015, 2020, 'TL'),
  ('Hyundai',    'Tucson',     'Tucson IV',  2020, NULL, 'NX4'),

  -- Kia Sportage
  ('Kia',        'Sportage',   'Sportage III',2010, 2015, 'SL'),
  ('Kia',        'Sportage',   'Sportage IV', 2015, 2021, 'QL'),
  ('Kia',        'Sportage',   'Sportage V',  2021, NULL, 'NQ5'),

  -- Volkswagen Tiguan
  ('Volkswagen', 'Tiguan',     'Tiguan I',   2007, 2016, 'PQ46'),
  ('Volkswagen', 'Tiguan',     'Tiguan II',  2016, NULL, 'MQB'),

  -- Toyota RAV4
  ('Toyota',     'RAV4',       'RAV4 IV',    2012, 2018, 'MC'),
  ('Toyota',     'RAV4',       'RAV4 V',     2018, NULL, 'TNGA-K'),

  -- Ford Kuga
  ('Ford',       'Kuga',       'Kuga II',    2012, 2019, 'C1'),
  ('Ford',       'Kuga',       'Kuga III',   2019, NULL, 'C2'),

  -- Mazda CX-5
  ('Mazda',      'CX-5',       'CX-5 I',     2012, 2017, 'SkyActiv'),
  ('Mazda',      'CX-5',       'CX-5 II',    2017, NULL, 'SKY-VA'),

  -- Honda CR-V
  ('Honda',      'CR-V',       'CR-V IV',    2012, 2018, 'RM'),
  ('Honda',      'CR-V',       'CR-V V',     2018, 2023, 'RW/RT'),
  ('Honda',      'CR-V',       'CR-V VI',    2023, NULL, 'RS'),

  -- Opel Grandland
  ('Opel',       'Grandland',  'Grandland X',2017, 2021, 'EMP2'),
  ('Opel',       'Grandland',  'Grandland II',2021, NULL, 'EMP2'),

  -- Citroën C5 Aircross
  ('Citroen',    'C5 Aircross','C5 Aircross I',2018, NULL, 'EMP2'),

  -- Renault Kadjar
  ('Renault',    'Kadjar',     'Kadjar I',   2015, 2022, 'CMF-CD'),

  -- Renault Austral
  ('Renault',    'Austral',    'Austral I',  2022, NULL, 'CMF-CD'),

  -- Audi Q5
  ('Audi',       'Q5',         'Q5 8R',      2008, 2016, 'MLB'),
  ('Audi',       'Q5',         'Q5 FY',      2016, NULL, 'MLB Evo'),

  -- Volvo XC40
  ('Volvo',      'XC40',       'XC40 I',     2017, NULL, 'CMA'),

  -- Volvo XC60
  ('Volvo',      'XC60',       'XC60 I',     2008, 2017, 'P3'),
  ('Volvo',      'XC60',       'XC60 II',    2017, NULL, 'SPA'),

  -- BMW X3
  ('BMW',        'X3',         'X3 E83',     2003, 2010, 'E83'),
  ('BMW',        'X3',         'X3 F25',     2010, 2017, 'F25'),
  ('BMW',        'X3',         'X3 G01',     2017, NULL, 'CLAR'),

  -- Mercedes-Benz GLC
  ('Mercedes-Benz','GLC',      'GLC X253',   2015, 2022, 'W205'),
  ('Mercedes-Benz','GLC',      'GLC X254',   2022, NULL, 'W206'),

  -- ── SUVs GRANDES ─────────────────────────────────────────────────────────

  -- BMW X5
  ('BMW',        'X5',         'X5 E70',     2006, 2013, 'E70'),
  ('BMW',        'X5',         'X5 F15',     2013, 2018, 'F15'),
  ('BMW',        'X5',         'X5 G05',     2018, NULL, 'CLAR'),

  -- BMW X6
  ('BMW',        'X6',         'X6 E71',     2008, 2014, 'E70'),
  ('BMW',        'X6',         'X6 F16',     2014, 2019, 'F15'),
  ('BMW',        'X6',         'X6 G06',     2019, NULL, 'CLAR'),

  -- Mercedes-Benz GLE
  ('Mercedes-Benz','GLE',      'GLE W166',   2015, 2019, 'W166'),
  ('Mercedes-Benz','GLE',      'GLE V167',   2019, NULL, 'W167'),

  -- Mercedes-Benz GLS
  ('Mercedes-Benz','GLS',      'GLS X166',   2015, 2019, 'W166'),
  ('Mercedes-Benz','GLS',      'GLS X167',   2019, NULL, 'W167'),

  -- Audi Q7
  ('Audi',       'Q7',         'Q7 4L',      2005, 2015, 'PL71'),
  ('Audi',       'Q7',         'Q7 4M',      2015, NULL, 'MLB Evo'),

  -- Audi Q8
  ('Audi',       'Q8',         'Q8 4M',      2018, NULL, 'MLB Evo'),

  -- Volvo XC90
  ('Volvo',      'XC90',       'XC90 I',     2002, 2014, 'P2'),
  ('Volvo',      'XC90',       'XC90 II',    2014, NULL, 'SPA'),

  -- Porsche Macan
  ('Porsche',    'Macan',      'Macan I',    2014, 2023, '95B'),
  ('Porsche',    'Macan',      'Macan II',   2023, NULL, 'J1 EV'),

  -- Porsche Cayenne
  ('Porsche',    'Cayenne',    'Cayenne II', 2010, 2017, '92A'),
  ('Porsche',    'Cayenne',    'Cayenne III',2017, NULL, '9YA'),

  -- Land Rover Range Rover Evoque
  ('Land Rover', 'Range Rover Evoque','Evoque I', 2011, 2018, 'L538'),
  ('Land Rover', 'Range Rover Evoque','Evoque II',2019, NULL, 'L551'),

  -- Land Rover Range Rover Velar
  ('Land Rover', 'Range Rover Velar','Velar I',   2017, NULL, 'L560'),

  -- Land Rover Range Rover Sport
  ('Land Rover', 'Range Rover Sport','Sport I',   2005, 2013, 'L320'),
  ('Land Rover', 'Range Rover Sport','Sport II',  2013, 2022, 'L494'),
  ('Land Rover', 'Range Rover Sport','Sport III', 2022, NULL, 'L461'),

  -- Land Rover Discovery Sport
  ('Land Rover', 'Discovery Sport','Disc Sport I',2014, NULL, 'L550'),

  -- Land Rover Defender
  ('Land Rover', 'Defender',   'Defender',   2020, NULL, 'D7u'),

  -- Jaguar F-Pace
  ('Jaguar',     'F-Pace',     'F-Pace I',   2016, NULL, 'X761'),

  -- Jaguar E-Pace
  ('Jaguar',     'E-Pace',     'E-Pace I',   2017, NULL, 'X540'),

  -- Maserati Grecale
  ('Maserati',   'Grecale',    'Grecale I',  2022, NULL, 'F160'),

  -- ── MPVs / FAMILIARES ────────────────────────────────────────────────────

  -- Citroën Berlingo
  ('Citroen',    'Berlingo',   'Berlingo II', 2008, 2018, 'B9'),
  ('Citroen',    'Berlingo',   'Berlingo III',2018, NULL, 'EMP2'),

  -- Peugeot Rifter
  ('Peugeot',    'Rifter',     'Rifter I',   2018, NULL, 'EMP2'),

  -- Opel Combo Life
  ('Opel',       'Combo Life', 'Combo Life E',2018, NULL, 'EMP2'),

  -- Volkswagen Touran
  ('Volkswagen', 'Touran',     'Touran I',   2003, 2010, 'PQ35'),
  ('Volkswagen', 'Touran',     'Touran II',  2015, NULL, 'MQB'),

  -- Volkswagen Caddy
  ('Volkswagen', 'Caddy',      'Caddy III',  2003, 2020, 'PQ35'),
  ('Volkswagen', 'Caddy',      'Caddy V',    2020, NULL, 'MQB'),

  -- Ford Tourneo Connect
  ('Ford',       'Tourneo Connect','Tourneo II', 2013, 2021, 'C1'),
  ('Ford',       'Tourneo Connect','Tourneo III',2022, NULL, 'MQB'),

  -- Ford S-Max
  ('Ford',       'S-Max',      'S-Max I',    2006, 2014, 'CD3'),
  ('Ford',       'S-Max',      'S-Max II',   2015, 2023, 'CD4'),

  -- SEAT Alhambra
  ('SEAT',       'Alhambra',   'Alhambra II',2010, 2022, 'PQ46'),

  -- Volkswagen Sharan
  ('Volkswagen', 'Sharan',     'Sharan II',  2010, 2022, 'PQ46'),

  -- Mercedes-Benz Classe V
  ('Mercedes-Benz','Classe V', 'W447',       2014, NULL, 'VS30'),

  -- Toyota Proace City Verso
  ('Toyota',     'Proace City Verso','Proace City Verso',2019, NULL, 'EMP2'),

  -- Peugeot 5008
  ('Peugeot',    '5008',       '5008 I',     2009, 2016, 'PF2'),
  ('Peugeot',    '5008',       '5008 II',    2016, NULL, 'EMP2'),

  -- Renault Scénic
  ('Renault',    'Scenic',     'Scénic IV',  2016, 2023, 'CMF-CD'),
  ('Renault',    'Scenic',     'Scénic E-Tech',2023, NULL, 'CMF-EV'),

  -- Dacia Jogger
  ('Dacia',      'Jogger',     'Jogger I',   2021, NULL, 'CMF-B'),

  -- ── SUBARU / SUZUKI ──────────────────────────────────────────────────────

  -- Subaru Outback
  ('Subaru',     'Outback',    'Outback V',  2014, 2019, 'BS'),
  ('Subaru',     'Outback',    'Outback VI', 2019, NULL, 'SGP'),

  -- Subaru Forester
  ('Subaru',     'Forester',   'Forester IV',2012, 2018, 'SJ'),
  ('Subaru',     'Forester',   'Forester V', 2018, NULL, 'SK'),

  -- Suzuki Swift
  ('Suzuki',     'Swift',      'Swift IV',   2010, 2017, 'FZ'),
  ('Suzuki',     'Swift',      'Swift V',    2017, NULL, 'AZ'),

  -- Suzuki Vitara
  ('Suzuki',     'Vitara',     'Vitara IV',  2015, NULL, 'LY'),

  -- Suzuki S-Cross
  ('Suzuki',     'S-Cross',    'S-Cross I',  2013, 2021, 'JY'),
  ('Suzuki',     'S-Cross',    'S-Cross II', 2021, NULL, 'KL')

)
INSERT INTO generations (model_id, name, year_start, year_end, platform)
SELECT ml.id, gd.name, gd.year_start, gd.year_end, gd.platform
FROM gen_data gd
JOIN (
    SELECT vm.id, b.name AS brand, vm.name AS model
    FROM vehicle_models vm
    JOIN brands b ON b.id = vm.brand_id
) ml ON ml.brand = gd.brand AND ml.model = gd.model;

-- Verify
SELECT b.name AS brand, vm.name AS model, g.name AS generation, g.year_start, g.year_end, g.platform
FROM generations g
JOIN vehicle_models vm ON vm.id = g.model_id
JOIN brands b ON b.id = vm.brand_id
ORDER BY b.name, vm.name, g.year_start;
-- Migration v52: Generation-aware schema
-- Adds: generation_id to normalized_listings, CI columns to generations,
--       market_price_stats_history, reliability_evidence, reliability_scores_history
--
-- Rationale: the used car market operates by generation (Golf VII vs Golf VIII),
-- not by model alone. Single-snapshot avg/min/max price data cannot support
-- uncertainty bands, temporal trends, or honest confidence intervals.

BEGIN;

-- ─────────────────────────────────────────────────────────────
-- 1. Add generation_id to normalized_listings
-- ─────────────────────────────────────────────────────────────
ALTER TABLE normalized_listings
    ADD COLUMN IF NOT EXISTS generation_id INTEGER REFERENCES generations(id);

CREATE INDEX IF NOT EXISTS idx_normalized_generation_id
    ON normalized_listings(generation_id);

-- ─────────────────────────────────────────────────────────────
-- 2. Reliability CI + market snapshot columns on generations
--    (denormalized for fast product reads — source of truth
--     is reliability_scores_history / market_price_stats_history)
-- ─────────────────────────────────────────────────────────────
ALTER TABLE generations
    ADD COLUMN IF NOT EXISTS reliability_score     NUMERIC(4,2),
    ADD COLUMN IF NOT EXISTS reliability_ci_low    NUMERIC(4,2),
    ADD COLUMN IF NOT EXISTS reliability_ci_high   NUMERIC(4,2),
    ADD COLUMN IF NOT EXISTS reliability_sources   JSONB NOT NULL DEFAULT '[]'::jsonb,
    ADD COLUMN IF NOT EXISTS reliability_data_quality TEXT
        CHECK (reliability_data_quality IN ('robust', 'limited', 'prior_only')),
    ADD COLUMN IF NOT EXISTS market_value_p50      INTEGER,
    ADD COLUMN IF NOT EXISTS market_value_band     JSONB NOT NULL DEFAULT '{}'::jsonb,
    ADD COLUMN IF NOT EXISTS market_value_sources  JSONB NOT NULL DEFAULT '[]'::jsonb,
    ADD COLUMN IF NOT EXISTS market_value_as_of    DATE;

-- ─────────────────────────────────────────────────────────────
-- 3. Market price history
--    Replaces single-snapshot model with monthly time series.
--    market_price_stats kept as-is for backwards compat;
--    new writes go to market_price_stats_history.
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS market_price_stats_history (
    id                  SERIAL PRIMARY KEY,
    generation_id       INTEGER NOT NULL REFERENCES generations(id),
    engine_id           INTEGER REFERENCES engines(id),
    price_context       TEXT NOT NULL
        CHECK (price_context IN ('particular', 'stand', 'importacao', 'todos')),
    vehicle_year        INTEGER NOT NULL,
    observed_month      DATE NOT NULL,       -- first day of the observation month
    p10_price           INTEGER,
    p50_price           INTEGER,
    p90_price           INTEGER,
    mean_price          INTEGER,
    sample_count        INTEGER,
    mad_price           INTEGER,            -- Median Absolute Deviation
    time_on_market_p50  INTEGER,            -- median days listed before removal
    sources             JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at          TIMESTAMPTZ DEFAULT now(),
    UNIQUE (generation_id, engine_id, price_context, vehicle_year, observed_month)
);

CREATE INDEX IF NOT EXISTS idx_mpsh_generation_month
    ON market_price_stats_history(generation_id, observed_month DESC);

CREATE INDEX IF NOT EXISTS idx_mpsh_engine
    ON market_price_stats_history(engine_id);

-- ─────────────────────────────────────────────────────────────
-- 4. Reliability evidence (raw inputs for the Bayesian scorer)
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS reliability_evidence (
    id             SERIAL PRIMARY KEY,
    generation_id  INTEGER NOT NULL REFERENCES generations(id),
    engine_id      INTEGER REFERENCES engines(id),
    evidence_type  TEXT NOT NULL
        CHECK (evidence_type IN ('recall', 'safety_gate', 'nlp_complaint', 'breakdown', 'inspection_proxy', 'tsb')),
    source         TEXT NOT NULL,           -- e.g. 'eu_safety_gate', 'standvirtual_nlp'
    source_url     TEXT,
    observed_month DATE NOT NULL,
    severity       TEXT,                    -- 'serious' | 'high' | 'medium' | 'low'
    n_eff          NUMERIC,                 -- effective sample size
    fail_eff       NUMERIC,                 -- effective failures
    succ_eff       NUMERIC,                 -- effective successes
    weight         NUMERIC,
    payload        JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at     TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_rel_evidence_gen_month
    ON reliability_evidence(generation_id, observed_month);

CREATE INDEX IF NOT EXISTS idx_rel_evidence_type
    ON reliability_evidence(evidence_type, source);

-- ─────────────────────────────────────────────────────────────
-- 5. Reliability scores history (output of the Bayesian scorer)
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS reliability_scores_history (
    id             SERIAL PRIMARY KEY,
    generation_id  INTEGER NOT NULL REFERENCES generations(id),
    engine_id      INTEGER REFERENCES engines(id),
    as_of_month    DATE NOT NULL,
    alpha          NUMERIC NOT NULL,        -- posterior alpha
    beta_param     NUMERIC NOT NULL,        -- posterior beta (named beta_param to avoid SQL keyword)
    p_mean         NUMERIC NOT NULL,        -- posterior mean probability
    score_1_10     NUMERIC(4,2) NOT NULL,
    ci_low_1_10    NUMERIC(4,2),           -- 5th percentile mapped to 1-10
    ci_high_1_10   NUMERIC(4,2),           -- 95th percentile mapped to 1-10
    evidence_count INTEGER DEFAULT 0,
    data_quality   TEXT
        CHECK (data_quality IN ('robust', 'limited', 'prior_only')),
    sources        JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at     TIMESTAMPTZ DEFAULT now(),
    UNIQUE (generation_id, engine_id, as_of_month)
);

CREATE INDEX IF NOT EXISTS idx_rsh_generation_month
    ON reliability_scores_history(generation_id, as_of_month DESC);

COMMIT;
-- Caractr v4.4 — RGPD schema cleanup
-- Drops undisclosed columns from concierge_requests that were never used
-- by the application and not listed in the privacy policy.
-- Also removes the unused 'tier' workflow column.

-- phone: collected in schema but not in frontend form and not disclosed in privacy policy
ALTER TABLE concierge_requests DROP COLUMN IF EXISTS phone;

-- timeline: workflow field never exposed to users
ALTER TABLE concierge_requests DROP COLUMN IF EXISTS timeline;

-- notes: free-text field never exposed to users
ALTER TABLE concierge_requests DROP COLUMN IF EXISTS notes;

-- tier: internal workflow tier, not used by current MVP
ALTER TABLE concierge_requests DROP COLUMN IF EXISTS tier;
-- Caractr v4.4 — Add anon_id to analytics_events
-- The frontend generates a persistent anonymous ID (localStorage) and sends it
-- with every event. This column allows linking pre-wizard events to post-wizard
-- sessions for the same anonymous user across visits.

ALTER TABLE analytics_events ADD COLUMN IF NOT EXISTS anon_id UUID;
CREATE INDEX IF NOT EXISTS idx_analytics_anon_id ON analytics_events (anon_id);
