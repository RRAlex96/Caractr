"""
EU Safety Gate scraper for Caractr reliability evidence.

Public API: https://ec.europa.eu/safety-gate-alerts/screen/webService
No authentication required. Rate limit: be polite (sleep between pages).

Fetches automotive recall/safety alerts, maps them to generations in the DB,
and writes rows to reliability_evidence.

Severity → evidence weight mapping:
  SERIOUS_RISK  → fail_eff = 6.0, weight = 1.0
  HIGH          → fail_eff = 3.0, weight = 0.6
  MEDIUM        → fail_eff = 1.5, weight = 0.3
  LOW / other   → fail_eff = 0.5, weight = 0.1
"""

import time
import logging
import re
from datetime import date, datetime

import requests
from difflib import SequenceMatcher
from sqlalchemy.orm import Session
from sqlalchemy import text

logger = logging.getLogger(__name__)

SAFETY_GATE_API = "https://ec.europa.eu/safety-gate-alerts/screen/webService/getAlerts"

CATEGORY_FILTER = "Motor vehicles"

SEVERITY_MAP = {
    "SERIOUS_RISK": {"fail_eff": 6.0, "weight": 1.0},
    "HIGH":         {"fail_eff": 3.0, "weight": 0.6},
    "MEDIUM":       {"fail_eff": 1.5, "weight": 0.3},
    "LOW":          {"fail_eff": 0.5, "weight": 0.1},
}

DEFAULT_SEVERITY = {"fail_eff": 0.5, "weight": 0.1}

# Brand name normalisation map (Safety Gate uses English names)
BRAND_NORM = {
    "volkswagen": "Volkswagen",
    "vw": "Volkswagen",
    "bmw": "BMW",
    "mercedes": "Mercedes-Benz",
    "mercedes-benz": "Mercedes-Benz",
    "audi": "Audi",
    "toyota": "Toyota",
    "renault": "Renault",
    "peugeot": "Peugeot",
    "citroen": "Citroen",
    "citroën": "Citroen",
    "ford": "Ford",
    "opel": "Opel",
    "vauxhall": "Opel",
    "honda": "Honda",
    "hyundai": "Hyundai",
    "kia": "Kia",
    "skoda": "Skoda",
    "škoda": "Skoda",
    "seat": "SEAT",
    "fiat": "Fiat",
    "alfa romeo": "Alfa Romeo",
    "volvo": "Volvo",
    "nissan": "Nissan",
    "mazda": "Mazda",
    "subaru": "Subaru",
    "suzuki": "Suzuki",
    "mitsubishi": "Mitsubishi",
    "land rover": "Land Rover",
    "range rover": "Land Rover",
    "jaguar": "Jaguar",
    "porsche": "Porsche",
    "tesla": "Tesla",
    "dacia": "Dacia",
    "cupra": "Cupra",
    "mini": "MINI",
    "lexus": "Lexus",
    "jeep": "Jeep",
    "dodge": "Dodge",
}


def _normalise_brand(raw: str) -> str | None:
    if not raw:
        return None
    key = raw.lower().strip()
    return BRAND_NORM.get(key) or BRAND_NORM.get(key.split()[0])


