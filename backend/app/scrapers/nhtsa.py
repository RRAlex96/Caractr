"""
NHTSA (National Highway Traffic Safety Administration) scraper for Caractr.

Public API: https://api.nhtsa.gov/
No authentication required. Covers all major brands sold in Portugal.

Two data types:
  1. Recalls — official manufacturer recall campaigns (high weight)
  2. Complaints — consumer-reported issues (volume signal, lower weight)

Evidence weight mapping:
  Recall (safety-critical component)  → fail_eff = 6.0, weight = 1.0
  Recall (other component)            → fail_eff = 3.0, weight = 0.6
  Complaint (crash=true OR injury>0)  → fail_eff = 4.0, weight = 0.8
  Complaint aggregate (N plain)       → fail_eff = N * 0.1 (capped at 6.0), weight = 0.3

Safety-critical components: engine, fuel, brake, steering, airbag,
  seatbelt, suspension, transmission (powertrain failures)
"""

import json
import time
import logging
import re
from datetime import date

import requests
from sqlalchemy.orm import Session
from sqlalchemy import text

logger = logging.getLogger(__name__)

NHTSA_BASE = "https://api.nhtsa.gov"
RECALLS_URL = NHTSA_BASE + "/recalls/recallsByVehicle"
COMPLAINTS_URL = NHTSA_BASE + "/complaints/complaintsByVehicle"

# Map DB brand names → NHTSA make names (NHTSA uses uppercase English)
BRAND_TO_NHTSA: dict[str, list[str]] = {
    "Alfa Romeo":   ["ALFA ROMEO"],
    "Alpine":       ["ALPINE"],
    "Audi":         ["AUDI"],
    "BMW":          ["BMW"],
    "BYD":          ["BYD"],
    "Citroen":      ["CITROEN"],
    "Cupra":        ["CUPRA"],
    "Dacia":        ["DACIA"],
    "DS":           ["DS"],
    "Fiat":         ["FIAT"],
    "Ford":         ["FORD"],
    "Honda":        ["HONDA"],
    "Hyundai":      ["HYUNDAI"],
    "Jaguar":       ["JAGUAR"],
    "Jeep":         ["JEEP"],
    "Kia":          ["KIA"],
    "Land Rover":   ["LAND ROVER"],
    "Lexus":        ["LEXUS"],
    "Maserati":     ["MASERATI"],
    "Mazda":        ["MAZDA"],
    "Mercedes-Benz": ["MERCEDES-BENZ"],
    "MG":           ["MG"],
    "MINI":         ["MINI"],
    "Nissan":       ["NISSAN"],
    "Omoda":        [],          # no NHTSA presence yet
    "Opel":         ["VAUXHALL"],  # NHTSA uses Vauxhall/Chevrolet for Opel-platform
    "Peugeot":      ["PEUGEOT"],
    "Porsche":      ["PORSCHE"],
    "Renault":      ["RENAULT"],
    "SEAT":         ["SEAT"],
    "Skoda":        ["VOLKSWAGEN"],  # Skoda sold under VW in North America; handle below
    "Smart":        ["SMART"],
    "Subaru":       ["SUBARU"],
    "Suzuki":       ["SUZUKI"],
    "Tesla":        ["TESLA"],
    "Toyota":       ["TOYOTA"],
    "Volkswagen":   ["VOLKSWAGEN"],
    "Volvo":        ["VOLVO"],
}

