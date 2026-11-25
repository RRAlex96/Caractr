"""
Check, model by model, that Standvirtual applies the make and model we search.

For every (brand, model) it builds the search URL the scraper would use, loads
the first results page and reads from it which filters the site applied and
how many results the search has. A make or model the site does not know is
dropped from the search without an error, so this is the only way to tell.

    cd backend
    python scripts/audit_sv_slugs.py --catalogue models.json --out audit.json
    python scripts/audit_sv_slugs.py --db --out audit.json      # brands/models from DATABASE_URL, read-only

models.json: [["Renault", "Clio"], ["BMW", "Serie 3"], ...]. One request per
model, 2 s apart (about 15 minutes for 200 models); an existing --out file is
resumed, not redone. Exit code 1 when a search is not scoped.
"""
import argparse
import json
import os
import sys
import time

import httpx

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "pt-PT,pt;q=0.9,en;q=0.7",
    "Accept-Encoding": "gzip, deflate",
    "Referer": "https://www.standvirtual.com",
}


def _catalogue_from_db() -> list:
    from sqlalchemy import create_engine, text
    url = os.environ["DATABASE_URL"]
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    with create_engine(url).connect() as conn:
        conn.execute(text("SET TRANSACTION READ ONLY"))
        rows = conn.execute(text(
            "SELECT b.name, m.name FROM vehicle_models m JOIN brands b ON b.id = m.brand_id ORDER BY 1, 2"
        )).fetchall()
        conn.rollback()
    return [[r[0], r[1]] for r in rows]


def _scope_row(search: dict) -> dict:
    """What the site did with a search: the make and model it applied (read by
    standvirtual.applied_make_model, which knows both the old filter_enum_make /
    filter_enum_model and the combined make_model_engine_code = "make|model" of
    mid-November 2026), the total and the models on the first page."""
    from app.scrapers import standvirtual as sv
    make, model = sv.applied_make_model(sv._search_meta(search))
    models_on_page = {}
    for edge in search.get("edges") or []:
        for p in (edge.get("node") or {}).get("parameters") or []:
            if p.get("key") == "model":
                models_on_page[p.get("value")] = models_on_page.get(p.get("value"), 0) + 1
    return {"applied_make": make, "applied_model": model, "total": search.get("totalCount"),
            "models_on_page": models_on_page, "result": "scoped" if make and model else "unscoped"}


def _check(client: httpx.Client, brand: str, model: str) -> dict:
    from app.scrapers import standvirtual as sv
    url = sv._build_search_url(brand, model)
    row = {"brand": brand, "model": model, "url": url[len(sv.SEARCH_URL):]}
    try:
        resp = client.get(url)
        row["status"] = resp.status_code
        search = sv._search_data(resp.text)
    except Exception as e:
        return {**row, "result": "error", "error": repr(e)}
    if search is None:
        return {**row, "result": "error", "error": "no search data in the page"}
    return {**row, **_scope_row(search)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--catalogue", help="JSON file: [[brand, model], ...]")
    ap.add_argument("--db", action="store_true", help="read brands and models from DATABASE_URL (read-only)")
    ap.add_argument("--out", default="sv_slug_audit.json")
    ap.add_argument("--pause", type=float, default=2.0)
    args = ap.parse_args()

    os.environ.setdefault("DATABASE_URL", "postgresql://user:pass@localhost:5432/audit")
    if args.db:
        pairs = _catalogue_from_db()
    elif args.catalogue:
        pairs = [p[:2] for p in json.load(open(args.catalogue, encoding="utf-8"))]
    else:
        ap.error("--catalogue or --db")

    rows = json.load(open(args.out, encoding="utf-8")) if os.path.exists(args.out) else []
    done = {(r["brand"], r["model"]) for r in rows if r.get("result") != "error"}
    rows = [r for r in rows if r.get("result") != "error"]
    with httpx.Client(follow_redirects=True, timeout=20, headers=HEADERS) as client:
        for brand, model in pairs:
            if (brand, model) in done:
                continue
            time.sleep(args.pause)
            row = _check(client, brand, model)
            rows.append(row)
            with open(args.out, "w", encoding="utf-8") as fh:
                json.dump(rows, fh, ensure_ascii=False, indent=0)
            print(f"{row['result']:9} {brand} {model!r}: {row['url']}  total={row.get('total')}"
                  f"{'  ' + row['error'] if row.get('error') else ''}", flush=True)

    counts = {}
    for r in rows:
        counts[r["result"]] = counts.get(r["result"], 0) + 1
    print(f"\n{len(rows)} models: {counts}; no listings at all: {sum(1 for r in rows if r.get('total') == 0)}")
    for r in rows:
        if r["result"] != "scoped":
            print(f"  {r['result'].upper():9} {r['brand']} {r['model']!r}: {r['url']}  applied make={r.get('applied_make')} model={r.get('applied_model')}")
    # Scoped yet empty: a rare model, or a slug the site applies but files
    # nothing under (sub-models searched in the path, 2026-11-17). Worth a look.
    for r in rows:
        if r["result"] == "scoped" and r.get("total") == 0:
            print(f"  EMPTY     {r['brand']} {r['model']!r}: {r['url']}  applied make={r.get('applied_make')} model={r.get('applied_model')}")
    return 0 if all(r["result"] == "scoped" for r in rows) else 1


if __name__ == "__main__":
    sys.exit(main())
