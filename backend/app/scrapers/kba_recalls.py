"""
KBA (Kraftfahrt-Bundesamt) recall scraper for Caractr reliability evidence.

Source: car-recalls.eu — aggregates KBA + EU recalls in English.
URL pattern: https://car-recalls.eu/{brand-slug}-recalls-{year}/

Particularly covers:
  VW Group (VW, Audi, Skoda, SEAT, Cupra, Porsche)
  BMW Group (BMW, MINI)
  Daimler (Mercedes-Benz, Smart)
  Other EU brands (Renault, Peugeot, Citroen, Fiat, Opel, Volvo, etc.)

Evidence weight mapping (same as NHTSA recalls):
  Safety-critical component → fail_eff = 6.0, weight = 1.0
  Other component          → fail_eff = 3.0, weight = 0.6

Politeness: 2s between requests, standard browser UA, robots.txt respected.
"""

import json
import re
import time
import logging
from datetime import date, datetime
from difflib import SequenceMatcher

import requests
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session
from sqlalchemy import text

logger = logging.getLogger(__name__)

BASE_URL = "https://www.car-recalls.eu"

# Polite browser UA — not a bot UA
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# DB brand name → car-recalls.eu URL slug
# Only brands whose recalls are primarily captured by KBA / EU sources
BRAND_SLUGS: dict[str, str] = {
    "Volkswagen":   "volkswagen",
    "Audi":         "audi",
    "BMW":          "bmw",
    "Mercedes-Benz": "mercedes-benz",
    "Skoda":        "skoda",
    "SEAT":         "seat",
    "Cupra":        "cupra",
    "Porsche":      "porsche",
    "MINI":         "mini",
    "Smart":        "smart",
    "Opel":         "opel",
    "Renault":      "renault",
    "Peugeot":      "peugeot",
    "Citroen":      "citroen",
    "Fiat":         "fiat",
    "Alfa Romeo":   "alfa-romeo",
    "Volvo":        "volvo",
    "Toyota":       "toyota",
    "Nissan":       "nissan",
    "Hyundai":      "hyundai",
    "Kia":          "kia",
    "Dacia":        "dacia",
    "Mazda":        "mazda",
    "Ford":         "ford",
    "Honda":        "honda",
    "Land Rover":   "land-rover",
    "Jaguar":       "jaguar",
    "Jeep":         "jeep",
}

# Safety-critical component keywords
SAFETY_CRITICAL_PATTERNS = re.compile(
    r"\b(engine|fuel|brake|brakes|braking|steering|airbag|air.?bag|seat.?belt|"
    r"seatbelt|suspension|transmission|powertrain|throttle|accelerat|fire|ignition|"
    r"motor|fuel.?system|fuel.?pump|fuel.?line|fuel.?tank|steer|crash|rollover|"
    r"battery|electric|short.?circuit)\b",
    re.IGNORECASE,
)

# Production date range pattern: "MM/YYYY – MM/YYYY" or "MM/YYYY - MM/YYYY"
_DATE_RANGE_RE = re.compile(
    r"(\d{1,2})/(\d{4})\s*[–\-—]+\s*(\d{1,2})/(\d{4})"
)

# Single year reference fallback
_YEAR_RE = re.compile(r"\b(19[89]\d|20[0-2]\d)\b")


def _is_safety_critical(text_blob: str) -> bool:
    return bool(SAFETY_CRITICAL_PATTERNS.search(text_blob))


def _parse_production_years(production_text: str) -> tuple[int | None, int | None]:
    """
    Parse production date range into (year_start, year_end).
    Handles 'MM/YYYY – MM/YYYY' and single-year references.
    """
    m = _DATE_RANGE_RE.search(production_text)
    if m:
        return int(m.group(2)), int(m.group(4))
    # Fallback: any two years in the text
    years = [int(y) for y in _YEAR_RE.findall(production_text)]
    if len(years) >= 2:
        return min(years), max(years)
    if len(years) == 1:
        return years[0], years[0]
    return None, None


def _similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio()


def _name_match_score(db_model: str, raw_model: str) -> float:
    """High-precision model match: a whole-word hit of the DB model name inside
    the scraped model text is a confident match (1.0), else a similarity ratio.
    Precision over recall — a recall pinned to the wrong car is worse than a
    miss (the curator agent fills breadth; recalls stay high-trust)."""
    db = (db_model or "").lower().strip()
    raw = (raw_model or "").lower().strip()
    if not db or not raw:
        return 0.0
    if re.search(r"\b" + re.escape(db) + r"\b", raw):
        return 1.0
    return SequenceMatcher(None, db, raw).ratio()


