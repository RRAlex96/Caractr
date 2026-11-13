"""Model-year step of the live market comparison.

Inside its mileage band, the 2018 BMW 530e (170 000 km, €25 400) was still
compared with nine listings of which six were 2020–2022 cars, and came out
"12% below market". Listing prices are now adjusted to the car's own year and
km when a fit of price on year and km is well supported; otherwise only
listings of its year ±1 are compared, and when there are too few of those and
the car's year is not the middle of the rest, the price reference is withheld.
"""
import statistics

import pytest

from app.services import ad_analysis_service as svc
from app.services.ad_analysis_service import (
    _adjust_pool_to_car,
    _build_analysis_prompt,
    _build_anomaly,
    _build_negotiation_numbers,
    _build_response,
    _cached_market_for,
    _market_ref_for_cache,
    _market_stats_from_pool,
    _price_stats,
    _select_year_comparables,
    _withhold_if_not_comparable,
)
from test_market_km_band import REAL_530E, _listing, _market

# The 16 listings of the 2017–2023 generation (the two 2024 cars are dropped by
# the year guard before this step).
REAL_POOL = [{"year": y, "km": km, "price": p} for y, km, p in REAL_530E if y <= 2023]


def _pool(rows):
    return [{"year": y, "km": km, "price": p} for y, km, p in rows]


def _priced(year, km, noise=0.0):
    """A listing priced by a clean rule: €30 000 for a 2020 car with 100 000 km,
    8% per model year, 1.5% per 10 000 km."""
    return (year, km, round(30000 * 1.08 ** (year - 2020) * (1 - 0.0015) ** ((km - 100000) / 1000) * (1 + noise)))


# Ten listings spread over 2018–2022 and 60 000–180 000 km, within ±2% of the rule.
SPREAD = [_priced(y, km, n) for y, km, n in [
    (2018, 180000, 0.01), (2018, 140000, -0.02), (2019, 150000, 0.02), (2019, 110000, -0.01),
    (2020, 120000, 0.00), (2020, 90000, 0.02), (2021, 100000, -0.02), (2021, 70000, 0.01),
    (2022, 80000, -0.01), (2022, 60000, 0.02),
]]


def test_real_530e_is_judged_against_prices_adjusted_to_its_year_and_km(monkeypatch):
    listings = [_listing(km, price, year) for year, km, price in REAL_530E]
    stats = _market(monkeypatch, listings, km=170000, year=2018)

    assert (stats["median_price"], stats["sample_count"]) == (22096, 16)
    assert (stats["min_price"], stats["max_price"]) == (20729, 23450)
    assert stats["year_comparison"] == {
        "basis": "adjusted", "car_year": 2018, "car_km": 170000,
        "median_year": 2021, "year_from": 2017, "year_to": 2023,
        "km_from": 54170, "km_to": 174606,
        "count": 16, "excluded_count": 0, "pool_count": 16,
        "per_year_pct": 8.2, "per_10k_km_pct": -1.3, "margin_pct": 3.5,
    }
    # Mileage is part of the adjustment: there is no separate km band.
    assert "km_comparison" not in stats
    # market_price_stats still gets the whole pool, unadjusted.
    assert stats["pool_stats"]["median_price"] == 29895
    assert _withhold_if_not_comparable(stats) is stats

    # €25 400 was "15.0% below" the pool and "12.1% below" the km band.
    assert round((25400 - stats["median_price"]) / stats["median_price"] * 100, 1) == 15.0


def test_leave_one_out_on_the_real_pool():
    """Each real listing judged against the other 15: how far the reference is
    from the price that listing is actually asking."""
    errors, withheld = [], []
    for i, car in enumerate(REAL_POOL):
        others = REAL_POOL[:i] + REAL_POOL[i + 1:]
        stats = _withhold_if_not_comparable(_market_stats_from_pool(others, car["km"], "", car["year"]))
        if "median_price" not in stats:
            withheld.append((car["year"], car["km"]))
            continue
        assert stats["year_comparison"]["basis"] == "adjusted"
        errors.append(abs(stats["median_price"] - car["price"]) / car["price"] * 100)

    # The lowest-km car, the only 2017 car and the highest-km car: judging them
    # from the other 15 would be extrapolating.
    assert withheld == [(2023, 54170), (2017, 140000), (2022, 174606)]
    assert len(errors) == 13
    assert round(statistics.mean(errors), 1) == 3.4
    assert round(max(errors), 1) == 8.9


