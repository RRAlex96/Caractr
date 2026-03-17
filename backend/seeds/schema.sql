-- =============================================================
-- CarroJusto MVP - Schema SQL Completo (v1 + v2)
-- Base de dados: PostgreSQL 18
-- Executar: psql -U postgres -d carrojusto_dev -f schema.sql
-- =============================================================

-- 1. MARCAS
CREATE TABLE brands (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,      -- Ex: 'Toyota', 'BMW'
    country VARCHAR(50),                    -- Ex: 'Japão', 'Alemanha'
    created_at TIMESTAMP DEFAULT NOW()
);

-- 2. MODELOS DE VEÍCULOS
CREATE TABLE vehicle_models (
    id SERIAL PRIMARY KEY,
    brand_id INTEGER NOT NULL REFERENCES brands(id),
    name VARCHAR(100) NOT NULL,             -- Ex: 'Corolla', 'Série 3'
    body_type VARCHAR(30) NOT NULL,         -- compacto, berlina, carrinha, suv, monovolume
    segment VARCHAR(30),                    -- económico, médio, premium, luxo
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(brand_id, name)
);

-- 3. GERAÇÕES
CREATE TABLE generations (
    id SERIAL PRIMARY KEY,
    model_id INTEGER NOT NULL REFERENCES vehicle_models(id),
    name VARCHAR(50),                       -- Ex: 'E90', 'Mk4', 'Fase 2'
    year_start INTEGER NOT NULL,
    year_end INTEGER,                       -- NULL = ainda em produção
    created_at TIMESTAMP DEFAULT NOW()
);

-- 4. MOTORES
CREATE TABLE engines (
    id SERIAL PRIMARY KEY,
    model_id INTEGER NOT NULL REFERENCES vehicle_models(id),
    code VARCHAR(50),                       -- Ex: '1.6 TDI', '2.0 TFSI', '1.8 Hybrid'
    fuel_type VARCHAR(20) NOT NULL,         -- gasolina, diesel, hibrido, eletrico, gpl
    displacement_cc INTEGER,                -- Cilindrada em cc (ex: 1598)
    power_hp INTEGER,                       -- Potência em cv
    consumption_mixed DECIMAL(4,1),         -- Consumo misto em l/100km
    reliability_score INTEGER CHECK (reliability_score BETWEEN 1 AND 10),
    maintenance_cost_year INTEGER,          -- Custo médio anual estimado (€)
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(model_id, code)
);

-- 5. PROBLEMAS CONHECIDOS POR MOTOR
--    Filosofia: informar sem assustar.
--    Não existe nível "crítico" — se um motor fosse assim
--    tão problemático, não deveria estar na base.
CREATE TABLE engine_issues (
    id SERIAL PRIMARY KEY,
    engine_id INTEGER NOT NULL REFERENCES engines(id),
    issue_name VARCHAR(200) NOT NULL,       -- Ex: 'Corrente de distribuição'
    severity VARCHAR(20) NOT NULL,          -- baixa, media, alta (uso interno para scoring)
    typical_km_start INTEGER,               -- Uso interno, não mostrado ao utilizador
    typical_km_end INTEGER,                 -- Uso interno, não mostrado ao utilizador
    repair_cost_estimate INTEGER,           -- Custo estimado da reparação (€)
    description TEXT,                       -- Descrição clara do problema
    alert_level VARCHAR(20) DEFAULT 'informativo'
        CHECK (alert_level IN ('informativo', 'atencao', 'verificacao')),
    what_to_ask TEXT,                       -- O que sugerir ao utilizador perguntar ao vendedor
    if_maintained TEXT,                     -- O que acontece se o carro estiver bem mantido
    preventable BOOLEAN DEFAULT TRUE,       -- Se é prevenível com manutenção adequada
    created_at TIMESTAMP DEFAULT NOW()
);

-- 6. CARÁCTER DE CONDUÇÃO
CREATE TABLE driving_character (
    id SERIAL PRIMARY KEY,
    model_id INTEGER NOT NULL REFERENCES vehicle_models(id),
    comfort_score INTEGER CHECK (comfort_score BETWEEN 1 AND 10),
    driving_fun_score INTEGER CHECK (driving_fun_score BETWEEN 1 AND 10),
    city_score INTEGER CHECK (city_score BETWEEN 1 AND 10),
    highway_score INTEGER CHECK (highway_score BETWEEN 1 AND 10),
    family_score INTEGER CHECK (family_score BETWEEN 1 AND 10),
    noise_level VARCHAR(20),                -- baixo, medio, alto
    description TEXT,                       -- Texto descritivo do carácter
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(model_id)
);

