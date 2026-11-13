"""The daily canary must say 'broken' for every way listing fetching breaks —
and must not cry wolf when one listing simply sold between search and read."""
import asyncio

from app.services.extraction_check import check_extraction

GOOD = {"_extraction_method": "next_data",
        "_data_quality": {"grade": "A", "missing_critical": []}}
GONE = {"_extraction_method": "listing_gone",
        "_data_quality": {"grade": "F", "missing_critical": ["brand", "model", "year", "km", "price"]}}
DEGRADED = {"_extraction_method": "html_semantic",
            "_data_quality": {"grade": "C", "missing_critical": ["km", "price"]}}


def _run(search_result, details):
    calls = []

    async def search(brand, model, max_results=5):
        if isinstance(search_result, Exception):
            raise search_result
        return search_result

    async def detail(url):
        calls.append(url)
        d = details[url]
        if isinstance(d, Exception):
            raise d
        return d

    return asyncio.run(check_extraction(search, detail)), calls


def _links(*urls):
    return [{"source_url": u} for u in urls]


def test_healthy_search_and_read():
    out, calls = _run(_links("https://sv/a", "https://sv/b"), {"https://sv/a": GOOD})
    assert out["ok"] and out["stage"] == "done" and out["grade"] == "A"
    assert out["error"] is None and calls == ["https://sv/a"]
    assert isinstance(out["elapsed_ms"], int)


def test_blocked_search_is_reported_at_the_search_stage():
    out, _ = _run(RuntimeError("403 Forbidden"), {})
    assert not out["ok"] and out["stage"] == "search" and "403" in out["error"]


def test_search_with_no_links_is_a_failure():
    out, _ = _run([{"source_url": ""}, {}], {})
    assert not out["ok"] and out["stage"] == "search" and out["search_results"] == 2


def test_a_sold_listing_does_not_fail_the_check_if_the_next_one_reads():
    out, calls = _run(_links("https://sv/a", "https://sv/b"),
                      {"https://sv/a": GONE, "https://sv/b": GOOD})
    assert out["ok"] and out["listing_url"] == "https://sv/b" and len(calls) == 2


def test_two_unreadable_listings_fail():
    out, calls = _run(_links("https://sv/a", "https://sv/b", "https://sv/c"),
                      {"https://sv/a": GONE, "https://sv/b": GONE})
    assert not out["ok"] and out["stage"] == "detail" and len(calls) == 2
    assert "listing_gone" in out["error"]


def test_missing_fields_fail_even_though_the_page_loaded():
    out, _ = _run(_links("https://sv/a"), {"https://sv/a": DEGRADED})
    assert not out["ok"] and out["missing"] == ["km", "price"] and out["grade"] == "C"
    assert "structure" in out["error"]


def test_a_crash_while_reading_is_caught_and_the_next_listing_tried():
    out, _ = _run(_links("https://sv/a", "https://sv/b"),
                  {"https://sv/a": TimeoutError("slow"), "https://sv/b": GOOD})
    assert out["ok"] and out["listing_url"] == "https://sv/b"
