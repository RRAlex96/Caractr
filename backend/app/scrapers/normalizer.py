"""
Caractr — Listing Normalizer
Maps raw scraped listings to vehicle_models in the database.
Computes deal scoring metrics.
"""

from datetime import datetime, timezone
from typing import Optional
import re


# ── Model name matching ────────────────────────────────────────────────────

# Patterns to strip from raw titles before matching
TITLE_NOISE = re.compile(
    r"\b(usado|usado|ocasião|novo|km|€|\d{4})\b",
    re.IGNORECASE
)

def _normalise_name(name: str) -> str:
    """Lowercase, strip noise, normalise whitespace."""
    name = TITLE_NOISE.sub(" ", name or "")
    name = re.sub(r"\s+", " ", name).strip().lower()
    return name


def _match_model(title: str, known_models: list[dict]) -> tuple[Optional[int], str]:
    """
    Try to match a listing title against the list of known vehicle models.
    Returns (model_id, confidence): confidence = 'alta' | 'media' | 'baixa' | None
    known_models: list of dicts with {id, brand_name, model_name}
    """
    norm_title = _normalise_name(title)

    best_model_id = None
    best_confidence = "baixa"
    best_match_len = 0

    for model in known_models:
        brand = _normalise_name(model["brand_name"])
        name = _normalise_name(model["model_name"])
        full = f"{brand} {name}"

        # Alta: exact full match
        if full in norm_title:
            match_len = len(full)
            if match_len > best_match_len:
                best_model_id = model["id"]
                best_confidence = "alta"
                best_match_len = match_len
                continue

        # Media: brand + model both present (non-overlapping)
        if brand in norm_title and name in norm_title:
            match_len = len(brand) + len(name)
            if match_len > best_match_len and best_confidence != "alta":
                best_model_id = model["id"]
                best_confidence = "media"
                best_match_len = match_len
                continue

        # Baixa: model name only (skip very short names to avoid false positives)
        if len(name) >= 4 and name in norm_title:
            if best_confidence not in ("alta", "media") and len(name) > best_match_len:
                best_model_id = model["id"]
                best_confidence = "baixa"
                best_match_len = len(name)

    return best_model_id, best_confidence if best_model_id else None


# ── Deal scoring ─────────────────────────────────────────────────────────────

def _compute_price_delta(listing_price: int, avg_price: float) -> float:
    """
    Normalised price delta:
    +1.0 = listing is 20%+ below market (strong deal)
     0.0 = at market
    -1.0 = listing is 20%+ above market
    """
    if not listing_price or not avg_price or avg_price <= 0:
        return 0.0
    delta = (avg_price - listing_price) / avg_price
    return round(max(-1.0, min(1.0, delta / 0.20)), 4)


def _compute_km_per_year(km: Optional[int], year: Optional[int]) -> Optional[float]:
    if not km or not year:
        return None
    current_year = datetime.now(timezone.utc).year
    age = max(1, current_year - year)
    return round(km / age, 0)


def _classify_deal_tier(
    price_delta: float,
    km_per_year: Optional[float],
    listing_price: Optional[int],
    avg_price: Optional[float],
    seller_type: str,
) -> str:
    """
    Classify deal tier based on price delta, km usage, and red flags.
    Returns: forte | razoavel | cuidado | evitar
    """
    # Red flags → evitar
    if listing_price and avg_price and listing_price < avg_price * 0.75:
        return "evitar"  # Suspiciously cheap (possible scam)
    if km_per_year and km_per_year > 25000:
        return "evitar"  # Very high mileage vehicle

    # Price-based classification
    if price_delta >= 0.5:  # 10%+ below market
        tier = "forte"
    elif price_delta >= 0.0:  # at market or slight discount
        tier = "razoavel"
    elif price_delta >= -0.5:  # up to 10% above market
        tier = "cuidado"
    else:  # more than 10% above market
        tier = "evitar"

    # Downgrade for high km even if price is ok
    if tier == "forte" and km_per_year and km_per_year > 20000:
        tier = "razoavel"
    elif tier == "razoavel" and km_per_year and km_per_year > 22000:
        tier = "cuidado"

    # Downgrade stand prices above market
    if seller_type == "stand" and avg_price and listing_price and listing_price > avg_price * 1.15:
        if tier in ("forte", "razoavel"):
            tier = "cuidado"

    return tier


def _compute_deal_score(price_delta: float, km_per_year: Optional[float]) -> float:
    """
    Composite deal score 0.0–1.0.
    Higher = better deal.
    """
    # Base from price delta (-1 to +1 → 0 to 1)
    base = (price_delta + 1.0) / 2.0

    # Km penalty
    km_penalty = 0.0
    if km_per_year:
        if km_per_year > 25000:
            km_penalty = 0.35
        elif km_per_year > 20000:
            km_penalty = 0.20
        elif km_per_year > 15000:
            km_penalty = 0.08

    return round(max(0.0, min(1.0, base - km_penalty)), 4)


# ── Main normalizer ────────────────────────────────────────────────────────

def normalize_listing(
    raw: dict,
    known_models: list[dict],
    market_prices: dict[int, dict],  # model_id → {avg_price, min_price, max_price}
) -> Optional[dict]:
    """
    Normalise a raw listing dict. Returns a normalized_listings row dict or None if invalid.

    raw: output of standvirtual scraper
    known_models: list of {id, brand_name, model_name} from DB
    market_prices: map of model_id → market price stats
    """
    if not raw.get("source_url") or not raw.get("price"):
        return None

    model_id, confidence = _match_model(raw.get("title", ""), known_models)
    km_per_year = _compute_km_per_year(raw.get("km"), raw.get("year"))

    # Market stats
    avg_price = None
    price_delta = 0.0
    price_vs_market = 0.0
    deal_tier = "razoavel"
    deal_score = 0.5

    if model_id and model_id in market_prices:
        stats = market_prices[model_id]
        avg_price = stats.get("avg_price")
        if avg_price and raw.get("price"):
            price_vs_market = round((raw["price"] - avg_price) / avg_price, 4)
            price_delta = _compute_price_delta(raw["price"], avg_price)

    deal_tier = _classify_deal_tier(
        price_delta, km_per_year, raw.get("price"), avg_price, raw.get("seller_type", "desconhecido")
    )
    deal_score = _compute_deal_score(price_delta, km_per_year)

    # Brand/model name extraction from match or title
    brand_name = ""
    model_name = ""
    if model_id:
        for m in known_models:
            if m["id"] == model_id:
                brand_name = m["brand_name"]
                model_name = m["model_name"]
                break

    return {
        "raw_listing_id": raw.get("raw_id"),   # set by caller after DB insert
        "model_id": model_id,
        "brand_name": brand_name,
        "model_name": model_name,
        "year": raw.get("year"),
        "km": raw.get("km"),
        "price": raw.get("price"),
        "fuel_type": raw.get("fuel_type"),
        "match_confidence": confidence,
        "price_vs_market": price_vs_market,
        "price_delta": price_delta,
        "km_per_year": km_per_year,
        "seller_type": raw.get("seller_type"),
        "listing_age_days": raw.get("listing_age"),
        "photo_count": raw.get("photo_count"),
        "deal_tier": deal_tier,
        "deal_score": deal_score,
        "description": raw.get("description", ""),
        "llm_analysis": None,
        "analysis_cached_at": None,
    }
