"""
Market Aggregator — computes p10/p50/p90 + MAD from price observations.

Primary source: price_observations table (multi-source, richer data).
Fallback: normalized_listings for generations not covered by observations.

Run after market_scraper_runner to turn raw data into price statistics.

For each (generation_id, price_context, vehicle_year) group with >= 3 data points:
  - Computes p10, p50, p90, mean, MAD (Median Absolute Deviation)
  - Writes snapshot to market_price_stats_history
  - Denormalises latest p50 + band to generations table

MAD-based anomaly detection:
  z_mad = (price - p50) / (1.4826 * MAD)
  |z_mad| > 3.5 → flag as outlier (excluded from statistics but kept in DB)
"""

import json
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
MIN_PUBLISH_SAMPLE = 6  # clean listings needed before a fresh price replaces market_price_stats
MAD_OUTLIER_Z   = 3.5  # z-score threshold for MAD outlier removal
# Only listings seen this recently count: a price is what the car is listed at
# now, and price_observations keeps a listing's row after it has sold.
MAX_OBSERVATION_AGE_DAYS = 60
# An aggregated price nothing has refreshed for this long is removed.
MAX_PRICE_AGE_DAYS = 75

# Map seller_type → price_context (the CHECK constraint on market_price_stats_history)
_SELLER_TO_CONTEXT = {
    "particular": "particular",
    "privado":    "particular",
    "stand":      "stand",
    "profissional": "stand",
    "importacao": "importacao",
}


