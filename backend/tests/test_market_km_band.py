"""Mileage step of the live market comparison.

A 2018 BMW 530e with 170 000 km at €25 400 was shown as 15% below a median
built from 2017–2023 cars, most with far fewer kilometres. The comparison must
be made against listings in the car's km band when at least 5 are, must say
what it compared, and must withhold the price reference when nothing in the
pool is comparable in mileage.
"""
import asyncio

from app.scrapers import dispatcher
from app.services import ad_analysis_service as svc
from app.services.ad_analysis_service import (
    _build_anomaly,
    _build_negotiation_numbers,
    _build_response,
    _cached_market_for,
    _km_band,
    _withhold_if_km_mismatch,
)


def _listing(km, price, year=2019):
    return {"year": year, "km": km, "price": price, "fuel_type": "Diesel",
            "title": "BMW 520d", "source_url": f"https://x/carros/anuncio/bmw-520-ID{km}{price}.html"}


def _market(monkeypatch, listings, km, year=2019, calls=None):
    """_fetch_live_market_data over a fixed set of search results (no network)."""
    async def fake_fetch(**kwargs):
        if calls is not None:
            calls.append(kwargs)
        return listings

    monkeypatch.setattr(dispatcher, "fetch_listings_all_sources", fake_fetch)
    if calls is None or not calls:
        monkeypatch.setattr(svc, "_market_cache", {})
    return asyncio.run(svc._fetch_live_market_data(
        "BMW", "520", year, gen_year_start=2017, gen_year_end=2023, km=km))


# Low-mileage cars asking ~€30k and high-mileage ones asking ~€20k.
LOW_KM = [_listing(km, p) for km, p in
          [(40000, 29000), (45000, 30000), (50000, 30500), (55000, 31000), (60000, 29500), (62000, 30000)]]
HIGH_KM = [_listing(km, p) for km, p in
           [(160000, 19000), (165000, 20000), (170000, 20500), (175000, 21000), (180000, 19500)]]


def test_km_band_is_thirty_percent_with_a_floor():
    assert _km_band(170000) == (119000, 221000)
    assert _km_band(100000) == (70000, 130000)
    # Below ~83 000 km the ±25 000 km floor applies.
    assert _km_band(40000) == (15000, 65000)
    assert _km_band(10000) == (0, 35000)
    # Rounded outwards to whole thousands.
    assert _km_band(87500) == (61000, 114000)


def test_high_mileage_car_is_compared_with_high_mileage_listings(monkeypatch):
    without_km = _market(monkeypatch, LOW_KM + HIGH_KM, km=None)
    assert without_km["median_price"] == 29000          # the old behaviour
    assert "km_comparison" not in without_km

    stats = _market(monkeypatch, LOW_KM + HIGH_KM, km=170000)
    assert stats["median_price"] == 20000
    assert stats["sample_count"] == 5
    assert stats["km_comparison"] == {
        "basis": "band", "car_km": 170000, "km_from": 119000, "km_to": 221000,
        "in_band_count": 5, "pool_count": 11, "pool_median_km": 62000,
    }
    # The whole pool is kept for market_price_stats, shared by all mileages.
    assert stats["pool_stats"]["median_price"] == 29000
    assert stats["pool_stats"]["sample_count"] == 11


def test_low_mileage_car_is_compared_with_low_mileage_listings(monkeypatch):
    stats = _market(monkeypatch, LOW_KM + HIGH_KM, km=50000)
    assert stats["median_price"] == 30000
    assert stats["sample_count"] == 6
    assert stats["km_comparison"]["basis"] == "band"
    assert (stats["km_comparison"]["km_from"], stats["km_comparison"]["km_to"]) == (25000, 75000)


def test_thin_band_keeps_the_pool_when_the_car_is_typical_of_it(monkeypatch):
    spread = [_listing(km, p) for km, p in
              [(40000, 30000), (70000, 27000), (95000, 25000), (115000, 24000), (150000, 21000), (190000, 18000)]]
    stats = _market(monkeypatch, spread, km=100000)
    # Only 3 listings in 70 000–130 000 km, but the pool's median km (105 000)
    # is inside the band: the whole pool is a fair comparison.
    assert stats["km_comparison"]["basis"] == "pool"
    assert stats["km_comparison"]["in_band_count"] == 3
    assert stats["sample_count"] == 6
    assert stats["median_price"] == 24500
    assert "pool_stats" not in stats


def test_no_comparable_mileage_withholds_the_price_reference(monkeypatch):
    stats = _market(monkeypatch, LOW_KM + HIGH_KM[:2], km=200000)
    assert stats["km_comparison"]["basis"] == "mismatch"
    assert stats["km_comparison"]["in_band_count"] == 2
    # The pool's stats are still returned: they are what goes to the database.
    assert stats["sample_count"] == 8 and stats["median_price"] == 29750

    withheld = _withhold_if_km_mismatch(stats)
    assert withheld["km_comparison"] == stats["km_comparison"]
    assert withheld["source"] == "live"
    for key in ("avg_price", "median_price", "min_price", "max_price", "sample_count"):
        assert key not in withheld

    # A 200 000 km car at €16 000 is not "suspiciously cheap" against 50 000 km cars.
    car = {"price": 16000, "km": 200000, "year": 2019, "seller_type": "particular"}
    assert _build_anomaly(car, stats, []) is not None
    assert _build_anomaly(car, withheld, []) is None
    assert _build_negotiation_numbers(car, withheld) is None


