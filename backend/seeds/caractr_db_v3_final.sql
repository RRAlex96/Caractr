-- CARACTR DB v3.2 - CLEAN COMPLETE REBUILD
-- Generated automatically - all ASCII safe

-- ============================================================
-- CARACTR DATABASE v3.0 - COMPLETE REBUILD
-- ~200 modelos, ~500 motorizacoes, mercado PT
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

-- BRANDS
INSERT INTO brands (name, country, segment) VALUES ('Renault', 'Franca', 'generalista');
INSERT INTO brands (name, country, segment) VALUES ('Peugeot', 'Franca', 'generalista');
INSERT INTO brands (name, country, segment) VALUES ('Citroen', 'Franca', 'generalista');
INSERT INTO brands (name, country, segment) VALUES ('Dacia', 'Romenia', 'economico');
INSERT INTO brands (name, country, segment) VALUES ('Opel', 'Alemanha', 'generalista');
INSERT INTO brands (name, country, segment) VALUES ('Toyota', 'Japao', 'generalista');
INSERT INTO brands (name, country, segment) VALUES ('Volkswagen', 'Alemanha', 'generalista');
INSERT INTO brands (name, country, segment) VALUES ('SEAT', 'Espanha', 'generalista');
INSERT INTO brands (name, country, segment) VALUES ('Skoda', 'Chequia', 'generalista');
INSERT INTO brands (name, country, segment) VALUES ('Hyundai', 'Coreia do Sul', 'generalista');
INSERT INTO brands (name, country, segment) VALUES ('Kia', 'Coreia do Sul', 'generalista');
INSERT INTO brands (name, country, segment) VALUES ('Ford', 'EUA', 'generalista');
INSERT INTO brands (name, country, segment) VALUES ('Nissan', 'Japao', 'generalista');
INSERT INTO brands (name, country, segment) VALUES ('Mazda', 'Japao', 'generalista');
INSERT INTO brands (name, country, segment) VALUES ('Honda', 'Japao', 'generalista');
INSERT INTO brands (name, country, segment) VALUES ('Fiat', 'Italia', 'generalista');
INSERT INTO brands (name, country, segment) VALUES ('BMW', 'Alemanha', 'premium');
INSERT INTO brands (name, country, segment) VALUES ('Mercedes-Benz', 'Alemanha', 'premium');
INSERT INTO brands (name, country, segment) VALUES ('Audi', 'Alemanha', 'premium');
INSERT INTO brands (name, country, segment) VALUES ('Volvo', 'Suecia', 'premium');
INSERT INTO brands (name, country, segment) VALUES ('Alfa Romeo', 'Italia', 'premium');
INSERT INTO brands (name, country, segment) VALUES ('Cupra', 'Espanha', 'premium');
INSERT INTO brands (name, country, segment) VALUES ('DS', 'Franca', 'premium');
INSERT INTO brands (name, country, segment) VALUES ('Lexus', 'Japao', 'premium');
INSERT INTO brands (name, country, segment) VALUES ('Jaguar', 'Reino Unido', 'premium');
INSERT INTO brands (name, country, segment) VALUES ('Land Rover', 'Reino Unido', 'premium');
INSERT INTO brands (name, country, segment) VALUES ('Porsche', 'Alemanha', 'luxo');
INSERT INTO brands (name, country, segment) VALUES ('Maserati', 'Italia', 'luxo');
INSERT INTO brands (name, country, segment) VALUES ('MINI', 'Reino Unido', 'premium');
INSERT INTO brands (name, country, segment) VALUES ('Tesla', 'EUA', 'premium');
INSERT INTO brands (name, country, segment) VALUES ('BYD', 'China', 'generalista');
INSERT INTO brands (name, country, segment) VALUES ('MG', 'China', 'generalista');
INSERT INTO brands (name, country, segment) VALUES ('Omoda', 'China', 'generalista');
INSERT INTO brands (name, country, segment) VALUES ('Smart', 'Alemanha', 'premium');
INSERT INTO brands (name, country, segment) VALUES ('Jeep', 'EUA', 'generalista');
INSERT INTO brands (name, country, segment) VALUES ('Subaru', 'Japao', 'generalista');
INSERT INTO brands (name, country, segment) VALUES ('Suzuki', 'Japao', 'generalista');
INSERT INTO brands (name, country, segment) VALUES ('Alpine', 'Franca', 'premium');

-- VEHICLE MODELS
INSERT INTO vehicle_models (brand_id, name, body_type, segment, years_produced) VALUES
((SELECT id FROM brands WHERE name='Renault'), 'Clio', 'citadino', 'economico', '2019-presente'),
((SELECT id FROM brands WHERE name='Peugeot'), '208', 'citadino', 'economico', '2019-presente'),
((SELECT id FROM brands WHERE name='Citroen'), 'C3', 'citadino', 'economico', '2016-presente'),
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
((SELECT id FROM brands WHERE name='Citroen'), 'C1', 'citadino', 'economico', '2014-2022'),
((SELECT id FROM brands WHERE name='Peugeot'), '108', 'citadino', 'economico', '2014-2022'),
((SELECT id FROM brands WHERE name='Opel'), 'Adam', 'citadino', 'economico', '2012-2019');
INSERT INTO vehicle_models (brand_id, name, body_type, segment, years_produced) VALUES
((SELECT id FROM brands WHERE name='Volkswagen'), 'Golf', 'compacto', 'medio', '2019-presente'),
((SELECT id FROM brands WHERE name='Peugeot'), '308', 'compacto', 'medio', '2021-presente'),
((SELECT id FROM brands WHERE name='Renault'), 'Megane', 'compacto', 'medio', '2016-2023'),
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
((SELECT id FROM brands WHERE name='BMW'), 'Serie 1', 'compacto', 'premium', '2019-presente'),
((SELECT id FROM brands WHERE name='Mercedes-Benz'), 'Classe A', 'compacto', 'premium', '2018-presente'),
((SELECT id FROM brands WHERE name='Volvo'), 'V40', 'compacto', 'premium', '2012-2019'),
((SELECT id FROM brands WHERE name='Cupra'), 'Leon', 'compacto', 'premium', '2020-presente'),
((SELECT id FROM brands WHERE name='DS'), '4', 'compacto', 'premium', '2021-presente'),
((SELECT id FROM brands WHERE name='Citroen'), 'C4', 'compacto', 'medio', '2020-presente'),
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
((SELECT id FROM brands WHERE name='BMW'), 'Serie 2 Gran Coupe', 'compacto', 'premium', '2020-presente'),
((SELECT id FROM brands WHERE name='Skoda'), 'Superb', 'berlina', 'medio', '2019-presente'),
((SELECT id FROM brands WHERE name='Volkswagen'), 'Passat', 'berlina', 'medio', '2019-presente'),
((SELECT id FROM brands WHERE name='Peugeot'), '508', 'berlina', 'medio', '2018-presente');
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
((SELECT id FROM brands WHERE name='Citroen'), 'C3 Aircross', 'suv', 'economico', '2017-presente'),
((SELECT id FROM brands WHERE name='Citroen'), 'C5 Aircross', 'suv', 'medio', '2018-presente'),
((SELECT id FROM brands WHERE name='Renault'), 'Kadjar', 'suv', 'medio', '2015-2022'),
((SELECT id FROM brands WHERE name='Renault'), 'Austral', 'suv', 'medio', '2022-presente'),
((SELECT id FROM brands WHERE name='Renault'), 'Arkana', 'suv', 'medio', '2021-presente'),
((SELECT id FROM brands WHERE name='Volkswagen'), 'T-Cross', 'suv', 'economico', '2019-presente'),
((SELECT id FROM brands WHERE name='Toyota'), 'Yaris Cross', 'suv', 'economico', '2021-presente'),
((SELECT id FROM brands WHERE name='BMW'), 'X1', 'suv', 'premium', '2022-presente'),
((SELECT id FROM brands WHERE name='Mercedes-Benz'), 'GLA', 'suv', 'premium', '2020-presente'),
((SELECT id FROM brands WHERE name='Audi'), 'Q2', 'suv', 'premium', '2016-presente');
INSERT INTO vehicle_models (brand_id, name, body_type, segment, years_produced) VALUES
((SELECT id FROM brands WHERE name='BMW'), 'Serie 3', 'berlina', 'premium', '2018-presente'),
((SELECT id FROM brands WHERE name='Mercedes-Benz'), 'Classe C', 'berlina', 'premium', '2021-presente'),
((SELECT id FROM brands WHERE name='Audi'), 'A4', 'berlina', 'premium', '2019-presente'),
((SELECT id FROM brands WHERE name='Volvo'), 'S60', 'berlina', 'premium', '2019-presente'),
((SELECT id FROM brands WHERE name='Volvo'), 'V60', 'carrinha', 'premium', '2018-presente'),
((SELECT id FROM brands WHERE name='Alfa Romeo'), 'Giulia', 'berlina', 'premium', '2016-presente'),
((SELECT id FROM brands WHERE name='Skoda'), 'Superb Combi', 'carrinha', 'medio', '2019-presente'),
((SELECT id FROM brands WHERE name='BMW'), 'Serie 5', 'berlina', 'premium', '2023-presente'),
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
INSERT INTO vehicle_models (brand_id, name, body_type, segment, years_produced) VALUES
((SELECT id FROM brands WHERE name='Dacia'), 'Jogger', 'mpv', 'economico', '2022-presente'),
((SELECT id FROM brands WHERE name='Renault'), 'Scenic', 'mpv', 'medio', '2024-presente'),
((SELECT id FROM brands WHERE name='Citroen'), 'Berlingo', 'mpv', 'economico', '2018-presente'),
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
((SELECT id FROM brands WHERE name='BMW'), 'Serie 2 Active Tourer', 'mpv', 'premium', '2022-presente');
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
INSERT INTO vehicle_models (brand_id, name, body_type, segment, years_produced) VALUES
((SELECT id FROM brands WHERE name='BMW'), 'Serie 4', 'compacto', 'premium', '2020-presente'),
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
INSERT INTO vehicle_models (brand_id, name, body_type, segment, years_produced) VALUES
((SELECT id FROM brands WHERE name='Mercedes-Benz'), 'E Coupe', 'compacto', 'luxo', '2017-2023');

