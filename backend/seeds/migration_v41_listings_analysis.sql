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
