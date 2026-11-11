"""
EU Safety Gate scraper for Caractr reliability evidence.

Safety Gate (ec.europa.eu/safety-gate-alerts) is the EU's official rapid-alert
system — the most authoritative recall source for cars sold in Portugal.
No authentication. Be polite: throttle between requests.

The old JSON endpoint (/screen/webService/getAlerts) was retired in 2026 and
now serves the web app's HTML. The public API the web app itself uses:

  POST public/api/notification/mostRecent/?   {"language","page"}  100/page,
       the ~350 newest alerts (≈ last 3 weeks)          → monthly incremental
  GET  public/api/webreport/notifications?search=      9/page, the full
       archive back to 2005 (not date-ordered)          → one-off backfill
  GET  public/api/notification/{id}?language=en        full alert detail

List items only carry brand + a generic product name, so we pre-filter on
those and fetch detail only for vehicle alerts from brands we carry.

Severity: Safety Gate publishes no per-alert risk *level*. Notifications under
Art. 12 GPSD ("A12", reference prefix "SR/" or "A12/") are by legal definition
products posing a SERIOUS risk; anything else is treated as medium.

Severity → evidence weight mapping:
  serious → fail_eff = 6.0, weight = 1.0
  high    → fail_eff = 3.0, weight = 0.6
  medium  → fail_eff = 1.5, weight = 0.3
  low     → fail_eff = 0.5, weight = 0.1
"""

import json
import logging
import re
import time
from datetime import date, datetime
from difflib import SequenceMatcher

import requests
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.scrapers.model_match import best_generation, name_match

logger = logging.getLogger(__name__)

API_BASE = "https://ec.europa.eu/safety-gate-alerts/public/api/"
ALERT_PAGE = "https://ec.europa.eu/safety-gate-alerts/screen/webReport/alertDetail/{id}?lang=en"
HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "X-Requested-With": "XMLHttpRequest",
    "User-Agent": "Caractr-reliability-research/1.0 (non-commercial)",
}

SEVERITY_MAP = {
    "serious": {"fail_eff": 6.0, "weight": 1.0},
    "high":    {"fail_eff": 3.0, "weight": 0.6},
    "medium":  {"fail_eff": 1.5, "weight": 0.3},
    "low":     {"fail_eff": 0.5, "weight": 0.1},
}
DEFAULT_SEVERITY = {"fail_eff": 0.5, "weight": 0.1}

# Generic product names that mark a list item as a road vehicle.
_VEHICLE_NAME = re.compile(r"\b(car|cars|vehicle|vehicles|van|suv|pick-?up|motor ?home)\b", re.I)


def _canonical_severity(raw: str) -> str:
    """Normalise any Safety Gate risk string to serious|high|medium|low."""
    s = (raw or "").lower()
    if "serious" in s:
        return "serious"
    if "high" in s:
        return "high"
    if "medium" in s or "moderate" in s:
        return "medium"
    return "low"


def _severity_from_notification(detail: dict) -> str:
    """Art. 12 GPSD notifications are serious-risk by definition."""
    code = ((detail.get("notificationType") or {}).get("code") or "").upper()
    ref = (detail.get("reference") or "").upper()
    if code == "A12" or ref.startswith("SR/") or ref.startswith("A12/"):
        return "serious"
    return "medium"


def _name_match_score(db_model: str, raw_product: str) -> float:
    """1.0 for a strict whole-word match (see model_match), else 0.0 —
    no fuzzy similarity: it put S-Klasse recalls on the A-Class."""
    return 1.0 if name_match(db_model, raw_product) else 0.0


# Brand name normalisation map (Safety Gate uses English / registry names)
BRAND_NORM = {
    "volkswagen": "Volkswagen", "vw": "Volkswagen", "bmw": "BMW",
    "mercedes": "Mercedes-Benz", "mercedes-benz": "Mercedes-Benz", "audi": "Audi",
    "toyota": "Toyota", "renault": "Renault", "peugeot": "Peugeot",
    "citroen": "Citroen", "citroën": "Citroen", "ford": "Ford", "opel": "Opel",
    "vauxhall": "Opel", "honda": "Honda", "hyundai": "Hyundai", "kia": "Kia",
    "skoda": "Skoda", "škoda": "Skoda", "seat": "SEAT", "fiat": "Fiat",
    "alfa romeo": "Alfa Romeo", "volvo": "Volvo", "nissan": "Nissan",
    "mazda": "Mazda", "subaru": "Subaru", "suzuki": "Suzuki",
    "mitsubishi": "Mitsubishi", "land rover": "Land Rover", "range rover": "Land Rover",
    "jaguar": "Jaguar", "porsche": "Porsche", "tesla": "Tesla", "dacia": "Dacia",
    "cupra": "Cupra", "mini": "MINI", "lexus": "Lexus", "jeep": "Jeep", "dodge": "Dodge",
}