-- ============================================================
-- CARACTR DATABASE v3.0 - AUTO-GENERATED SEED
-- 128 modelos
-- ============================================================


-- -- Renault Clio --
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.0 TCe 90', 'gasolina', 999, 90, 160, 'manual 5', 5.8, 131, 7.0, 380
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Clio' AND b.name = 'Renault';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.0 TCe 100 LPG', 'gpl', 999, 100, 160, 'manual 5', 6.5, 120, 7.0, 350
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Clio' AND b.name = 'Renault';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.6 E-Tech 145 Hibrido', 'hibrido', 1598, 145, 205, 'auto', 4.3, 98, 7.5, 350
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Clio' AND b.name = 'Renault';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 7, 5, 8, 6, 5, 'baixo', 'Polivalente e confortavel para a classe. Bom compromisso para uso diario em cidade e estrada.'
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

-- -- Peugeot 208 --
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
SELECT vm.id, 7, 6, 9, 6, 4, 'baixo', 'Interior premium para o segmento. i-Cockpit polariza mas e moderno. Agil na cidade.'
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
SELECT e.id, 'medio', 'Motor 1.2 PureTech com correia humida - verificar manutencao. Recall aplicado em 2021.', '2019-2021', '600-1200EUR', 'PSA/Stellantis recall'
FROM engines e JOIN vehicle_models vm ON e.model_id = vm.id JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = '208' AND b.name = 'Peugeot' LIMIT 1;

-- -- Citroen C3 --
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.2 PureTech 83', 'gasolina', 1199, 83, 205, 'manual 5', 5.4, 123, 7.0, 380
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'C3' AND b.name = 'Citroen';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.2 PureTech 110', 'gasolina', 1199, 110, 205, 'manual 6', 5.6, 127, 6.5, 400
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'C3' AND b.name = 'Citroen';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 7, 4, 8, 5, 5, 'baixo', 'Confortavel com suspensao macia. Design simpatico. Pouco entusiasmante mas agradavel.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'C3' AND b.name = 'Citroen';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 13000, 10000, 16500, 38, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'C3' AND b.name = 'Citroen';

-- -- Dacia Sandero --
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
SELECT vm.id, 5, 4, 7, 6, 6, 'medio', 'Relacao qualidade-preco imbativel. Espaco surpreendente. Sem luxos mas honesto.'
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

-- -- Opel Corsa --
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
SELECT vm.id, 6, 5, 8, 6, 4, 'baixo', 'Base Peugeot 208 com personalidade mais discreta. Ergonomia alema, plataforma francesa.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Corsa' AND b.name = 'Opel';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 15000, 12000, 18500, 35, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Corsa' AND b.name = 'Opel';

-- -- Toyota Yaris --
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.5 Hibrido 116cv', 'hibrido', 1490, 116, 120, 'auto cvt', 3.8, 87, 9.5, 280
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Yaris' AND b.name = 'Toyota';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.5 VVT-i 125cv', 'gasolina', 1490, 125, 153, 'manual 6', 5.6, 127, 8.5, 300
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Yaris' AND b.name = 'Toyota';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 7, 5, 9, 6, 4, 'baixo', 'Hibrido exemplar para cidade. Consumos reais impressionantes. Fiabilidade Toyota.'
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

-- -- Volkswagen Polo --
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.0 TSI 95', 'gasolina', 999, 95, 175, 'manual 5', 5.4, 123, 7.5, 400
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Polo' AND b.name = 'Volkswagen';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.0 TSI 110 DSG', 'gasolina', 999, 110, 200, 'auto 7', 5.6, 128, 7.0, 450
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Polo' AND b.name = 'Volkswagen';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 7, 5, 8, 7, 5, 'baixo', 'Mini Golf. Qualidade de construcao acima da media do segmento. Discreto mas solido.'
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

-- -- SEAT Ibiza --
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.0 TSI 95', 'gasolina', 999, 95, 175, 'manual 5', 5.3, 121, 7.5, 380
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Ibiza' AND b.name = 'SEAT';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.0 TSI 110', 'gasolina', 999, 110, 200, 'manual 6', 5.5, 125, 7.0, 400
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Ibiza' AND b.name = 'SEAT';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 6, 6, 8, 7, 5, 'baixo', 'Versao iberica do Polo. Mais dinamico, suspensao mais firme. Bom para quem gosta de conduzir.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Ibiza' AND b.name = 'SEAT';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 14500, 11500, 18000, 38, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Ibiza' AND b.name = 'SEAT';

-- -- Skoda Fabia --
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.0 TSI 95', 'gasolina', 999, 95, 175, 'manual 5', 5.2, 119, 7.5, 370
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Fabia' AND b.name = 'Skoda';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.0 TSI 110', 'gasolina', 999, 110, 200, 'manual 6', 5.4, 123, 7.0, 390
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Fabia' AND b.name = 'Skoda';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 7, 5, 8, 7, 6, 'baixo', 'O maior do segmento. Espaco de compacto num citadino. Pratico, racional, sem fitas.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Fabia' AND b.name = 'Skoda';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 15000, 12000, 18500, 32, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Fabia' AND b.name = 'Skoda';

-- -- Hyundai i20 --
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.0 T-GDi 100', 'gasolina', 998, 100, 172, 'manual 5', 5.5, 125, 8.0, 350
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'i20' AND b.name = 'Hyundai';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.2 MPI 84', 'gasolina', 1197, 84, 118, 'manual 5', 5.8, 132, 8.5, 320
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'i20' AND b.name = 'Hyundai';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 7, 5, 8, 6, 5, 'baixo', 'Bem equipado e bem construido. 5 anos de garantia. Opcao segura e sem surpresas.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'i20' AND b.name = 'Hyundai';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 14000, 11000, 17500, 30, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'i20' AND b.name = 'Hyundai';

-- -- Kia Rio --
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.0 T-GDi 100', 'gasolina', 998, 100, 172, 'manual 6', 5.4, 123, 8.0, 350
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Rio' AND b.name = 'Kia';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.0 T-GDi 120 DCT', 'gasolina', 998, 120, 172, 'auto 7', 5.7, 130, 7.5, 380
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Rio' AND b.name = 'Kia';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 6, 5, 8, 6, 5, 'baixo', 'Gemeo do i20 com design diferente. 7 anos de garantia de fabrica. Imbativel em tranquilidade.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Rio' AND b.name = 'Kia';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 13500, 10500, 17000, 28, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Rio' AND b.name = 'Kia';

-- -- Ford Fiesta --
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
SELECT vm.id, 6, 8, 8, 7, 4, 'baixo', 'Referencia de conducao no segmento. Chassis brilhante. Descontinuado mas ainda muito relevante em usados.'
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
SELECT e.id, 'baixo', 'Motor 1.0 EcoBoost pre-2017: problema de arrefecimento. Versoes 2017+ corrigidas.', '2014-2017', '800-1500EUR', 'Ford TSB'
FROM engines e JOIN vehicle_models vm ON e.model_id = vm.id JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Fiesta' AND b.name = 'Ford' LIMIT 1;

-- -- Nissan Micra --
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.0 IG-T 92', 'gasolina', 999, 92, 160, 'manual 5', 5.4, 123, 7.5, 350
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Micra' AND b.name = 'Nissan';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '0.9 IG-T 90', 'gasolina', 898, 90, 140, 'manual 5', 5.0, 114, 7.0, 340
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Micra' AND b.name = 'Nissan';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 6, 5, 8, 5, 4, 'medio', 'Compacto e bem desenhado. Posicao de conducao agradavel. Motor 0.9 um pouco justo.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Micra' AND b.name = 'Nissan';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 12500, 9500, 16000, 25, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Micra' AND b.name = 'Nissan';

-- -- Mazda 2 --
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.5 Skyactiv-G 90', 'gasolina', 1496, 90, 148, 'manual 6', 5.4, 123, 8.5, 350
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = '2' AND b.name = 'Mazda';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.5 Hibrido 116', 'hibrido', 1490, 116, 120, 'auto cvt', 3.8, 87, 9.5, 280
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = '2' AND b.name = 'Mazda';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 7, 6, 8, 6, 4, 'baixo', 'Versao rebadged do Yaris com identidade Mazda. Hibrido Toyota debaixo do capo. Fiavel e refinado.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = '2' AND b.name = 'Mazda';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2024, 19000, 17000, 22000, 15, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = '2' AND b.name = 'Mazda';

-- -- Honda Jazz --
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.5 e:HEV 109', 'hibrido', 1498, 109, 253, 'auto cvt', 4.5, 102, 9.0, 300
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Jazz' AND b.name = 'Honda';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 7, 4, 9, 6, 6, 'baixo', 'Mestre do espaco interior. Bancos Magic Seats geniais. Hibrido eficiente. Aborrecido mas brilhante.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Jazz' AND b.name = 'Honda';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 19000, 16000, 23000, 20, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Jazz' AND b.name = 'Honda';

-- -- Fiat 500 --
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.0 Mild Hybrid 70', 'hibrido', 999, 70, 92, 'manual 6', 4.9, 112, 7.0, 350
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = '500' AND b.name = 'Fiat';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '500e 118cv', 'eletrico', 0, 118, 220, 'auto', 14.5, 0, 7.5, 220
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = '500' AND b.name = 'Fiat';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 5, 5, 9, 4, 3, 'medio', 'Icone de estilo urbano. Perfeito para a cidade, limitado fora dela. O eletrico e o futuro do modelo.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = '500' AND b.name = 'Fiat';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 12000, 8500, 16000, 35, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = '500' AND b.name = 'Fiat';

-- -- Fiat Panda --
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.0 Mild Hybrid 70', 'hibrido', 999, 70, 92, 'manual 6', 5.0, 114, 7.0, 300
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Panda' AND b.name = 'Fiat';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 5, 3, 8, 4, 5, 'medio', 'Utilitario puro. Simples, barato, funcional. Surpreendente em espaco. Zero pretensoes.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Panda' AND b.name = 'Fiat';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 10500, 8000, 13500, 30, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Panda' AND b.name = 'Fiat';