# Some DB model names need translation to how NHTSA records them
MODEL_OVERRIDES: dict[tuple[str, str], str] = {
    ("Volkswagen", "Golf"):            "GOLF",
    ("Volkswagen", "Polo"):            "POLO",
    ("Volkswagen", "Tiguan"):          "TIGUAN",
    ("Volkswagen", "Passat"):          "PASSAT",
    ("Volkswagen", "T-Roc"):          "T-ROC",
    ("Volkswagen", "T-Cross"):        "T-CROSS",
    ("Volkswagen", "Touran"):         "TOURAN",
    ("Volkswagen", "ID.3"):           "ID.3",
    ("Volkswagen", "Caddy"):          "CADDY",
    ("Volkswagen", "Sharan"):         "SHARAN",
    ("Volkswagen", "up!"):            "UP",
    ("BMW", "Serie 1"):               "1 SERIES",
    ("BMW", "Serie 2 Active Tourer"): "2 SERIES",
    ("BMW", "Serie 2 Gran Coupe"):    "2 SERIES GRAN COUPE",
    ("BMW", "Serie 3"):               "3 SERIES",
    ("BMW", "Serie 4"):               "4 SERIES",
    ("BMW", "Serie 5"):               "5 SERIES",
    ("Mercedes-Benz", "Classe A"):    "A-CLASS",
    ("Mercedes-Benz", "Classe B"):    "B-CLASS",
    ("Mercedes-Benz", "Classe C"):    "C-CLASS",
    ("Mercedes-Benz", "Classe E"):    "E-CLASS",
    ("Mercedes-Benz", "Classe V"):    "V-CLASS",
    ("Mercedes-Benz", "E Coupe"):     "E-CLASS COUPE",
    ("Mercedes-Benz", "GLC"):         "GLC",
    ("Mercedes-Benz", "GLE"):         "GLE",
    ("Mercedes-Benz", "GLS"):         "GLS",
    ("Mercedes-Benz", "GLA"):         "GLA",
    ("Mercedes-Benz", "CLA"):         "CLA",
    ("Mercedes-Benz", "CLE"):         "CLE",
    ("Renault", "Clio"):              "CLIO",
    ("Renault", "Megane"):            "MEGANE",
    ("Renault", "Captur"):            "CAPTUR",
    ("Renault", "5 E-Tech"):          "5",
    ("Toyota", "Yaris Cross"):        "YARIS CROSS",
    ("Toyota", "GR Yaris"):          "GR YARIS",
    ("Toyota", "Aygo X"):            "AYGO X",
    ("Toyota", "C-HR"):              "C-HR",
    ("Toyota", "Proace City Verso"):  "PROACE CITY VERSO",
    ("Kia", "Ceed"):                 "CEED",
    ("Kia", "Picanto"):              "PICANTO",
    ("Kia", "Stonic"):               "STONIC",
    ("Kia", "EV6"):                  "EV6",
    ("Kia", "EV3"):                  "EV3",
    ("Kia", "Niro"):                 "NIRO",
    ("Hyundai", "Ioniq 5"):          "IONIQ 5",
    ("Hyundai", "Ioniq 6"):          "IONIQ 6",
    ("Hyundai", "Bayon"):            "BAYON",
    ("Peugeot", "E-308"):            "E-308",
    ("Land Rover", "Range Rover Evoque"):  "RANGE ROVER EVOQUE",
    ("Land Rover", "Range Rover Sport"):   "RANGE ROVER SPORT",
    ("Land Rover", "Range Rover Velar"):   "RANGE ROVER VELAR",
    ("Land Rover", "Discovery Sport"):     "DISCOVERY SPORT",
    ("Subaru", "BRZ"):               "BRZ",
    ("Honda", "e:Ny1"):              "E:NY1",
    ("Opel", "Combo Life"):          "COMBO LIFE",
    ("Opel", "Grandland"):           "GRANDLAND X",
    ("MINI", "Countryman"):          "COUNTRYMAN",
    ("MINI", "Clubman"):             "CLUBMAN",
    ("MINI", "Cooper"):              "COOPER",
}

# Safety-critical component keywords → high weight
SAFETY_CRITICAL_PATTERNS = re.compile(
    r"\b(engine|fuel|brake|brakes|braking|steering|airbag|air bag|seat belt|seatbelt|"
    r"suspension|transmission|powertrain|throttle|accelerat|fire|ignition|"
    r"motor|fuel system|fuel pump|fuel line|fuel tank)\b",
    re.IGNORECASE,
)


def _nhtsa_model_name(brand: str, model: str) -> str:
    """Return the NHTSA-style model name for a DB (brand, model) pair."""
    override = MODEL_OVERRIDES.get((brand, model))
    if override:
        return override
    return model.upper()


def _is_safety_critical(text_blob: str) -> bool:
    return bool(SAFETY_CRITICAL_PATTERNS.search(text_blob))


def _fetch_recalls(make: str, model: str, year: int, timeout: int = 20) -> list[dict]:
    try:
        resp = requests.get(
            RECALLS_URL,
            params={"make": make, "model": model, "modelYear": year},
            timeout=timeout,
        )
        if resp.status_code == 404:
            return []
        resp.raise_for_status()
        data = resp.json()
        return data.get("results", [])
    except Exception as e:
        logger.debug(f"NHTSA recalls error {make}/{model}/{year}: {e}")
        return []


