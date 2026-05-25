"""
Market Scraper Runner — bulk listing collection for market price data.

Iterates all generations in the DB, fetches live listings from Standvirtual + OLX
scoped to each generation's year range, stores in raw_listings and normalized_listings.

Designed to run monthly from the background scheduler.
After this completes, run market_aggregator.run_aggregation() to compute
p10/p50/p90 and update market_price_stats_history + generations table.
"""

import asyncio
import json
import logging
import re
from datetime import date, datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import text

logger = logging.getLogger(__name__)

# Top Portuguese market models — prioritised for first run.
# These cover ~80% of used car searches. All other models get a lighter pass.
PRIORITY_MODELS = {
    ("Renault", "Clio"), ("Volkswagen", "Golf"), ("Peugeot", "208"),
    ("Volkswagen", "Polo"), ("Toyota", "Yaris"), ("Toyota", "Corolla"),
    ("Dacia", "Duster"), ("Opel", "Corsa"), ("Peugeot", "308"),
    ("Skoda", "Octavia"), ("Renault", "Captur"), ("Hyundai", "Tucson"),
    ("Kia", "Sportage"), ("Ford", "Focus"), ("SEAT", "Ibiza"),
    ("Volkswagen", "Tiguan"), ("BMW", "Serie 3"), ("Audi", "A3"),
    ("Mercedes-Benz", "Classe C"), ("Toyota", "RAV4"), ("Mazda", "CX-5"),
    ("Volvo", "XC60"), ("Skoda", "Karoq"), ("Hyundai", "Kona"),
    ("Dacia", "Sandero"), ("Peugeot", "2008"), ("Renault", "Megane"),
    ("Ford", "Puma"), ("SEAT", "Leon"), ("Honda", "Jazz"),
}

MAX_PER_SOURCE_PRIORITY = 60
MAX_PER_SOURCE_OTHER    = 20


def _extract_external_id(url: str) -> Optional[str]:
    """
    Extract platform listing ID from URL for deduplication.
    Standvirtual: /carros/brand/model/ID123456789.html
    OLX:          /d/anuncio/title-IDabcdef12345.html
    """
    if not url:
        return None
    # Standvirtual numeric ID
    m = re.search(r"/ID(\d{6,})", url)
    if m:
        return f"sv_{m.group(1)}"
    # OLX alphanumeric ID
    m = re.search(r"-ID([A-Za-z0-9]{6,})(?:\.html)?$", url)
    if m:
        return f"olx_{m.group(1)}"
    # Fallback: hash of URL
    return f"url_{abs(hash(url)) % 10**10}"


def _detect_source(url: str) -> str:
    if not url:
        return "unknown"
    if "standvirtual" in url:
        return "standvirtual"
    if "olx.pt" in url:
        return "olx"
    return "other"


def _already_stored(db: Session, source: str, external_id: str) -> Optional[int]:
    """Return existing raw_listing.id if this (source, external_id) pair exists."""
    row = db.execute(text("""
        SELECT id FROM raw_listings
        WHERE source = :source AND external_id = :ext_id
        LIMIT 1
    """), {"source": source, "ext_id": external_id}).fetchone()
    return row[0] if row else None


def _insert_raw_listing(db: Session, listing: dict, source: str, external_id: str) -> int:
    """Insert into raw_listings and return the new id."""
    row = db.execute(text("""
        INSERT INTO raw_listings
            (source, external_id, url, raw_data, seller_type, photo_count,
             description, scraped_at)
        VALUES
            (:source, :ext_id, :url, :raw::jsonb, :seller_type, :photo_count,
             :description, now())
        RETURNING id
    """), {
        "source":      source,
        "ext_id":      external_id,
        "url":         listing.get("source_url", ""),
        "raw":         json.dumps({
            "title":     listing.get("title", ""),
            "price":     listing.get("price"),
            "year":      listing.get("year"),
            "km":        listing.get("km"),
            "fuel_type": listing.get("fuel_type"),
            "location":  listing.get("location", ""),
        }),
        "seller_type":  listing.get("seller_type", "desconhecido"),
        "photo_count":  listing.get("photo_count", 0),
        "description":  listing.get("description", ""),
    }).fetchone()
    return row[0]


def _normalise_fuel(raw: Optional[str]) -> Optional[str]:
    if not raw:
        return None
    f = raw.lower()
    if "gasolina" in f or "petrol" in f:
        return "gasolina"
    if "diesel" in f or "gasóleo" in f or "gasoleo" in f:
        return "diesel"
    if "híbrido" in f or "hibrido" in f or "hybrid" in f:
        return "hibrido"
    if "elétrico" in f or "eletrico" in f or "electric" in f:
        return "eletrico"
    if "gpl" in f:
        return "gpl"
    return None


