"""
Market snapshot — every car listed on Standvirtual under the catalogue's brands.

Why: market_price_stats was seeded with placeholder prices and
price_observations held 36 rows. The old batch scraper asked each source for
20–60 listings per generation by model name, so it never saw body variants
(the site files "A3 Sportback" as its own model) and read a fraction of the
market. This reads all of it, once, politely, and keeps what a price needs.

Two steps, deliberately apart:

  collect   network only, no database. One search per make, every result
            page, in the site's own data (__NEXT_DATA__). Writes one JSON line
            per listing. Run from a residential connection.
  load      database only. Assigns each listing to a catalogue model and
            generation and upserts it into price_observations (by listing URL).
            market_aggregator.run_aggregation then turns observations into
            prices.

A listing is assigned to a catalogue model by the site's own model of it
("a3-sportback" -> Audi A3), through ad_analysis_service.match_catalogue_model
— the same strict matcher a single analysed listing goes through. Listings of
models the catalogue does not have are kept in the file (model_id null) so the
gaps can be counted, and are not loaded.

No seller data is read or stored: no names, phones, or seller ids.
"""
import asyncio
import json
import math
import random
import re
from datetime import date, datetime, timezone
from typing import Callable, Optional

from app.scrapers import standvirtual as sv
from app.scrapers.sv_models import find_make, find_model
from app.scrapers.sv_models_data import SV_MODELS
from app.scrapers.sv_series import find_series, find_variant
from app.scrapers.sv_series_data import SV_SERIES
from app.services.ad_analysis_service import _norm_name, _pick_generation, match_catalogue_model
from app.services.known_issues import normalize_fuel

# The site's fuel ids -> ours. `powertrain` keeps the site's id, which also
# tells a plug-in from a full hybrid.
_FUEL_BY_SV_ID = {
    "diesel": "diesel", "gaz": "gasolina", "electric": "eletrico",
    "hibride-gaz": "hibrido", "hibride-diesel": "hibrido", "plugin-hybrid": "hibrido",
    "gpl": "gpl", "gnc": "gpl",
}
_CONVERTIBLE = re.compile(r"\b(cabrio|cabriolet|roadster|spider|spyder|descapotavel)\b")
_COUPE = re.compile(r"\bcoupe\b")

# Catalogue models that are one fuel of a site model: the catalogue's "MG ZS
# EV" is the site's "zs" (petrol, hybrid and electric) with electric power.
_ELECTRIC_ONLY = {("mg", "zs")}

_PAGE_PAUSE = (1.1, 1.9)          # seconds between requests
_RETRY_WAITS = (8, 30, 90)        # after a failed request
_MAX_SPAN = 2500                  # results one search is paged through; more is split by year


# ── Which catalogue model is a listing? ──────────────────────────────────────

def site_model_names(make: str) -> dict:
    """{site model id: (name, series name or None)} for one make: plain models,
    and for BMW, Mercedes-Benz, Lexus and the Porsche 911 the sub-models
    ("320" of "Série 3")."""
    names = {mid: (name, None) for mid, name in SV_MODELS.get(make, {}).items()}
    for series_id, (series_name, subs) in SV_SERIES.get(make, {}).items():
        series_name = series_name.replace(" (Todos)", "")
        names[series_id] = (series_name, None)
        for sub_id, sub_name in subs.items():
            names[sub_id] = (sub_name, series_name)
    return names


