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
