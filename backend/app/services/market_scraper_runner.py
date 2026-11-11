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

from app.scrapers.model_match import listing_matches_generation

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
    CustoJusto:   /.../{numeric-id}.htm  or  /ad/{slug}/{id}
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
    # CustoJusto: URLs end with /12345678.htm or similar numeric ID
    if "custojusto" in url:
        m = re.search(r"/(\d{5,})\.htm", url)
        if m:
            return f"cj_{m.group(1)}"
    # Fallback: hash of URL
    return f"url_{abs(hash(url)) % 10**10}"


def _detect_source(url: str) -> str:
    if not url:
        return "unknown"
    if "standvirtual" in url:
        return "standvirtual"
    if "olx.pt" in url:
        return "olx"
    if "custojusto" in url:
        return "custojusto"
    return "other"


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


def _record_batch_observation(
    db: Session,
    model_id: int,
    generation_id: int,
    listing: dict,
    source: str,
    url: str,
) -> bool:
    """Record a batch-scraped listing as a price observation (upsert by URL).
    Runs in a SAVEPOINT so one bad row can't abort the whole refresh.
    Returns True if written."""
    price = listing.get("price")
    if not price or price < 500 or price > 500_000:
        return False

    domain = ""
    if "standvirtual" in url:
        domain = "standvirtual.com"
    elif "olx.pt" in url:
        domain = "olx.pt"
    elif "custojusto" in url:
        domain = "custojusto.pt"

    try:
        with db.begin_nested():
            _upsert_observation(db, model_id, generation_id, listing, price, domain, url)
        return True
    except Exception as e:
        logger.warning(f"Price observation insert error {url}: {e}")
        return False


def _upsert_observation(db, model_id, generation_id, listing, price, domain, url) -> None:
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


def run_market_scraper(db: Session, only_generation_ids: list[int] | None = None) -> dict:
    """
    Synchronous entry point for the background scheduler.

    Fetches listings for all generations (or just `only_generation_ids`, for a
    quick smoke test), upserts them into price_observations, and returns a
    stats dict. Aggregation (market_aggregator) turns those into prices.
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
    # Sibling model names per brand, so "Corolla Cross" listings never count
    # as "Corolla" (see model_match.listing_matches_generation).
    siblings: dict[str, list[str]] = {}
    for r in gen_rows:
        siblings.setdefault(r["brand_name"], [])
        if r["model_name"] not in siblings[r["brand_name"]]:
            siblings[r["brand_name"]].append(r["model_name"])
    if only_generation_ids:
        wanted = set(only_generation_ids)
        gen_rows = [r for r in gen_rows if r["generation_id"] in wanted]
    stats["listings_rejected_wrong_car"] = 0

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

                if not price or price < 500 or price > 500_000:
                    stats["listings_no_price"] += 1
                    continue

                if not listing_matches_generation(listing, brand, model, row["year_start"],
                                                  row["year_end"], siblings.get(brand, [])):
                    stats["listings_rejected_wrong_car"] += 1
                    continue

                # Scraped listings feed price_observations (the aggregator's
                # primary input), upserted by URL. raw_listings /
                # normalized_listings now belong to the ad-analysis cache and
                # have a different schema — writing there broke every refresh.
                seen = db.execute(
                    text("SELECT 1 FROM price_observations WHERE source_url = :u"), {"u": url}
                ).fetchone() is not None
                if _record_batch_observation(db, model_id, gen_id, listing, lsource, url):
                    stats["listings_duplicate" if seen else "listings_new"] += 1
                else:
                    stats["errors"] += 1

            if listings:
                db.commit()
                stats["generations_scraped"] += 1

        except Exception as e:
            logger.error(f"Generation scrape error gen={gen_id} {brand} {model}: {e}")
            db.rollback()
            stats["errors"] += 1

    # The batch NLP pass (listing_nlp.run_nlp_pass) mined descriptions stored in
    # normalized_listings with a generation_id. The batch scraper no longer
    # stores descriptions there (that table is the ad-analysis cache, without
    # generation_id), so the pass is not run here.

    logger.info(f"Market scraper complete: {stats}")
    return stats
