"""
Measure the live market pool for a set of common cars — no database needed.

Calls _fetch_live_market_data directly, once per car, and reports what the
Standvirtual search said it has (total results), how many listings came back,
how many survived the filters (the pool), the final sample the price reference
is computed from, the basis of the year/km step, and how long it took.

    cd backend
    python scripts/measure_market_pool.py --tag after --out ../../measurements

Writes <out>/market_pool_<tag>.json (including the raw listings, so filter
choices can be replayed offline) and prints a table. Hits the live marketplace:
one search per car, a pause between cars. Do not run it in a loop.
"""
import argparse
import asyncio
import json
import os
import re
import sys
import time

os.environ.setdefault("DATABASE_URL", "postgresql://user:pass@localhost:5432/measure")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from app.scrapers import dispatcher, standvirtual  # noqa: E402
from app.services import ad_analysis_service as svc  # noqa: E402

# label, brand, model, year, fuel (as the listing page labels it), km,
# generation window (as the generations table would give it), engine hint
# (what _extract_engine_hint finds in a typical description), BMW variant code,
# Standvirtual's own model slug (read from the listing page in production; the
# site files Mercedes and BMW under the variant, "a-180" / "530").
CARS = [
    ("Renault Clio 2019 petrol",        "Renault", "Clio", 2019, "Gasolina", 90000, 2019, None, "1.0 TCe", None, None),
    ("VW Golf 2017 diesel",             "Volkswagen", "Golf", 2017, "Diesel", 150000, 2012, 2019, "1.6 TDI", None, None),
    ("Peugeot 208 2020 petrol",         "Peugeot", "208", 2020, "Gasolina", 70000, 2019, None, "1.2 PureTech", None, None),
    ("BMW 530 2018 plug-in hybrid",     "BMW", "530", 2018, "Híbrido Plug-In", 170000, 2017, 2023, None, "530", "530"),
    ("Fiat 500 2018 petrol",            "Fiat", "500", 2018, "Gasolina", 80000, 2007, None, "1.2", None, None),
    ("Mercedes A 180 d 2019 diesel",    "Mercedes-Benz", "A 180", 2019, "Diesel", 120000, 2018, None, None, None, "a-180"),
    ("Nissan Qashqai 2018 diesel",      "Nissan", "Qashqai", 2018, "Diesel", 140000, 2013, 2021, "1.5 dCi", None, None),
    ("Toyota Yaris 2021 hybrid",        "Toyota", "Yaris", 2021, "Híbrido (Gasolina)", 60000, 2020, None, "1.5", None, None),
    ("Dacia Sandero 2020 petrol",       "Dacia", "Sandero", 2020, "Gasolina", 80000, 2012, 2020, "1.0 SCe", None, None),
    ("Tesla Model 3 2021 electric",     "Tesla", "Model 3", 2021, "Elétrico", 90000, 2017, None, None, None, None),
]

# Cars the catalogue files under a series, analysed from a listing that is not
# from Standvirtual: no site slug, only the listing's title (last field). The
# sub-model to search has to be read from it (--set series).
SERIES_CARS = [
    ("BMW Serie 3 '320d Touring'",      "BMW", "Serie 3", 2020, "Diesel", 120000, 2019, None, None, None, None, "BMW 320d Touring Pack M"),
    ("BMW Serie 1 '116d'",              "BMW", "Serie 1", 2017, "Diesel", 130000, 2011, 2019, None, None, None, "BMW 116d EfficientDynamics"),
    ("BMW Serie 5 '530e'",              "BMW", "Serie 5", 2018, "Híbrido Plug-In", 170000, 2017, 2023, None, None, None, "BMW 530e iPerformance Pack M"),
    ("Mercedes Classe A 'A 180 d'",     "Mercedes-Benz", "Classe A", 2019, "Diesel", 120000, 2018, None, None, None, None, "Mercedes-Benz A 180 d Style Aut."),
    ("Mercedes Classe C 'C 220 d'",     "Mercedes-Benz", "Classe C", 2017, "Diesel", 160000, 2014, 2021, None, None, None, "Mercedes-Benz C 220 d Avantgarde"),
    ("Lexus NX 'NX 300h'",              "Lexus", "NX", 2018, "Híbrido (Gasolina)", 110000, 2014, 2021, None, None, None, "Lexus NX 300h Executive+"),
    ("Mercedes Classe A, no sub-model", "Mercedes-Benz", "Classe A", 2019, "Diesel", 120000, 2018, None, None, None, None, "Mercedes Classe A AMG Line 2019"),
]