def _normalise_brand(raw: str) -> str | None:
    """'Volkswagen (VW)', 'VW - Volkswagen AG', 'BMW AG' → canonical brand."""
    if not raw:
        return None
    key = raw.lower().strip()
    if key in BRAND_NORM:
        return BRAND_NORM[key]
    # Try multi-word keys first ("alfa romeo", "land rover"), then single tokens.
    for k in sorted(BRAND_NORM, key=len, reverse=True):
        if re.search(r"(?<![\w-])" + re.escape(k) + r"(?![\w-])", key):
            return BRAND_NORM[k]
    return None


def _split_models(name_specific: str) -> list[str]:
    """'Caddy, Golf Sportsvan, Golf Variant 7\\t' → ['Caddy', 'Golf Sportsvan', 'Golf Variant 7']."""
    parts = re.split(r"[,;/+\n\t]|\band\b", name_specific or "")
    return [p.strip() for p in parts if p and len(p.strip()) >= 2]


_DATE_YEAR = re.compile(r"\b(19[89]\d|20[0-3]\d)\b")


def _range(years: list[int]) -> list[int]:
    ys = sorted(set(years))
    if len(ys) >= 2 and ys[-1] - ys[0] <= 25:
        return list(range(ys[0], ys[-1] + 1))
    return ys


def _years_for_model(detail: dict, model_raw: str) -> list[int]:
    """Production years for ONE model of a multi-model alert. Batch entries are
    often per model ("Astra H : 03.01.2005 - 14.03.2014 // VIN ..."); pooling
    them credited an Astra H with years that belong to the Mokka A. VIN text is
    dropped so its digits can't be read as years."""
    entries = [(b.get("batchNumber") or "") for b in
               ((detail.get("product") or {}).get("batchNumbers") or [])]
    own, generic = [], []
    for e in entries:
        dates = e.split("//")[0]
        if ":" in dates:
            label, dates = dates.split(":", 1)
            if name_match(model_raw, label) or name_match(label.strip(), model_raw):
                own += [int(y) for y in _DATE_YEAR.findall(dates)]
            continue  # labelled for a different model
        generic += [int(y) for y in _DATE_YEAR.findall(dates)]
    if own:
        return _range(own)
    if generic:
        return _range(generic)
    return _years_from_detail(detail)


def _years_from_detail(detail: dict) -> list[int]:
    """Production years from batch-number date ranges ('04.09.2013 - 01.07.2024')
    plus any 4-digit years in the free text."""
    product = detail.get("product") or {}
    blob = " ".join(
        [b.get("batchNumber") or "" for b in (product.get("batchNumbers") or [])]
        + [product.get("nameSpecific") or ""]
    )
    found = sorted({int(y) for y in re.findall(r"\b(19[89]\d|20[0-3]\d)\b", blob)})
    if len(found) >= 2 and found[-1] - found[0] <= 25:
        return list(range(found[0], found[-1] + 1))
    return found


def _risk_description(detail: dict) -> str:
    for v in ((detail.get("risk") or {}).get("versions") or []):
        if (v.get("language") or {}).get("key") == "EN" and v.get("riskDescription"):
            return v["riskDescription"]
    for v in ((detail.get("risk") or {}).get("versions") or []):
        if v.get("riskDescription"):
            return v["riskDescription"]
    return ""


def _risk_types(detail: dict) -> list[str]:
    return [r.get("name") for r in ((detail.get("risk") or {}).get("riskType") or []) if r.get("name")]