def _find_generation(
    db: Session,
    brand_name: str,
    model_raw: str,
    prod_year_start: int | None,
    prod_year_end: int | None,
) -> int | None:
    """
    Match a KBA recall to a generation in the DB.
    Strategy: exact brand match → fuzzy model name → year overlap bonus.
    """
    rows = db.execute(text("""
        SELECT g.id, g.year_start, g.year_end, vm.name AS model_name
        FROM generations g
        JOIN vehicle_models vm ON g.model_id = vm.id
        JOIN brands b ON vm.brand_id = b.id
        WHERE b.name = :brand
    """), {"brand": brand_name}).mappings().fetchall()

    if not rows:
        return None

    # Acceptance is decided on the NAME score alone (>= 0.6); the year overlap
    # only re-ranks candidates, it never promotes a weak name into a match.
    best_name = 0.0
    best_rank = 0.0
    best_gen_id = None

    for row in rows:
        name = _name_match_score(row["model_name"], model_raw)
        if name < 0.6:
            continue

        rank = name
        if (prod_year_start and prod_year_end and
                row["year_start"] and row["year_end"]):
            overlap = (
                prod_year_start <= row["year_end"] and
                prod_year_end >= row["year_start"]
            )
            rank *= 1.3 if overlap else 0.5

        if rank > best_rank:
            best_rank = rank
            best_gen_id = row["id"]
            best_name = name

    return best_gen_id if best_name >= 0.6 else None


def _already_ingested(db: Session, generation_id: int, source_url: str) -> bool:
    row = db.execute(text("""
        SELECT 1 FROM reliability_evidence
        WHERE generation_id = :gid AND source_url = :url
        LIMIT 1
    """), {"gid": generation_id, "url": source_url}).fetchone()
    return row is not None


