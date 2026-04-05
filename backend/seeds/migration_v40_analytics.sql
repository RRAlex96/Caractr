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
