"""
Market Aggregator — computes p10/p50/p90 + MAD from normalized_listings.

Run after market_scraper_runner to turn raw listings into price statistics.

For each (generation_id, seller_type, vehicle_year) group with >= 3 listings:
  - Computes p10, p50, p90, mean, MAD (Median Absolute Deviation)
  - Writes snapshot to market_price_stats_history
  - Denormalises latest p50 + band to generations table

MAD-based anomaly detection:
  z_mad = (price - p50) / (1.4826 * MAD)
  |z_mad| > 3.5 → flag as outlier (excluded from statistics but kept in DB)
"""

import logging
from datetime import date
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import text

try:
    import numpy as np
    _HAS_NUMPY = True
except ImportError:
    _HAS_NUMPY = False

logger = logging.getLogger(__name__)

MIN_SAMPLE_SIZE = 3    # minimum listings for a statistics row
MAD_OUTLIER_Z   = 3.5  # z-score threshold for MAD outlier removal


def _percentile(values: list[float], p: float) -> int:
    """Compute percentile without numpy (fallback)."""
    if not values:
        return 0
    s = sorted(values)
    n = len(s)
    idx = (p / 100.0) * (n - 1)
    lo, hi = int(idx), min(int(idx) + 1, n - 1)
    return int(s[lo] + (idx - lo) * (s[hi] - s[lo]))


def _median(values: list[float]) -> float:
    s = sorted(values)
    n = len(s)
    mid = n // 2
    return (s[mid - 1] + s[mid]) / 2.0 if n % 2 == 0 else s[mid]


def _compute_stats(prices: list[float]) -> Optional[dict]:
    """
    Compute p10/p50/p90/mean/MAD for a list of prices.
    Removes MAD outliers first (if >= 5 samples).
    Returns None if fewer than MIN_SAMPLE_SIZE samples after filtering.
    """
    if len(prices) < MIN_SAMPLE_SIZE:
        return None

    if _HAS_NUMPY:
        arr = np.array(prices, dtype=float)
        p50 = float(np.median(arr))
        mad = float(np.median(np.abs(arr - p50)))

        # Remove outliers if we have enough data
        if len(arr) >= 5 and mad > 0:
            z_scores = np.abs(arr - p50) / (1.4826 * mad)
            arr = arr[z_scores <= MAD_OUTLIER_Z]

        if len(arr) < MIN_SAMPLE_SIZE:
            return None

        return {
            "p10":  int(np.percentile(arr, 10)),
            "p50":  int(np.median(arr)),
            "p90":  int(np.percentile(arr, 90)),
            "mean": int(np.mean(arr)),
            "mad":  int(np.median(np.abs(arr - np.median(arr)))),
            "n":    len(arr),
        }
    else:
        # Pure-Python fallback
        p50_raw = _median(prices)
        mad_raw = _median([abs(p - p50_raw) for p in prices])

        filtered = prices
        if len(prices) >= 5 and mad_raw > 0:
            filtered = [p for p in prices
                        if abs(p - p50_raw) / (1.4826 * mad_raw) <= MAD_OUTLIER_Z]

        if len(filtered) < MIN_SAMPLE_SIZE:
            return None

        return {
            "p10":  _percentile(filtered, 10),
            "p50":  int(_median(filtered)),
            "p90":  _percentile(filtered, 90),
            "mean": int(sum(filtered) / len(filtered)),
            "mad":  int(_median([abs(p - _median(filtered)) for p in filtered])),
            "n":    len(filtered),
        }


