"""
Export the data behind the public model pages (/carros/<slug>) to the frontend.

    python -m scripts.export_model_pages            # reads DATABASE_URL, writes frontend/data/models.json

The pages are generated at build time from this file, so they never wait for
the API (which sleeps on the free tier) and a search engine always gets a
complete page. Run it after each monthly market snapshot and commit the file.

Only what the database can stand behind goes in: measured prices by
registration year, engines with their years and the listings they were seen
in, generations with the page their years were checked on, the brand's
reliability with the studies it rests on, and human-approved known faults
(none while every entry is still a draft). Read-only.
"""
import json
import os
import re
import sys
import unicodedata
from collections import defaultdict
from datetime import date

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND)
OUT = os.path.join(os.path.dirname(BACKEND), "frontend", "data", "models.json")

# A page is worth indexing when the market gives it something to say.
MIN_PRICED_YEARS = 3
PRICE_YEARS_SHOWN = 15
RELATED = 4


def slugify(text: str) -> str:
    text = text.replace("+", " plus").replace("#", "")      # Ford Ka+ is not the Ka; Smart #1
    s = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def model_slug(brand: str, model: str) -> str:
    return slugify(f"{brand} {model}")


def _num(v):
    if v is None:
        return None
    f = float(v)
    return int(f) if f == int(f) else round(f, 1)


def build(db) -> dict:
    from sqlalchemy import text

    from app.services.known_issues import load_issues, matches_engine, to_payload, years_overlap

    rows = lambda sql, **kw: [dict(r) for r in db.execute(text(sql), kw).mappings()]  # noqa: E731
    models = rows("""
        SELECT vm.id, b.name AS brand, vm.name AS model, vm.body_type, vm.segment,
               dc.comfort_score, dc.driving_fun_score, dc.city_score, dc.highway_score,
               dc.family_score, dc.description
        FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
        LEFT JOIN driving_character dc ON dc.model_id = vm.id
        WHERE COALESCE(vm.body_type, '') <> ''
        ORDER BY b.name, vm.name
    """)
    gens = defaultdict(list)
    for g in rows("""SELECT model_id, name, year_start, year_end, fuel_type, source_url,
                            market_value_p50, depreciation_pct_year
                     FROM generations ORDER BY year_start"""):
        gens[g["model_id"]].append(g)
    engines = defaultdict(list)
    for e in rows("""SELECT model_id, code, fuel_type, plug_in, displacement_cc, power_hp, transmission,
                            consumption_mixed, co2_emissions, year_from, year_to, listings_seen,
                            reliability_score, maintenance_cost_year
                     FROM engines ORDER BY COALESCE(listings_seen, 0) DESC, power_hp"""):
        engines[e["model_id"]].append(e)
    prices = defaultdict(list)
    for p in rows("""SELECT model_id, year, avg_price, min_price, max_price, sample_count, updated_at
                     FROM market_price_stats WHERE source = 'aggregated' ORDER BY year DESC"""):
        prices[p["model_id"]].append(p)
    on_sale = {r["model_id"]: r["n"] for r in rows("""
        SELECT model_id, COUNT(*) AS n FROM price_observations
        WHERE extraction_method = 'search_snapshot'
          AND observed_at > NOW() - INTERVAL '60 days' AND model_id IS NOT NULL
        GROUP BY model_id""")}
    brand_rel = {r["brand"]: r for r in rows("""
        SELECT b.name AS brand, r.score, r.studies, r.sources FROM brand_reliability r
        JOIN brands b ON b.id = r.brand_id""")}
    snapshot = rows("""SELECT collected_on, listings_read FROM market_snapshot_runs
                       ORDER BY collected_on DESC LIMIT 1""")
    issues = load_issues()          # approved entries only

    out = []
    for m in models:
        mid = m["id"]
        py = [{"year": p["year"], "p10": p["min_price"], "p50": p["avg_price"], "p90": p["max_price"],
               "n": p["sample_count"]} for p in prices[mid][:PRICE_YEARS_SHOWN]]
        eng = [{
            "code": e["code"], "fuel": e["fuel_type"], "plug_in": bool(e["plug_in"]),
            "cc": e["displacement_cc"], "hp": e["power_hp"], "gearbox": e["transmission"],
            "consumption": _num(e["consumption_mixed"]), "co2": e["co2_emissions"],
            "year_from": e["year_from"], "year_to": e["year_to"], "listings": e["listings_seen"],
            "reliability": _num(e["reliability_score"]), "maintenance": e["maintenance_cost_year"],
        } for e in engines[mid]]
        model_gens = gens[mid]
        known = []
        for issue in issues:
            if any(years_overlap(issue, g["year_start"], g["year_end"]) for g in model_gens) and any(
                    matches_engine(issue, brand=m["brand"], model=m["model"], label=e["code"] or "",
                                   fuel=e["fuel_type"] or "", displacement_cc=e["displacement_cc"],
                                   transmission=e["transmission"] or "", power_hp=e["power_hp"])
                    for e in engines[mid]):
                known.append(to_payload(issue))
        rel = brand_rel.get(m["brand"])
        indexable = len(py) >= MIN_PRICED_YEARS and bool(eng)
        out.append({
            "slug": model_slug(m["brand"], m["model"]),
            "brand": m["brand"], "model": m["model"],
            "body": m["body_type"], "segment": m["segment"],
            "character": None if m["comfort_score"] is None else {
                "comfort": m["comfort_score"], "fun": m["driving_fun_score"], "city": m["city_score"],
                "highway": m["highway_score"], "family": m["family_score"], "text": m["description"]},
            "generations": [{"name": g["name"], "from": g["year_start"], "to": g["year_end"],
                             "fuel_only": g["fuel_type"], "source": g["source_url"],
                             "depreciation": None if g["depreciation_pct_year"] is None
                             else round(float(g["depreciation_pct_year"]), 4)} for g in model_gens],
            "prices": py,
            "engines": eng,
            "on_sale": on_sale.get(mid, 0),
            "brand_reliability": None if not rel else {
                "score": _num(rel["score"]), "studies": rel["studies"],
                "sources": [s.get("name") for s in (rel["sources"] or [])]},
            "known_issues": known,
            "indexable": indexable,
        })

    # Related models: same body type, closest typical price.
    def typical(p):
        return p["prices"][0]["p50"] if p["prices"] else None
    for p in out:
        if not typical(p):
            p["related"] = []
            continue
        same = [q for q in out if q is not p and q["body"] == p["body"] and typical(q) and q["indexable"]]
        same.sort(key=lambda q: abs(typical(q) - typical(p)))
        p["related"] = [q["slug"] for q in same[:RELATED]]

    slugs = [p["slug"] for p in out]
    dupes = {s for s in slugs if slugs.count(s) > 1}
    if dupes:
        raise SystemExit(f"two models share a page address: {sorted(dupes)}")
    return {
        "generated_on": date.today().isoformat(),
        "snapshot": None if not snapshot else {
            "collected_on": snapshot[0]["collected_on"].isoformat(), "listings": snapshot[0]["listings_read"]},
        "models": out,
    }


def main() -> int:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(BACKEND, ".env"))
    from sqlalchemy import text

    from app.db.database import SessionLocal

    db = SessionLocal()
    try:
        db.execute(text("SET TRANSACTION READ ONLY"))
        data = build(db)
    finally:
        db.rollback()
        db.close()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    n = len(data["models"])
    idx = sum(m["indexable"] for m in data["models"])
    print(f"{OUT}: {n} models, {idx} indexable, {os.path.getsize(OUT) // 1024} KB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