def test_clean_pool_recovers_the_year_and_km_effects():
    adjusted, info = _adjust_pool_to_car(_pool(SPREAD), 2019, 130000)
    assert info["basis"] == "adjusted"
    assert info["per_year_pct"] == pytest.approx(8.0, abs=1.0)
    assert info["per_10k_km_pct"] == pytest.approx(-1.5, abs=0.5)
    expected = _priced(2019, 130000)[2]
    assert _price_stats(adjusted)["median_price"] == pytest.approx(expected, rel=0.02)
    # The spread left after adjusting is the listings' own noise, not the year mix.
    assert max(adjusted) / min(adjusted) < 1.06


@pytest.mark.parametrize("rows, year, km, reason", [
    (SPREAD, None, 130000, "unknown"),
    (SPREAD, 2019, None, "unknown"),
    (SPREAD[:7], 2019, 130000, "few"),                       # 7 listings
    ([_priced(2019, km) for km in range(60000, 160000, 10000)], 2019, 100000, "single"),  # one model year
    (SPREAD, 2017, 130000, "outside"),                       # older than every listing
    (SPREAD, 2023, 70000, "outside"),                        # newer than every listing
    (SPREAD, 2019, 200000, "outside"),                       # more km than every listing
    (SPREAD, 2019, 40000, "outside"),                        # fewer km than every listing
    (SPREAD, 2022, 180000, "outside"),                       # inside both ranges, far from any listing
])
def test_no_adjustment_without_support(rows, year, km, reason):
    assert _adjust_pool_to_car(_pool(rows), year, km) == (None, reason)


def test_no_adjustment_when_the_fit_is_implausible_or_loose():
    # Price rising with mileage: not a depreciation curve.
    backwards = [(y, km, round(p * (1 + (km - 100000) / 200000))) for y, km, p in SPREAD]
    assert _adjust_pool_to_car(_pool(backwards), 2019, 130000) == (None, "unstable")
    # 60% per model year: implausibly steep.
    steep = [(y, km, round(p * 1.5 ** (y - 2020))) for y, km, p in SPREAD]
    assert _adjust_pool_to_car(_pool(steep), 2020, 110000) == (None, "unstable")
    # Prices ±20% around the rule (trims, condition): the margin is too wide.
    loose = [_priced(y, km, 0.2 if i % 2 else -0.2) for i, (y, km, _) in enumerate(SPREAD)]
    assert _adjust_pool_to_car(_pool(loose), 2020, 110000) == (None, "unstable")


def test_a_listing_far_from_the_others_is_left_out_of_the_fit():
    clean = _market_stats_from_pool(REAL_POOL, 170000, "", 2018)
    for junk in ({"year": 2019, "km": 100000, "price": 2000},      # deposit shown as the price
                 {"year": 2020, "km": 120000, "price": 17500}):    # salvage car, ~38% under
        stats = _market_stats_from_pool(REAL_POOL + [junk], 170000, "", 2018)
        assert stats["median_price"] == clean["median_price"]
        assert stats["year_comparison"]["count"] == 16
        assert stats["year_comparison"]["excluded_count"] == 1
        assert stats["year_comparison"]["pool_count"] == 17

    # A listing in line with the others is used, and moves the reference a little.
    stats = _market_stats_from_pool(REAL_POOL + [{"year": 2019, "km": 150000, "price": 22000}], 170000, "", 2018)
    assert stats["year_comparison"]["count"] == 17
    assert stats["year_comparison"]["excluded_count"] == 0
    assert stats["median_price"] == pytest.approx(clean["median_price"], rel=0.02)