def test_other_bases_are_not_withheld(monkeypatch):
    stats = _market(monkeypatch, LOW_KM + HIGH_KM, km=170000)
    assert _withhold_if_km_mismatch(stats) is stats
    assert _withhold_if_km_mismatch({}) == {}


def test_listings_without_km_are_never_counted_inside_the_band(monkeypatch):
    unknown = [_listing(None, 35000) for _ in range(4)]
    stats = _market(monkeypatch, HIGH_KM + unknown, km=170000)
    assert stats["sample_count"] == 5
    assert stats["median_price"] == 20000
    assert stats["km_comparison"]["pool_count"] == 9


def test_too_few_listings_with_km_leaves_the_comparison_as_it_was(monkeypatch):
    unknown = [_listing(None, p) for p in (30000, 31000, 32000, 33000)]
    stats = _market(monkeypatch, HIGH_KM[:4] + unknown, km=170000)
    assert "km_comparison" not in stats
    assert stats["sample_count"] == 8


def test_cached_pool_serves_cars_of_any_mileage(monkeypatch):
    calls = []
    monkeypatch.setattr(svc, "_market_cache", {})
    high = _market(monkeypatch, LOW_KM + HIGH_KM, km=170000, calls=calls)
    low = _market(monkeypatch, LOW_KM + HIGH_KM, km=50000, calls=calls)
    assert len(calls) == 1                      # second car served from the cache
    assert (high["median_price"], low["median_price"]) == (20000, 30000)


def test_response_says_what_was_compared(monkeypatch):
    stats = _market(monkeypatch, LOW_KM + HIGH_KM, km=170000)
    listing = {"brand_name": "BMW", "model_name": "520", "year": 2019, "km": 170000,
               "price": 21000, "source_url": "https://www.standvirtual.com/carros/anuncio/x-ID1.html"}
    deal = _build_response(listing, {}, market_stats=stats)["deal"]
    assert deal["market_median_price"] == 20000
    assert deal["market_sample_count"] == 5
    assert deal["market_km_comparison"]["basis"] == "band"
    assert (deal["market_km_comparison"]["km_from"], deal["market_km_comparison"]["km_to"]) == (119000, 221000)

    assert _build_response(listing, {}, market_stats=None)["deal"]["market_km_comparison"] is None


def test_cached_analysis_keeps_a_withheld_reference_withheld():
    db_stats = {"avg_price": 29800.0, "min_price": 19000, "max_price": 31000,
                "sample_count": 8, "source": "live_scraped"}
    mismatch = {"basis": "mismatch", "car_km": 200000, "km_from": 140000, "km_to": 260000,
                "in_band_count": 2, "pool_count": 8, "pool_median_km": 57500}

    cached = _cached_market_for(db_stats, {"_market_km": mismatch})
    assert "avg_price" not in cached and "sample_count" not in cached
    assert cached["km_comparison"] == mismatch

    # Analyses compared on a band, on the pool, or before this change: DB stats as before.
    assert _cached_market_for(db_stats, {"_market_km": {**mismatch, "basis": "band"}}) == db_stats
    assert _cached_market_for(db_stats, {}) == db_stats
    assert _cached_market_for(None, None) == {}


# The comparables Standvirtual returned for the 530e case on 2026-11-13:
# (year, km, price). The two 2024 cars are outside the 2017–2023 generation.
REAL_530E = [
    (2024, 14491, 2000), (2023, 54170, 38750), (2023, 63923, 38990), (2021, 69150, 29980),
    (2021, 96190, 29900), (2021, 98200, 31990), (2020, 99989, 29890), (2020, 99989, 28250),
    (2024, 122070, 44990), (2019, 125600, 26900), (2022, 128500, 31900), (2020, 139276, 25900),
    (2021, 139757, 29000), (2017, 140000, 20900), (2022, 142385, 32000), (2021, 146441, 28900),
    (2018, 161000, 22990), (2022, 174606, 29980),
]


def test_real_530e_pool(monkeypatch):
    listings = [_listing(km, price, year) for year, km, price in REAL_530E]

    before = _market(monkeypatch, listings, km=None, year=2018)
    assert (before["median_price"], before["sample_count"]) == (29895, 16)

    after = _market(monkeypatch, listings, km=170000, year=2018)
    assert (after["median_price"], after["sample_count"]) == (28900, 9)
    assert after["km_comparison"]["basis"] == "band"
    assert after["km_comparison"]["pool_median_km"] == 127050
    assert after["pool_stats"]["median_price"] == 29895