def _similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def _fetch_alerts(page: int = 0, page_size: int = 100) -> dict:
    """Fetch one page of Safety Gate alerts."""
    params = {
        "lang": "en",
        "offset": page * page_size,
        "limit": page_size,
        "category": CATEGORY_FILTER,
        "sortField": "publicationDate",
        "sortDirection": "desc",
    }
    resp = requests.get(SAFETY_GATE_API, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


def _extract_years_from_alert(alert: dict) -> list[int]:
    """Try to extract model years mentioned in the alert description."""
    text_fields = " ".join(filter(None, [
        alert.get("productName", ""),
        alert.get("description", ""),
        alert.get("measures", ""),
    ]))
    years = re.findall(r"\b(19[89]\d|20[0-2]\d)\b", text_fields)
    return list(set(int(y) for y in years))


def _find_generation(db: Session, brand_name: str, model_name_raw: str,
                     years: list[int]) -> int | None:
    """
    Attempt to match a Safety Gate alert to a generation in the DB.

    Strategy:
    1. Match brand exactly (normalised)
    2. Fuzzy-match model name against vehicle_models.name
    3. If years are present, intersect with generation year_start/year_end
    Returns generation.id or None.
    """
    rows = db.execute(text("""
        SELECT g.id, g.year_start, g.year_end, vm.name as model_name,
               b.name as brand_name
        FROM generations g
        JOIN vehicle_models vm ON g.model_id = vm.id
        JOIN brands b ON vm.brand_id = b.id
        WHERE b.name = :brand
    """), {"brand": brand_name}).mappings().fetchall()

    if not rows:
        return None

    # Fuzzy model name match
    best_score = 0.0
    best_gen_id = None

    for row in rows:
        sim = _similarity(model_name_raw, row["model_name"])
        if sim < 0.45:
            continue

        # If years are available, prefer matching generation
        if years and row["year_start"] and row["year_end"]:
            year_overlap = any(row["year_start"] <= y <= row["year_end"] for y in years)
            if not year_overlap:
                sim *= 0.5  # penalise non-overlapping years

        if sim > best_score:
            best_score = sim
            best_gen_id = row["id"]

    return best_gen_id if best_score >= 0.45 else None


def _already_ingested(db: Session, generation_id: int, source_url: str) -> bool:
    """Check if this exact alert URL was already stored."""
    row = db.execute(text("""
        SELECT 1 FROM reliability_evidence
        WHERE generation_id = :gid AND source_url = :url
        LIMIT 1
    """), {"gid": generation_id, "url": source_url}).fetchone()
    return row is not None


def ingest_safety_gate(db: Session, max_pages: int = 10,
                       sleep_seconds: float = 1.0) -> dict:
    """
    Main entry point. Fetches Safety Gate alerts and writes evidence rows.

    Returns summary: {ingested, skipped_no_match, skipped_duplicate, errors}
    """
    stats = {"ingested": 0, "skipped_no_match": 0,
             "skipped_duplicate": 0, "errors": 0}
    observed_month = date.today().replace(day=1)

    for page in range(max_pages):
        try:
            data = _fetch_alerts(page=page)
        except Exception as e:
            logger.error(f"Safety Gate API error page {page}: {e}")
            stats["errors"] += 1
            break

        alerts = data.get("alerts", data.get("results", []))
        if not alerts:
            break

        for alert in alerts:
            try:
                brand_raw = alert.get("brand", "") or alert.get("manufacturer", "")
                model_raw = alert.get("productName", "") or alert.get("product", "")
                severity  = alert.get("riskLevel", alert.get("riskType", "")).upper()
                pub_date  = alert.get("publicationDate", "")
                alert_url = alert.get("url", alert.get("link", ""))
                alert_ref = alert.get("reference", alert.get("id", ""))

                brand_norm = _normalise_brand(brand_raw)
                if not brand_norm or not model_raw:
                    stats["skipped_no_match"] += 1
                    continue

                years = _extract_years_from_alert(alert)
                gen_id = _find_generation(db, brand_norm, model_raw, years)

                if gen_id is None:
                    logger.debug(f"No generation match: {brand_norm} {model_raw}")
                    stats["skipped_no_match"] += 1
                    continue

                if alert_url and _already_ingested(db, gen_id, alert_url):
                    stats["skipped_duplicate"] += 1
                    continue

                sev_data = SEVERITY_MAP.get(severity, DEFAULT_SEVERITY)

                db.execute(text("""
                    INSERT INTO reliability_evidence
                        (generation_id, evidence_type, source, source_url,
                         observed_month, severity, fail_eff, succ_eff, weight, payload)
                    VALUES
                        (:gen_id, 'safety_gate', 'eu_safety_gate', :url,
                         :month, :severity, :fail_eff, 0, :weight, :payload::jsonb)
                    ON CONFLICT DO NOTHING
                """), {
                    "gen_id":    gen_id,
                    "url":       alert_url,
                    "month":     observed_month,
                    "severity":  severity,
                    "fail_eff":  sev_data["fail_eff"],
                    "weight":    sev_data["weight"],
                    "payload":   __import__("json").dumps({
                        "reference": alert_ref,
                        "brand_raw": brand_raw,
                        "model_raw": model_raw,
                        "pub_date":  pub_date,
                        "years":     years,
                    }),
                })
                stats["ingested"] += 1

            except Exception as e:
                logger.error(f"Error processing alert: {e}")
                stats["errors"] += 1

        db.commit()
        logger.info(f"Safety Gate page {page}: {len(alerts)} alerts processed")

        if len(alerts) < 100:
            break

        time.sleep(sleep_seconds)

    return stats
