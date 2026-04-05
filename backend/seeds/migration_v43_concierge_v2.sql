-- Caractr migration v4.3 — Concierge v2 schema
-- Adds consent flags and feedback_tags, removes tier dependency

ALTER TABLE concierge_requests
  ADD COLUMN IF NOT EXISTS consent_caractr BOOLEAN NOT NULL DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS consent_dealer  BOOLEAN NOT NULL DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS feedback_tags   JSONB   NOT NULL DEFAULT '[]'::jsonb;

-- Index for dealer consent queries (lead gen pipeline)
CREATE INDEX IF NOT EXISTS idx_concierge_consent_dealer
  ON concierge_requests (consent_dealer)
  WHERE consent_dealer = TRUE;

COMMENT ON COLUMN concierge_requests.consent_caractr IS 'User consented to Caractr contact — required';
COMMENT ON COLUMN concierge_requests.consent_dealer  IS 'User consented to dealer partner referral — optional, lead gen';
COMMENT ON COLUMN concierge_requests.feedback_tags   IS 'Quick feedback reasons from results page (e.g. wrong brand, too sporty)';
