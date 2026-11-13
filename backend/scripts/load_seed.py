"""
Load the schema + catalogue seed into a fresh database (e.g. a new Neon DB).

Usage (from backend/, with the venv active):

    # PowerShell
    $env:DATABASE_URL="postgresql://…neon…?sslmode=require"; python -m scripts.load_seed
    # bash
    DATABASE_URL="postgresql://…neon…?sslmode=require" python -m scripts.load_seed

Runs the SQL files in dependency order. Meant for a FRESH database; safe to
read, and it stops with a clear message if a file errors. Newer columns/tables
(price_observations, depreciation, admin_notes, listing_snapshots) are created
automatically the first time the app boots, so they're not needed here.
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
SEED_FILES = [
    "seeds/full_deploy_schema.sql",         # schema (17 tables) + full catalogue
    "seeds/migration_v51_generations.sql",  # generation windows
    "seeds/migration_v56_split_wide_generations.sql",  # split the >12-year catch-all windows
    "seeds/migration_v57_close_replaced_generations.sql",  # close replaced / discontinued generations
    "seeds/migration_v58_changeover_years.sql",  # one generation per changeover year
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
        for rel in SEED_FILES:
            path = os.path.join(here, rel)
            if not os.path.exists(path):
                print(f"✗ missing {rel} — skipping")
                continue
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
