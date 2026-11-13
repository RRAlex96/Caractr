"""Year window of the live market comparison.

A catch-all generation row (BMW 530 "Geração principal" 1988–now) let a 2018
530e be priced against 2017–2024 cars and called well priced. A generation
wider than 8 years must narrow the comparison to the car's own year ±2.
"""
import asyncio

from app.scrapers import dispatcher
from app.services import ad_analysis_service as svc
from app.services.ad_analysis_service import _comparison_year_window


def test_normal_generation_uses_its_own_window():
    # Golf Mk7 2012–2019: 7 years, left alone.
    assert _comparison_year_window(2015, 2012, 2019)[:2] == (2012, 2019)
    # Exactly 8 years is still a normal generation.
    assert _comparison_year_window(2015, 2010, 2018)[:2] == (2010, 2018)
    # Current generation, open-ended, 6 years old.
    assert _comparison_year_window(2022, 2020, None, current_year=2026)[:2] == (2020, None)


def test_wide_generation_is_narrowed_to_two_years_either_side():
    # The production bug: BMW 530, 1988–now, 2018 car.
    assert _comparison_year_window(2018, 1988, None, current_year=2026)[:2] == (2016, 2020)
    # Closed wide generation (VW Caddy 2003–2020).
    assert _comparison_year_window(2012, 2003, 2020)[:2] == (2010, 2014)


def test_narrowed_window_never_leaves_the_generation():
    assert _comparison_year_window(2004, 2003, 2020)[:2] == (2003, 2006)
    assert _comparison_year_window(2019, 2003, 2020)[:2] == (2017, 2020)


def test_no_generation_falls_back_to_three_years():
    assert _comparison_year_window(2018, None, None)[:2] == (2015, 2021)
    assert _comparison_year_window(None, None, None)[:2] == (None, None)


def _listing(year, price):
    return {"year": year, "price": price, "fuel_type": "Híbrido Plug-In",
            "title": "BMW 530e", "source_url": f"https://x/carros/anuncio/bmw-530-ID{year}{price}.html"}


def test_wide_generation_median_ignores_much_newer_cars(monkeypatch):
    """End to end through _fetch_live_market_data: the search is asked for
    2016–2020 only, and newer cars that slip through are dropped from the median."""
    asked = {}
    listings = (
        [_listing(y, p) for y, p in [(2017, 24000), (2018, 25000), (2018, 26000), (2019, 28000)]]
        + [_listing(y, p) for y, p in [(2022, 41000), (2023, 46000), (2024, 52000), (2024, 55000)]]
    )

    async def fake_fetch(**kwargs):
        asked.update(kwargs)
        return listings

    monkeypatch.setattr(dispatcher, "fetch_listings_all_sources", fake_fetch)
    monkeypatch.setattr(svc, "_market_cache", {})

    stats = asyncio.run(svc._fetch_live_market_data(
        "BMW", "530", 2018, gen_year_start=1988, gen_year_end=None))

    assert (asked["year_from"], asked["year_to"]) == (2016, 2020)
    assert stats["sample_count"] == 4
    assert stats["median_price"] == 25500      # was 34500 with the 2022–2024 cars in
    assert stats["max_price"] == 28000


def test_wide_generation_cache_is_per_comparison_window(monkeypatch):
    """Two cars of one wide generation must not share a cached median."""
    async def fake_fetch(**kwargs):
        return [_listing(y, 10000 + (y - 2000) * 1000)
                for y in range(kwargs["year_from"], kwargs["year_to"] + 1)]

    monkeypatch.setattr(dispatcher, "fetch_listings_all_sources", fake_fetch)
    monkeypatch.setattr(svc, "_market_cache", {})

    old = asyncio.run(svc._fetch_live_market_data("BMW", "530", 2008, gen_year_start=1988))
    new = asyncio.run(svc._fetch_live_market_data("BMW", "530", 2018, gen_year_start=1988))
    assert old["median_price"] == 18000
    assert new["median_price"] == 28000