def _map_price_context(seller_type: str) -> str:
    """Map a raw seller_type to a valid price_context enum value."""
    return _SELLER_TO_CONTEXT.get((seller_type or "").lower(), "todos")


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
    Aggregate price data into market_price_stats_history.

    Data sources (merged, deduplicated by source_url):
      1. price_observations — primary, multi-source (SV + OLX + CJ + dealer + user analyses)
      2. normalized_listings — fallback for generations not covered by observations

    Denormalises latest p50 + band to generations table.
    Returns stats dict.
    """
    stats = {
        "groups_processed": 0, "groups_skipped": 0,
        "generations_updated": 0, "errors": 0,
        "observations_used": 0, "normalized_fallback_used": 0,
        "source_domains": [],
    }
    observed_month = date.today().replace(day=1)

    # ── 1. Load price observations (primary, multi-source) ─────────────────
    # Structure: (generation_id, vehicle_year, seller_type, price, source_domain)
    po_rows = []
    try:
        po_rows = db.execute(text("""
            SELECT
                generation_id,
                vehicle_year,
                seller_type,
                price,
                source_domain
            FROM price_observations
            WHERE price IS NOT NULL
              AND price BETWEEN 500 AND 500000
              AND generation_id IS NOT NULL
              AND observed_at > now() - make_interval(days => :max_age)
            ORDER BY generation_id, vehicle_year
        """), {"max_age": MAX_OBSERVATION_AGE_DAYS}).fetchall()
        stats["observations_used"] = len(po_rows)
    except Exception as e:
        logger.warning(f"price_observations query failed (table may not exist): {e}")
        db.rollback()

    # ── 2. normalized_listings fallback — retired ──────────────────────────
    # normalized_listings is now the ad-analysis cache (no generation_id), and
    # both batch scrapes and user analyses already land in price_observations,
    # so there is nothing left for a fallback to add. Querying the old column
    # crashed every aggregation run.
    nl_rows: list = []

    # ── 3. Group by (generation_id, price_context, year) ──────────────────
    # Track sources per group for provenance
    groups: dict[tuple, list[float]] = {}
    group_sources: dict[tuple, set[str]] = {}
    covered_generations: set[int] = set()

    # Primary: price_observations
    for r in po_rows:
        gen_id = r[0]
        year = r[1] or 0
        ctx = _map_price_context(r[2])
        price = float(r[3])
        domain = r[4] or "unknown"

        key = (gen_id, ctx, year)
        groups.setdefault(key, []).append(price)
        group_sources.setdefault(key, set()).add(domain)
        covered_generations.add(gen_id)

        # Also add to the "todos" context for combined stats
        if ctx != "todos":
            todos_key = (gen_id, "todos", year)
            groups.setdefault(todos_key, []).append(price)
            group_sources.setdefault(todos_key, set()).add(domain)

    # Fallback: normalized_listings for generations NOT in price_observations
    fallback_count = 0
    for r in nl_rows:
        gen_id = r[0]
        if gen_id in covered_generations:
            continue  # already have richer data from observations
        year = r[1] or 0
        ctx = _map_price_context(r[2])
        price = float(r[3])

        key = (gen_id, ctx, year)
        groups.setdefault(key, []).append(price)
        group_sources.setdefault(key, set()).add("normalized_listings")
        fallback_count += 1

        if ctx != "todos":
            todos_key = (gen_id, "todos", year)
            groups.setdefault(todos_key, []).append(price)
            group_sources.setdefault(todos_key, set()).add("normalized_listings")

    stats["normalized_fallback_used"] = fallback_count

    # Track all unique source domains across the aggregation
    all_domains: set[str] = set()
    for sources in group_sources.values():
        all_domains.update(sources)
    stats["source_domains"] = sorted(all_domains)

    # ── 4. Clear existing rows for this month before re-inserting ──────────
    try:
        db.execute(text("""
            DELETE FROM market_price_stats_history
            WHERE observed_month = :month AND engine_id IS NULL
        """), {"month": observed_month})
        db.commit()
    except Exception as e:
        logger.error(f"Pre-delete error: {e}")
        db.rollback()

    # ── 5. Write per-(generation, context, year) stats ────────────────────
    for (gen_id, price_context, year), prices in groups.items():
        if year == 0:
            continue
        result = _compute_stats(prices)
        if not result:
            stats["groups_skipped"] += 1
            continue
        try:
            sources_list = sorted(group_sources.get((gen_id, price_context, year), set()))
            db.execute(text("""
                INSERT INTO market_price_stats_history
                    (generation_id, price_context, vehicle_year, observed_month,
                     p10_price, p50_price, p90_price, mean_price, sample_count,
                     mad_price, sources)
                VALUES
                    (:gen_id, :ctx, :year, :month,
                     :p10, :p50, :p90, :mean, :n,
                     :mad, CAST(:sources AS jsonb))
            """), {
                "gen_id":  gen_id,
                "ctx":     price_context,
                "year":    year,
                "month":   observed_month,
                "p10":     result["p10"],
                "p50":     result["p50"],
                "p90":     result["p90"],
                "mean":    result["mean"],
                "n":       result["n"],
                "mad":     result["mad"],
                "sources": json.dumps(sources_list),
            })
            stats["groups_processed"] += 1
        except Exception as e:
            logger.error(f"History insert error gen={gen_id} {price_context} {year}: {e}")
            stats["errors"] += 1

    db.commit()

    # ── 6. Denormalise: update generations with median p50 + band ─────────
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
                  -- every seller type together; the per-seller rows repeat
                  -- the same listings
                  AND price_context = 'todos'
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

    # ── 7. Refresh market_price_stats from price_observations ───────────────
    # The ad_analysis_service reads market_price_stats for price deltas.
    # This keeps it in sync with the multi-source price_observations flywheel.
    try:
        mps_result = _refresh_market_price_stats(db)
        stats["market_price_stats_refreshed"] = mps_result
    except Exception as e:
        logger.error(f"market_price_stats refresh error: {e}")
        stats["market_price_stats_refreshed"] = {"error": str(e)}

    logger.info(f"Market aggregation complete: {stats}")
    return stats


# A listing this much more powerful than the model's typical car of those
# years is a sports version (Golf GTI and R among Golfs): priced apart.
SPORTS_VERSION_POWER = 1.5
_POWER_WINDOW_YEARS = 2


def mainstream_prices(listings: dict) -> dict:
    """
    {(model_id, year): [prices]} from {(model_id, year): [(price, power_hp or None)]},
    without the sports versions.

    The price of a model-year is the median of what is for sale, and what is
    for sale is not the same mix every year: the 2019 Golfs on the market were
    mostly GTI and R (median 245 cv, 24 125 EUR), the 2023 ones mostly 1.0 TSI
    from rental fleets (110 cv, 19 450 EUR), so a Golf looked 24% cheaper new
    than four years old. A listing with more than SPORTS_VERSION_POWER times
    the median power of the model's listings of that year and the two either
    side is left out, when at least MIN_PUBLISH_SAMPLE listings remain; a year
    that is all sports versions keeps them. Listings that do not state their
    power stay in.
    """
    out: dict = {}
    for (model_id, year), rows in listings.items():
        powers = [hp for step in range(-_POWER_WINDOW_YEARS, _POWER_WINDOW_YEARS + 1)
                  for _price, hp in listings.get((model_id, year + step), []) if hp]
        prices = [price for price, _hp in rows]
        if len(powers) >= MIN_PUBLISH_SAMPLE:
            limit = _median(powers) * SPORTS_VERSION_POWER
            kept = [price for price, hp in rows if not hp or hp <= limit]
            if len(kept) >= MIN_PUBLISH_SAMPLE:
                prices = kept
        out[(model_id, year)] = prices
    return out


def model_year_stats(groups: dict) -> dict:
    """
    {(model_id, year): stats or None} from {(model_id, year): [prices]}.

    A year with at least MIN_PUBLISH_SAMPLE clean listings is priced on its
    own. A thinner one — a low-volume model has two or three listings in most
    years — is priced on its own listings plus those of the year before and
    the year after, and failing that of two years each side, when together
    they reach the threshold. Without this, an Audi Q5 had a price for 2011
    and 2017 and none in between, and a budget that buys a 2015 one was shown
    the 2011. A year with no listing of its own gets no row, and None is
    returned when even five years together are too few: no price is better
    than one from three listings.
    """
    out: dict = {}
    for (model_id, year), prices in groups.items():
        st = _compute_stats(prices)
        for reach in (1, 2):
            if st and st["n"] >= MIN_PUBLISH_SAMPLE:
                break
            pooled = list(prices)
            for step in range(1, reach + 1):
                pooled += groups.get((model_id, year - step), []) + groups.get((model_id, year + step), [])
            st = _compute_stats(pooled) if len(pooled) > len(prices) else st
        out[(model_id, year)] = st if st and st["n"] >= MIN_PUBLISH_SAMPLE else None
    return out


def _refresh_market_price_stats(db: Session) -> dict:
    """
    Upsert market_price_stats from price_observations aggregated by (model_id, year).
    Only updates rows where we have >= MIN_SAMPLE_SIZE observations.
    This keeps the analysis pipeline's price reference fresh.
    """
    upserted = skipped = 0
    try:
        # Robust stats, not raw AVG/MIN/MAX: a single mis-bucketed listing (a
        # 210 000 € Ferrari scraped under "Golf") used to set a Golf's price.
        # avg_price = MAD-trimmed median (the analysis' market reference),
        # min/max = trimmed p10/p90, and a fresh group must have at least
        # MIN_PUBLISH_SAMPLE clean observations before it may replace a price.
        obs = db.execute(text("""
            SELECT model_id, vehicle_year, price, engine_power_hp
            FROM price_observations
            WHERE model_id IS NOT NULL AND vehicle_year IS NOT NULL
              AND price BETWEEN 500 AND 500000
              AND observed_at > now() - make_interval(days => :max_age)
        """), {"max_age": MAX_OBSERVATION_AGE_DAYS}).fetchall()
        listings: dict[tuple, list[tuple]] = {}
        for model_id, year, price, power in obs:
            listings.setdefault((model_id, year), []).append((float(price), power))
        groups = mainstream_prices(listings)

        rows = []
        for (model_id, year), st in model_year_stats(groups).items():
            if st is None:
                skipped += 1
                continue
            rows.append((model_id, year, st["n"], st["p50"], st["p10"], st["p90"]))

        for r in rows:
            model_id, year, cnt, avg_p, min_p, max_p = r
            db.execute(text("""
                INSERT INTO market_price_stats
                    (model_id, year, avg_price, min_price, max_price,
                     sample_count, source, updated_at)
                VALUES
                    (:model_id, :year, :avg, :mn, :mx,
                     :cnt, 'aggregated', NOW())
                ON CONFLICT (model_id, year) DO UPDATE SET
                    avg_price     = EXCLUDED.avg_price,
                    min_price     = EXCLUDED.min_price,
                    max_price     = EXCLUDED.max_price,
                    sample_count  = EXCLUDED.sample_count,
                    source        = 'aggregated',
                    -- the row it replaces may be a seeded one tied to one
                    -- engine and to private sellers; this one is neither
                    engine_id     = NULL,
                    price_context = 'todos',
                    updated_at    = NOW()
            """), {
                "model_id": model_id,
                "year":     year,
                "avg":      avg_p,
                "mn":       min_p,
                "mx":       max_p,
                "cnt":      cnt,
            })
            upserted += 1

        # A model-year whose listings have thinned out below the publish
        # threshold keeps its last price for a while, then loses it.
        expired = db.execute(text("""
            DELETE FROM market_price_stats
            WHERE source = 'aggregated'
              AND updated_at < now() - make_interval(days => :max_age)
        """), {"max_age": MAX_PRICE_AGE_DAYS}).rowcount

        db.commit()
    except Exception as e:
        logger.warning(f"market_price_stats refresh failed: {e}")
        db.rollback()
        return {"error": str(e)}

    return {"upserted": upserted, "skipped_thin_or_noisy": skipped, "expired": expired}


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