# Safety Gate only returns risk types as enum keys; label them for PT readers.
RISK_PT = {
    "injuries": "Risco de ferimentos", "fire": "Risco de incêndio",
    "environment": "Risco ambiental", "burns": "Risco de queimaduras",
    "electricshock": "Risco de choque elétrico", "electric.shock": "Risco de choque elétrico",
    "chemical": "Risco químico", "damage.to.sight": "Risco para a visão",
    "suffocation": "Risco de asfixia", "cuts": "Risco de cortes", "other": "Outro risco",
}


def _risk_types_pt(detail: dict) -> list[str]:
    out = []
    for r in ((detail.get("risk") or {}).get("riskType") or []):
        key = (r.get("key") or "").replace("riskType.", "").lower()
        out.append(RISK_PT.get(key) or RISK_PT.get(key.replace("_", ".")) or (r.get("name") or "").title())
    return [o for o in out if o]


def _risk_description_lang(detail: dict, lang: str) -> str:
    for v in ((detail.get("risk") or {}).get("versions") or []):
        if (v.get("language") or {}).get("key") == lang.upper() and v.get("riskDescription"):
            return v["riskDescription"]
    return ""


def _measures(detail: dict) -> str:
    ms = ((detail.get("measureTaken") or {}).get("measures") or [])
    names = [((m.get("measureCategory") or {}).get("name") or "").replace("_", " ").lower() for m in ms]
    return "; ".join(sorted({n for n in names if n}))


def _is_vehicle_detail(detail: dict) -> bool:
    key = (((detail.get("product") or {}).get("productCategory") or {}).get("key") or "")
    return "motor.vehicles" in key


def _find_generation(db: Session, brand_name: str, model_name_raw: str,
                     years: list[int]) -> int | None:
    """Match one alert model string to a generation (rules in model_match)."""
    rows = db.execute(text("""
        SELECT g.id, g.year_start, g.year_end, vm.name as model_name, g.name AS gen_name
        FROM generations g
        JOIN vehicle_models vm ON g.model_id = vm.id
        JOIN brands b ON vm.brand_id = b.id
        WHERE b.name = :brand
    """), {"brand": brand_name}).mappings().fetchall()
    return best_generation(rows, model_name_raw, years)


def _already_ingested(db: Session, generation_id: int, source_url: str) -> bool:
    """Check if this exact alert URL was already stored for this generation."""
    row = db.execute(text("""
        SELECT 1 FROM reliability_evidence
        WHERE generation_id = :gid AND source_url = :url
        LIMIT 1
    """), {"gid": generation_id, "url": source_url}).fetchone()
    return row is not None


def _url_seen(db: Session, source_url: str) -> bool:
    return db.execute(text("SELECT 1 FROM reliability_evidence WHERE source_url = :u LIMIT 1"),
                      {"u": source_url}).fetchone() is not None


# ── HTTP ─────────────────────────────────────────────────────────────────────

def _fetch_recent_page(page: int) -> dict:
    r = requests.post(API_BASE + "notification/mostRecent/?",
                      json={"language": "en", "page": str(page)},
                      headers={**HEADERS, "Content-Type": "application/json"}, timeout=30)
    r.raise_for_status()
    return r.json()