-- -- Toyota Aygo X --
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.0 VVT-i 72', 'gasolina', 998, 72, 93, 'manual 5', 4.9, 112, 9.0, 250
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Aygo X' AND b.name = 'Toyota';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 5, 4, 9, 4, 3, 'medio', 'Citadino puro com estilo crossover. Motor pequeno mas fiavel. Perfeito para cidade e estacionar.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Aygo X' AND b.name = 'Toyota';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2023, 14500, 12000, 17000, 18, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Aygo X' AND b.name = 'Toyota';

-- -- Hyundai i10 --
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

-- -- Kia Picanto --
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.0 MPI 67', 'gasolina', 998, 67, 96, 'manual 5', 4.8, 109, 8.5, 270
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Picanto' AND b.name = 'Kia';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.0 T-GDi 100', 'gasolina', 998, 100, 172, 'manual 5', 5.2, 118, 8.0, 300
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Picanto' AND b.name = 'Kia';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 5, 5, 9, 4, 3, 'medio', 'Versao T-GDi surpreendentemente animada. Garantia 7 anos. Boa opcao de primeiro carro com caracter.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Picanto' AND b.name = 'Kia';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 10500, 8000, 13500, 25, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Picanto' AND b.name = 'Kia';

-- -- Volkswagen up! --
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.0 MPI 65', 'gasolina', 999, 65, 95, 'manual 5', 4.9, 112, 8.0, 300
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'up!' AND b.name = 'Volkswagen';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 5, 5, 9, 4, 3, 'baixo', 'Citadino alemao com qualidade solida. Descontinuado mas excelente em usados. Economico e fiavel.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'up!' AND b.name = 'Volkswagen';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2020, 8500, 6000, 11500, 40, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'up!' AND b.name = 'Volkswagen';

-- -- Renault Twingo --
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.0 SCe 65', 'gasolina', 999, 65, 95, 'manual 5', 5.2, 118, 6.5, 320
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Twingo' AND b.name = 'Renault';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 5, 5, 9, 3, 3, 'medio', 'Motor traseiro, tracao traseira - unico no segmento. Raio de viragem minusculo. Puro citadino.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Twingo' AND b.name = 'Renault';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2021, 9500, 7000, 12500, 28, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Twingo' AND b.name = 'Renault';

-- -- Citroen C1 --
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.0 VTi 72', 'gasolina', 998, 72, 93, 'manual 5', 4.6, 105, 8.5, 250
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'C1' AND b.name = 'Citroen';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 4, 4, 9, 3, 3, 'medio', 'Gemeo do Aygo/108. Motor Toyota fiavel. Minimalista mas funcional na cidade.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'C1' AND b.name = 'Citroen';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2020, 7500, 5500, 10000, 35, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'C1' AND b.name = 'Citroen';

-- -- Peugeot 108 --
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.0 VTi 72', 'gasolina', 998, 72, 93, 'manual 5', 4.6, 105, 8.5, 250
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = '108' AND b.name = 'Peugeot';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 4, 4, 9, 3, 3, 'medio', 'Variante mais estilosa do trio Toyota/Citroen/Peugeot. Motor Toyota, fiabilidade assegurada.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = '108' AND b.name = 'Peugeot';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2020, 7500, 5500, 10500, 30, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = '108' AND b.name = 'Peugeot';

-- -- Opel Adam --
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.2 70cv', 'gasolina', 1229, 70, 115, 'manual 5', 5.5, 125, 7.0, 350
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Adam' AND b.name = 'Opel';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 5, 4, 8, 4, 3, 'medio', 'Citadino estiloso descontinuado. Personalizacao era o forte. Bons precos em usados.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Adam' AND b.name = 'Opel';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2018, 7000, 5000, 9500, 20, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Adam' AND b.name = 'Opel';

-- -- Volkswagen Golf --
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
SELECT vm.id, 8, 7, 7, 8, 6, 'baixo', 'A referencia do segmento. Equilibrado em tudo. Tecnologia de topo. Nunca empolga mas nunca desilude.'
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
SELECT e.id, 'baixo', 'DSG 7 velocidades: trocar oleo a cada 60.000km. Importante para longevidade.', '2019+', '300-400EUR', 'VW manutencao'
FROM engines e JOIN vehicle_models vm ON e.model_id = vm.id JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Golf' AND b.name = 'Volkswagen' LIMIT 1;

-- -- Peugeot 308 --
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
SELECT vm.id, 7, 6, 7, 7, 6, 'baixo', 'Nova geracao muito bem desenhada. Interior premium para o segmento. i-Cockpit divide opinioes.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = '308' AND b.name = 'Peugeot';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 21000, 17000, 26000, 35, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = '308' AND b.name = 'Peugeot';
INSERT INTO engine_issues (engine_id, severity, description, affected_years, fix_cost_estimate, source)
SELECT e.id, 'medio', 'Motor 1.2 PureTech: correia humida - verificar manutencao rigorosamente.', '2021+', '600-1200EUR', 'Stellantis'
FROM engines e JOIN vehicle_models vm ON e.model_id = vm.id JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = '308' AND b.name = 'Peugeot' LIMIT 1;

-- -- Renault Megane --
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.3 TCe 140', 'gasolina', 1332, 140, 240, 'manual 6', 6.2, 141, 7.0, 420
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Megane' AND b.name = 'Renault';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.3 TCe 140 EDC', 'gasolina', 1332, 140, 240, 'auto 7', 6.4, 146, 6.5, 450
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Megane' AND b.name = 'Renault';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.5 Blue dCi 115', 'diesel', 1461, 115, 260, 'manual 6', 4.2, 111, 7.5, 400
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Megane' AND b.name = 'Renault';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 7, 5, 7, 7, 6, 'baixo', 'Bom espaco e conforto. Motor 1.3 TCe e parceria Mercedes. Solido mas sem brilho.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Megane' AND b.name = 'Renault';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 18000, 14000, 22500, 40, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Megane' AND b.name = 'Renault';

-- -- Toyota Corolla --
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.8 Hibrido 122cv', 'hibrido', 1798, 122, 142, 'auto cvt', 4.5, 101, 9.5, 320
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Corolla' AND b.name = 'Toyota';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '2.0 Hibrido 196cv', 'hibrido', 1987, 196, 190, 'auto cvt', 5.0, 112, 9.0, 350
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Corolla' AND b.name = 'Toyota';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 8, 6, 8, 8, 7, 'baixo', 'Hibrido de referencia. Silencioso, economico, fiavel como um relogio. O 2.0 surpreende na potencia.'
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

-- -- SEAT Leon --
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
SELECT vm.id, 7, 7, 7, 8, 6, 'baixo', 'Golf iberico com mais caracter na conducao. Suspensao mais firme, mais divertido. Mesmo nivel tecnico.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Leon' AND b.name = 'SEAT';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 19500, 15500, 24000, 35, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Leon' AND b.name = 'SEAT';

-- -- Skoda Octavia --
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
SELECT vm.id, 8, 5, 7, 9, 8, 'baixo', 'Rei do espaco-preco. Interior de berlina num compacto. Pragmatico, racional, excelente em estrada.'
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

-- -- Ford Focus --
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
SELECT vm.id, 7, 8, 7, 8, 6, 'baixo', 'Melhor chassis do segmento. Prazer de conducao genuino. Descontinuado mas rei dos usados.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Focus' AND b.name = 'Ford';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 18500, 14500, 23000, 42, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Focus' AND b.name = 'Ford';

-- -- Opel Astra --
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.2 PureTech 130', 'gasolina', 1199, 130, 230, 'manual 6', 5.8, 132, 6.5, 430
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Astra' AND b.name = 'Opel';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.5 Diesel 130', 'diesel', 1499, 130, 300, 'manual 6', 4.3, 113, 7.5, 420
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Astra' AND b.name = 'Opel';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 7, 5, 7, 7, 6, 'baixo', 'Nova geracao sobre plataforma Stellantis. Design ousado. Interior moderno. Falta emocao na conducao.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Astra' AND b.name = 'Opel';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2023, 22000, 18000, 26500, 20, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Astra' AND b.name = 'Opel';

-- -- Hyundai i30 --
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
SELECT vm.id, 7, 6, 7, 7, 6, 'baixo', 'Bem construido e bem equipado. Design discreto. 5 anos de garantia. Escolha sensata.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'i30' AND b.name = 'Hyundai';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 18000, 14000, 22500, 32, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'i30' AND b.name = 'Hyundai';

-- -- Kia Ceed --
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.0 T-GDi 120', 'gasolina', 998, 120, 172, 'manual 6', 5.7, 130, 8.0, 380
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Ceed' AND b.name = 'Kia';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.5 T-GDi 160 DCT', 'gasolina', 1482, 160, 253, 'auto 7', 6.1, 139, 7.5, 410
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Ceed' AND b.name = 'Kia';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 7, 6, 7, 7, 6, 'baixo', 'Gemeo do i30 com design mais europeu. 7 anos de garantia. Versao SW e excelente para familias.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Ceed' AND b.name = 'Kia';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 17500, 13500, 22000, 28, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Ceed' AND b.name = 'Kia';

-- -- Mazda 3 --
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '2.0 Skyactiv-G 122', 'gasolina', 1998, 122, 213, 'manual 6', 6.0, 137, 8.5, 400
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = '3' AND b.name = 'Mazda';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '2.0 Skyactiv-X 186', 'gasolina', 1998, 186, 240, 'manual 6', 5.8, 132, 8.0, 450
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = '3' AND b.name = 'Mazda';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 8, 8, 7, 8, 5, 'baixo', 'Premium disfarcado de generalista. Interior requintado. Conducao envolvente. Falta espaco traseiro.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = '3' AND b.name = 'Mazda';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 21000, 17000, 26000, 22, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = '3' AND b.name = 'Mazda';

