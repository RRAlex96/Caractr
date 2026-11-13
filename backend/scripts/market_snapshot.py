"""
Market snapshot: read every listing of the catalogue's makes on Standvirtual,
then load it into price_observations. See app/services/market_snapshot.py.

    # from backend/, residential connection
    python -m scripts.market_snapshot collect snapshot.jsonl            # network only (~45 min)
    python -m scripts.market_snapshot collect snapshot.jsonl --makes audi,bmw
    python -m scripts.market_snapshot report  snapshot.jsonl            # what was read; no database
    python -m scripts.market_snapshot load    snapshot.jsonl            # writes to DATABASE_URL

`collect` reads the catalogue (read-only) from DATABASE_URL, or from a JSON
file given with --catalogue. It resumes: a make already in the file is skipped.
`load` writes to whatever database DATABASE_URL names — production when
backend/.env points at production. Follow it with the aggregate step:

    python -m scripts.monthly_refresh --skip market,safety_gate,nhtsa,curator,scorer,retention
"""
import argparse
import asyncio
import json
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _catalogue(path: str | None) -> list:
    if path:
        return json.load(open(path, encoding="utf-8"))
    from sqlalchemy import text
    from app.db.database import SessionLocal
    db = SessionLocal()
    try:
        db.execute(text("SET TRANSACTION READ ONLY"))
        return [dict(r) for r in db.execute(text("""
            SELECT vm.id, b.name AS brand_name, vm.name AS model_name, vm.body_type
            FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id ORDER BY vm.id
        """)).mappings()]
    finally:
        db.close()


def _records(path: str) -> list:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def _report(path: str) -> None:
    from app.services.market_snapshot import is_plausible
    recs = _records(path)
    in_cat = [r for r in recs if r.get("model_id") is not None]
    print(f"{len(recs)} listings, {len(in_cat)} under catalogue models "
          f"({100 * len(in_cat) / max(1, len(recs)):.0f}%), "
          f"{sum(is_plausible(r) for r in in_cat)} usable for prices")
    missing = Counter((r["make"], r["sv_model"]) for r in recs if r.get("model_id") is None)
    print("most-listed site models the catalogue does not have:")
    for (make, model), n in missing.most_common(40):
        print(f"  {n:5d}  {make} {model}")


def main() -> int:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

    ap = argparse.ArgumentParser()
    ap.add_argument("step", choices=["collect", "report", "load"])
    ap.add_argument("file")
    ap.add_argument("--makes", help="site make ids, comma-separated (collect only)")
    ap.add_argument("--catalogue", help="catalogue JSON instead of the database (collect only)")
    args = ap.parse_args()

    if args.step == "collect":
        from app.services.market_snapshot import collect
        makes = [m.strip() for m in args.makes.split(",")] if args.makes else None
        report = asyncio.run(collect(_catalogue(args.catalogue), args.file, makes,
                                     log=lambda s: print(s, flush=True)))
        print(json.dumps(report, indent=1))
        return 0 if all(m["complete"] for m in report["makes"].values()) else 1
    if args.step == "report":
        _report(args.file)
        return 0
    from app.db.database import SessionLocal
    from app.services.market_snapshot import load
    db = SessionLocal()
    try:
        print(json.dumps(load(db, _records(args.file)), indent=1))
    finally:
        db.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
