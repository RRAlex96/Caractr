-- ═══════════════════════════════════════════════════════════════════════════
-- Migration v53: price_observations — source-agnostic market intelligence
-- ═══════════════════════════════════════════════════════════════════════════
--
-- Every price data point from every source flows into this table equally:
--   - Standvirtual batch scrape → observation_type = 'batch'
--   - OLX batch scrape → observation_type = 'batch'
--   - User analyses a soauto.pt link → observation_type = 'user_analysis'
--   - User analyses a random dealer site → observation_type = 'user_analysis'
--   - CustoJusto batch scrape → observation_type = 'batch'
--
-- This is the foundation for:
--   1. Cross-source price validation (SV vs CustoJusto vs dealer sites)
--   2. Organic data growth (every analysis = free market data)
--   3. Depreciation curves over time
--   4. Source health monitoring (detect when a scraper degrades)
--
-- Separate from normalized_listings (analysis-focused) and
-- market_price_stats_history (aggregated snapshots).
-- ═══════════════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS price_observations (
    id                SERIAL PRIMARY KEY,

    -- Vehicle identity
    model_id          INTEGER REFERENCES vehicle_models(id),
    generation_id     INTEGER REFERENCES generations(id),
    vehicle_year      INTEGER,
    km                INTEGER,
    price             INTEGER NOT NULL CHECK (price BETWEEN 500 AND 500000),
    fuel_type         VARCHAR(30),

    -- Seller context
    seller_type       VARCHAR(20) DEFAULT 'desconhecido',   -- privado | stand | desconhecido

    -- Source provenance (the key differentiator)
    source_type       VARCHAR(20) NOT NULL,                 -- marketplace | dealer | private | unknown
    source_domain     VARCHAR(100),                         -- standvirtual.com | soauto.pt | custojusto.pt
    source_url        TEXT,                                 -- full listing URL

    -- Extraction quality (detect degradation)
    extraction_method VARCHAR(30),                          -- next_data | generic | fallback | fetch_failed
    data_quality      REAL CHECK (data_quality BETWEEN 0 AND 1),  -- 0.0–1.0

    -- How this observation was collected
    observation_type  VARCHAR(20) NOT NULL DEFAULT 'user_analysis',  -- batch | user_analysis

    -- Timestamps
    observed_at       TIMESTAMPTZ DEFAULT now(),

    -- Prevent exact URL duplicates (same listing can be re-observed with UPDATE)
    UNIQUE (source_url)
);

-- Primary query pattern: "what's the price range for this model/year?"
CREATE INDEX IF NOT EXISTS idx_po_model_year
    ON price_observations(model_id, vehicle_year);

-- Time-series queries: "how has pricing changed over the last 3 months?"
CREATE INDEX IF NOT EXISTS idx_po_observed
    ON price_observations(observed_at DESC);

-- Source health: "how many observations per source domain this week?"
CREATE INDEX IF NOT EXISTS idx_po_source_domain
    ON price_observations(source_domain, observed_at DESC);

-- Generation-level aggregation (feeds into market_price_stats_history)
CREATE INDEX IF NOT EXISTS idx_po_generation
    ON price_observations(generation_id, vehicle_year);

-- Source type analysis: "marketplace vs dealer price comparison"
CREATE INDEX IF NOT EXISTS idx_po_source_type
    ON price_observations(source_type, model_id);
