-- Caractr v4.4 — Add anon_id to analytics_events
-- The frontend generates a persistent anonymous ID (localStorage) and sends it
-- with every event. This column allows linking pre-wizard events to post-wizard
-- sessions for the same anonymous user across visits.

ALTER TABLE analytics_events ADD COLUMN IF NOT EXISTS anon_id UUID;
CREATE INDEX IF NOT EXISTS idx_analytics_anon_id ON analytics_events (anon_id);