-- -- Honda Civic --
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '2.0 e:HEV 184', 'hibrido', 1993, 184, 315, 'auto cvt', 4.7, 107, 9.0, 380
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Civic' AND b.name = 'Honda';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.5 VTEC Turbo 182', 'gasolina', 1498, 182, 240, 'auto cvt', 6.5, 148, 8.0, 400
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Civic' AND b.name = 'Honda';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 8, 7, 7, 8, 6, 'baixo', 'Nova geracao madura e premium. Hibrido brilhante. Conducao refinada. Design elegante e sobrio.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Civic' AND b.name = 'Honda';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2023, 28000, 24000, 33000, 15, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Civic' AND b.name = 'Honda';

-- -- Audi A3 --
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
SELECT vm.id, 8, 6, 7, 8, 5, 'baixo', 'Premium compacto de referencia. Qualidade interior excelente. Virtual Cockpit. Conducao refinada.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'A3' AND b.name = 'Audi';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 27000, 22000, 33000, 35, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'A3' AND b.name = 'Audi';

-- -- BMW Serie 1 --
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '116i 109cv', 'gasolina', 1499, 109, 190, 'manual 6', 5.9, 134, 7.5, 550
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Serie 1' AND b.name = 'BMW';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '118i 136cv', 'gasolina', 1499, 136, 220, 'auto 7', 6.0, 137, 7.0, 580
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Serie 1' AND b.name = 'BMW';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '116d 116cv', 'diesel', 1995, 116, 280, 'manual 6', 4.3, 113, 7.5, 530
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Serie 1' AND b.name = 'BMW';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '120d xDrive 190cv', 'diesel', 1995, 190, 400, 'auto 8', 5.2, 137, 7.0, 620
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Serie 1' AND b.name = 'BMW';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 7, 8, 7, 8, 4, 'baixo', 'Tracao dianteira mas conducao BMW. Mais divertido que A3. Interior orientado ao condutor.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Serie 1' AND b.name = 'BMW';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 26000, 21000, 32000, 30, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Serie 1' AND b.name = 'BMW';

-- -- Mercedes-Benz Classe A --
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

-- -- Volvo V40 --
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, 'T2 122cv', 'gasolina', 1969, 122, 220, 'manual 6', 6.0, 137, 7.0, 500
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'V40' AND b.name = 'Volvo';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, 'D2 120cv', 'diesel', 1969, 120, 280, 'manual 6', 4.0, 105, 7.5, 480
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'V40' AND b.name = 'Volvo';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 8, 5, 7, 7, 5, 'baixo', 'Seguranca Volvo num compacto premium. Descontinuado mas bons precos em usados. Confortavel.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'V40' AND b.name = 'Volvo';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2019, 16000, 12000, 20000, 35, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'V40' AND b.name = 'Volvo';

-- -- Cupra Leon --
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
SELECT vm.id, 7, 9, 7, 9, 5, 'medio', 'SEAT Leon com esteroides. Conducao empolgante. O 2.0 TSI e serio. Hibrido impressionante.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Leon' AND b.name = 'Cupra';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 28000, 23000, 34000, 22, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Leon' AND b.name = 'Cupra';

-- -- DS 4 --
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.2 PureTech 130 EAT8', 'gasolina', 1199, 130, 230, 'auto 8', 6.1, 139, 6.0, 500
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = '4' AND b.name = 'DS';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.6 E-Tense 225 PHEV', 'hibrido', 1598, 225, 360, 'auto 8', 1.3, 30, 6.5, 520
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = '4' AND b.name = 'DS';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 8, 4, 7, 7, 5, 'baixo', 'Interior luxuoso e diferente. Design ousado. Conforto acima da media. Conducao anodina.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = '4' AND b.name = 'DS';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 25000, 20000, 31000, 12, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = '4' AND b.name = 'DS';

-- -- Citroen C4 --
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.2 PureTech 130', 'gasolina', 1199, 130, 230, 'auto 8', 5.8, 132, 6.5, 420
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'C4' AND b.name = 'Citroen';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.5 BlueHDi 130', 'diesel', 1499, 130, 300, 'auto 8', 4.3, 113, 7.5, 430
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'C4' AND b.name = 'Citroen';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, 'e-C4 136cv', 'eletrico', 0, 136, 260, 'auto', 15.5, 0, 7.5, 220
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'C4' AND b.name = 'Citroen';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 8, 4, 7, 7, 6, 'baixo', 'Suspensao com batentes hidraulicos - conforto excecional. Design crossover. Zero desportividade, todo o conforto.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'C4' AND b.name = 'Citroen';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 19000, 15000, 24000, 28, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'C4' AND b.name = 'Citroen';

-- -- Fiat Tipo --
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.0 100cv', 'gasolina', 999, 100, 190, 'manual 6', 5.8, 132, 6.5, 380
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Tipo' AND b.name = 'Fiat';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.6 Multijet 130', 'diesel', 1598, 130, 320, 'manual 6', 4.5, 119, 7.0, 400
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Tipo' AND b.name = 'Fiat';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 6, 4, 6, 7, 7, 'medio', 'Maximo espaco pelo minimo preco. Interior basico mas funcional. Berlina de familia acessivel.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Tipo' AND b.name = 'Fiat';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 13000, 10000, 17000, 25, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Tipo' AND b.name = 'Fiat';

-- -- Skoda Scala --
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.0 TSI 110', 'gasolina', 999, 110, 200, 'manual 6', 5.5, 125, 7.5, 390
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Scala' AND b.name = 'Skoda';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.5 TSI 150 DSG', 'gasolina', 1498, 150, 250, 'auto 7', 5.9, 134, 7.0, 430
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Scala' AND b.name = 'Skoda';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 7, 5, 7, 7, 6, 'baixo', 'Alternativa ao Octavia mais acessivel. Bom espaco. Pragmatica como um Skoda deve ser.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Scala' AND b.name = 'Skoda';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 17000, 13500, 21000, 22, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Scala' AND b.name = 'Skoda';

-- -- Volkswagen ID.3 --
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, 'ID.3 Pro 204cv 58kWh', 'eletrico', 0, 204, 310, 'auto', 15.5, 0, 7.5, 250
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'ID.3' AND b.name = 'Volkswagen';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, 'ID.3 Pro S 204cv 77kWh', 'eletrico', 0, 204, 310, 'auto', 16.0, 0, 7.5, 250
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'ID.3' AND b.name = 'Volkswagen';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 7, 5, 8, 7, 5, 'baixo', 'Golf eletrico. Espacoso, silencioso, pratico. Software melhorou muito. Autonomia real ~350-450km.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'ID.3' AND b.name = 'Volkswagen';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 27000, 22000, 33000, 25, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'ID.3' AND b.name = 'Volkswagen';

-- -- MG 4 --
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, 'MG4 Standard 170cv 51kWh', 'eletrico', 0, 170, 250, 'auto', 15.0, 0, 7.0, 220
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = '4' AND b.name = 'MG';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, 'MG4 Long Range 204cv 64kWh', 'eletrico', 0, 204, 250, 'auto', 15.5, 0, 7.0, 220
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = '4' AND b.name = 'MG';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 6, 6, 8, 7, 5, 'baixo', 'Relacao preco-autonomia imbativel. Conducao surpreendentemente divertida. Interior basico.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = '4' AND b.name = 'MG';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2023, 22000, 18000, 27000, 18, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = '4' AND b.name = 'MG';

-- -- Toyota Prius --
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '2.0 Hibrido 196cv', 'hibrido', 1987, 196, 190, 'auto cvt', 4.2, 95, 9.0, 350
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Prius' AND b.name = 'Toyota';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 8, 6, 8, 8, 5, 'baixo', 'Renascimento do icone hibrido. Agora bonito e rapido. Consumos incriveis. Tecnologia Toyota.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Prius' AND b.name = 'Toyota';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2024, 32000, 28000, 37000, 10, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Prius' AND b.name = 'Toyota';

-- -- MINI Cooper --
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
SELECT vm.id, 6, 8, 8, 6, 3, 'medio', 'Go-kart feeling. Divertido como poucos. Interior unico com personalidade. Custos premium.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Cooper' AND b.name = 'MINI';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 22000, 17000, 28000, 25, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Cooper' AND b.name = 'MINI';

-- -- Audi A1 --
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '25 TFSI 95', 'gasolina', 999, 95, 175, 'manual 5', 5.4, 123, 7.5, 480
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'A1' AND b.name = 'Audi';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '30 TFSI 110', 'gasolina', 999, 110, 200, 'manual 6', 5.5, 125, 7.0, 500
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'A1' AND b.name = 'Audi';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 7, 5, 8, 6, 4, 'baixo', 'Mini A3. Qualidade premium num formato compacto. Virtual Cockpit disponivel. Preco premium.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'A1' AND b.name = 'Audi';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 21000, 17000, 26000, 20, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'A1' AND b.name = 'Audi';

-- -- Mercedes-Benz CLA --
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
SELECT vm.id, 7, 6, 7, 8, 4, 'baixo', 'Coupe 4 portas elegante. Linha de cintura baixa. MBUX de topo. Banco traseiro apertado.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'CLA' AND b.name = 'Mercedes-Benz';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 30000, 25000, 36000, 22, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'CLA' AND b.name = 'Mercedes-Benz';

-- -- BMW Serie 2 Gran Coupe --
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '218i 136cv', 'gasolina', 1499, 136, 220, 'auto 7', 6.0, 137, 7.0, 560
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Serie 2 Gran Coupe' AND b.name = 'BMW';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '220d 190cv', 'diesel', 1995, 190, 400, 'auto 8', 4.8, 126, 7.0, 580
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Serie 2 Gran Coupe' AND b.name = 'BMW';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 7, 7, 7, 8, 4, 'baixo', 'Entrada na gama BMW com estilo coupe. Conducao dinamica. Banco traseiro justo.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Serie 2 Gran Coupe' AND b.name = 'BMW';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 28000, 23000, 34000, 18, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Serie 2 Gran Coupe' AND b.name = 'BMW';

