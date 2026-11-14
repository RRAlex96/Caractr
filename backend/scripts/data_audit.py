"""
Audit the reference data and score it. Read-only. See app/services/data_audit.py.

    python -m scripts.data_audit                 # scorecard on the terminal
    python -m scripts.data_audit --out file.md   # ... and written to a file
    python -m scripts.data_audit --json          # machine-readable
    python -m scripts.data_audit --strict        # exit 1 when a critical check fails
    python -m scripts.data_audit --only integrity,plausibility,safeties --strict
                                                 # a database built from the seeds (CI): no market data in it

Reads whatever database DATABASE_URL names.
"""
import argparse
import json
import os
import sys

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--out")
    ap.add_argument("--only", help="dimensions to run, comma-separated (integrity, plausibility, coverage, "
                                   "freshness, provenance, safeties)")
    args = ap.parse_args()

    from dotenv import load_dotenv
    load_dotenv(os.path.join(BACKEND, ".env"))
    from sqlalchemy import text

    from app.db.database import SessionLocal
    from app.services.data_audit import as_json, as_markdown, run_audit

    db = SessionLocal()
    try:
        db.execute(text("SET TRANSACTION READ ONLY"))
        audit = run_audit(db, only=args.only.split(",") if args.only else None)
    finally:
        db.rollback()
        db.close()

    report = json.dumps(as_json(audit), ensure_ascii=False, indent=1) if args.json else as_markdown(audit)
    if args.out:
        with open(args.out, "w", encoding="utf-8", newline="\n") as f:
            f.write(report)
    sys.stdout.buffer.write(report.encode("utf-8"))
    if audit["critical_failures"]:
        print(f"\ncritical checks failing: {', '.join(audit['critical_failures'])}", file=sys.stderr)
    return 1 if args.strict and audit["critical_failures"] else 0


if __name__ == "__main__":
    sys.exit(main())
