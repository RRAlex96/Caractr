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

MIN_YEAR_POINTS = 2   # need at least 2 year-price points to compute a curve
MIN_SAMPLES     = 3   # per year-bucket minimum observations


def _compute_annual_depreciation(year_prices: list[tuple[int, float]]) -> Optional[dict]:
    """
    Given [(vehicle_year, median_price), ...] sorted by year DESC,
    compute the annual depreciation rate and curve.

    Returns {
        "pct_year": 0.12,
        "curve": [{"age": 0, "pct_of_new": 1.0}, {"age": 1, "pct_of_new": 0.88}, ...]
    } or None if insufficient data.
    """
    if len(year_prices) < MIN_YEAR_POINTS:
        return None

    # Sort by year DESC (newest first)
    sorted_yp = sorted(year_prices, key=lambda x: x[0], reverse=True)
    newest_year = sorted_yp[0][0]
    newest_price = sorted_yp[0][1]

    if newest_price <= 0:
        return None

    # Build the curve: for each year, compute pct_of_newest
    curve = []
    annual_rates = []

    for year, price in sorted_yp:
        age = newest_year - year
        pct_of_new = round(price / newest_price, 4)
        curve.append({"age": age, "pct_of_new": pct_of_new, "year": year, "p50": int(price)})

        # Compute per-step annual rate (between consecutive years)
        if age > 0 and pct_of_new > 0:
            # annual rate = 1 - (pct_of_new)^(1/age)
            try:
                annual_rate = 1 - (pct_of_new ** (1.0 / age))
                if 0 < annual_rate < 0.5:  # sanity: 0-50% per year
                    annual_rates.append(annual_rate)
            except (ValueError, ZeroDivisionError):
                pass

    if not annual_rates:
        return None

    # Weighted average: favour rates computed from more recent age gaps
    # (closer years are more reliable than extrapolating from 10-year spread)
    weights = list(range(len(annual_rates), 0, -1))
    weighted_sum = sum(r * w for r, w in zip(annual_rates, weights))
    weighted_avg = weighted_sum / sum(weights)

    return {
        "pct_year": round(weighted_avg, 4),
        "curve": curve,
    }


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
              AND price BETWEEN 500 AND 500000
            GROUP BY generation_id, vehicle_year
            HAVING COUNT(*) >= :min_n
            ORDER BY generation_id, vehicle_year DESC
        """), {"min_n": MIN_SAMPLES}).fetchall()

        for r in rows:
            gen_id = r[0]
            gen_year_prices.setdefault(gen_id, []).append((r[1], float(r[3])))
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
                p50_price
            FROM market_price_stats_history
            WHERE generation_id IS NOT NULL
              AND vehicle_year IS NOT NULL
              AND vehicle_year > 0
              AND p50_price IS NOT NULL
              AND sample_count >= :min_n
            ORDER BY generation_id, vehicle_year DESC
        """), {"min_n": MIN_SAMPLES}).fetchall()

        for r in fallback_rows:
            gen_id = r[0]
            if gen_id in covered_gens:
                continue
            gen_year_prices.setdefault(gen_id, []).append((r[1], float(r[2])))
    except Exception as e:
        logger.warning(f"market_price_stats_history fallback failed: {e}")
        db.rollback()

    # ── 3. Compute depreciation for each generation
    for gen_id, year_prices in gen_year_prices.items():
        result = _compute_annual_depreciation(year_prices)

        if not result:
            stats["generations_skipped"] += 1
            continue

        try:
            db.execute(text("""
                UPDATE generations
                SET depreciation_pct_year = :pct,
                    depreciation_curve    = :curve::jsonb,
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
        "holds_value": pct < 0.08,
        "loses_fast": pct > 0.15,
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