-- -- Skoda Superb --
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
SELECT vm.id, 9, 5, 6, 9, 9, 'baixo', 'Berlina disfarcada de compacto. Espaco de Classe E por preco de Golf. Conforto e espaco enormes.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Superb' AND b.name = 'Skoda';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 25000, 20000, 31000, 25, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Superb' AND b.name = 'Skoda';

-- -- Volkswagen Passat --
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.5 TSI 150 DSG', 'gasolina', 1498, 150, 250, 'auto 7', 5.9, 134, 7.5, 470
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Passat' AND b.name = 'Volkswagen';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '2.0 TDI 150 DSG', 'diesel', 1968, 150, 360, 'auto 7', 4.5, 119, 7.5, 490
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Passat' AND b.name = 'Volkswagen';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 8, 5, 6, 9, 8, 'baixo', 'Carrinha/berlina solida e refinada. Excelente para estrada. Espaco generoso. Fiavel.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Passat' AND b.name = 'Volkswagen';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 26000, 21000, 32000, 30, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Passat' AND b.name = 'Volkswagen';

-- -- Peugeot 508 --
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
SELECT vm.id, 8, 6, 6, 8, 6, 'baixo', 'A mais bonita do segmento. Interior espetacular. Conforto soberbo. Alternativa seria aos alemaes.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = '508' AND b.name = 'Peugeot';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 24000, 19000, 30000, 22, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = '508' AND b.name = 'Peugeot';

-- -- Peugeot 2008 --
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
SELECT vm.id, 7, 5, 8, 7, 6, 'baixo', 'SUV urbano elegante. Interior premium com i-Cockpit. Referencia no segmento B-SUV em Portugal.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = '2008' AND b.name = 'Peugeot';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 20000, 16000, 25000, 42, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = '2008' AND b.name = 'Peugeot';
INSERT INTO engine_issues (engine_id, severity, description, affected_years, fix_cost_estimate, source)
SELECT e.id, 'medio', 'Motor 1.2 PureTech: correia humida - confirmar manutencao.', '2019-2021', '600-1200EUR', 'Stellantis'
FROM engines e JOIN vehicle_models vm ON e.model_id = vm.id JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = '2008' AND b.name = 'Peugeot' LIMIT 1;

-- -- Renault Captur --
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.0 TCe 90', 'gasolina', 999, 90, 160, 'manual 5', 5.9, 134, 7.0, 380
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Captur' AND b.name = 'Renault';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.3 TCe 140 EDC', 'gasolina', 1332, 140, 240, 'auto 7', 6.3, 143, 7.0, 430
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Captur' AND b.name = 'Renault';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.6 E-Tech 145 Hibrido', 'hibrido', 1598, 145, 205, 'auto', 4.7, 107, 7.5, 380
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Captur' AND b.name = 'Renault';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 7, 4, 8, 6, 6, 'baixo', 'Crossover bem-sucedido. Banco traseiro deslizante inteligente. Hibrido convincente.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Captur' AND b.name = 'Renault';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 18500, 14500, 23000, 40, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Captur' AND b.name = 'Renault';

-- -- Dacia Duster --
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
SELECT vm.id, 5, 4, 6, 6, 7, 'medio', 'SUV mais acessivel. Verdadeiro 4x4 disponivel. Interior simples mas espacoso. Relacao preco-capacidade unica.'
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

-- -- Nissan Qashqai --
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.3 DIG-T 140', 'gasolina', 1332, 140, 240, 'manual 6', 6.5, 148, 7.0, 430
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Qashqai' AND b.name = 'Nissan';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.3 DIG-T 158 Xtronic', 'gasolina', 1332, 158, 270, 'auto cvt', 6.7, 152, 7.0, 460
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Qashqai' AND b.name = 'Nissan';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.5 e-Power 190 Hibrido', 'hibrido', 1497, 190, 330, 'auto', 5.3, 120, 7.5, 400
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Qashqai' AND b.name = 'Nissan';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 7, 5, 7, 7, 7, 'baixo', 'Inventor do segmento C-SUV. e-Power e uma solucao inteligente. Confortavel e bem equipado.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Qashqai' AND b.name = 'Nissan';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 24000, 19500, 29000, 35, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Qashqai' AND b.name = 'Nissan';

-- -- Peugeot 3008 --
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
SELECT vm.id, 8, 5, 7, 7, 7, 'baixo', 'Interior espetacular. Conforto de topo no segmento. Design forte. Referencia em Portugal.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = '3008' AND b.name = 'Peugeot';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 26000, 21000, 32000, 38, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = '3008' AND b.name = 'Peugeot';

-- -- Hyundai Tucson --
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
SELECT vm.id, 7, 5, 7, 7, 8, 'baixo', 'Design radical que divide. Muito espaco interior. Hibrido e a melhor escolha. Garantia 5 anos.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Tucson' AND b.name = 'Hyundai';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 26000, 21000, 32000, 35, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Tucson' AND b.name = 'Hyundai';

-- -- Kia Sportage --
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
SELECT vm.id, 7, 5, 7, 8, 8, 'baixo', 'Gemeo do Tucson com mais espaco e design arrojado. 7 anos de garantia. Excelente para familias.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Sportage' AND b.name = 'Kia';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 27000, 22000, 33000, 32, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Sportage' AND b.name = 'Kia';

-- -- Volkswagen T-Roc --
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
SELECT vm.id, 7, 6, 7, 7, 6, 'baixo', 'Golf elevado. Qualidade VW num formato SUV. Conducao segura. Um pouco caro para o que oferece.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'T-Roc' AND b.name = 'Volkswagen';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 23000, 18500, 28000, 38, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'T-Roc' AND b.name = 'Volkswagen';

-- -- Volkswagen Tiguan --
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
SELECT vm.id, 8, 6, 7, 8, 8, 'baixo', 'SUV familiar de referencia. Espaco, qualidade e versatilidade. Preco elevado mas justificado.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Tiguan' AND b.name = 'Volkswagen';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 30000, 24000, 37000, 32, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Tiguan' AND b.name = 'Volkswagen';

-- -- Toyota C-HR --
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.8 Hibrido 122cv', 'hibrido', 1798, 122, 142, 'auto cvt', 4.8, 109, 9.0, 320
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'C-HR' AND b.name = 'Toyota';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '2.0 Hibrido 184cv', 'hibrido', 1987, 184, 190, 'auto cvt', 5.0, 114, 9.0, 350
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'C-HR' AND b.name = 'Toyota';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 7, 6, 8, 7, 5, 'baixo', 'Coupe-SUV com design radical. Visibilidade traseira limitada. Hibrido fiavel. Conducao agradavel.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'C-HR' AND b.name = 'Toyota';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 23000, 19000, 28000, 30, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'C-HR' AND b.name = 'Toyota';

-- -- Toyota RAV4 --
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '2.5 Hibrido 218cv', 'hibrido', 2487, 218, 221, 'auto cvt', 5.0, 114, 9.5, 350
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'RAV4' AND b.name = 'Toyota';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '2.5 Hibrido 222cv AWD', 'hibrido', 2487, 222, 221, 'auto cvt', 5.3, 120, 9.5, 380
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'RAV4' AND b.name = 'Toyota';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '2.5 PHEV 306cv', 'hibrido', 2487, 306, 227, 'auto cvt', 1.0, 22, 9.0, 400
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'RAV4' AND b.name = 'Toyota';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 8, 5, 7, 8, 8, 'baixo', 'SUV hibrido campeao. Espaco familiar generoso. Fiabilidade Toyota legendaria. PHEV com autonomia real ~60km.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'RAV4' AND b.name = 'Toyota';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 30000, 25000, 36000, 35, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'RAV4' AND b.name = 'Toyota';

-- -- SEAT Arona --
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.0 TSI 95', 'gasolina', 999, 95, 175, 'manual 5', 5.5, 125, 7.5, 380
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Arona' AND b.name = 'SEAT';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.0 TSI 110', 'gasolina', 999, 110, 200, 'manual 6', 5.6, 128, 7.0, 400
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Arona' AND b.name = 'SEAT';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 6, 5, 8, 6, 5, 'baixo', 'Ibiza elevado. Bom para cidade. Espaco justo. Preco competitivo. Simpatico mas sem destaque.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Arona' AND b.name = 'SEAT';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 16500, 13000, 20500, 30, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Arona' AND b.name = 'SEAT';

-- -- SEAT Ateca --
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
SELECT vm.id, 7, 7, 7, 8, 7, 'baixo', 'T-Roc com mais espaco e melhor relacao preco. Conducao dinamica para SUV. Escolha inteligente.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Ateca' AND b.name = 'SEAT';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 22000, 17500, 27000, 28, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Ateca' AND b.name = 'SEAT';

-- -- Skoda Kamiq --
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
SELECT vm.id, 7, 5, 8, 7, 6, 'baixo', 'SUV urbano com espaco de compacto. Simply Clever Skoda. Pratico e racional como sempre.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Kamiq' AND b.name = 'Skoda';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 18000, 14500, 22500, 25, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Kamiq' AND b.name = 'Skoda';

-- -- Skoda Karoq --
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
SELECT vm.id, 7, 5, 7, 7, 7, 'baixo', 'Tiguan checo. Mesmo nivel tecnico, preco mais competitivo. Bancos traseiros VarioFlex geniais.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Karoq' AND b.name = 'Skoda';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 22500, 18000, 28000, 25, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Karoq' AND b.name = 'Skoda';

-- -- Skoda Kodiaq --
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
SELECT vm.id, 8, 4, 6, 8, 9, 'baixo', 'SUV 7 lugares acessivel. Espaco enorme. Conforto de estrada. O mais pratico da familia VW.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Kodiaq' AND b.name = 'Skoda';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 28000, 23000, 34000, 22, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Kodiaq' AND b.name = 'Skoda';

-- -- Ford Puma --
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

-- -- Ford Kuga --
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
SELECT vm.id, 7, 5, 7, 7, 7, 'baixo', 'SUV familiar competente. PHEV com boa autonomia eletrica. Espaco generoso. Ligeiramente anonimo.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Kuga' AND b.name = 'Ford';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 24000, 19000, 30000, 28, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Kuga' AND b.name = 'Ford';

