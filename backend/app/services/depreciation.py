"""
Depreciation Curve Engine — compute annual value loss per generation.

Strategy: cross-sectional depreciation from price_observations.
Instead of waiting years for time-series data, compare prices of the same
model across different vehicle_year values observed at the same point in time.

Example:
  VW Golf VIII (2020-2024), observed today:
    2024 model → p50 = 25000
    2023 model → p50 = 22500 (−10%)
    2022 model → p50 = 19500 (−13%)
    2021 model → p50 = 17000 (−13%)
  → weighted avg annual depreciation ≈ 12%/year

Output per generation:
  - depreciation_pct_year: single annual rate (e.g. 0.12)
  - depreciation_curve: [{age: 1, pct_of_new: 0.90}, {age: 2, pct_of_new: 0.78}, ...]

Run as part of the aggregation pipeline after market stats are computed.
"""

import json
import logging
from datetime import date
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import text

logger = logging.getLogger(__name__)

MIN_YEAR_POINTS = 3    # registration years with a price, per generation
MIN_SAMPLES     = 5    # listings behind one year's median
MIN_LISTINGS    = 40   # listings behind the whole curve
MIN_RATE, MAX_RATE = 0.03, 0.25   # a plausible yearly loss; outside it, no figure
MAX_RATE_ERROR  = 0.03  # standard error of the yearly rate the fit may have
MAX_OBSERVATION_AGE_DAYS = 60
# "Holds its value" / "loses value fast" are said of about one generation in
# seven each. On the snapshot of 2026-11-13 (154 generations with a rate) the
# rates run from 3.6% to 13.3% a year, median 7.5%, 15th and 85th percentiles
# 5.6% and 10.2%. The old cut-offs (under 8%, over 15%) called 58% of
# generations value-holders and none fast losers.
HOLDS_VALUE_BELOW = 0.055
LOSES_FAST_ABOVE = 0.10


def _compute_annual_depreciation(year_prices: list[tuple]) -> Optional[dict]:
    """
    Given [(vehicle_year, median_price[, listings]), ...], the yearly rate at
    which the price falls with the car's age, and the curve of medians.

    The rate is the slope of log(price) on registration year, each year
    weighted by the listings behind its median. It used to be an average of
    each year's loss against the newest year alone, so one thin or unusual
    newest year (three listings of a top trim) set the rate for the whole
    generation, and rates of 0.3% a year were stored.

    No figure rather than a weak one. Returns None when there are fewer than
    MIN_YEAR_POINTS years or MIN_LISTINGS listings, when the fit is loose
    (standard error of the rate above MAX_RATE_ERROR), or when the rate falls
    outside MIN_RATE–MAX_RATE: an old generation whose prices have flattened,
    or a mix of versions that changed along the years, is not a depreciation
    curve.

    Returns {"pct_year": 0.12, "curve": [{"age", "pct_of_new", "year", "p50"}, ...]}.
    """
    import math

    points = [(int(t[0]), float(t[1]), float(t[2]) if len(t) > 2 and t[2] else 1.0)
              for t in year_prices if t[1] and t[1] > 0]
    if len(points) < MIN_YEAR_POINTS:
        return None
    weighted = any(len(t) > 2 for t in year_prices)
    total = sum(w for _, _, w in points)
    if weighted and total < MIN_LISTINGS:
        return None

    # Weighted least squares of log(price) on year.
    mean_x = sum(w * x for x, _, w in points) / total
    mean_y = sum(w * math.log(y) for _, y, w in points) / total
    sxx = sum(w * (x - mean_x) ** 2 for x, _, w in points)
    if sxx <= 0:
        return None
    slope = sum(w * (x - mean_x) * (math.log(y) - mean_y) for x, y, w in points) / sxx
    residual = sum(w * (math.log(y) - mean_y - slope * (x - mean_x)) ** 2 for x, y, w in points)
    dof = len(points) - 2
    slope_error = math.sqrt(residual / dof / sxx) if dof > 0 else float("inf")

    rate = 1 - math.exp(-slope)          # a year older is worth this much less
    if not (MIN_RATE <= rate <= MAX_RATE) or slope_error > MAX_RATE_ERROR:
        return None

    newest_first = sorted(points, key=lambda t: -t[0])
    newest_year, newest_price, _ = newest_first[0]
    curve = [{"age": newest_year - year, "pct_of_new": round(price / newest_price, 4),
              "year": year, "p50": int(price)} for year, price, _ in newest_first]
    return {"pct_year": round(rate, 4), "curve": curve}


