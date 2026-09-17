"""
Monthly data refresh for Caractr.

Run this ONCE A MONTH from your own machine (a residential IP — Standvirtual/OLX
don't bot-block it the way they block Railway's datacenter IP). It points at
whatever database DATABASE_URL names, so set it to the production Postgres to
refresh the live catalogue:

    # from backend/
    DATABASE_URL=<prod-postgres-url> python -m scripts.monthly_refresh

It does three things, each idempotent and safe to re-run:
  1. market refresh   — re-scrape + re-aggregate market prices per model/year
  2. reliability       — ingest recalls (Safety Gate / NHTSA / KBA) + Bayesian score
  3. data retention    — prune expired rows per the retention policy

This is the on-demand replacement for the always-on background loops, which are
disabled on the scale-to-zero deploy (ENABLE_BACKGROUND_JOBS=false).
"""
import os
import sys
import time

# Allow running as `python -m scripts.monthly_refresh` or directly.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main() -> None:
    if not os.getenv("DATABASE_URL"):
        print("⚠  DATABASE_URL is not set — refusing to run against an unknown DB.")
        sys.exit(1)

    from app.main import (
        _run_market_refresh_sync,
        _run_reliability_sync,
        _run_data_retention_sync,
    )

    started = time.time()
    print("=== Caractr monthly refresh ===")

    for label, fn in (
        ("market refresh", _run_market_refresh_sync),
        ("reliability", _run_reliability_sync),
        ("data retention", _run_data_retention_sync),
    ):
        t0 = time.time()
        print(f"\n--- {label} ---")
        try:
            fn()
            print(f"--- {label} done in {time.time() - t0:.0f}s ---")
        except Exception as e:  # keep going — one step failing shouldn't block the rest
            print(f"!!! {label} FAILED: {e}")

    print(f"\n=== monthly refresh complete in {time.time() - started:.0f}s ===")


if __name__ == "__main__":
    main()
