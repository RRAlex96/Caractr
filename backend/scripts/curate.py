"""
Run the Curator agent: fill reliability gaps in the model catalogue.

Run on demand (monthly, or whenever the Modelos tab shows gaps), from your own
machine, pointed at the production DB:

    cd backend
    # PowerShell
    $env:DATABASE_URL="postgresql://…neon…?sslmode=require"; python -m scripts.curate
    # bash
    DATABASE_URL="…" python -m scripts.curate [limit]

It researches up to <limit> models (default 10), auto-saves the high-confidence
ones, and leaves the rest in the pending list for you to review in the admin.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main() -> None:
    if not os.getenv("DATABASE_URL"):
        print("⚠  DATABASE_URL not set — point it at your Neon database first.")
        sys.exit(1)
    if not os.getenv("GEMINI_API_KEY"):
        print("⚠  GEMINI_API_KEY not set — the agent needs the LLM to research.")
        sys.exit(1)

    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 10

    from app.db.database import SessionLocal
    from app.services.curator_agent import run_curator

    db = SessionLocal()
    try:
        print(f"=== Curator agent — up to {limit} models ===")
        report = run_curator(db, limit=limit)
        if report.get("error"):
            print("✗", report["error"]); sys.exit(1)
        for line in report["log"]:
            print("  " + line)
        print(f"\n{report['gaps']} gaps · {report['researched']} researched · "
              f"{report['saved']} saved · {report['queued']} queued for review · "
              f"{report['errors']} errors")
    finally:
        db.close()


if __name__ == "__main__":
    main()
