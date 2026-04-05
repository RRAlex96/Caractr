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