def build_assigner(catalogue: list) -> Callable[[str, str, str], Optional[dict]]:
    """
    assign(make, site model id, title, powertrain) -> {"model_id", "convertible"} or None.

    `catalogue`: vehicle_models rows as {id, brand_name, model_name, body_type}.
    Stub models (no body type — auto-created from an unmatched listing) are
    never assigned to.
    """
    real = [c for c in catalogue if (c.get("body_type") or "").strip()]
    brand_of_make: dict = {}
    explicit: dict = {}       # (make, site id) -> catalogue id, from our own aliases
    for c in real:
        make = find_make(c["brand_name"])
        if not make:
            continue
        brand_of_make.setdefault(make, c["brand_name"])
        if find_series(make, c["model_name"]) or find_variant(make, c["model_name"]):
            continue
        for site_id in (find_model(make, c["model_name"]) or "").split("--"):
            if site_id:
                # A name the alias table spells out ("Superb Combi" -> superb-break)
                # beats the base model that would also match ("Superb").
                current = explicit.get((make, site_id))
                if current is None or len(c["model_name"]) > len(current[1]):
                    explicit[(make, site_id)] = (c["id"], c["model_name"])
    names = {make: site_model_names(make) for make in brand_of_make}
    by_id = {c["id"]: c for c in real}
    cache: dict = {}

    def match(brand: str, name: str) -> Optional[int]:
        words = name.split()
        if not words:
            return None
        row = match_catalogue_model(real, brand, name, words[0])
        return row["id"] if row else None

    def assign(make: str, site_id: str, title: str = "", powertrain: str = "") -> Optional[dict]:
        brand = brand_of_make.get(make)
        if not brand or not site_id:
            return None
        if (make, site_id) in _ELECTRIC_ONLY and powertrain != "electric":
            return None
        name, series_name = names[make].get(site_id, (None, None))
        title_n = _norm_name(title)
        open_top = bool(_CONVERTIBLE.search(title_n) or _CONVERTIBLE.search(_norm_name(name or "")))
        # Mercedes files a coupé under the saloon's sub-model ("E 220"); only
        # the title says it. The catalogue has the E Coupé as its own model.
        coupe = make == "mercedes-benz" and bool(_COUPE.search(title_n))
        key = (make, site_id, coupe)
        if key not in cache:
            model_id = None
            if (make, site_id) in explicit:
                model_id = explicit[(make, site_id)][0]
            elif name:
                model_id = match(brand, f"{name} Coupé" if coupe else name)
                if model_id is None and series_name:
                    model_id = match(brand, series_name)
            cache[key] = model_id
        model_id = cache[key]
        if model_id is None:
            return None
        return {"model_id": model_id,
                "model_name": by_id[model_id]["model_name"],
                # An open-top version of a car that is not one prices differently.
                "convertible": open_top}

    assign.makes = sorted(brand_of_make)          # type: ignore[attr-defined]
    assign.brand_of_make = brand_of_make          # type: ignore[attr-defined]
    return assign


# ── collect ──────────────────────────────────────────────────────────────────

def _search_url(make: str, page: int = 1, year_from: Optional[int] = None,
                year_to: Optional[int] = None) -> str:
    params = []
    if year_from:
        params.append(f"search[filter_float_first_registration_year:from]={year_from}")
    if year_to:
        params.append(f"search[filter_float_first_registration_year:to]={year_to}")
    if page > 1:
        params.append(f"page={page}")
    return f"{sv.SEARCH_URL}/{make}" + ("?" + "&".join(params) if params else "")


def listing_from_node(node: dict) -> Optional[dict]:
    """One search result as a snapshot record; None when it has no URL or price."""
    url = node.get("url") or ""
    params = {p.get("key"): p for p in (node.get("parameters") or []) if isinstance(p, dict)}

    def value(key: str, field: str = "value") -> str:
        return str((params.get(key) or {}).get(field) or "")

    amount = ((node.get("price") or {}).get("amount") or {})
    price = amount.get("units") if amount.get("currencyCode") == "EUR" else None
    if not url or not isinstance(price, (int, float)) or price <= 0:
        return None
    seller = ((node.get("seller") or {}).get("__typename") or "")
    cc = re.search(r"\d{3,5}", value("engine_capacity"))
    return {
        "sv_id": str(node.get("id") or ""),
        "url": url,
        "title": node.get("title") or "",
        "make": value("make"),
        "sv_model": value("model"),
        "version": value("version", "displayValue"),
        "powertrain": value("fuel_type"),
        "gearbox": value("gearbox"),
        "km": sv._parse_km(value("mileage")),
        "cc": int(cc.group(0)) if cc else None,
        "hp": sv._card_power_hp(value("engine_power"), value("engine_power", "displayValue")),
        "year": sv._parse_year(value("first_registration_year")),
        "origin": value("origin"),
        "price": int(price),
        "seller_type": ("privado" if seller == "PrivateSeller"
                        else "stand" if seller == "ProfessionalSeller" else "desconhecido"),
        "listed_at": node.get("createdAt"),
    }


async def _get_search(client, url: str, log: Callable[[str], None]) -> Optional[dict]:
    """The search data of one results page, retried a few times; None when the
    site keeps refusing."""
    for attempt, wait in enumerate((0, *_RETRY_WAITS)):
        if wait:
            log(f"    retry in {wait}s ({url})")
            await asyncio.sleep(wait)
        try:
            resp = await client.get(url)
            if resp.status_code == 200:
                search = sv._search_data(resp.text)
                if search is not None:
                    return search
                log(f"    no search data in page (attempt {attempt + 1})")
            else:
                log(f"    HTTP {resp.status_code} (attempt {attempt + 1})")
        except Exception as e:
            log(f"    {type(e).__name__}: {e} (attempt {attempt + 1})")
    return None