def _compute_km_per_year(km: Optional[int], year: Optional[int]) -> Optional[float]:
    if not km or not year:
        return None
    age = max(1, date.today().year - year)
    return round(km / age, 1)


def _insert_normalized(
    db: Session,
    raw_id: int,
    model_id: int,
    generation_id: int,
    listing: dict,
    avg_price: Optional[float],
) -> None:
    """Insert a row into normalized_listings."""
    price = listing.get("price")
    km    = listing.get("km")
    year  = listing.get("year")
    km_py = _compute_km_per_year(km, year)

    # Price vs market using existing avg_price from market_price_stats (seed)
    price_vs_market = 0.0
    price_delta = 0.0
    if price and avg_price and avg_price > 0:
        price_vs_market = round((price - avg_price) / avg_price, 4)
        raw_delta = (avg_price - price) / avg_price
        price_delta = round(max(-1.0, min(1.0, raw_delta / 0.20)), 4)

    # Simple deal tier
    deal_tier = "razoavel"
    if price and avg_price:
        if price < avg_price * 0.75:
            deal_tier = "evitar"  # suspiciously cheap
        elif price_delta >= 0.5:
            deal_tier = "forte"
        elif price_delta >= 0.0:
            deal_tier = "razoavel"
        elif price_delta >= -0.5:
            deal_tier = "cuidado"
        else:
            deal_tier = "evitar"
    if km_py and km_py > 25000:
        deal_tier = "evitar"

    deal_score = round(max(0.0, min(1.0,
        ((price_delta + 1.0) / 2.0) - (0.35 if km_py and km_py > 25000 else
                                        0.20 if km_py and km_py > 20000 else
                                        0.08 if km_py and km_py > 15000 else 0.0)
    )), 4)

    db.execute(text("""
        INSERT INTO normalized_listings
            (raw_listing_id, model_id, generation_id, year, km, price,
             seller_type, location, price_vs_market, price_delta, km_per_year,
             photo_count, deal_tier, deal_score, description, created_at)
        VALUES
            (:raw_id, :model_id, :gen_id, :year, :km, :price,
             :seller_type, :location, :pvm, :pdelta, :kmpy,
             :photos, :tier, :score, :desc, now())
        ON CONFLICT DO NOTHING
    """), {
        "raw_id":      raw_id,
        "model_id":    model_id,
        "gen_id":      generation_id,
        "year":        year,
        "km":          km,
        "price":       price,
        "seller_type": listing.get("seller_type", "desconhecido"),
        "location":    listing.get("location", ""),
        "pvm":         price_vs_market,
        "pdelta":      price_delta,
        "kmpy":        km_py,
        "photos":      listing.get("photo_count", 0),
        "tier":        deal_tier,
        "score":       deal_score,
        "desc":        listing.get("description", ""),
    })


def _record_batch_observation(
    db: Session,
    model_id: int,
    generation_id: int,
    listing: dict,
    source: str,
    url: str,
) -> None:
    """Record a batch-scraped listing as a price observation."""
    price = listing.get("price")
    if not price or price < 500 or price > 500_000:
        return

    domain = ""
    if "standvirtual" in url:
        domain = "standvirtual.com"
    elif "olx.pt" in url:
        domain = "olx.pt"
    elif "custojusto" in url:
        domain = "custojusto.pt"

    try:
        db.execute(text("""
            INSERT INTO price_observations
                (model_id, generation_id, vehicle_year, km, price, fuel_type,
                 seller_type, source_type, source_domain, source_url,
                 extraction_method, data_quality, observation_type, observed_at)
            VALUES
                (:model_id, :gen_id, :year, :km, :price, :fuel,
                 :seller, 'marketplace', :domain, :url,
                 'batch_scraper', NULL, 'batch', now())
            ON CONFLICT (source_url) DO UPDATE SET
                price       = EXCLUDED.price,
                km          = COALESCE(EXCLUDED.km, price_observations.km),
                observed_at = now()
        """), {
            "model_id": model_id,
            "gen_id":   generation_id,
            "year":     listing.get("year"),
            "km":       listing.get("km"),
            "price":    price,
            "fuel":     _normalise_fuel(listing.get("fuel_type")),
            "seller":   listing.get("seller_type", "desconhecido"),
            "domain":   domain,
            "url":      url,
        })
    except Exception as e:
        logger.warning(f"Price observation insert error: {e}")