def _fetch_archive_page(page: int) -> dict:
    r = requests.get(API_BASE + "webreport/notifications",
                     params={"language": "en", "page": str(page), "search": ""},
                     headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.json()


def _fetch_detail(alert_id, language: str = "en") -> dict:
    r = requests.get(API_BASE + f"notification/{alert_id}", params={"language": language},
                     headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.json()


def _pt_texts(alert_id, brand: str, model_raw: str, detail_en: dict) -> dict:
    """Portuguese title/description (the EU's own translation). Best-effort:
    on any failure the English text is still shown."""
    try:
        d = _fetch_detail(alert_id, "pt")
    except Exception:
        d = {}
    desc = _risk_description_lang(d, "PT")
    risks = _risk_types_pt(detail_en)
    return {
        "title_pt": f"{brand} {model_raw}: " + (", ".join(risks) or "Recall"),
        "description_pt": desc[:500],
    }


def _is_candidate(item: dict) -> str | None:
    """Cheap list-level filter: a vehicle product from a brand we carry.
    Returns the normalised brand, or None."""
    product = item.get("product") or {}
    if not _VEHICLE_NAME.search(product.get("name") or ""):
        return None
    for b in (product.get("brands") or []):
        brand = _normalise_brand(b.get("brand") or "")
        if brand:
            return brand
    return None


# ── ingestion ────────────────────────────────────────────────────────────────

def _ingest_detail(db: Session, brand: str, detail: dict, stats: dict) -> None:
    alert_id = detail.get("id")
    url = ALERT_PAGE.format(id=alert_id)
    models = _split_models((detail.get("product") or {}).get("nameSpecific") or "")
    severity = _severity_from_notification(detail)
    sev_data = SEVERITY_MAP.get(severity, DEFAULT_SEVERITY)
    pub = (detail.get("publicationDate") or "")[:10]
    try:
        observed = datetime.strptime(pub, "%Y-%m-%d").date().replace(day=1)
    except ValueError:
        observed = date.today().replace(day=1)
    risk_desc = _risk_description(detail)
    risk_types = _risk_types(detail)

    matched = set()
    pt_cache: dict | None = None  # fetched once, only if a model matches
    for model_raw in models:
        years = _years_for_model(detail, model_raw)
        gen_id = _find_generation(db, brand, model_raw, years)
        if gen_id is None or gen_id in matched:
            continue
        matched.add(gen_id)
        if _already_ingested(db, gen_id, url):
            stats["skipped_duplicate"] += 1
            continue
        title = f"{brand} {model_raw}: " + (", ".join(t.title() for t in risk_types) or "Recall")
        if pt_cache is None:
            pt_cache = _pt_texts(alert_id, brand, "{model}", detail)
        pt = {"title_pt": pt_cache["title_pt"].replace("{model}", model_raw),
              "description_pt": pt_cache["description_pt"]}
        db.execute(text("""
            INSERT INTO reliability_evidence
                (generation_id, evidence_type, source, source_url,
                 observed_month, severity, fail_eff, succ_eff, weight, payload)
            VALUES
                (:gen_id, 'safety_gate', 'eu_safety_gate', :url,
                 :month, :severity, :fail_eff, 0, :weight, CAST(:payload AS jsonb))
            ON CONFLICT DO NOTHING
        """), {
            "gen_id": gen_id, "url": url, "month": observed, "severity": severity,
            "fail_eff": sev_data["fail_eff"], "weight": sev_data["weight"],
            "payload": json.dumps({
                "reference":   detail.get("reference"),
                "brand_raw":   brand,
                "model_raw":   model_raw,
                "models_all":  models,
                "title":       title[:200],
                "description": risk_desc[:500],
                "title_pt":    pt["title_pt"][:200],
                "description_pt": pt["description_pt"],
                "risk":        ", ".join(risk_types)[:300],
                "measures":    _measures(detail)[:300],
                "severity":    severity,
                "pub_date":    pub,
                "years":       years,
            }),
        })
        stats["ingested"] += 1
    if not matched:
        stats["skipped_no_match"] += 1


def ingest_safety_gate(db: Session, max_pages: int | None = 10,
                       sleep_seconds: float = 1.0, mode: str = "recent",
                       start_page: int = 0) -> dict:
    """
    Fetch Safety Gate vehicle alerts and write evidence rows. Idempotent.

    mode="recent"  — the ~350 newest alerts (monthly incremental).
    mode="archive" — page through the full archive (one-off backfill; ~5,300
                     pages of 9). Re-runnable: already-stored alerts are skipped
                     without fetching their detail. start_page resumes an
                     interrupted backfill (progress is logged every 200 pages).

    Returns {ingested, skipped_no_match, skipped_duplicate, candidates, pages, errors}.
    """
    stats = {"ingested": 0, "skipped_no_match": 0, "skipped_duplicate": 0,
             "candidates": 0, "pages": 0, "errors": 0}
    fetch = _fetch_recent_page if mode == "recent" else _fetch_archive_page

    page, total_pages = start_page, None
    while max_pages is None or page < start_page + max_pages:
        try:
            data = fetch(page)
        except Exception as e:
            logger.error(f"Safety Gate {mode} page {page}: {e}")
            print(f"[safety_gate] {mode} page {page} failed: {e}")
            stats["errors"] += 1
            break
        total_pages = data.get("totalPages", total_pages)
        items = data.get("content") or []
        stats["pages"] += 1
        if not items:
            break

        for item in items:
            try:
                brand = _is_candidate(item)
                if not brand:
                    continue
                stats["candidates"] += 1
                if _url_seen(db, ALERT_PAGE.format(id=item.get("id"))):
                    stats["skipped_duplicate"] += 1
                    continue
                detail = _fetch_detail(item["id"])
                time.sleep(sleep_seconds)
                if not _is_vehicle_detail(detail):
                    continue
                _ingest_detail(db, brand, detail, stats)
            except Exception as e:
                db.rollback()
                logger.error(f"Safety Gate alert {item.get('reference')}: {e}")
                stats["errors"] += 1
        db.commit()

        if mode == "archive" and page % 200 == 0:
            print(f"[safety_gate] archive page {page}/{total_pages}: {stats}", flush=True)
        page += 1
        if total_pages is not None and page >= total_pages:
            break
        time.sleep(sleep_seconds)

    return stats


def backfill_portuguese(db: Session, sleep_seconds: float = 0.5) -> dict:
    """Add title_pt/description_pt to Safety Gate rows stored without them.
    One PT detail request per distinct alert. Idempotent."""
    rows = db.execute(text("""
        SELECT id, source_url, payload FROM reliability_evidence
        WHERE source = 'eu_safety_gate' AND NOT (payload ? 'description_pt')
    """)).mappings().fetchall()
    stats = {"rows": len(rows), "alerts": 0, "updated": 0, "errors": 0}
    by_url: dict[str, list] = {}
    for r in rows:
        by_url.setdefault(r["source_url"], []).append(r)
    for url, group in by_url.items():
        stats["alerts"] += 1
        try:
            alert_id = url.split("alertDetail/")[1].split("?")[0]
            desc = _risk_description_lang(_fetch_detail(alert_id, "pt"), "PT")[:500]
        except Exception:
            stats["errors"] += 1
            desc = ""
        for r in group:
            p = r["payload"] if isinstance(r["payload"], dict) else json.loads(r["payload"] or "{}")
            fake = {"risk": {"riskType": [{"key": f"riskType.{t.strip().lower()}", "name": t.strip()}
                                          for t in (p.get("risk") or "").split(",") if t.strip()]}}
            risks = _risk_types_pt(fake)
            title_pt = f"{p.get('brand_raw', '')} {p.get('model_raw', '')}: " + (", ".join(risks) or "Recall")
            db.execute(text("""
                UPDATE reliability_evidence
                SET payload = payload || CAST(:extra AS jsonb)
                WHERE id = :id
            """), {"id": r["id"], "extra": json.dumps({"title_pt": title_pt.strip()[:200],
                                                         "description_pt": desc})})
            stats["updated"] += 1
        db.commit()
        time.sleep(sleep_seconds)
    return stats


def rematch_safety_gate(db: Session) -> dict:
    """Re-run generation matching for stored Safety Gate rows using their saved
    brand / model string / production years — no network. Moves rows whose
    best generation changed under newer matching rules and removes rows that
    no longer match at all. Idempotent."""
    rows = db.execute(text("""
        SELECT id, generation_id, source_url, payload FROM reliability_evidence
        WHERE source = 'eu_safety_gate'
    """)).mappings().fetchall()
    stats = {"rows": len(rows), "moved": 0, "removed": 0, "unchanged": 0, "duplicates_removed": 0}
    for r in rows:
        p = r["payload"] if isinstance(r["payload"], dict) else json.loads(r["payload"] or "{}")
        brand, model_raw = p.get("brand_raw"), p.get("model_raw")
        years = [int(y) for y in (p.get("years") or []) if str(y).isdigit()]
        new_gen = _find_generation(db, brand, model_raw, years) if brand and model_raw else None
        if new_gen == r["generation_id"]:
            stats["unchanged"] += 1
            continue
        if new_gen is None:
            db.execute(text("DELETE FROM reliability_evidence WHERE id = :id"), {"id": r["id"]})
            stats["removed"] += 1
        elif _already_ingested(db, new_gen, r["source_url"]):
            db.execute(text("DELETE FROM reliability_evidence WHERE id = :id"), {"id": r["id"]})
            stats["duplicates_removed"] += 1
        else:
            db.execute(text("UPDATE reliability_evidence SET generation_id = :g WHERE id = :id"),
                       {"g": new_gen, "id": r["id"]})
            stats["moved"] += 1
    db.commit()
    return stats
