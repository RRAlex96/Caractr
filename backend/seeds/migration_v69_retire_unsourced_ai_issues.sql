-- Migration v6.9 — retire the known-issue rows an AI wrote without sources
--
-- 43 of the 50 rows in engine_issues were written on 2026-11-11 by the AI
-- curator with no source to check ("IA (curator · sem fontes)"): plausible
-- sentences about ten engines, none of them verifiable. Since the audit of
-- 2026-11-14 they are no longer passed to buyers or to the analysis; keeping
-- them only invites someone to show them again.
--
-- They are removed. The engines they were attached to stay (their figures
-- were checked in v65). Known faults shown to buyers come from the curated,
-- sourced list (seeds/known_engine_issues.json), which a person approves.
--
-- A copy of the removed rows is in the pre-migration backup of the database.
-- Idempotent.

BEGIN;

DELETE FROM engine_issues WHERE source LIKE 'IA (%sem fontes%';

COMMIT;

SELECT COALESCE(source, '(none)') AS source, COUNT(*) FROM engine_issues GROUP BY 1 ORDER BY 2 DESC;