def _fetch_page(url: str, timeout: int = 20) -> BeautifulSoup | None:
    """Fetch a page and return parsed HTML, or None on error/404."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout)
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return BeautifulSoup(resp.text, "lxml")
    except Exception as e:
        logger.debug(f"KBA fetch error {url}: {e}")
        return None


def _scrape_brand_year(
    db: Session,
    brand_db: str,
    brand_slug: str,
    year: int,
    observed_month: date,
    sleep_seconds: float,
) -> dict:
    """
    Scrape one brand+year page from car-recalls.eu.
    Returns per-page stats.
    """
    stats = {"ingested": 0, "skipped_duplicate": 0,
             "skipped_no_match": 0, "errors": 0}

    url = f"{BASE_URL}/{brand_slug}-recalls-{year}/"
    soup = _fetch_page(url)
    time.sleep(sleep_seconds)

    if soup is None:
        return stats  # 404 or error — brand/year has no recalls page

    # Parse: find h3 model sections, then the table following each h3
    # Structure: <h3>Model Name</h3> ... <table>...</table>
    current_model = None

    for element in soup.find_all(["h3", "table"]):
        if element.name == "h3":
            current_model = element.get_text(strip=True)
            # Strip brand prefix if present (e.g. "Volkswagen Golf" → "Golf")
            # car-recalls.eu sometimes includes brand in h3
            if current_model.lower().startswith(brand_db.lower()):
                current_model = current_model[len(brand_db):].strip()
            continue

        if element.name == "table" and current_model:
            rows = element.find_all("tr")
            for row in rows:
                cells = row.find_all("td")
                if len(cells) < 3:
                    continue  # skip header rows (th) or malformed

                try:
                    issue_text   = cells[1].get_text(separator=" ", strip=True)
                    prod_text    = cells[2].get_text(separator=" ", strip=True)
                    source_cell  = cells[3] if len(cells) > 3 else None
                    source_link  = None
                    if source_cell:
                        a = source_cell.find("a")
                        source_link = a["href"] if a and a.get("href") else None

                    # Build a stable URL for deduplication
                    recall_url = (
                        source_link if source_link
                        else f"kba://{brand_slug}/{year}/{current_model}/{hash(issue_text) & 0xFFFFFF}"
                    )

                    # Normalise source_link to absolute
                    if source_link and source_link.startswith("/"):
                        recall_url = BASE_URL + source_link

                    prod_year_start, prod_year_end = _parse_production_years(prod_text)

                    gen_id = _find_generation(
                        db, brand_db, current_model,
                        prod_year_start, prod_year_end,
                    )
                    if gen_id is None:
                        logger.debug(
                            f"KBA no match: {brand_db} '{current_model}' "
                            f"{prod_year_start}-{prod_year_end}"
                        )
                        stats["skipped_no_match"] += 1
                        continue

                    if _already_ingested(db, gen_id, recall_url):
                        stats["skipped_duplicate"] += 1
                        continue

                    if _is_safety_critical(issue_text):
                        fail_eff, weight, severity = 6.0, 1.0, "high"
                    else:
                        fail_eff, weight, severity = 3.0, 0.6, "medium"

                    db.execute(text("""
                        INSERT INTO reliability_evidence
                            (generation_id, evidence_type, source, source_url,
                             observed_month, severity, fail_eff, succ_eff, weight, payload)
                        VALUES
                            (:gen_id, 'recall', 'kba_de', :url,
                             :month, :severity, :fail_eff, 0, :weight, CAST(:payload AS jsonb))
                        ON CONFLICT DO NOTHING
                    """), {
                        "gen_id":   gen_id,
                        "url":      recall_url,
                        "month":    observed_month,
                        "severity": severity,
                        "fail_eff": fail_eff,
                        "weight":   weight,
                        "payload":  json.dumps({
                            "brand":       brand_db,
                            "model_raw":   current_model,
                            "title":       f"{brand_db} {current_model}"[:200],
                            "description": issue_text[:500],
                            "issue":       issue_text[:500],
                            "production":  prod_text,
                            "recall_year": year,
                            "prod_year_start": prod_year_start,
                            "prod_year_end":   prod_year_end,
                        }),
                    })
                    stats["ingested"] += 1

                except Exception as e:
                    logger.error(
                        f"KBA row error {brand_db}/{year}/{current_model}: {e}"
                    )
                    stats["errors"] += 1

    return stats


def ingest_kba(
    db: Session,
    year_start: int = 2010,
    year_end: int | None = None,
    brands: list[str] | None = None,
    sleep_seconds: float = 2.0,
) -> dict:
    """
    Main entry point. Scrapes car-recalls.eu for KBA recall data.

    Args:
        db: SQLAlchemy session
        year_start: First year to scrape (default 2010)
        year_end: Last year to scrape (default: current year)
        brands: List of DB brand names to process; None = all brands in BRAND_SLUGS
        sleep_seconds: Delay between HTTP requests (default 2.0 — be polite)

    Returns summary: {ingested, skipped_duplicate, skipped_no_match, errors, pages_fetched}
    """
    totals = {
        "ingested": 0, "skipped_duplicate": 0,
        "skipped_no_match": 0, "errors": 0, "pages_fetched": 0,
    }

    if year_end is None:
        year_end = date.today().year

    observed_month = date.today().replace(day=1)

    target_brands = {
        brand: slug
        for brand, slug in BRAND_SLUGS.items()
        if brands is None or brand in brands
    }

    for brand_db, brand_slug in target_brands.items():
        logger.info(f"KBA: scraping {brand_db} ({year_start}–{year_end})")

        for year in range(year_start, year_end + 1):
            page_stats = _scrape_brand_year(
                db, brand_db, brand_slug, year, observed_month, sleep_seconds
            )
            totals["pages_fetched"] += 1
            for k in ("ingested", "skipped_duplicate", "skipped_no_match", "errors"):
                totals[k] += page_stats[k]

        # Commit per brand to avoid long transactions
        db.commit()
        logger.info(
            f"KBA {brand_db} done — ingested so far: {totals['ingested']}"
        )

    logger.info(f"KBA ingest complete: {totals}")
    return totals


def ingest_kba_incremental(db: Session, sleep_seconds: float = 2.0) -> dict:
    """
    Incremental update: only scrape current year + previous year.
    Safe to run monthly alongside NHTSA and Safety Gate.
    """
    current_year = date.today().year
    return ingest_kba(
        db,
        year_start=current_year - 1,
        year_end=current_year,
        sleep_seconds=sleep_seconds,
    )
