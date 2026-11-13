"""Engine-power band of the live market comparison.

A model's listings mix engines that are different cars in price: a Golf diesel
pool holds 105 cv and 184 cv cars, a MINI hatch pool Ones and John Cooper
Works. When the listing states the car's power, its comparables are the
listings within 15% of it — asked of the site in the search and checked on
every result — and never the others as a fallback.
"""
import asyncio
import json

import pytest

from app.scrapers import dispatcher, olx, standvirtual
from app.scrapers.standvirtual import _build_search_url, _card_power_hp, _listings_from_search
from app.services import ad_analysis_service as svc
from app.services.ad_analysis_service import _power_range


@pytest.mark.parametrize("power, band", [
    (115, (97, 133)),
    (100, (85, 115)),
    (190, (161, 219)),
    ("136", (115, 157)),
    (None, None),
    (0, None),
    ("", None),
    ("n/a", None),
    (12, None),          # not a car's power
    (5000, None),
])
def test_power_band_is_fifteen_percent_either_side(power, band):
    assert _power_range(power) == band


def test_search_url_carries_the_power_band():
    url = _build_search_url("Volkswagen", "Golf", None, 2012, 2019, "Diesel", None, 1, (97, 133))
    assert "search[filter_float_engine_power:from]=97" in url
    assert "search[filter_float_engine_power:to]=133" in url
    assert url.startswith("https://www.standvirtual.com/carros/vw/golf?")
    assert "engine_power" not in _build_search_url("Volkswagen", "Golf", None, 2012, 2019, "Diesel")
    # With a series and a second page.
    url = _build_search_url("BMW", "Serie 3", None, None, None, "Diesel", None, 2, (161, 219))
    assert url == ("https://www.standvirtual.com/carros/bmw?search[filter_enum_model]=serie-3"
                   "&search[filter_enum_fuel_type][0]=diesel&search[filter_float_engine_power:from]=161"
                   "&search[filter_float_engine_power:to]=219&page=2")


@pytest.mark.parametrize("value, display, power", [
    ("200", "200 cv", 200),
    ("110", "110 kW", 150),       # labelled in kW: converted
    ("", "116 cv", 116),
    ("", "", None),
    ("8", "8 cv", None),
])
def test_power_of_a_search_result(value, display, power):
    assert _card_power_hp(value, display) == power


def test_search_results_carry_their_power():
    search = {"edges": [{"node": {
        "url": "https://www.standvirtual.com/carros/anuncio/vw-golf-ID1.html", "title": "VW Golf 1.6 TDI",
        "price": {"amount": {"units": 14000, "currencyCode": "EUR"}},
        "parameters": [{"key": "engine_power", "value": "115", "displayValue": "115 cv"},
                       {"key": "model", "value": "golf", "displayValue": "Golf"}],
    }}]}
    assert _listings_from_search(search)[0]["engine_power_hp"] == 115


def test_dispatcher_passes_the_power_band_to_standvirtual_only(monkeypatch):
    seen = {}

    async def sv(*args):
        seen["sv"] = args
        return []

    async def ox(*args):
        seen["olx"] = args
        return []

    monkeypatch.setattr(standvirtual, "fetch_listings", sv)
    monkeypatch.setattr(olx, "fetch_listings", ox)
    asyncio.run(dispatcher.fetch_listings_all_sources(
        "Volkswagen", "Golf", max_per_source=160, fuel_type="Diesel", max_pages=4, power_range=(97, 133)))
    assert seen["sv"][-2:] == (4, (97, 133))
    assert (97, 133) not in seen["olx"]


# ── The analysis ─────────────────────────────────────────────────────────────

def _golf(n, power, price, title="VW Golf", source="standvirtual"):
    return {"year": 2017, "km": 120000 + 500 * n, "price": price, "fuel_type": "Diesel", "title": title,
            "engine_power_hp": power, "source": source,
            "source_url": f"https://x/carros/anuncio/vw-golf-ID{n}.html"}


GOLFS = (
    [_golf(n, 115, 14000 + 10 * n, "VW Golf 1.6 TDI Confortline") for n in range(10)]
    + [_golf(20 + n, 110, 13500 + 10 * n, "VW Golf 1.6 TDI Trendline") for n in range(6)]
    + [_golf(40 + n, 150, 18000 + 10 * n, "VW Golf 2.0 TDI Highline") for n in range(8)]
    + [_golf(60 + n, 184, 24000 + 10 * n, "VW Golf 2.0 TDI GTD") for n in range(8)]
)


def _market(monkeypatch, calls, power, listings=GOLFS, brand="Volkswagen", model="Golf", **kwargs):
    async def fake_fetch(**fetch_kwargs):
        calls.append(fetch_kwargs)
        return listings

    monkeypatch.setattr(dispatcher, "fetch_listings_all_sources", fake_fetch)
    return asyncio.run(svc._fetch_live_market_data(
        brand, model, 2017, fuel_type="Diesel", gen_year_start=2012, gen_year_end=2019,
        power_hp=power, **kwargs))


def test_car_is_compared_with_listings_of_about_its_power(monkeypatch):
    calls = []
    monkeypatch.setattr(svc, "_market_cache", {})
    stats = _market(monkeypatch, calls, 115)
    assert calls[0]["power_range"] == (97, 133)             # asked of the site
    assert stats["sample_count"] == 16                      # the 115s and the 110s, checked on every result
    assert stats["max_price"] < 15000                       # no 150 cv or GTD
    assert stats["power_comparison"] == {"car_power_hp": 115, "power_from": 97, "power_to": 133, "pool_count": 16}

    gtd = _market(monkeypatch, calls, 184)
    assert gtd["sample_count"] == 8 and gtd["min_price"] >= 24000
    assert len(calls) == 2                                  # its own cached pool