-- -- Nissan Juke --
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.0 DIG-T 114', 'gasolina', 999, 114, 200, 'manual 6', 5.8, 132, 7.0, 400
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Juke' AND b.name = 'Nissan';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.6 Hybrid 143', 'hibrido', 1598, 143, 205, 'auto', 5.0, 114, 7.5, 380
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Juke' AND b.name = 'Nissan';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 6, 5, 8, 6, 4, 'baixo', 'Design polarizante. Compacto e agil na cidade. Hibrido e a melhor opcao. Espaco traseiro justo.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Juke' AND b.name = 'Nissan';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 18000, 14000, 22500, 25, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Juke' AND b.name = 'Nissan';

-- -- Hyundai Kona --
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
SELECT vm.id, 6, 5, 8, 6, 5, 'baixo', 'Versatil e fiavel. EV com excelente autonomia. Hibrido eficiente. Garantia 5 anos. Seguro.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Kona' AND b.name = 'Hyundai';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 20000, 16000, 25000, 30, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Kona' AND b.name = 'Hyundai';

-- -- Hyundai Bayon --
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.0 T-GDi 100', 'gasolina', 998, 100, 172, 'manual 5', 5.6, 128, 8.0, 350
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Bayon' AND b.name = 'Hyundai';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.0 T-GDi 100 48V', 'hibrido', 998, 100, 172, 'manual 6', 5.4, 123, 8.0, 360
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Bayon' AND b.name = 'Hyundai';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 6, 4, 8, 6, 5, 'baixo', 'i20 com roupa de SUV. Pratico e acessivel. Ideal para quem quer SUV sem gastar muito.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Bayon' AND b.name = 'Hyundai';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 16500, 13000, 20500, 22, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Bayon' AND b.name = 'Hyundai';

-- -- Kia Stonic --
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.0 T-GDi 100', 'gasolina', 998, 100, 172, 'manual 6', 5.5, 125, 8.0, 350
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Stonic' AND b.name = 'Kia';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.0 T-GDi 120 DCT', 'gasolina', 998, 120, 172, 'auto 7', 5.8, 132, 7.5, 380
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Stonic' AND b.name = 'Kia';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 6, 5, 8, 6, 5, 'baixo', 'Rio em versao SUV. 7 anos de garantia. Bom para cidade. Simples e eficaz.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Stonic' AND b.name = 'Kia';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 16000, 12500, 20000, 22, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Stonic' AND b.name = 'Kia';

-- -- Kia Niro --
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
SELECT vm.id, 7, 4, 8, 7, 7, 'baixo', 'Multienergias: hibrido, PHEV ou eletrico. Pratico e bem equipado. Garantia 7 anos. Familia moderna.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Niro' AND b.name = 'Kia';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2023, 28000, 23000, 34000, 18, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Niro' AND b.name = 'Kia';

-- -- Mazda CX-30 --
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '2.0 Skyactiv-G 122', 'gasolina', 1998, 122, 213, 'manual 6', 6.2, 141, 8.5, 400
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'CX-30' AND b.name = 'Mazda';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '2.0 Skyactiv-X 186', 'gasolina', 1998, 186, 240, 'manual 6', 6.0, 137, 8.0, 450
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'CX-30' AND b.name = 'Mazda';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 8, 7, 7, 7, 6, 'baixo', 'Mazda 3 elevado. Interior requintado. Conducao envolvente para SUV. Qualidade de acabamento excecional.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'CX-30' AND b.name = 'Mazda';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 23000, 19000, 28000, 20, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'CX-30' AND b.name = 'Mazda';

-- -- Mazda CX-5 --
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
SELECT vm.id, 8, 7, 6, 8, 7, 'baixo', 'SUV premium disfarcado. Conducao genuina, interior sofisticado. Fiavel e duravel. Subvalorizado.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'CX-5' AND b.name = 'Mazda';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 25000, 20000, 31000, 25, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'CX-5' AND b.name = 'Mazda';

-- -- Mazda CX-3 --
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '2.0 Skyactiv-G 121', 'gasolina', 1998, 121, 213, 'manual 6', 6.0, 137, 8.5, 380
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'CX-3' AND b.name = 'Mazda';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 7, 6, 8, 6, 4, 'baixo', 'Pequeno mas premium. Conducao Mazda tipica. Espaco traseiro limitado. Qualidade acima da concorrencia.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'CX-3' AND b.name = 'Mazda';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 17500, 14000, 21500, 18, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'CX-3' AND b.name = 'Mazda';

-- -- Honda HR-V --
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.5 e:HEV 131', 'hibrido', 1498, 131, 253, 'auto cvt', 5.0, 114, 9.0, 350
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'HR-V' AND b.name = 'Honda';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 7, 5, 8, 7, 6, 'baixo', 'Hibrido Honda eficiente. Magic Seats do Jazz. Espaco surpreendente. Design clean. Fiavel.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'HR-V' AND b.name = 'Honda';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 25000, 21000, 30000, 15, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'HR-V' AND b.name = 'Honda';

-- -- Honda CR-V --
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.5 VTEC Turbo 193', 'gasolina', 1498, 193, 243, 'auto cvt', 7.0, 159, 8.5, 420
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'CR-V' AND b.name = 'Honda';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '2.0 i-MMD Hibrido 184', 'hibrido', 1993, 184, 315, 'auto cvt', 5.3, 120, 9.0, 380
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'CR-V' AND b.name = 'Honda';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 8, 5, 7, 8, 8, 'baixo', 'SUV familiar de referencia. Espaco generoso. Hibrido muito eficiente. Fiabilidade Honda legendaria.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'CR-V' AND b.name = 'Honda';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 28000, 23000, 34000, 20, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'CR-V' AND b.name = 'Honda';

-- -- Opel Mokka --
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
SELECT vm.id, 6, 5, 8, 6, 4, 'baixo', 'Design Vizor marcante. Compacto e agil. Base Peugeot 2008 com identidade alema. Eletrico interessante.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Mokka' AND b.name = 'Opel';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 19500, 15500, 24000, 22, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Mokka' AND b.name = 'Opel';

-- -- Opel Grandland --
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
SELECT vm.id, 7, 4, 7, 7, 7, 'baixo', 'SUV familiar Opel. Plataforma Peugeot 3008. Confortavel e espacoso. Design mais conservador.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Grandland' AND b.name = 'Opel';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 24000, 19000, 30000, 20, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Grandland' AND b.name = 'Opel';

-- -- Citroen C3 Aircross --
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.2 PureTech 110', 'gasolina', 1199, 110, 205, 'manual 6', 5.8, 132, 6.5, 400
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'C3 Aircross' AND b.name = 'Citroen';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.2 PureTech 130 EAT6', 'gasolina', 1199, 130, 230, 'auto 6', 6.1, 139, 6.0, 430
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'C3 Aircross' AND b.name = 'Citroen';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 7, 4, 8, 6, 6, 'baixo', 'SUV simpatico e confortavel. Suspensao macia. Ideal para cidade e familia. Ar descontraido.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'C3 Aircross' AND b.name = 'Citroen';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 16500, 13000, 20500, 25, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'C3 Aircross' AND b.name = 'Citroen';

-- -- Citroen C5 Aircross --
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.2 PureTech 130 EAT8', 'gasolina', 1199, 130, 230, 'auto 8', 6.2, 141, 6.5, 440
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'C5 Aircross' AND b.name = 'Citroen';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.5 BlueHDi 130 EAT8', 'diesel', 1499, 130, 300, 'auto 8', 4.8, 126, 7.5, 430
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'C5 Aircross' AND b.name = 'Citroen';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.6 Hybrid 225 PHEV', 'hibrido', 1598, 225, 360, 'auto 8', 1.5, 34, 7.0, 470
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'C5 Aircross' AND b.name = 'Citroen';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 8, 4, 7, 7, 7, 'baixo', 'Conforto de referencia com batentes hidraulicos. Macio como um sofa. Ignora buracos. Zero desportividade.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'C5 Aircross' AND b.name = 'Citroen';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 23000, 18000, 28500, 22, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'C5 Aircross' AND b.name = 'Citroen';

-- -- Renault Kadjar --
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.3 TCe 140', 'gasolina', 1332, 140, 240, 'manual 6', 6.5, 148, 7.0, 420
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Kadjar' AND b.name = 'Renault';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.5 Blue dCi 115', 'diesel', 1461, 115, 260, 'manual 6', 4.8, 126, 7.5, 400
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Kadjar' AND b.name = 'Renault';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 7, 4, 7, 7, 7, 'medio', 'Qashqai frances. Confortavel e espacoso. Descontinuado - bons precos em usados.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Kadjar' AND b.name = 'Renault';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2021, 17000, 13000, 21500, 35, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Kadjar' AND b.name = 'Renault';

-- -- Renault Austral --
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.2 E-Tech Hibrido 200', 'hibrido', 1199, 200, 205, 'auto', 4.7, 107, 7.0, 430
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Austral' AND b.name = 'Renault';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.3 TCe 160 EDC', 'gasolina', 1332, 160, 270, 'auto 7', 6.5, 148, 7.0, 450
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Austral' AND b.name = 'Renault';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 8, 5, 7, 7, 7, 'baixo', 'Substituto do Kadjar. Interior premium surpreendente. Hibrido eficiente. Salto de qualidade enorme.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Austral' AND b.name = 'Renault';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2023, 28000, 23000, 34000, 15, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Austral' AND b.name = 'Renault';

-- -- Renault Arkana --
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.3 TCe 140', 'gasolina', 1332, 140, 240, 'manual 6', 6.3, 143, 7.0, 420
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Arkana' AND b.name = 'Renault';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.6 E-Tech 145 Hibrido', 'hibrido', 1598, 145, 205, 'auto', 4.8, 109, 7.5, 400
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Arkana' AND b.name = 'Renault';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 7, 5, 7, 7, 6, 'baixo', 'Coupe-SUV acessivel. Design dinamico. Hibrido eficiente. Alternativa interessante ao Captur para quem quer mais estilo.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Arkana' AND b.name = 'Renault';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 22000, 18000, 27000, 20, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Arkana' AND b.name = 'Renault';

