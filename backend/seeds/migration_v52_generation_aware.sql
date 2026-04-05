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