def run_aggregation(db: Session) -> dict:
    """
    Aggregate normalized_listings into market_price_stats_history.
    Denormalises latest p50 + band to generations table.
    Returns stats dict.
    """
    stats = {"groups_processed": 0, "groups_skipped": 0, "generations_updated": 0, "errors": 0}
    observed_month = date.today().replace(day=1)

    # Load all normalized listings that have price + generation_id
    rows = db.execute(text("""
        SELECT
            nl.generation_id,
            nl.year,
            nl.seller_type,
            nl.price
        FROM normalized_listings nl
        WHERE nl.price IS NOT NULL
          AND nl.price BETWEEN 500 AND 500000
          AND nl.generation_id IS NOT NULL
        ORDER BY nl.generation_id, nl.seller_type, nl.year
    """)).fetchall()

    # Group by (generation_id, seller_type, year)
    groups: dict[tuple, list[float]] = {}
    for r in rows:
        key = (r[0], r[2] or "desconhecido", r[1] or 0)
        groups.setdefault(key, []).append(float(r[3]))

    # Also group by (generation_id, seller_type) ignoring year — for sparse data
    gen_seller_groups: dict[tuple, list[float]] = {}
    for (gen_id, seller, year), prices in groups.items():
        gkey = (gen_id, seller)
        gen_seller_groups.setdefault(gkey, []).extend(prices)

    # Clear existing rows for this month before re-inserting (NULL engine_id prevents ON CONFLICT)
    try:
        db.execute(text("""
            DELETE FROM market_price_stats_history
            WHERE observed_month = :month AND engine_id IS NULL
        """), {"month": observed_month})
        db.commit()
    except Exception as e:
        logger.error(f"Pre-delete error: {e}")
        db.rollback()

    # Write per-year rows
    for (gen_id, seller_type, year), prices in groups.items():
        if year == 0:
            continue
        result = _compute_stats(prices)
        if not result:
            stats["groups_skipped"] += 1
            continue
        try:
            db.execute(text("""
                INSERT INTO market_price_stats_history
                    (generation_id, price_context, vehicle_year, observed_month,
                     p10_price, p50_price, p90_price, mean_price, sample_count,
                     mad_price, sources)
                VALUES
                    (:gen_id, :ctx, :year, :month,
                     :p10, :p50, :p90, :mean, :n,
                     :mad, '["standvirtual"]'::jsonb)
            """), {
                "gen_id": gen_id,
                "ctx":    seller_type,
                "year":   year,
                "month":  observed_month,
                "p10":    result["p10"],
                "p50":    result["p50"],
                "p90":    result["p90"],
                "mean":   result["mean"],
                "n":      result["n"],
                "mad":    result["mad"],
            })
            stats["groups_processed"] += 1
        except Exception as e:
            logger.error(f"History insert error gen={gen_id} {seller_type} {year}: {e}")
            stats["errors"] += 1

    db.commit()

    # Denormalise: update generations table with median p50 + band across all contexts
    try:
        db.execute(text("""
            UPDATE generations g
            SET
                market_value_p50   = sub.p50,
                market_value_band  = sub.band,
                market_value_as_of = :month
            FROM (
                SELECT
                    generation_id,
                    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY p50_price)::INTEGER AS p50,
                    jsonb_build_object(
                        'p10', MIN(p10_price),
                        'p90', MAX(p90_price),
                        'sample_count', SUM(sample_count)
                    ) AS band
                FROM market_price_stats_history
                WHERE observed_month = :month
                  AND sample_count >= :min_n
                GROUP BY generation_id
            ) sub
            WHERE g.id = sub.generation_id
        """), {"month": observed_month, "min_n": MIN_SAMPLE_SIZE})

        db.commit()

        updated = db.execute(text("""
            SELECT COUNT(*) FROM generations
            WHERE market_value_as_of = :month
        """), {"month": observed_month}).scalar()
        stats["generations_updated"] = updated or 0

    except Exception as e:
        logger.error(f"Denormalisation error: {e}")
        db.rollback()
        stats["errors"] += 1

    logger.info(f"Market aggregation complete: {stats}")
    return stats


def get_price_band_for_listing(
    db: Session,
    generation_id: int,
    vehicle_year: int,
    seller_type: str = "desconhecido",
) -> Optional[dict]:
    """
    Get the most recent price band for a specific (generation, year) combination.
    Used by ad_analysis_service for real-time deal scoring.
    Returns None if no market data available.

    MAD-based anomaly flag for a listing price:
      z_mad > 3.5  → 'suspeito_barato' (price < p50) or 'caro' (price > p50)
    """
    row = db.execute(text("""
        SELECT p10_price, p50_price, p90_price, mad_price, sample_count, observed_month
        FROM market_price_stats_history
        WHERE generation_id = :gen_id
          AND (price_context = :ctx OR price_context = 'desconhecido')
          AND (vehicle_year = :year OR vehicle_year = 0)
          AND sample_count >= :min_n
        ORDER BY
            CASE WHEN vehicle_year = :year THEN 0 ELSE 1 END,
            CASE WHEN price_context = :ctx  THEN 0 ELSE 1 END,
            observed_month DESC
        LIMIT 1
    """), {
        "gen_id": generation_id,
        "ctx":    seller_type,
        "year":   vehicle_year,
        "min_n":  MIN_SAMPLE_SIZE,
    }).mappings().fetchone()

    if not row:
        return None

    return {
        "p10":          row["p10_price"],
        "p50":          row["p50_price"],
        "p90":          row["p90_price"],
        "mad":          row["mad_price"],
        "sample_count": row["sample_count"],
        "as_of":        str(row["observed_month"]),
    }


def flag_price_anomaly(price: int, band: dict) -> str:
    """
    Return anomaly flag for a listing price given a market band.
    Uses MAD-based z-score for robust outlier detection.
    """
    p50 = band.get("p50")
    mad = band.get("mad")
    if not p50 or not mad or mad == 0:
        # Fall back to simple percentile check
        if band.get("p10") and price < band["p10"] * 0.85:
            return "suspeito_barato"
        if band.get("p90") and price > band["p90"] * 1.15:
            return "caro"
        return "normal"

    z = abs(price - p50) / (1.4826 * mad)
    if z > MAD_OUTLIER_Z:
        return "suspeito_barato" if price < p50 else "caro"
    return "normal"