def _fetch_complaints(make: str, model: str, year: int, timeout: int = 20) -> list[dict]:
    try:
        resp = requests.get(
            COMPLAINTS_URL,
            params={"make": make, "model": model, "modelYear": year},
            timeout=timeout,
        )
        if resp.status_code == 404:
            return []
        resp.raise_for_status()
        data = resp.json()
        return data.get("results", [])
    except Exception as e:
        logger.debug(f"NHTSA complaints error {make}/{model}/{year}: {e}")
        return []


def _already_ingested(db: Session, generation_id: int, source_url: str) -> bool:
    row = db.execute(text("""
        SELECT 1 FROM reliability_evidence
        WHERE generation_id = :gid AND source_url = :url
        LIMIT 1
    """), {"gid": generation_id, "url": source_url}).fetchone()
    return row is not None


def _upsert_evidence(db: Session, generation_id: int, engine_id, evidence_type: str,
                     source_url: str, observed_month: date, fail_eff: float,
                     weight: float, payload: dict) -> None:
    db.execute(text("""
        INSERT INTO reliability_evidence
            (generation_id, engine_id, evidence_type, source, source_url,
             observed_month, fail_eff, succ_eff, weight, payload)
        VALUES
            (:gen_id, :eng_id, :ev_type, 'nhtsa', :url,
             :month, :fail_eff, 0, :weight, :payload::jsonb)
        ON CONFLICT DO NOTHING
    """), {
        "gen_id":   generation_id,
        "eng_id":   engine_id,
        "ev_type":  evidence_type,
        "url":      source_url,
        "month":    observed_month,
        "fail_eff": fail_eff,
        "weight":   weight,
        "payload":  json.dumps(payload),
    })


def ingest_nhtsa_for_generation(
    db: Session,
    generation_id: int,
    brand: str,
    model: str,
    year_start: int,
    year_end: int,
    engine_id=None,
    sleep_seconds: float = 0.5,
) -> dict:
    """
    Ingest NHTSA recalls and complaints for all model years in a generation range.
    Returns per-call stats.
    """
    stats = {"recalls_ingested": 0, "complaints_ingested": 0,
             "skipped_duplicate": 0, "errors": 0, "years_checked": 0}

    nhtsa_makes = BRAND_TO_NHTSA.get(brand, [])
    if not nhtsa_makes:
        return stats  # brand not mapped to NHTSA

    nhtsa_model = _nhtsa_model_name(brand, model)
    observed_month = date.today().replace(day=1)
    years = range(year_start, min(year_end, date.today().year) + 1)

    for make in nhtsa_makes:
        for year in years:
            stats["years_checked"] += 1

            # ── Recalls ──────────────────────────────────────────
            try:
                recalls = _fetch_recalls(make, nhtsa_model, year)
                for recall in recalls:
                    campaign_number = recall.get("NHTSACampaignNumber", "")
                    component = recall.get("Component", "")
                    summary = recall.get("Summary", "")
                    consequence = recall.get("Consequence", "")
                    remedy = recall.get("Remedy", "")
                    report_date = recall.get("ReportReceivedDate", "")

                    source_url = (
                        f"https://www.nhtsa.gov/vehicle/recalls#campaigns/{campaign_number}"
                        if campaign_number else
                        f"nhtsa://recall/{make}/{nhtsa_model}/{year}/{hash(summary)}"
                    )

                    if _already_ingested(db, generation_id, source_url):
                        stats["skipped_duplicate"] += 1
                        continue

                    text_blob = f"{component} {summary} {consequence}"
                    if _is_safety_critical(text_blob):
                        fail_eff, weight = 6.0, 1.0
                    else:
                        fail_eff, weight = 3.0, 0.6

                    _upsert_evidence(
                        db, generation_id, engine_id,
                        evidence_type="recall",
                        source_url=source_url,
                        observed_month=observed_month,
                        fail_eff=fail_eff,
                        weight=weight,
                        payload={
                            "campaign": campaign_number,
                            "component": component,
                            "summary": summary[:500],
                            "consequence": consequence[:300],
                            "remedy": remedy[:300],
                            "report_date": report_date,
                            "make": make,
                            "model": nhtsa_model,
                            "year": year,
                        },
                    )
                    stats["recalls_ingested"] += 1

            except Exception as e:
                logger.error(f"Recall processing error {make}/{nhtsa_model}/{year}: {e}")
                stats["errors"] += 1

            time.sleep(sleep_seconds)

            # ── Complaints ────────────────────────────────────────
            try:
                complaints = _fetch_complaints(make, nhtsa_model, year)

                if complaints:
                    # Separate severe from routine
                    severe = [c for c in complaints
                              if c.get("crash") or c.get("fire") or
                              (c.get("numberOfInjuries") or 0) > 0 or
                              (c.get("numberOfDeaths") or 0) > 0]
                    routine = [c for c in complaints if c not in severe]

                    # Ingest each severe complaint individually
                    for complaint in severe:
                        complaint_id = complaint.get("odiNumber", "")
                        component = complaint.get("components", "")
                        summary = (complaint.get("summary") or "")[:500]
                        source_url = (
                            f"https://api.nhtsa.gov/complaints/{complaint_id}"
                            if complaint_id else
                            f"nhtsa://complaint/severe/{make}/{nhtsa_model}/{year}/{hash(summary)}"
                        )

                        if _already_ingested(db, generation_id, source_url):
                            stats["skipped_duplicate"] += 1
                            continue

                        _upsert_evidence(
                            db, generation_id, engine_id,
                            evidence_type="nlp_complaint",
                            source_url=source_url,
                            observed_month=observed_month,
                            fail_eff=4.0,
                            weight=0.8,
                            payload={
                                "odi_number": complaint_id,
                                "component": component,
                                "crash": complaint.get("crash"),
                                "fire": complaint.get("fire"),
                                "injuries": complaint.get("numberOfInjuries"),
                                "deaths": complaint.get("numberOfDeaths"),
                                "summary": summary,
                                "make": make,
                                "model": nhtsa_model,
                                "year": year,
                            },
                        )
                        stats["complaints_ingested"] += 1

                    # Routine complaints → one aggregate evidence row per year
                    if routine:
                        n = len(routine)
                        agg_url = (
                            f"nhtsa://complaints/routine/{make}/{nhtsa_model}/{year}"
                        )
                        if not _already_ingested(db, generation_id, agg_url):
                            fail_eff = min(n * 0.1, 6.0)
                            _upsert_evidence(
                                db, generation_id, engine_id,
                                evidence_type="nlp_complaint",
                                source_url=agg_url,
                                observed_month=observed_month,
                                fail_eff=fail_eff,
                                weight=0.3,
                                payload={
                                    "aggregate": True,
                                    "n_complaints": n,
                                    "make": make,
                                    "model": nhtsa_model,
                                    "year": year,
                                },
                            )
                            stats["complaints_ingested"] += 1
                        else:
                            stats["skipped_duplicate"] += 1

            except Exception as e:
                logger.error(f"Complaint processing error {make}/{nhtsa_model}/{year}: {e}")
                stats["errors"] += 1

            time.sleep(sleep_seconds)

    return stats