def _search_total(html: str):
    """totalCount of the Standvirtual search embedded in a results page."""
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.S)
    if not m:
        return None
    try:
        for entry in json.loads(m.group(1))["props"]["pageProps"]["urqlState"].values():
            search = json.loads(entry["data"]).get("advertSearch")
            if search:
                return search.get("totalCount")
    except Exception:
        return None
    return None


async def _measure(car) -> dict:
    label, brand, model, year, fuel, km, gen_from, gen_to, hint, variant, sv_slug = car[:11]
    title = car[11] if len(car) > 11 else None
    if not sv_slug and title and hasattr(svc, "_market_model_slug"):
        sv_slug = svc._market_model_slug({"source_title": title}, brand, model, None)
    pages, fetched = [], {}

    # The page parser (the card parser before result pages were read from the
    # search data, so the script also runs on older code).
    parser = "_parse_search_page" if hasattr(standvirtual, "_parse_search_page") else "_extract_listings_from_html"
    real_parse = getattr(standvirtual, parser)

    def spy_parse(html, source_url):
        parsed = real_parse(html, source_url)
        cards = parsed[0] if isinstance(parsed, tuple) else parsed
        pages.append({"url": source_url, "total": _search_total(html), "cards": len(cards)})
        return parsed

    real_fetch = dispatcher.fetch_listings_all_sources

    async def spy_fetch(**kwargs):
        listings = await real_fetch(**kwargs)
        fetched["listings"] = listings
        return listings

    setattr(standvirtual, parser, spy_parse)
    dispatcher.fetch_listings_all_sources = spy_fetch
    svc._market_cache.clear()
    started = time.time()
    try:
        stats = await asyncio.wait_for(svc._fetch_live_market_data(
            brand, model, year, fuel_type=fuel, engine_hint=hint,
            gen_year_start=gen_from, gen_year_end=gen_to,
            variant_code=variant, sv_model_slug=sv_slug, km=km), timeout=45)
    except asyncio.TimeoutError:
        stats = {"timeout": True}
    seconds = round(time.time() - started, 1)
    setattr(standvirtual, parser, real_parse)
    dispatcher.fetch_listings_all_sources = real_fetch

    pool = next(iter(svc._market_cache.values()), {}).get("pool", [])
    judged = svc._withhold_if_not_comparable(stats) if stats.get("median_price") else stats
    sample = judged.get("sample_count") or 0
    basis = ((stats.get("year_comparison") or {}).get("basis")
             or (stats.get("km_comparison") or {}).get("basis"))
    listings = fetched.get("listings") or []
    return {
        "label": label, "car": {"year": year, "km": km, "fuel": fuel, "engine_hint": hint, "title": title},
        "searched_as": sv_slug,
        "search_total": pages[0]["total"] if pages else None,
        "pages": pages,
        "fetched": len(listings),
        "pool": len(pool),
        "sample": sample,
        "median": judged.get("median_price"),
        "basis": basis,
        "margin_pct": (stats.get("year_comparison") or {}).get("margin_pct"),
        "verdict": bool(judged.get("median_price")) and sample >= svc._MIN_RELIABLE_MARKET_SAMPLE,
        "seconds": seconds,
        "stats": stats,
        "listings": [{k: l.get(k) for k in ("source", "source_url", "title", "price", "year", "km", "fuel_type")}
                     for l in listings],
    }


async def _main(tag: str, out_dir: str, only: str, car_set: str) -> None:
    rows = []
    for car in (SERIES_CARS if car_set == "series" else CARS):
        if only and only.lower() not in car[0].lower():
            continue
        rows.append(await _measure(car))
        await asyncio.sleep(2.0)   # one search per car, unhurried
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"market_pool_{tag}.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(rows, fh, ensure_ascii=False, indent=1)

    print(f"\n{'car':32} {'total':>6} {'pages':>5} {'fetched':>7} {'pool':>5} {'sample':>6} "
          f"{'median':>7} {'basis':>9} {'verdict':>7} {'secs':>5}")
    for r in rows:
        print(f"{r['label']:32} {str(r['search_total']):>6} {len(r['pages']):>5} {r['fetched']:>7} "
              f"{r['pool']:>5} {r['sample']:>6} {str(r['median']):>7} {str(r['basis']):>9} "
              f"{'yes' if r['verdict'] else 'no':>7} {r['seconds']:>5}")
    print(f"\nsaved {path}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="run")
    ap.add_argument("--out", default="measurements")
    ap.add_argument("--only", default="", help="substring of a car label")
    ap.add_argument("--set", default="common", choices=["common", "series"], dest="car_set")
    args = ap.parse_args()
    asyncio.run(_main(args.tag, args.out, args.only, args.car_set))