async def collect_make(client, make: str, log: Callable[[str], None] = print,
                       year_from: Optional[int] = None, year_to: Optional[int] = None) -> dict:
    """
    Every listing of one make (optionally one span of registration years).
    Returns {"listings": [...], "total": the site's count, "complete": bool}.
    A search of more than _MAX_SPAN results is split in two by year.
    """
    first = await _get_search(client, _search_url(make, 1, year_from, year_to), log)
    if first is None:
        return {"listings": [], "total": None, "complete": False}
    meta = sv._search_meta(first)
    if "filter_enum_make" not in meta["applied"]:
        log(f"  {make}: make not recognised by the site — skipped")
        return {"listings": [], "total": None, "complete": False}
    total, size = meta["total"], meta["page_size"] or 32
    if total > _MAX_SPAN:
        lo, hi = year_from or 1990, year_to or date.today().year
        if lo < hi:
            mid = (lo + hi) // 2
            a = await collect_make(client, make, log, year_from, mid)
            b = await collect_make(client, make, log, mid + 1, year_to)
            return {"listings": a["listings"] + b["listings"],
                    "total": (a["total"] or 0) + (b["total"] or 0),
                    "complete": a["complete"] and b["complete"]}
    listings = [r for r in (listing_from_node((e or {}).get("node") or {})
                            for e in first.get("edges") or []) if r]
    complete = True
    for page in range(2, math.ceil(total / size) + 1):
        await asyncio.sleep(random.uniform(*_PAGE_PAUSE))
        search = await _get_search(client, _search_url(make, page, year_from, year_to), log)
        if search is None:
            complete = False
            break
        edges = search.get("edges") or []
        if not edges:
            break
        listings += [r for r in (listing_from_node((e or {}).get("node") or {}) for e in edges) if r]
    span = f" {year_from or ''}–{year_to or ''}" if (year_from or year_to) else ""
    log(f"  {make}{span}: {len(listings)} read of {total}")
    return {"listings": listings, "total": total, "complete": complete}