def ingest_nhtsa_all(db: Session, sleep_seconds: float = 0.5) -> dict:
    """
    Full backfill: ingest NHTSA evidence for all (generation, brand, model, years) in the DB.
    Run once on first setup, then call monthly for incremental updates.

    Returns aggregate stats.
    """
    totals = {"recalls_ingested": 0, "complaints_ingested": 0,
              "skipped_duplicate": 0, "errors": 0, "years_checked": 0,
              "generations_processed": 0}

    gen_rows = db.execute(text("""
        SELECT DISTINCT
            g.id          AS generation_id,
            g.year_start,
            g.year_end,
            vm.name       AS model_name,
            b.name        AS brand_name
        FROM generations g
        JOIN vehicle_models vm ON g.model_id = vm.id
        JOIN brands b ON vm.brand_id = b.id
        ORDER BY b.name, vm.name, g.year_start
    """)).mappings().fetchall()

    for row in gen_rows:
        gen_id     = row["generation_id"]
        brand      = row["brand_name"]
        model      = row["model_name"]
        year_start = row["year_start"] or 2010
        year_end   = row["year_end"]   or date.today().year

        try:
            stats = ingest_nhtsa_for_generation(
                db, gen_id, brand, model, year_start, year_end,
                sleep_seconds=sleep_seconds,
            )
            for k in ("recalls_ingested", "complaints_ingested",
                      "skipped_duplicate", "errors", "years_checked"):
                totals[k] += stats[k]
            totals["generations_processed"] += 1

            if (totals["generations_processed"] % 10) == 0:
                db.commit()
                logger.info(
                    f"NHTSA progress: {totals['generations_processed']} generations, "
                    f"{totals['recalls_ingested']} recalls, "
                    f"{totals['complaints_ingested']} complaints"
                )

        except Exception as e:
            logger.error(f"NHTSA gen={gen_id} {brand} {model}: {e}")
            totals["errors"] += 1

    db.commit()
    logger.info(f"NHTSA ingest complete: {totals}")
    return totals