# A pool too small to fit (6 listings): the year is handled by selection.
def test_listings_of_the_cars_year_are_preferred_when_five_are(monkeypatch):
    rows = [(2018, 150000, 21000), (2018, 160000, 20500), (2019, 150000, 22500), (2019, 170000, 21500),
            (2017, 180000, 19000), (2022, 160000, 29000), (2023, 150000, 33000)]
    stats = _market(monkeypatch, [_listing(km, p, y) for y, km, p in rows], km=165000, year=2018)
    assert stats["km_comparison"]["basis"] == "band"
    assert stats["year_comparison"] == {
        "basis": "near", "car_year": 2018, "median_year": 2019,
        "year_from": 2017, "year_to": 2019, "count": 5, "not_adjusted": "few",
    }
    assert (stats["median_price"], stats["sample_count"]) == (21000, 5)
    assert stats["pool_stats"]["sample_count"] == 7


def test_year_mix_that_cannot_be_adjusted_withholds_the_price_reference(monkeypatch):
    # The real pool without the two listings that anchor the old, high-km end:
    # the 2018 car is now older than all but one and has more km than most.
    rows = [r for r in REAL_530E if r[0] not in (2017, 2024) and r[1] != 174606]
    stats = _market(monkeypatch, [_listing(km, p, y) for y, km, p in rows], km=170000, year=2018)

    assert stats["km_comparison"]["basis"] == "band"
    assert stats["year_comparison"] == {
        "basis": "mismatch", "car_year": 2018, "median_year": 2021,
        "year_from": 2018, "year_to": 2022, "count": 7, "not_adjusted": "outside",
    }
    # The stats are still returned: the pool's are what goes to the database.
    assert stats["median_price"] == 28900 and stats["pool_stats"]["sample_count"] == 14

    withheld = _withhold_if_not_comparable(stats)
    for key in ("avg_price", "median_price", "min_price", "max_price", "sample_count", "pool_stats"):
        assert key not in withheld
    assert withheld["year_comparison"] == stats["year_comparison"]

    car = {"price": 25400, "km": 170000, "year": 2018, "seller_type": "profissional"}
    assert _build_negotiation_numbers(car, stats) is not None
    assert _build_negotiation_numbers(car, withheld) is None
    # A 2018 car at €19 000 is not "below market" against 2021 cars.
    cheap = {**car, "price": 19000}
    assert _build_anomaly(cheap, stats, []) is not None
    assert _build_anomaly(cheap, withheld, []) is None


def test_car_in_the_middle_of_the_years_keeps_the_selection():
    rows = [(2018, 100000, 20000), (2019, 100000, 22000), (2020, 100000, 24000),
            (2021, 100000, 26000), (2022, 100000, 28000), (2022, 110000, 27500)]
    compared, info = _select_year_comparables(_pool(rows), 2020)
    assert info["basis"] == "typical" and info["median_year"] == 2020.5
    assert compared == _pool(rows)
    # One year off the middle is a mismatch: at ~8% a year that is not a detail.
    assert _select_year_comparables(_pool(rows), 2019)[1]["basis"] == "mismatch"
    assert _select_year_comparables(_pool(rows), 2022)[1]["basis"] == "mismatch"


def test_all_listings_within_a_year_are_kept_even_without_a_year():
    rows = _pool([(2019, 90000, 22000), (2020, 80000, 24000), (2020, 85000, 23500),
                  (2021, 70000, 26000), (2021, 60000, 26500)]) + [{"year": None, "km": 75000, "price": 25000}]
    compared, info = _select_year_comparables(rows, 2020)
    assert info["basis"] == "typical" and info["count"] == 6
    assert compared == rows


def test_unknown_years_leave_the_comparison_as_it_was(monkeypatch):
    listings = [_listing(km, p, None) for km, p in
                [(150000, 21000), (160000, 20500), (170000, 20000), (175000, 21500), (180000, 19500), (165000, 20800)]]
    stats = _market(monkeypatch, listings, km=170000, year=2018)
    assert "year_comparison" not in stats
    assert stats["km_comparison"]["basis"] == "band"
    assert stats["sample_count"] == 6
    # And a car whose year is unknown is not judged on year at all.
    assert _select_year_comparables(REAL_POOL, None) == (REAL_POOL, None)


