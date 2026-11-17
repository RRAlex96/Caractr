"""
Load the schema + catalogue seed into a fresh database (e.g. a new Neon DB).

Usage (from backend/, with the venv active):

    # PowerShell
    $env:DATABASE_URL="postgresql://…neon…?sslmode=require"; python -m scripts.load_seed
    # bash
    DATABASE_URL="postgresql://…neon…?sslmode=require" python -m scripts.load_seed

Runs the SQL files in dependency order. Meant for a FRESH database; it stops
with a clear message, and exit status 1, if a file is missing or errors.

The tables and columns the app creates when it boots (price_observations,
listing_snapshots, the rebuilt raw_listings, depreciation columns ...) are
created here too, right after the base schema, by running the app's own
startup migrations: the numbered migrations after it refer to them. Without
that step a fresh database could not be built from this repository (v60 failed
on raw_listings.source_url).

    python -m scripts.load_seed --twice     # then v60 onwards again: those must be idempotent
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# full_deploy_schema.sql is the canonical, self-contained schema + catalogue
# (~38 brands and hundreds of models/engines/driving-character rows). The older
# seed_data_refined_v2 / seed_data_v3_expansion files target a previous
# engine_issues schema (an "issue_name" column that no longer exists) and are
# intentionally NOT loaded. migration_v51_generations adds generation windows
# and matches the current schema.
STARTUP = "app:startup-migrations"

SEED_FILES = [
    "seeds/full_deploy_schema.sql",         # schema (17 tables) + full catalogue
    STARTUP,                                # what the app creates at boot (app.main._run_startup_migrations)
    "seeds/migration_v51_generations.sql",  # generation windows
    "seeds/migration_v56_split_wide_generations.sql",  # split the >12-year catch-all windows
    "seeds/migration_v57_close_replaced_generations.sql",  # close replaced / discontinued generations
    "seeds/migration_v58_changeover_years.sql",  # one generation per changeover year
    "seeds/migration_v59_generation_fuel.sql",  # fuel_type column; Fiat 500e is electric-only
    "seeds/migration_v60_merge_bmw_530.sql",  # no-op on a fresh database (no stub model to merge)
    "seeds/migration_v61_engines_and_character.sql",  # engines + character for the models that had none
    "seeds/migration_v63_generation_corrections.sql",  # generation years checked against published sources
    "seeds/migration_v64_safeties.sql",  # constraints; provenance columns and tables
    "seeds/migration_v65_engine_corrections.sql",  # engine figures checked against published specifications
    "seeds/migration_v66_new_models.sql",  # 193 models the market sells and the catalogue lacked
    "seeds/migration_v67_engines_new_models.sql",  # their engines, from the market snapshot
    "seeds/migration_v68_brand_reliability.sql",  # reliability anchored on published studies
    "seeds/migration_v69_retire_unsourced_ai_issues.sql",  # no-op on a fresh database
    "seeds/migration_v70_deferrable_generation_rule.sql",  # no-op on a fresh database (v64 already deferrable)
    "seeds/migration_v71_engines_for_curated_faults.sql",  # engine years and older generations, so curated faults match
    # migration_v62_remove_seeded_prices.sql is NOT loaded here: it removes the
    # placeholder prices and refuses to run until a market snapshot has been
    # loaded and aggregated (scripts/market_snapshot.py, then monthly_refresh).
]


def main() -> None:
    url = os.getenv("DATABASE_URL")
    if not url:
        print("⚠  DATABASE_URL not set — point it at your new Neon database first.")
        sys.exit(1)

    import psycopg2

    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    conn = psycopg2.connect(url)
    try:
        rerun = ("seeds/migration_v6", "seeds/migration_v7")
        runs = SEED_FILES + ([f for f in SEED_FILES if f.startswith(rerun)] if "--twice" in sys.argv else [])
        for rel in runs:
            if rel == STARTUP:
                print("→ app startup migrations …")
                from app.main import _run_startup_migrations
                _run_startup_migrations()
                print("  ✓ app startup migrations")
                continue
            path = os.path.join(here, rel)
            if not os.path.exists(path):
                print(f"✗ missing {rel}")
                sys.exit(1)
            sql = open(path, encoding="utf-8").read()
            print(f"→ loading {rel} ({len(sql) // 1024} KB) …")
            try:
                with conn.cursor() as cur:
                    cur.execute(sql)
                conn.commit()
                print(f"  ✓ {rel}")
            except Exception as e:
                conn.rollback()
                print(f"  ✗ {rel} FAILED: {e}")
                print("    (stopping — fix this before continuing)")
                sys.exit(1)

        # Sanity check: did the catalogue actually land?
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM vehicle_models")
            models = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM engines")
            engines = cur.fetchone()[0]
        print(f"\n✓ Done. Catalogue: {models} models, {engines} engines.")
        if models < 10:
            print("⚠  Fewer models than expected — the recommendation engine may be thin.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
