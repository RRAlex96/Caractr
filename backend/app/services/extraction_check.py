"""
Extraction canary — can this server still find and read a Standvirtual listing?

The whole product depends on fetching listings, and the two ways it breaks are
both silent: the site blocks our server's address, or it changes its page
structure and fields start coming back empty. This check does one search and
reads one listing, exactly as a real analysis would, without calling the AI
or touching the database. A scheduled job calls it daily (see
.github/workflows/health.yml).
"""
import time
from typing import Awaitable, Callable, Optional

# A common model, so the search always has results.
_PROBE_BRAND, _PROBE_MODEL = "Renault", "Clio"
_UNREADABLE = {"listing_gone", "fetch_failed"}


async def check_extraction(
    fetch_search: Optional[Callable[..., Awaitable[list]]] = None,
    fetch_detail: Optional[Callable[[str], Awaitable[dict]]] = None,
) -> dict:
    """
    Returns {"ok", "stage", "search_results", "listing_url", "grade",
    "missing", "method", "error", "elapsed_ms"}. `ok` means a listing was read
    with every critical field (grade A or B). `stage` is where it stopped.
    """
    if fetch_search is None or fetch_detail is None:
        from app.scrapers.standvirtual import fetch_listing_detail, fetch_listings
        fetch_search = fetch_search or fetch_listings
        fetch_detail = fetch_detail or fetch_listing_detail

    started = time.monotonic()
    out: dict = {"ok": False, "stage": "search", "search_results": 0, "listing_url": None,
                 "grade": None, "missing": [], "method": None, "error": None}

    def done() -> dict:
        out["elapsed_ms"] = int((time.monotonic() - started) * 1000)
        return out

    try:
        listings = await fetch_search(_PROBE_BRAND, _PROBE_MODEL, max_results=5)
    except Exception as e:
        out["error"] = f"search failed: {type(e).__name__}: {str(e)[:160]}"
        return done()

    urls = [u for u in ((l or {}).get("source_url") for l in listings or [])
            if isinstance(u, str) and u.startswith("http")]
    out["search_results"] = len(listings or [])
    if not urls:
        out["error"] = "search returned no listing links (blocked, or the results page changed)"
        return done()

    out["stage"] = "detail"
    # A listing can sell between the search and the read, so allow a second try.
    for url in urls[:2]:
        try:
            detail = await fetch_detail(url)
        except Exception as e:
            out["error"] = f"listing read failed: {type(e).__name__}: {str(e)[:160]}"
            continue
        method = detail.get("_extraction_method")
        quality = detail.get("_data_quality") or {}
        out.update(listing_url=url, method=method, grade=quality.get("grade"),
                   missing=list(quality.get("missing_critical") or []))
        if method in _UNREADABLE:
            out["error"] = f"listing unreadable ({method})"
            continue
        out["ok"] = out["grade"] in ("A", "B") and not out["missing"]
        out["error"] = None if out["ok"] else "listing read, but fields are missing (page structure changed?)"
        out["stage"] = "done"
        break
    return done()