def test_cached_pool_keeps_the_year_and_serves_cars_of_any_year(monkeypatch):
    calls = []
    monkeypatch.setattr(svc, "_market_cache", {})
    listings = [_listing(km, price, year) for year, km, price in REAL_530E]
    old = _market(monkeypatch, listings, km=170000, year=2018, calls=calls)
    young = _market(monkeypatch, listings, km=100000, year=2021, calls=calls)
    assert len(calls) == 1                      # second car served from the cache
    assert (old["median_price"], young["median_price"]) == (22096, 30678)
    assert young["year_comparison"]["basis"] == "adjusted"
    (entry,) = svc._market_cache.values()
    assert set(entry["pool"][0]) == {"price", "km", "year"}


def test_response_says_how_the_year_was_handled(monkeypatch):
    listings = [_listing(km, price, year) for year, km, price in REAL_530E]
    stats = _market(monkeypatch, listings, km=170000, year=2018)
    listing = {"brand_name": "BMW", "model_name": "530", "year": 2018, "km": 170000,
               "price": 25400, "source_url": "https://www.standvirtual.com/carros/anuncio/x-ID1.html"}
    deal = _build_response(listing, {}, market_stats=stats)["deal"]
    assert deal["market_median_price"] == 22096
    assert deal["market_sample_count"] == 16
    assert deal["market_km_comparison"] is None
    assert deal["market_year_comparison"]["basis"] == "adjusted"
    assert deal["market_year_comparison"]["margin_pct"] == 3.5

    assert _build_response(listing, {}, market_stats=None)["deal"]["market_year_comparison"] is None


def test_prompt_tells_the_llm_the_reference_is_adjusted():
    stats = _market_stats_from_pool(REAL_POOL, 170000, "", 2018)
    listing = {"brand_name": "BMW", "model_name": "530", "year": 2018, "km": 170000,
               "price": 25400, "price_delta_pct": 15.0, "price_delta": -0.75}
    prompt = _build_analysis_prompt(listing, {}, stats, None)
    assert "(16 anúncios, preços ajustados ao ano e aos km deste carro)" in prompt
    assert "15.0% acima do mercado" in prompt


def test_cached_analysis_is_served_with_the_reference_it_was_judged_against():
    # What the database holds for the model and year: the whole pool.
    db_stats = {"avg_price": 29738.0, "min_price": 20900, "max_price": 38990,
                "sample_count": 16, "source": "live_scraped", "age_days": 2, "stale": False}

    adjusted = _market_stats_from_pool(REAL_POOL, 170000, "", 2018)
    ref = _market_ref_for_cache(adjusted)
    assert "pool_stats" not in ref and "source" not in ref
    cached = _cached_market_for(db_stats, {"_market_ref": ref})
    assert (cached["median_price"], cached["avg_price"], cached["sample_count"]) == (22096, 22251, 16)
    assert cached["year_comparison"]["basis"] == "adjusted"
    assert (cached["source"], cached["age_days"]) == ("live_scraped", 2)

    # A withheld reference stays withheld.
    mismatch = {"basis": "mismatch", "car_year": 2018, "median_year": 2021,
                "year_from": 2018, "year_to": 2022, "count": 7, "not_adjusted": "outside"}
    withheld = _withhold_if_not_comparable({**_price_stats([28900, 29000, 31900]), "source": "live",
                                            "year_comparison": mismatch})
    cached = _cached_market_for(db_stats, {"_market_ref": _market_ref_for_cache(withheld)})
    assert "avg_price" not in cached and "median_price" not in cached and "sample_count" not in cached
    assert cached["year_comparison"] == mismatch

    # Nothing compared per car (no live data, or neither year nor km known): DB stats.
    assert _market_ref_for_cache({"avg_price": 1, "source": "db"}) is None
    assert _market_ref_for_cache(None) is None
    assert _cached_market_for(db_stats, {"_market_ref": None}) == db_stats