async def _scrape_generation(
    brand: str,
    model: str,
    year_start: int,
    year_end: int,
    is_priority: bool,
) -> list[dict]:
    """Scrape listings from Standvirtual + OLX for one generation."""
    from app.scrapers.dispatcher import fetch_listings_all_sources

    max_per = MAX_PER_SOURCE_PRIORITY if is_priority else MAX_PER_SOURCE_OTHER
    try:
        listings = await fetch_listings_all_sources(
            brand, model,
            max_per_source=max_per,
            year_from=year_start,
            year_to=year_end,
        )
        return listings
    except Exception as e:
        logger.warning(f"Scrape failed {brand} {model} {year_start}-{year_end}: {e}")
        return []


def run_market_scraper(db: Session) -> dict:
    """
    Synchronous entry point for the background scheduler.

    Fetches listings for all generations, stores raw + normalized rows,
    and returns a stats dict.
    """
    stats = {
        "generations_scraped": 0,
        "listings_new": 0,
        "listings_duplicate": 0,
        "listings_no_price": 0,
        "errors": 0,
    }

    # Load all generations
    gen_rows = db.execute(text("""
        SELECT
            g.id          AS generation_id,
            g.model_id,
            g.year_start,
            g.year_end,
            vm.name       AS model_name,
            b.name        AS brand_name
        FROM generations g
        JOIN vehicle_models vm ON g.model_id = vm.id
        JOIN brands b ON vm.brand_id = b.id
        ORDER BY b.name, vm.name, g.year_start
    """)).mappings().fetchall()

    # Load existing seed market_price_stats for price delta reference
    mps_rows = db.execute(text("""
        SELECT model_id, year, avg_price
        FROM market_price_stats
        WHERE avg_price IS NOT NULL
    """)).fetchall()
    market_lookup: dict[tuple, float] = {}
    for r in mps_rows:
        market_lookup[(r[0], r[1])] = r[2]
        # Also store model-level average (year=None)
        if (r[0], None) not in market_lookup:
            market_lookup[(r[0], None)] = r[2]

    for row in gen_rows:
        gen_id     = row["generation_id"]
        model_id   = row["model_id"]
        brand      = row["brand_name"]
        model      = row["model_name"]
        year_start = row["year_start"] or 2010
        year_end   = row["year_end"]   or date.today().year
        is_priority = (brand, model) in PRIORITY_MODELS

        try:
            # Run async scraper in the current event loop context
            listings = asyncio.run(_scrape_generation(
                brand, model, year_start, year_end, is_priority
            ))

            for listing in listings:
                url = listing.get("source_url", "")
                price = listing.get("price")
                lsource = _detect_source(url)
                ext_id  = _extract_external_id(url)

                if not ext_id:
                    stats["listings_no_price"] += 1
                    continue

                if not price:
                    stats["listings_no_price"] += 1
                    continue

                # Check duplicate
                existing_id = _already_stored(db, lsource, ext_id)
                if existing_id:
                    stats["listings_duplicate"] += 1
                    continue

                try:
                    raw_id = _insert_raw_listing(db, listing, lsource, ext_id)

                    # Find avg_price reference for this model+year
                    yr = listing.get("year")
                    avg_price = (
                        market_lookup.get((model_id, yr)) or
                        market_lookup.get((model_id, None))
                    )

                    _insert_normalized(
                        db, raw_id, model_id, gen_id, listing, avg_price
                    )

                    # Feed the price intelligence flywheel
                    _record_batch_observation(
                        db, model_id, gen_id, listing, lsource, url
                    )
                    stats["listings_new"] += 1

                except Exception as e:
                    logger.error(f"Insert error {url}: {e}")
                    db.rollback()
                    stats["errors"] += 1
                    continue

            if listings:
                db.commit()
                stats["generations_scraped"] += 1

        except Exception as e:
            logger.error(f"Generation scrape error gen={gen_id} {brand} {model}: {e}")
            db.rollback()
            stats["errors"] += 1

    # NLP pass: extract problem-signal evidence from listing descriptions
    try:
        from app.services.listing_nlp import run_nlp_pass
        nlp_stats = run_nlp_pass(db)
        stats["nlp_evidence_rows"] = nlp_stats["evidence_rows_written"]
        stats["nlp_signals_found"] = nlp_stats["signals_found"]
        logger.info(f"NLP pass: {nlp_stats}")
    except Exception as e:
        logger.error(f"NLP pass error: {e}")
        stats["nlp_evidence_rows"] = 0

    logger.info(f"Market scraper complete: {stats}")
    return stats
