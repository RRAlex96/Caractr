"""
Reliability Runner — orchestrates the weekly Bayesian scoring job.

For each (generation, engine) pair:
1. Load evidence rows from reliability_evidence
2. Load engine fuel_type and estimate age_years from generation.year_start
3. Run bayesian_reliability.compute_reliability_score()
4. Write result to reliability_scores_history
5. Denormalise latest score+CI to generations table (fast product reads)
"""

import json
import logging
from datetime import date, datetime

from sqlalchemy.orm import Session
from sqlalchemy import text

from app.services.bayesian_reliability import compute_reliability_score, scores_are_valid

logger = logging.getLogger(__name__)


def run_reliability_scorer(db: Session) -> dict:
    """
    Run the Bayesian reliability scorer for all generations.
    Returns stats dict: {processed, updated, skipped_invalid, errors}
    """
    stats = {"processed": 0, "updated": 0, "skipped_invalid": 0, "errors": 0}
    as_of_month = date.today().replace(day=1)
    current_year = date.today().year

    # Load all generations with their engine fuel types
    gen_rows = db.execute(text("""
        SELECT DISTINCT
            g.id          AS generation_id,
            g.year_start,
            g.year_end,
            e.id          AS engine_id,
            e.fuel_type
        FROM generations g
        JOIN vehicle_models vm ON g.model_id = vm.id
        LEFT JOIN engines e ON e.model_id = vm.id
        ORDER BY g.id, e.id
    """)).mappings().fetchall()

    for row in gen_rows:
        gen_id   = row["generation_id"]
        eng_id   = row["engine_id"]  # may be None if no engine linked
        fuel     = row["fuel_type"]

        # Estimate age from midpoint of generation years
        year_start = row["year_start"] or 2015
        year_end   = row["year_end"]   or current_year
        mid_year   = (year_start + year_end) // 2
        age_years  = max(0, current_year - mid_year)

        try:
            # Load evidence for this generation (optionally filtered by engine)
            evidence_rows = db.execute(text("""
                SELECT fail_eff, succ_eff, weight, source
                FROM reliability_evidence
                WHERE generation_id = :gid
                  AND (:eng_id IS NULL OR engine_id IS NULL OR engine_id = :eng_id)
            """), {"gid": gen_id, "eng_id": eng_id}).mappings().fetchall()

            evidence = [dict(r) for r in evidence_rows]
            result = compute_reliability_score(evidence, fuel_type=fuel, age_years=age_years)

            if not scores_are_valid(result):
                logger.warning(f"Invalid score for gen={gen_id} eng={eng_id}: {result}")
                stats["skipped_invalid"] += 1
                continue

            # Write to history
            db.execute(text("""
                INSERT INTO reliability_scores_history
                    (generation_id, engine_id, as_of_month,
                     alpha, beta_param, p_mean, score_1_10,
                     ci_low_1_10, ci_high_1_10,
                     evidence_count, data_quality, sources)
                VALUES
                    (:gen_id, :eng_id, :month,
                     :alpha, :beta_param, :p_mean, :score,
                     :ci_low, :ci_high,
                     :ev_count, :quality, CAST(:sources AS jsonb))
                ON CONFLICT (generation_id, engine_id, as_of_month)
                DO UPDATE SET
                    alpha          = EXCLUDED.alpha,
                    beta_param     = EXCLUDED.beta_param,
                    p_mean         = EXCLUDED.p_mean,
                    score_1_10     = EXCLUDED.score_1_10,
                    ci_low_1_10    = EXCLUDED.ci_low_1_10,
                    ci_high_1_10   = EXCLUDED.ci_high_1_10,
                    evidence_count = EXCLUDED.evidence_count,
                    data_quality   = EXCLUDED.data_quality,
                    sources        = EXCLUDED.sources,
                    created_at     = now()
            """), {
                "gen_id":    gen_id,
                "eng_id":    eng_id,
                "month":     as_of_month,
                "alpha":     result["alpha"],
                "beta_param": result["beta_param"],
                "p_mean":    result["p_mean"],
                "score":     result["score_1_10"],
                "ci_low":    result["ci_low_1_10"],
                "ci_high":   result["ci_high_1_10"],
                "ev_count":  result["evidence_count"],
                "quality":   result["data_quality"],
                "sources":   json.dumps(result["sources"]),
            })

            stats["processed"] += 1

        except Exception as e:
            logger.error(f"Scorer error gen={gen_id} eng={eng_id}: {e}")
            stats["errors"] += 1

    # Denormalise latest score per generation onto generations table
    # (Use the score averaged/best across engines — take the mean for simplicity)
    try:
        db.execute(text("""
            UPDATE generations g
            SET
                reliability_score     = sub.score,
                reliability_ci_low    = sub.ci_low,
                reliability_ci_high   = sub.ci_high,
                reliability_data_quality = sub.quality,
                reliability_sources   = sub.sources
            FROM (
                SELECT
                    generation_id,
                    ROUND(AVG(score_1_10)::numeric, 2)  AS score,
                    ROUND(MIN(ci_low_1_10)::numeric, 2) AS ci_low,
                    ROUND(MAX(ci_high_1_10)::numeric, 2) AS ci_high,
                    MODE() WITHIN GROUP (ORDER BY data_quality) AS quality,
                    to_jsonb(array_remove(array_agg(DISTINCT src), NULL)) AS sources
                FROM reliability_scores_history rsh
                LEFT JOIN LATERAL jsonb_array_elements_text(rsh.sources) AS src ON true
                WHERE as_of_month = :month
                GROUP BY generation_id
            ) sub
            WHERE g.id = sub.generation_id
              -- A prior-only result (no real evidence) must never overwrite a
              -- real estimate already on the generation (e.g. curator research).
              -- Real evidence (recalls, complaints) always takes precedence.
              AND (
                    sub.quality <> 'prior_only'
                 OR g.reliability_score IS NULL
                 OR COALESCE(g.reliability_data_quality, 'prior_only') = 'prior_only'
              )
        """), {"month": as_of_month})

        db.commit()
        stats["updated"] = stats["processed"]
        logger.info(f"Reliability runner complete: {stats}")

    except Exception as e:
        logger.error(f"Denormalisation error: {e}")
        db.rollback()
        stats["errors"] += 1

    return stats
