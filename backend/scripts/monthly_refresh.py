"""
Monthly data refresh for Caractr — the one command that keeps the data fresh.

Run it ONCE A MONTH from your own machine (a residential IP — marketplaces
block datacenter IPs). It uses whatever database DATABASE_URL names, so it
refreshes production when backend/.env points at production:

    # from backend/
    python -m scripts.monthly_refresh            # everything
    python -m scripts.monthly_refresh --skip market,nhtsa

Steps (each isolated — one failing never skips the others; all idempotent):
  1. market       every listing of the catalogue's makes on Standvirtual →
                  price_observations (scripts/market_snapshot.py; ~45 min;
                  the listings read are kept in backend/snapshots/)
  2. aggregate    robust prices → market_price_stats + generation bands
  3. depreciation curves from the clean observations
  4. safety_gate  newest ~350 EU Safety Gate alerts (≈ last 3 weeks)
  5. nhtsa        NHTSA recalls/complaints (slow: ~1 h; already-stored skipped)
  6. curator      LLM research for models with no estimate yet (needs
                  GEMINI_API_KEY; CURATOR_LIMIT, default 10). Runs BEFORE the
                  scorer; unsourced findings can never raise a deal-breaker.
  7. scorer       Bayesian reliability score for every generation
  8. retention    prune expired rows

Not included:
  - KBA via car-recalls.eu — the site was restructured (brand/year pages now
    404). German recalls also reach EU Safety Gate, which is covered.
  - Safety Gate full history — one-off backfill (~5,300 pages, roughly 12 h
    at a polite rate), safe to interrupt and resume with start_page (progress
    is logged every 200 pages; the Nov 2026 run stopped after page 1000):
        python -c "from app.db.database import SessionLocal; \\
          from app.scrapers import safety_gate as sg; db = SessionLocal(); \\
          print(sg.ingest_safety_gate(db, max_pages=None, mode='archive', start_page=1000)); \\
          print(sg.rematch_safety_gate(db)); print(sg.backfill_portuguese(db))"
    then run the scorer step:  python -m scripts.monthly_refresh --skip \\
        market,aggregate,depreciation,safety_gate,nhtsa,curator,retention

Exit code is non-zero if any step failed.
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _session_step(fn):
    """Run fn(db) with its own session, so a failed step can't poison the next."""
    def run():
        from app.db.database import SessionLocal
        db = SessionLocal()
        try:
            return fn(db)
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()
    return run


def _steps():
    from app.scrapers.nhtsa import ingest_nhtsa_all
    from app.scrapers.safety_gate import ingest_safety_gate
    from app.services.depreciation import run_depreciation_curves
    from app.services.market_aggregator import run_aggregation

    def scorer(db):
        # Imported here: it needs scipy, which a skipped scorer step should not.
        from app.services.reliability_runner import run_reliability_scorer
        return run_reliability_scorer(db)

    def curator(db):
        if not os.getenv("GEMINI_API_KEY"):
            return "skipped: GEMINI_API_KEY not set"
        from app.services.curator_agent import run_curator
        report = run_curator(db, limit=int(os.getenv("CURATOR_LIMIT", "10")))
        if report.get("error"):
            raise RuntimeError(report["error"])
        return {k: report[k] for k in ("gaps", "researched", "saved", "queued", "errors")}

    def market(db):
        import asyncio
        from datetime import date
        from sqlalchemy import text
        from app.services import market_snapshot

        catalogue = [dict(r) for r in db.execute(text("""
            SELECT vm.id, b.name AS brand_name, vm.name AS model_name, vm.body_type
            FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id ORDER BY vm.id
        """)).mappings()]
        folder = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "snapshots")
        os.makedirs(folder, exist_ok=True)
        # One file a month: a run interrupted halfway resumes where it stopped.
        path = os.path.join(folder, f"standvirtual_{date.today():%Y_%m}.jsonl")
        report = asyncio.run(market_snapshot.collect(catalogue, path, log=lambda s: print(s, flush=True)))
        incomplete = [m for m, r in report["makes"].items() if not r["complete"]]
        with open(path, encoding="utf-8") as f:
            import json
            records = [json.loads(line) for line in f if line.strip()]
        counts = market_snapshot.load(db, records)
        if incomplete:
            raise RuntimeError(f"makes not read to the end (run again to resume): {incomplete}; loaded {counts}")
        return counts

    def retention(_db):
        from app.main import _run_data_retention_sync
        _run_data_retention_sync()
        return "ok"

    return [
        ("market",       _session_step(market)),
        ("aggregate",    _session_step(run_aggregation)),
        ("depreciation", _session_step(run_depreciation_curves)),
        ("safety_gate",  _session_step(lambda db: ingest_safety_gate(db, max_pages=10, sleep_seconds=1.0))),
        ("nhtsa",        _session_step(lambda db: ingest_nhtsa_all(db, sleep_seconds=0.4))),
        ("curator",      _session_step(curator)),
        ("scorer",       _session_step(scorer)),
        ("retention",    retention),
    ]


def main(argv: list[str]) -> int:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
    if not os.getenv("DATABASE_URL"):
        print("⚠  DATABASE_URL is not set — refusing to run against an unknown DB.")
        return 1

    skip = set()
    if "--skip" in argv:
        skip = {s.strip() for s in argv[argv.index("--skip") + 1].split(",")}

    started = time.time()
    print("=== Caractr monthly refresh ===")
    results = []
    for name, run in _steps():
        if name in skip:
            results.append((name, "SKIP", "", 0))
            continue
        t0 = time.time()
        print(f"\n--- {name} ---", flush=True)
        try:
            out = run()
            results.append((name, "OK", out, time.time() - t0))
            print(f"--- {name} OK in {time.time() - t0:.0f}s: {out}", flush=True)
        except Exception as e:
            results.append((name, "FAIL", f"{type(e).__name__}: {e}", time.time() - t0))
            print(f"!!! {name} FAILED: {type(e).__name__}: {e}", flush=True)

    print(f"\n=== summary ({time.time() - started:.0f}s) ===")
    for name, status, out, secs in results:
        print(f"  {status:4s} {name:13s} {secs:6.0f}s  {str(out)[:110]}")
    return 1 if any(r[1] == "FAIL" for r in results) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