-- 7. ESTATÍSTICAS DE PREÇO DE MERCADO
CREATE TABLE market_price_stats (
    id SERIAL PRIMARY KEY,
    model_id INTEGER NOT NULL REFERENCES vehicle_models(id),
    engine_id INTEGER REFERENCES engines(id),
    year INTEGER NOT NULL,
    price_context VARCHAR(20) DEFAULT 'particular'
        CHECK (price_context IN ('particular', 'stand', 'importacao')),
    avg_price INTEGER,                      -- Preço médio (€)
    min_price INTEGER,
    max_price INTEGER,
    sample_count INTEGER DEFAULT 0,         -- Quantos anúncios usados no cálculo
    confidence VARCHAR(20),                 -- alta, media, baixa
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(model_id, engine_id, year, price_context)
);

-- 8. ANÚNCIOS BRUTOS (importados)
CREATE TABLE raw_listings (
    id SERIAL PRIMARY KEY,
    source VARCHAR(50) NOT NULL,            -- standvirtual, olx, autoscout24
    source_url TEXT NOT NULL UNIQUE,
    source_id VARCHAR(100),                 -- ID do anúncio na fonte
    raw_title TEXT,
    raw_price INTEGER,
    raw_year INTEGER,
    raw_km INTEGER,
    raw_fuel VARCHAR(50),
    raw_location VARCHAR(100),
    raw_html TEXT,                           -- HTML guardado para re-parse
    fetched_at TIMESTAMP DEFAULT NOW(),
    parsed BOOLEAN DEFAULT FALSE
);

-- 9. ANÚNCIOS NORMALIZADOS
CREATE TABLE normalized_listings (
    id SERIAL PRIMARY KEY,
    raw_listing_id INTEGER NOT NULL REFERENCES raw_listings(id),
    model_id INTEGER REFERENCES vehicle_models(id),
    engine_id INTEGER REFERENCES engines(id),
    brand_name VARCHAR(100),
    model_name VARCHAR(100),
    year INTEGER,
    km INTEGER,
    price INTEGER,
    fuel_type VARCHAR(20),
    match_confidence VARCHAR(20),           -- alta, media, baixa
    normalized_at TIMESTAMP DEFAULT NOW()
);

-- 10. CUSTOS DE IMPORTAÇÃO ESTIMADOS
CREATE TABLE import_cost_estimates (
    id SERIAL PRIMARY KEY,
    segment VARCHAR(30) NOT NULL UNIQUE,    -- económico, médio, premium, luxo
    legalization_cost INTEGER DEFAULT 800,
    transport_cost INTEGER DEFAULT 500,
    inspection_cost INTEGER DEFAULT 150,
    iuc_first_year INTEGER,
    other_costs INTEGER DEFAULT 200,
    total_estimated INTEGER GENERATED ALWAYS AS
        (legalization_cost + transport_cost +
         inspection_cost + COALESCE(iuc_first_year, 0) +
         other_costs) STORED,
    notes TEXT,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 11. ÍNDICES PARA PERFORMANCE
CREATE INDEX idx_vehicle_models_brand ON vehicle_models(brand_id);
CREATE INDEX idx_vehicle_models_body ON vehicle_models(body_type);
CREATE INDEX idx_engines_model ON engines(model_id);
CREATE INDEX idx_engines_fuel ON engines(fuel_type);
CREATE INDEX idx_engine_issues_engine ON engine_issues(engine_id);
CREATE INDEX idx_market_price_model_year ON market_price_stats(model_id, year);
CREATE INDEX idx_normalized_model ON normalized_listings(model_id);
CREATE INDEX idx_raw_listings_source ON raw_listings(source);

-- 12. SEED INICIAL: CUSTOS DE IMPORTAÇÃO
INSERT INTO import_cost_estimates
    (segment, legalization_cost, transport_cost, inspection_cost, iuc_first_year, other_costs, notes)
VALUES
    ('economico', 700, 400, 130, 50, 150, 'Carros pequenos, cilindrada baixa, IUC reduzido'),
    ('medio', 800, 500, 150, 120, 200, 'Segmento médio, custos standard de importação'),
    ('premium', 1000, 600, 150, 250, 300, 'Carros premium, IUC mais alto pela cilindrada/emissões'),
    ('luxo', 1200, 800, 200, 400, 400, 'Carros de luxo, custos de legalização e IUC elevados');
