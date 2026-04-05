-- Caractr v4.4 — RGPD schema cleanup
-- Drops undisclosed columns from concierge_requests that were never used
-- by the application and not listed in the privacy policy.
-- Also removes the unused 'tier' workflow column.

-- phone: collected in schema but not in frontend form and not disclosed in privacy policy
ALTER TABLE concierge_requests DROP COLUMN IF EXISTS phone;

-- timeline: workflow field never exposed to users
ALTER TABLE concierge_requests DROP COLUMN IF EXISTS timeline;

-- notes: free-text field never exposed to users
ALTER TABLE concierge_requests DROP COLUMN IF EXISTS notes;

-- tier: internal workflow tier, not used by current MVP
ALTER TABLE concierge_requests DROP COLUMN IF EXISTS tier;