def test_power_band_is_cached_per_band_and_reported_on_a_cache_hit(monkeypatch):
    calls = []
    monkeypatch.setattr(svc, "_market_cache", {})
    first = _market(monkeypatch, calls, 115)
    again = _market(monkeypatch, calls, 115)
    assert len(calls) == 1
    assert again["power_comparison"] == first["power_comparison"]
    assert again["median_price"] == first["median_price"]


def test_no_listing_of_the_cars_power_means_no_reference(monkeypatch):
    """A Golf R among diesels of 105–184 cv: the others are never the fallback."""
    monkeypatch.setattr(svc, "_market_cache", {})
    assert _market(monkeypatch, [], 300) == {}


def test_few_listings_of_the_cars_power_give_no_verdict(monkeypatch):
    monkeypatch.setattr(svc, "_market_cache", {})
    listings = GOLFS + [_golf(90 + n, 300, 38000) for n in range(3)]
    stats = _market(monkeypatch, [], 300, listings=listings)
    assert stats["sample_count"] == 3 < svc._MIN_RELIABLE_MARKET_SAMPLE


def test_without_the_cars_power_nothing_changes(monkeypatch):
    calls = []
    monkeypatch.setattr(svc, "_market_cache", {})
    stats = _market(monkeypatch, calls, None)
    assert calls[0]["power_range"] is None
    assert stats["sample_count"] == len(GOLFS)
    assert "power_comparison" not in stats
    # ... and the engine named in the title still cuts the pool.
    monkeypatch.setattr(svc, "_market_cache", {})
    assert _market(monkeypatch, calls, None, engine_hint="1.6 TDI")["sample_count"] == 16


def test_engine_hint_is_not_applied_on_top_of_the_power_band(monkeypatch):
    monkeypatch.setattr(svc, "_market_cache", {})
    listings = GOLFS + [_golf(100 + n, 116, 14200, "VW Golf 1.5 TDI") for n in range(4)]
    assert _market(monkeypatch, [], 115, listings=listings, engine_hint="1.6 TDI")["sample_count"] == 20


def test_results_without_a_power_are_kept_only_from_the_scoped_search(monkeypatch):
    monkeypatch.setattr(svc, "_market_cache", {})
    listings = (
        [_golf(n, 115, 14000) for n in range(6)]
        + [_golf(20 + n, None, 14100) for n in range(2)]                      # Standvirtual, scoped by the URL
        + [_golf(40 + n, None, 9000, source="olx") for n in range(5)]         # cannot be checked
    )
    stats = _market(monkeypatch, [], 115, listings=listings)
    assert stats["sample_count"] == 8 and stats["min_price"] == 14000


def test_series_without_a_sub_model_is_searched_within_the_power_band(monkeypatch):
    """A Série 3 whose title names no sub-model, but whose power is known."""
    calls = []
    monkeypatch.setattr(svc, "_market_cache", {})
    listings = ([_golf(n, 190, 30000 + 10 * n, "BMW 320 d") for n in range(8)]
                + [_golf(20 + n, 150, 26000, "BMW 318 d") for n in range(8)])
    stats = _market(monkeypatch, calls, 190, listings=listings, brand="BMW", model="Serie 3")
    assert stats["sample_count"] == 8 and stats["min_price"] == 30000
    assert calls[0]["sv_model_slug"] is None and calls[0]["power_range"] == (161, 219)
    # Without the power it is still not searched.
    assert _market(monkeypatch, calls, None, listings=listings, brand="BMW", model="Serie 3") == {}
    assert len(calls) == 1


def test_mini_is_compared_by_power_instead_of_trim_when_it_is_known(monkeypatch):
    calls = []
    monkeypatch.setattr(svc, "_market_cache", {})
    listings = ([_golf(n, 136, 18000 + 10 * n, "MINI 3 Portas Cooper") for n in range(8)]
                + [_golf(20 + n, 192, 23000, "MINI 3 Portas Cooper S") for n in range(8)]
                + [_golf(40 + n, 136, 18500, "MINI 5 Portas") for n in range(2)])   # no trim in the title
    stats = _market(monkeypatch, calls, 136, listings=listings, brand="MINI", model="Cooper")
    assert stats["sample_count"] == 10                      # trim not required of the car or the listings
    assert stats["max_price"] < 19000
    # Power unknown: back to the trim.
    assert _market(monkeypatch, calls, None, listings=listings, brand="MINI", model="Cooper") == {}
    assert _market(monkeypatch, calls, None, listings=listings, brand="MINI", model="Cooper",
                   trim="cooper")["sample_count"] == 8


def test_power_comparison_reaches_the_cached_reference():
    stats = {"median_price": 14000, "avg_price": 14000, "min_price": 13000, "max_price": 15000,
             "sample_count": 16, "source": "live",
             "power_comparison": {"car_power_hp": 115, "power_from": 97, "power_to": 133, "pool_count": 16}}
    ref = svc._market_ref_for_cache(stats)
    assert ref["power_comparison"]["power_from"] == 97
    assert json.loads(json.dumps(ref)) == ref