def run_depreciation_curves(db: Session) -> dict:
    """
    Compute depreciation curves for all generations with sufficient price data.
    Updates the generations table with depreciation_pct_year, depreciation_curve.

    Data source: price_observations (multi-source), grouped by generation + vehicle_year.
    Falls back to market_price_stats_history if price_observations is empty.

    Returns stats dict.
    """
    stats = {
        "generations_computed": 0,
        "generations_skipped": 0,
        "avg_depreciation_pct": None,
    }
    today = date.today()
    all_rates: list[float] = []

    # ── 1. Get median prices per (generation_id, vehicle_year) from price_observations
    gen_year_prices: dict[int, list[tuple[int, float]]] = {}

    try:
        rows = db.execute(text("""
            SELECT
                generation_id,
                vehicle_year,
                COUNT(*) AS n,
                PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY price) AS p50
            FROM price_observations
            WHERE generation_id IS NOT NULL
              AND vehicle_year IS NOT NULL
              AND price BETWEEN 1001 AND 500000
              AND observed_at > now() - make_interval(days => :max_age)
            GROUP BY generation_id, vehicle_year
            HAVING COUNT(*) >= :min_n
            ORDER BY generation_id, vehicle_year DESC
        """), {"min_n": MIN_SAMPLES, "max_age": MAX_OBSERVATION_AGE_DAYS}).fetchall()

        for r in rows:
            gen_id = r[0]
            gen_year_prices.setdefault(gen_id, []).append((r[1], float(r[3]), int(r[2])))
    except Exception as e:
        logger.warning(f"price_observations query failed: {e}")
        db.rollback()

    # ── 2. Fallback: use market_price_stats_history for generations not covered
    covered_gens = set(gen_year_prices.keys())

    try:
        fallback_rows = db.execute(text("""
            SELECT
                generation_id,
                vehicle_year,
                p50_price,
                sample_count
            FROM market_price_stats_history
            WHERE generation_id IS NOT NULL
              AND vehicle_year IS NOT NULL
              AND vehicle_year > 0
              AND p50_price IS NOT NULL
              AND sample_count >= :min_n
              AND price_context = 'todos'
              AND observed_month = (SELECT MAX(observed_month) FROM market_price_stats_history)
            ORDER BY generation_id, vehicle_year DESC
        """), {"min_n": MIN_SAMPLES}).fetchall()

        for r in fallback_rows:
            gen_id = r[0]
            if gen_id in covered_gens:
                continue
            gen_year_prices.setdefault(gen_id, []).append((r[1], float(r[2]), int(r[3])))
    except Exception as e:
        logger.warning(f"market_price_stats_history fallback failed: {e}")
        db.rollback()

    # ── 3. Compute depreciation for each generation
    computed: set = set()
    for gen_id, year_prices in gen_year_prices.items():
        result = _compute_annual_depreciation(year_prices)

        if not result:
            stats["generations_skipped"] += 1
            continue
        computed.add(gen_id)

        try:
            db.execute(text("""
                UPDATE generations
                SET depreciation_pct_year = :pct,
                    depreciation_curve    = CAST(:curve AS jsonb),
                    depreciation_as_of    = :as_of
                WHERE id = :gen_id
            """), {
                "gen_id": gen_id,
                "pct":    result["pct_year"],
                "curve":  json.dumps(result["curve"]),
                "as_of":  today,
            })
            stats["generations_computed"] += 1
            all_rates.append(result["pct_year"])
        except Exception as e:
            logger.error(f"Depreciation update error gen={gen_id}: {e}")
            db.rollback()

    # A figure this run could not confirm is removed, not left to age.
    try:
        stale = db.execute(text("""
            UPDATE generations
            SET depreciation_pct_year = NULL, depreciation_curve = '[]'::jsonb, depreciation_as_of = NULL
            WHERE depreciation_pct_year IS NOT NULL AND NOT (id = ANY(:kept))
        """), {"kept": sorted(computed)}).rowcount
        stats["generations_cleared"] = stale
    except Exception as e:
        logger.error(f"Depreciation clean-up error: {e}")
        db.rollback()

    db.commit()

    if all_rates:
        stats["avg_depreciation_pct"] = round(sum(all_rates) / len(all_rates), 4)

    logger.info(f"Depreciation curves complete: {stats}")
    return stats


def get_depreciation_for_generation(db: Session, generation_id: int) -> Optional[dict]:
    """
    Get pre-computed depreciation data for a specific generation.
    Returns None if no depreciation data available.
    """
    row = db.execute(text("""
        SELECT depreciation_pct_year, depreciation_curve, depreciation_as_of
        FROM generations
        WHERE id = :gen_id
          AND depreciation_pct_year IS NOT NULL
    """), {"gen_id": generation_id}).mappings().fetchone()

    if not row:
        return None

    curve = row["depreciation_curve"]
    if isinstance(curve, str):
        try:
            curve = json.loads(curve)
        except Exception:
            curve = []

    pct = float(row["depreciation_pct_year"])

    return {
        "annual_pct": pct,
        "annual_pct_label": f"{pct * 100:.1f}%/ano",
        "holds_value": pct < HOLDS_VALUE_BELOW,
        "loses_fast": pct > LOSES_FAST_ABOVE,
        "curve": curve,
        "as_of": str(row["depreciation_as_of"]) if row["depreciation_as_of"] else None,
    }


def estimate_future_value(
    current_price: int,
    annual_depreciation: float,
    years: int = 3,
) -> list[dict]:
    """
    Project future value based on current price and annual depreciation rate.
    Returns [{year: 1, value: 22000, pct_of_current: 0.88}, ...]
    """
    projections = []
    for y in range(1, years + 1):
        value = int(current_price * ((1 - annual_depreciation) ** y))
        projections.append({
            "year": y,
            "value": value,
            "pct_of_current": round(value / current_price, 4) if current_price > 0 else 0,
            "loss": current_price - value,
        })
    return projections