-- -- Volkswagen T-Cross --
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

-- -- Toyota Yaris Cross --
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.5 Hibrido 116cv', 'hibrido', 1490, 116, 120, 'auto cvt', 4.4, 100, 9.5, 300
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Yaris Cross' AND b.name = 'Toyota';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.5 Hibrido 116cv AWD', 'hibrido', 1490, 116, 120, 'auto cvt', 5.0, 114, 9.5, 330
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Yaris Cross' AND b.name = 'Toyota';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 7, 4, 9, 6, 6, 'baixo', 'Yaris com formato SUV. Hibrido referencia em consumos. Fiabilidade Toyota. Compacto e eficiente.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Yaris Cross' AND b.name = 'Toyota';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 22500, 19000, 27000, 30, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Yaris Cross' AND b.name = 'Toyota';

-- -- BMW X1 --
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
SELECT vm.id, 8, 7, 7, 8, 7, 'baixo', 'SUV premium acessivel. Nova geracao muito mais espacosa. Conducao BMW tipica. Eletrico impressionante.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'X1' AND b.name = 'BMW';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2023, 35000, 29000, 42000, 20, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'X1' AND b.name = 'BMW';

-- -- Mercedes-Benz GLA --
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
SELECT vm.id, 8, 5, 7, 7, 6, 'baixo', 'Classe A elevado. Interior MBUX de topo. Conforto premium. Espaco adequado para o segmento.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'GLA' AND b.name = 'Mercedes-Benz';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 32000, 26000, 39000, 22, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'GLA' AND b.name = 'Mercedes-Benz';

-- -- Audi Q2 --
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
SELECT vm.id, 7, 5, 8, 7, 4, 'baixo', 'Mini Q3. Premium compacto com cara de Audi. Qualidade interior boa. Preco premium pelo tamanho.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Q2' AND b.name = 'Audi';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 24000, 19000, 30000, 20, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Q2' AND b.name = 'Audi';

-- -- BMW Serie 3 --
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '318i 156cv', 'gasolina', 1998, 156, 250, 'auto 8', 6.2, 141, 7.5, 600
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Serie 3' AND b.name = 'BMW';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '320i 184cv', 'gasolina', 1998, 184, 300, 'auto 8', 6.5, 148, 7.5, 620
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Serie 3' AND b.name = 'BMW';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '320d 190cv', 'diesel', 1995, 190, 400, 'auto 8', 4.8, 126, 7.5, 600
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Serie 3' AND b.name = 'BMW';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '330i 258cv', 'gasolina', 1998, 258, 400, 'auto 8', 6.8, 155, 7.0, 680
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Serie 3' AND b.name = 'BMW';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '330e PHEV 292cv', 'hibrido', 1998, 292, 420, 'auto 8', 1.6, 37, 7.0, 650
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Serie 3' AND b.name = 'BMW';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 8, 9, 6, 9, 5, 'baixo', 'A referencia das berlinas desportivas. Conducao excepcional. Prazer genuino ao volante. O 330i e doce.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Serie 3' AND b.name = 'BMW';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 34000, 27000, 42000, 40, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Serie 3' AND b.name = 'BMW';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2021, 30000, 24000, 38000, 50, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Serie 3' AND b.name = 'BMW';

-- -- Mercedes-Benz Classe C --
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
SELECT vm.id, 9, 7, 7, 9, 5, 'baixo', 'Mini Classe S. Interior luxuoso com MBUX de nova geracao. Conforto supremo. Suspensao refinada.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Classe C' AND b.name = 'Mercedes-Benz';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 38000, 31000, 46000, 35, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Classe C' AND b.name = 'Mercedes-Benz';

-- -- Audi A4 --
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
SELECT vm.id, 8, 7, 6, 9, 5, 'baixo', 'Qualidade de construcao impecavel. Virtual Cockpit de referencia. Equilibrado e refinado. Avant e excelente.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'A4' AND b.name = 'Audi';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 33000, 27000, 41000, 35, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'A4' AND b.name = 'Audi';

-- -- Volvo S60 --
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
SELECT vm.id, 9, 6, 6, 9, 5, 'baixo', 'Seguranca Volvo numa berlina elegante. Design escandinavo sobrio. Conforto soberbo. Subvalorizada.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'S60' AND b.name = 'Volvo';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 32000, 26000, 39000, 15, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'S60' AND b.name = 'Volvo';

-- -- Volvo V60 --
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
SELECT vm.id, 9, 6, 6, 9, 7, 'baixo', 'A carrinha mais bonita do segmento. Seguranca, conforto, espaco. Escolha de quem sabe o que quer.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'V60' AND b.name = 'Volvo';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 33000, 27000, 40000, 18, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'V60' AND b.name = 'Volvo';

-- -- Alfa Romeo Giulia --
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
SELECT vm.id, 7, 10, 5, 9, 4, 'medio', 'Pura emocao italiana. Chassis de referencia - melhor que BMW. Motor Quadrifoglio e Ferrari. Fiabilidade e o preco da paixao.'
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
SELECT e.id, 'medio', 'Eletronica e sensores podem dar problemas. Manutencao mais cara que alemaes. Vale cada centimo se gostas de conduzir.', '2016+', 'variavel', 'Alfa Romeo forums'
FROM engines e JOIN vehicle_models vm ON e.model_id = vm.id JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Giulia' AND b.name = 'Alfa Romeo' LIMIT 1;

-- -- Tesla Model 3 --
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
SELECT vm.id, 7, 7, 8, 8, 5, 'baixo', 'Eletrico que mudou tudo. Autonomia real 400-500km. Performance brutal. Interior minimalista polarizante. Autopilot.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Model 3' AND b.name = 'Tesla';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 32000, 26000, 40000, 35, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Model 3' AND b.name = 'Tesla';

-- -- Tesla Model Y --
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, 'Model Y RWD 283cv', 'eletrico', 0, 283, 420, 'auto', 15.5, 0, 7.5, 260
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Model Y' AND b.name = 'Tesla';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, 'Model Y Long Range AWD 366cv', 'eletrico', 0, 366, 493, 'auto', 16.0, 0, 7.5, 290
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Model Y' AND b.name = 'Tesla';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 7, 6, 7, 8, 7, 'baixo', 'Model 3 com mais espaco. Pratico para familia. Mesma tecnologia. Carro mais vendido do mundo em 2023.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Model Y' AND b.name = 'Tesla';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2023, 37000, 31000, 44000, 28, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Model Y' AND b.name = 'Tesla';

-- -- Volvo XC40 --
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
SELECT vm.id, 8, 6, 8, 7, 6, 'baixo', 'SUV premium compacto. Seguranca Volvo. Design nordico. Interior requintado. Eletrico com boa autonomia.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'XC40' AND b.name = 'Volvo';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 30000, 24000, 37000, 25, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'XC40' AND b.name = 'Volvo';

-- -- Volvo XC60 --
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
SELECT vm.id, 9, 5, 6, 8, 7, 'baixo', 'SUV de referencia em seguranca e conforto. Interior sublime. O PHEV e espetacular. Design intemporal.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'XC60' AND b.name = 'Volvo';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 38000, 31000, 46000, 22, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'XC60' AND b.name = 'Volvo';

-- -- Cupra Formentor --
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
SELECT vm.id, 7, 8, 7, 8, 6, 'medio', 'SUV-coupe com alma desportiva. Design espetacular. O 2.0 TSI 245cv e serio. Marca em ascensao.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Formentor' AND b.name = 'Cupra';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 28000, 23000, 35000, 22, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Formentor' AND b.name = 'Cupra';

-- -- Lexus NX --
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '350h Hibrido 244cv', 'hibrido', 2487, 244, 239, 'auto cvt', 5.5, 125, 9.0, 400
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'NX' AND b.name = 'Lexus';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '450h+ PHEV 309cv', 'hibrido', 2487, 309, 227, 'auto cvt', 1.2, 27, 8.5, 450
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'NX' AND b.name = 'Lexus';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 8, 5, 7, 8, 7, 'baixo', 'Premium japones alternativo. Fiabilidade Toyota. Interior luxuoso. Hibrido eficiente. Silencioso e refinado.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'NX' AND b.name = 'Lexus';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2023, 42000, 36000, 50000, 12, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'NX' AND b.name = 'Lexus';

-- -- Land Rover Defender --
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
SELECT vm.id, 7, 7, 5, 7, 8, 'medio', 'Icone reinventado. Off-road serio com luxo moderno. Presenca inigualavel. Manutencao cara mas experiencia unica.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Defender' AND b.name = 'Land Rover';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 55000, 45000, 68000, 18, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Defender' AND b.name = 'Land Rover';
INSERT INTO engine_issues (engine_id, severity, description, affected_years, fix_cost_estimate, source)
SELECT e.id, 'medio', 'Eletronica pode ter falhas em primeiros anos. Sensores e sistemas complexos. Garantia 3 anos.', '2020+', 'variavel', 'JLR forums'
FROM engines e JOIN vehicle_models vm ON e.model_id = vm.id JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Defender' AND b.name = 'Land Rover' LIMIT 1;

-- -- Porsche Macan --
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
SELECT vm.id, 8, 9, 6, 9, 5, 'baixo', 'SUV desportivo por excelencia. Conducao de carro desportivo em formato SUV. O GTS e sensacional.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Macan' AND b.name = 'Porsche';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 52000, 42000, 65000, 15, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Macan' AND b.name = 'Porsche';

-- -- Porsche Cayenne --
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

-- -- BMW X3 --
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
SELECT vm.id, 8, 7, 6, 9, 7, 'baixo', 'SUV premium equilibrado. Conducao BMW sem compromissos. Espaco familiar. PHEV com boa autonomia.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'X3' AND b.name = 'BMW';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2023, 42000, 35000, 50000, 18, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'X3' AND b.name = 'BMW';

-- -- Mercedes-Benz GLC --
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
SELECT vm.id, 9, 6, 6, 8, 7, 'baixo', 'Mini GLE. Interior de luxo. Conforto extraordinario. PHEV com 100km de autonomia eletrica real. Premium total.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'GLC' AND b.name = 'Mercedes-Benz';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2023, 48000, 40000, 58000, 15, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'GLC' AND b.name = 'Mercedes-Benz';

