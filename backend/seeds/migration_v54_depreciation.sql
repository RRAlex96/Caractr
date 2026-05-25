-- ═══════════════════════════════════════════════════════════════════════════
-- Migration v54: Depreciation curve columns on generations
-- ═══════════════════════════════════════════════════════════════════════════
--
-- Adds depreciation tracking to each generation so the analysis pipeline
-- can predict value loss and flag "ages well" vs "loses value fast" cars.
--
-- depreciation_pct_year:  annual depreciation rate (e.g., 0.12 = 12%/year)
-- depreciation_curve:     JSONB with per-age price points for charting
-- depreciation_as_of:     when this was last computed
-- ═══════════════════════════════════════════════════════════════════════════

ALTER TABLE generations
    ADD COLUMN IF NOT EXISTS depreciation_pct_year  NUMERIC(5,4),   -- 0.0000–1.0000
    ADD COLUMN IF NOT EXISTS depreciation_curve     JSONB NOT NULL DEFAULT '[]'::jsonb,
    ADD COLUMN IF NOT EXISTS depreciation_as_of     DATE;
