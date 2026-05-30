-- Caractr v5.5 — Admin notes for concierge pipeline
-- Adds an internal operator-only notes field for concierge request management.
-- This is NOT the old 'notes' column (dropped in v4.4 RGPD cleanup, which was user-facing).
-- admin_notes is internal workflow data, never exposed to end users.

ALTER TABLE concierge_requests ADD COLUMN IF NOT EXISTS admin_notes TEXT;

-- Also add 'searching' to the status workflow (existing CHECK constraint is implicit via app code)
-- No DB constraint change needed — status is VARCHAR(30), app enforces valid values.