-- -- Audi Q5 --
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
SELECT vm.id, 8, 6, 6, 8, 7, 'baixo', 'SUV premium equilibrado. Qualidade Audi impecavel. quattro de referencia. Virtual Cockpit. Refinado em tudo.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Q5' AND b.name = 'Audi';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 40000, 33000, 49000, 20, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Q5' AND b.name = 'Audi';

-- -- Dacia Jogger --
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.0 TCe 110', 'gasolina', 999, 110, 200, 'manual 6', 6.3, 143, 7.0, 320
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Jogger' AND b.name = 'Dacia';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.6 Hybrid 140', 'hibrido', 1598, 140, 205, 'auto', 4.8, 109, 7.5, 350
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Jogger' AND b.name = 'Dacia';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 6, 3, 6, 6, 9, 'medio', '7 lugares pelo preco de um citadino. Melhor relacao espaco-preco do mercado. Sem luxos mas com espaco para tudo.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Jogger' AND b.name = 'Dacia';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2023, 17000, 14000, 21000, 25, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Jogger' AND b.name = 'Dacia';

-- -- Peugeot 5008 --
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
SELECT vm.id, 8, 4, 6, 7, 9, 'baixo', '7 lugares com estilo. Interior premium para a classe. Confortavel e espacoso. Alternativa elegante aos MPV.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = '5008' AND b.name = 'Peugeot';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 27000, 22000, 33000, 22, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = '5008' AND b.name = 'Peugeot';

-- -- Hyundai Ioniq 5 --
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, 'RWD 228cv 77kWh', 'eletrico', 0, 228, 350, 'auto', 17.0, 0, 8.0, 250
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Ioniq 5' AND b.name = 'Hyundai';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, 'AWD 325cv 77kWh', 'eletrico', 0, 325, 605, 'auto', 18.0, 0, 8.0, 270
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Ioniq 5' AND b.name = 'Hyundai';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 8, 7, 7, 8, 7, 'baixo', 'Design retro-futurista. Interior lounge. Carregamento 800V ultra-rapido. Um dos melhores EVs do mercado.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Ioniq 5' AND b.name = 'Hyundai';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2023, 38000, 32000, 46000, 18, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Ioniq 5' AND b.name = 'Hyundai';

-- -- Kia EV6 --
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
SELECT vm.id, 7, 8, 7, 8, 6, 'baixo', 'Plataforma Ioniq 5, personalidade desportiva. GT e brutal. Design de coupe. 800V. Premiado mundialmente.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'EV6' AND b.name = 'Kia';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2023, 40000, 34000, 48000, 15, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'EV6' AND b.name = 'Kia';

-- -- Volvo EX30 --
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, 'Single Motor 272cv', 'eletrico', 0, 272, 343, 'auto', 15.5, 0, 7.5, 230
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'EX30' AND b.name = 'Volvo';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 7, 6, 8, 7, 4, 'baixo', 'O Volvo mais acessivel. Interior minimalista radical. Compacto e agil. Seguranca Volvo. Entrada no mundo premium EV.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'EX30' AND b.name = 'Volvo';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2024, 33000, 29000, 38000, 10, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'EX30' AND b.name = 'Volvo';

-- -- Toyota GR Yaris --
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.6 Turbo 261cv AWD', 'gasolina', 1618, 261, 360, 'manual 6', 7.5, 171, 8.0, 450
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'GR Yaris' AND b.name = 'Toyota';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 5, 10, 6, 7, 3, 'medio', 'Homologacao de rali para a estrada. AWD, 261cv, 1.2 toneladas. Provavelmente o hot hatch mais puro a venda hoje. Lendario.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'GR Yaris' AND b.name = 'Toyota';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2023, 38000, 33000, 45000, 8, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'GR Yaris' AND b.name = 'Toyota';

-- -- Toyota GR86 --
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '2.4 Boxer 234cv', 'gasolina', 2387, 234, 250, 'manual 6', 8.5, 193, 8.0, 400
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'GR86' AND b.name = 'Toyota';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 5, 10, 5, 7, 2, 'medio', 'Coupe puro como ja nao se fazem. Leve, equilibrado, motor boxer. Diversao analogica. Nenhuma eletronica entre ti e a estrada.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'GR86' AND b.name = 'Toyota';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2023, 32000, 28000, 37000, 6, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'GR86' AND b.name = 'Toyota';

-- -- Mazda MX-5 --
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.5 Skyactiv-G 132cv', 'gasolina', 1496, 132, 152, 'manual 6', 6.5, 148, 9.0, 350
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'MX-5' AND b.name = 'Mazda';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '2.0 Skyactiv-G 184cv', 'gasolina', 1998, 184, 205, 'manual 6', 7.0, 159, 8.5, 380
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'MX-5' AND b.name = 'Mazda';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 5, 10, 6, 7, 1, 'medio', 'O roadster perfeito. Leve, equilibrado, capota manual satisfatoria. Sorrisos por quilometro e a metrica que interessa.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'MX-5' AND b.name = 'Mazda';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 25000, 20000, 31000, 12, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'MX-5' AND b.name = 'Mazda';

-- -- Alpine A110 --
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.8 Turbo 252cv', 'gasolina', 1798, 252, 320, 'auto 7', 6.5, 148, 7.0, 700
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'A110' AND b.name = 'Alpine';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.8 Turbo S 300cv', 'gasolina', 1798, 300, 340, 'auto 7', 6.8, 155, 7.0, 750
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'A110' AND b.name = 'Alpine';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 5, 10, 4, 8, 1, 'medio', 'Escultura automovel francesa. Chassis de mid-engine, 1100kg, aluminio. Conducao transcendente. Obra de arte.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'A110' AND b.name = 'Alpine';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 48000, 40000, 58000, 6, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'A110' AND b.name = 'Alpine';

-- -- Ford Mustang --
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '2.3 EcoBoost 290cv', 'gasolina', 2261, 290, 440, 'auto 10', 9.0, 205, 7.0, 600
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Mustang' AND b.name = 'Ford';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '5.0 V8 GT 450cv', 'gasolina', 4951, 450, 529, 'manual 6', 12.5, 284, 7.0, 800
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Mustang' AND b.name = 'Ford';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 6, 9, 4, 7, 3, 'alto', 'Muscle car americano. V8 inconfundivel. Presenca na estrada impossivel de ignorar. Consumos e tamanho americanos.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Mustang' AND b.name = 'Ford';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 38000, 30000, 48000, 10, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Mustang' AND b.name = 'Ford';

-- -- Subaru BRZ --
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '2.4 Boxer 234cv', 'gasolina', 2387, 234, 250, 'manual 6', 8.5, 193, 8.0, 400
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'BRZ' AND b.name = 'Subaru';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 5, 10, 5, 7, 2, 'medio', 'Gemeo do GR86 com identidade Subaru. Motor boxer puro. AWD ausente - e RWD puro. Diversao analogica.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'BRZ' AND b.name = 'Subaru';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2023, 31000, 27000, 36000, 5, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'BRZ' AND b.name = 'Subaru';

-- -- Suzuki Swift --
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.2 Hybrid 83cv', 'hibrido', 1197, 83, 107, 'manual 5', 4.6, 105, 8.5, 300
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Swift' AND b.name = 'Suzuki';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.4 Boosterjet Sport 129cv', 'gasolina', 1373, 129, 235, 'manual 6', 5.8, 132, 8.0, 350
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Swift' AND b.name = 'Suzuki';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 5, 7, 9, 5, 4, 'baixo', 'Leve e divertido. Sport e um pocket rocket. Fiavel como tudo da Suzuki. Preco justo, diversao garantida.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Swift' AND b.name = 'Suzuki';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 12000, 9000, 15500, 20, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Swift' AND b.name = 'Suzuki';

-- -- Suzuki Vitara --
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.4 Boosterjet Hybrid 129cv', 'hibrido', 1373, 129, 235, 'manual 6', 5.8, 132, 8.5, 350
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Vitara' AND b.name = 'Suzuki';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.4 Boosterjet AllGrip 129cv', 'hibrido', 1373, 129, 235, 'manual 6', 6.2, 141, 8.5, 370
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Vitara' AND b.name = 'Suzuki';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 6, 5, 7, 6, 6, 'medio', 'SUV compacto fiavel e com verdadeiro 4x4. AllGrip competente em terra. Japao no melhor: simples e duravel.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Vitara' AND b.name = 'Suzuki';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2022, 17000, 13500, 21000, 18, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'Vitara' AND b.name = 'Suzuki';

-- -- Suzuki S-Cross --
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.4 Boosterjet Hybrid 129cv', 'hibrido', 1373, 129, 235, 'manual 6', 5.8, 132, 8.5, 360
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'S-Cross' AND b.name = 'Suzuki';
INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp, torque_nm, transmission, consumption_mixed, co2_emissions, reliability_score, maintenance_cost_year)
SELECT vm.id, '1.4 Boosterjet AllGrip Hybrid', 'hibrido', 1373, 129, 235, 'auto 6', 6.2, 141, 8.5, 380
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'S-Cross' AND b.name = 'Suzuki';
INSERT INTO driving_character (model_id, comfort_score, driving_fun_score, city_score, highway_score, family_score, noise_level, description)
SELECT vm.id, 7, 5, 7, 7, 6, 'baixo', 'Evolucao do Vitara com mais refinamento. Interior melhorado. Fiabilidade Suzuki. Surpreendente valor.'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'S-Cross' AND b.name = 'Suzuki';
INSERT INTO market_price_stats (model_id, engine_id, price_context, year, avg_price, min_price, max_price, sample_count, source)
SELECT vm.id, (SELECT e.id FROM engines e WHERE e.model_id = vm.id LIMIT 1), 'particular', 2023, 22000, 18000, 27000, 12, 'Standvirtual/OLX 2025'
FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
WHERE vm.name = 'S-Cross' AND b.name = 'Suzuki';