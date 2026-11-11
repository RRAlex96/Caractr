"""
Regenerate the instant demo analyses shown on /exemplos.

The examples are static snapshots of real analyses, so the demo works even
when the backend is cold or a marketplace is blocking. They must be produced by
the real pipeline with the LLM actually working — a snapshot taken while the
LLM was failing silently ships template text to every visitor (this happened:
all four were "rule:gemini_error" when gemini-2.5-flash was retired).

    # from backend/, residential connection, GEMINI_API_KEY set
    python -m scripts.regenerate_examples            # all examples
    python -m scripts.regenerate_examples fiat-500x  # just one

An example file is only overwritten when the fresh analysis came from the LLM
and the listing extracted cleanly; otherwise the old snapshot is kept and the
reason is printed. Review the diff before committing.
"""
import asyncio
import glob
import json
import os
import sys

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND)
EXAMPLES = os.path.join(os.path.dirname(BACKEND), "frontend", "lib", "examples")


def _ok(result: dict) -> tuple[bool, str]:
    if result.get("error"):
        return False, f"error: {result['error']}"
    engine = result.get("_analysis_engine") or ""
    if engine != "gemini":
        return False, f"analysis engine was '{engine}' ({result.get('_llm_error', '')[:120]})"
    if not (result.get("analysis") or {}).get("verdict"):
        return False, "no verdict in analysis"
    grade = (result.get("_data_quality") or {}).get("grade")
    if grade not in ("A", "B"):
        return False, f"listing extraction grade {grade!r} (need A/B)"
    return True, "ok"


async def main(only: list[str]) -> int:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(BACKEND, ".env"))
    from app.db.database import SessionLocal
    from app.services.ad_analysis_service import analyse_listing

    files = sorted(glob.glob(os.path.join(EXAMPLES, "*.json")))
    if only:
        files = [f for f in files if os.path.basename(f)[:-5] in only]
    failures = 0
    db = SessionLocal()
    try:
        for path in files:
            name = os.path.basename(path)
            old = json.load(open(path, encoding="utf-8"))
            url = old.get("source_url")
            if not url:
                print(f"SKIP {name}: no source_url"); continue
            result = await analyse_listing(db, url, force_refresh=True)
            ok, why = _ok(result)
            if not ok:
                failures += 1
                print(f"KEEP {name}: {why}")
                continue
            # Keep the stable demo id so existing links keep working.
            result["analysis_id"] = old.get("analysis_id", result.get("analysis_id"))
            with open(path, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=1)
                f.write("\n")
            print(f"WROTE {name}: {result['analysis'].get('verdict')} — "
                  f"{(result['analysis'].get('verdict_reason') or '')[:80]}")
    finally:
        db.close()
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main(sys.argv[1:])))