async def collect(catalogue: list, out_path: str, makes: Optional[list] = None,
                  log: Callable[[str], None] = print) -> dict:
    """
    Read every listing of the catalogue's makes into `out_path` (JSON lines,
    one listing each, with the catalogue model it was assigned to). A make
    already in the file is skipped, so an interrupted run can be resumed.
    """
    import httpx
    import os

    assign = build_assigner(catalogue)
    done: set = set()
    if os.path.exists(out_path):
        with open(out_path, encoding="utf-8") as f:
            done = {json.loads(line)["make"] for line in f if line.strip()}
    todo = [m for m in (makes or assign.makes) if m not in done]
    report = {"makes": {}, "skipped_already_in_file": sorted(done)}
    headers = {
        "User-Agent": sv._random_ua(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "pt-PT,pt;q=0.9,en;q=0.7",
        "Referer": sv.BASE_URL,
    }
    async with httpx.AsyncClient(follow_redirects=True, timeout=25.0, headers=headers) as client:
        for make in todo:
            got = await collect_make(client, make, log)
            unique: dict = {}
            for rec in got["listings"]:
                unique.setdefault(rec["url"], rec)
            now = datetime.now(timezone.utc).isoformat(timespec="seconds")
            assigned = 0
            # Written only when the make was read to the end: a partial make
            # would be skipped as "done" on the next run.
            if got["complete"]:
                with open(out_path, "a", encoding="utf-8") as f:
                    for rec in unique.values():
                        rec["make"] = make
                        hit = assign(make, rec["sv_model"], rec["title"], rec["powertrain"])
                        rec["model_id"] = hit["model_id"] if hit else None
                        rec["convertible"] = bool(hit and hit["convertible"])
                        rec["read_at"] = now
                        assigned += rec["model_id"] is not None
                        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            report["makes"][make] = {"site_total": got["total"], "read": len(unique),
                                     "in_catalogue": assigned, "complete": got["complete"]}
            await asyncio.sleep(random.uniform(*_PAGE_PAUSE))
    return report


# ── load ─────────────────────────────────────────────────────────────────────

def is_plausible(rec: dict, this_year: Optional[int] = None) -> bool:
    """A listing a price statistic may use: a real price, year and mileage.
    1 000 € and below are placeholders ("preço sob consulta"); a car with no
    stated mileage, or a used one showing 0 km, cannot be compared."""
    this_year = this_year or date.today().year
    price, year, km = rec.get("price"), rec.get("year"), rec.get("km")
    if not price or price <= 1000 or price > 500_000:
        return False
    if not year or year < 1990 or year > this_year + 1:
        return False
    if km is None or km < 0 or km > 600_000:
        return False
    if km == 0 and year < this_year - 1:
        return False
    return True


def observation_rows(records: list, generations: list) -> tuple:
    """
    (rows for price_observations, counts) from snapshot records.

    `generations`: rows as {id, model_id, year_start, year_end, fuel_type}.
    A listing whose year no generation of its model covers is still loaded,
    with no generation (it then counts for the model's price by year, not for
    a generation's).
    """
    by_model: dict = {}
    for g in generations:
        by_model.setdefault(g["model_id"], []).append(g)
    this_year = date.today().year
    counts = {"records": len(records), "not_in_catalogue": 0, "convertible": 0,
              "implausible": 0, "no_generation": 0, "rows": 0}
    rows, seen = [], set()
    for rec in records:
        if rec.get("model_id") is None:
            counts["not_in_catalogue"] += 1
            continue
        if rec.get("convertible"):
            counts["convertible"] += 1
            continue
        if not is_plausible(rec, this_year) or rec["url"] in seen:
            counts["implausible"] += 1
            continue
        seen.add(rec["url"])
        fuel = _FUEL_BY_SV_ID.get(rec.get("powertrain") or "") or normalize_fuel(rec.get("powertrain")) or None
        year = rec["year"]
        covering = [g for g in by_model.get(rec["model_id"], [])
                    if (g["year_start"] or 0) <= year <= (g["year_end"] or 9999)]
        gen = _pick_generation(covering, fuel)
        if gen is None:
            counts["no_generation"] += 1
        rows.append({
            "model_id": rec["model_id"], "generation_id": gen["id"] if gen else None,
            "vehicle_year": year, "km": rec["km"], "price": rec["price"], "fuel_type": fuel,
            "seller_type": rec.get("seller_type") or "desconhecido",
            "source_url": rec["url"],
            "engine_power_hp": rec.get("hp"), "engine_cc": rec.get("cc"),
            "gearbox": rec.get("gearbox") or None, "powertrain": rec.get("powertrain") or None,
            "variant": rec.get("sv_model") or None, "version": (rec.get("version") or None),
            "origin": rec.get("origin") or None, "listed_at": rec.get("listed_at"),
            "observed_at": rec.get("read_at"),
        })
    counts["rows"] = len(rows)
    return rows, counts


SNAPSHOT_COLUMNS_SQL = """
ALTER TABLE price_observations
    ADD COLUMN IF NOT EXISTS engine_power_hp INTEGER,
    ADD COLUMN IF NOT EXISTS engine_cc       INTEGER,
    ADD COLUMN IF NOT EXISTS gearbox         VARCHAR(20),
    ADD COLUMN IF NOT EXISTS powertrain      VARCHAR(20),
    ADD COLUMN IF NOT EXISTS variant         VARCHAR(60),
    ADD COLUMN IF NOT EXISTS version         TEXT,
    ADD COLUMN IF NOT EXISTS origin          VARCHAR(20),
    ADD COLUMN IF NOT EXISTS listed_at       TIMESTAMPTZ
"""

_UPSERT_SQL = """
INSERT INTO price_observations
    (model_id, generation_id, vehicle_year, km, price, fuel_type, seller_type,
     source_type, source_domain, source_url, extraction_method, data_quality,
     observation_type, observed_at,
     engine_power_hp, engine_cc, gearbox, powertrain, variant, version, origin, listed_at)
VALUES
    (:model_id, :generation_id, :vehicle_year, :km, :price, :fuel_type, :seller_type,
     'marketplace', 'standvirtual.com', :source_url, 'search_snapshot', NULL,
     'batch', COALESCE(CAST(:observed_at AS timestamptz), now()),
     :engine_power_hp, :engine_cc, :gearbox, :powertrain, :variant, :version, :origin,
     CAST(:listed_at AS timestamptz))
ON CONFLICT (source_url) DO UPDATE SET
    model_id        = EXCLUDED.model_id,
    generation_id   = EXCLUDED.generation_id,
    vehicle_year    = EXCLUDED.vehicle_year,
    km              = EXCLUDED.km,
    price           = EXCLUDED.price,
    fuel_type       = EXCLUDED.fuel_type,
    seller_type     = EXCLUDED.seller_type,
    observed_at     = EXCLUDED.observed_at,
    engine_power_hp = EXCLUDED.engine_power_hp,
    engine_cc       = EXCLUDED.engine_cc,
    gearbox         = EXCLUDED.gearbox,
    powertrain      = EXCLUDED.powertrain,
    variant         = EXCLUDED.variant,
    version         = EXCLUDED.version,
    origin          = EXCLUDED.origin,
    listed_at       = EXCLUDED.listed_at
"""


def reassign(records: list, catalogue: list) -> list:
    """The records with their catalogue model worked out again, against
    `catalogue`. The model ids in a snapshot file are those of the catalogue it
    was collected with; the database it is loaded into may have other ids, new
    models, or a matcher that has learned a name since."""
    assign = build_assigner(catalogue)
    out = []
    for rec in records:
        hit = assign(rec.get("make") or "", rec.get("sv_model") or "", rec.get("title") or "",
                     rec.get("powertrain") or "")
        out.append({**rec, "model_id": hit["model_id"] if hit else None,
                    "convertible": bool(hit and hit["convertible"])})
    return out


# One row per snapshot loaded (also created by migration v64): when it was read,
# how many listings, how many belong to a catalogue model. The audit's market
# coverage figure is read from here.
SNAPSHOT_RUNS_SQL = """
    CREATE TABLE IF NOT EXISTS market_snapshot_runs (
        id               SERIAL PRIMARY KEY,
        source           VARCHAR(50) NOT NULL,
        collected_on     DATE        NOT NULL,
        listings_read    INTEGER     NOT NULL CHECK (listings_read >= 0),
        listings_matched INTEGER     NOT NULL CHECK (listings_matched >= 0),
        listings_loaded  INTEGER     NOT NULL CHECK (listings_loaded >= 0),
        makes            INTEGER,
        notes            JSONB       NOT NULL DEFAULT '{}'::jsonb,
        loaded_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT market_snapshot_runs_matched_le_read CHECK (listings_matched <= listings_read),
        CONSTRAINT uq_market_snapshot_runs UNIQUE (source, collected_on)
    )
"""

_RECORD_RUN_SQL = """
    INSERT INTO market_snapshot_runs
        (source, collected_on, listings_read, listings_matched, listings_loaded, makes, notes)
    VALUES (:source, :collected_on, :read, :matched, :loaded, :makes, CAST(:notes AS jsonb))
    ON CONFLICT (source, collected_on) DO UPDATE SET
        listings_read = EXCLUDED.listings_read, listings_matched = EXCLUDED.listings_matched,
        listings_loaded = EXCLUDED.listings_loaded, makes = EXCLUDED.makes,
        notes = EXCLUDED.notes, loaded_at = NOW()
"""


def run_summary(records: list, counts: dict) -> dict:
    """What market_snapshot_runs records about a load: `records` after reassign,
    `counts` from observation_rows. A convertible of a catalogue model counts
    as matched (the model is known; its price is left out on purpose)."""
    days = sorted((r.get("read_at") or "")[:10] for r in records if r.get("read_at"))
    return {
        "source": "standvirtual",
        "collected_on": days[-1] if days else None,
        "read": len(records),
        "matched": len(records) - counts.get("not_in_catalogue", 0),
        "loaded": counts.get("rows", 0),
        "makes": len({r.get("make") for r in records if r.get("make")}),
        "notes": json.dumps({k: v for k, v in counts.items() if k not in ("records", "rows")}),
    }


def load(db, records: list, batch: int = 500, log: Callable[[str], None] = print) -> dict:
    """Upsert snapshot records into price_observations (by listing URL). Each
    listing is assigned to a model of this database's catalogue first. The run
    is recorded in market_snapshot_runs."""
    from sqlalchemy import text

    db.execute(text(SNAPSHOT_COLUMNS_SQL))
    db.execute(text(SNAPSHOT_RUNS_SQL))
    db.commit()
    catalogue = [dict(r) for r in db.execute(text("""
        SELECT vm.id, b.name AS brand_name, vm.name AS model_name, vm.body_type
        FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id ORDER BY vm.id
    """)).mappings()]
    records = reassign(records, catalogue)
    generations = [dict(r) for r in db.execute(text(
        "SELECT id, model_id, year_start, year_end, fuel_type FROM generations")).mappings()]
    rows, counts = observation_rows(records, generations)
    for start in range(0, len(rows), batch):
        db.execute(text(_UPSERT_SQL), rows[start:start + batch])
        db.commit()
        log(f"  loaded {min(start + batch, len(rows))} of {len(rows)}")
    summary = run_summary(records, counts)
    if summary["collected_on"]:
        db.execute(text(_RECORD_RUN_SQL), summary)
        db.commit()
    return counts
