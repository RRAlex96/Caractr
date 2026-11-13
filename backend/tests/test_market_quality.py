"""
Market data quality. Cases are the real contaminated rows from the first
smoke-test scrape (Nov 2026): Standvirtual search results for "VW Golf 2020+"
included a Peugeot 308, Renault Clio, Mercedes C300, BMW i5 and a Ferrari Roma,
the Corolla 2018+ bucket had 1988/1994 cars, and 1 000 € placeholders.
"""
import pytest

from app.scrapers.model_match import listing_matches_generation, name_match
from app.services.market_aggregator import MIN_PUBLISH_SAMPLE, _compute_stats

SV = "https://www.standvirtual.com/carros/anuncio/"


def L(slug, year, price, title=""):
    return {"source_url": SV + slug, "year": year, "price": price, "title": title}


@pytest.mark.parametrize("listing", [
    L("peugeot-308-ver-puretech-130-eat6-stop-start-gt-line-edition-ID8Q1aSH.html", 2021, 15000),
    L("renault-clio-ver-1-2-rxe-ID8Q1aPC.html", 2021, 9000),
    L("mercedes-benz-c-300-ver-e-amg-line-ID8Q1lDz.html", 2023, 42900),
    L("bmw-i5-ver-edrive40-pack-desportivo-m-pro-ID8Q1haT.html", 2024, 51900),
    L("ferrari-roma-ver-standard-ID8Q109n.html", 2022, 209950),
])
def test_other_cars_in_search_results_are_rejected(listing):
    assert not listing_matches_generation(listing, "Volkswagen", "Golf", 2020, None)


def test_real_golf_is_accepted():
    assert listing_matches_generation(
        L("vw-golf-ver-1-5-tsi-e-hybrid-gte-dsg-ID8Q0ImG.html", 2022, 26400), "Volkswagen", "Golf", 2020, None)


def test_wrong_generation_year_is_rejected():
    old = L("toyota-corolla-ver-liftback-1-3-ID8Q1lCm.html", 1988, 1350)
    assert not listing_matches_generation(old, "Toyota", "Corolla", 2018, None)


def test_placeholder_price_is_rejected():
    gte = L("vw-golf-ver-1-5-tsi-e-hybrid-gte-dsg-ID8Q0ImG.html", 2025, 1000)
    assert not listing_matches_generation(gte, "Volkswagen", "Golf", 2020, None)


def test_more_specific_sibling_model_wins():
    cross = L("toyota-corolla-cross-ver-2-0-hybrid-ID8Q1xyz.html", 2023, 31000)
    assert not listing_matches_generation(cross, "Toyota", "Corolla", 2018, None,
                                          ["Corolla", "Corolla Cross", "Yaris"])
    assert listing_matches_generation(cross, "Toyota", "Corolla Cross", 2022, None,
                                      ["Corolla", "Corolla Cross", "Yaris"])


def test_bmw_series_codes():
    assert name_match("Série 3", "bmw 320 d auto")
    assert name_match("Série 3", "bmw 330e m sport")
    assert name_match("Série 3", "BMW 3 Series Touring")
    assert not name_match("Série 3", "bmw 520 d")
    assert not name_match("Série 3", "bmw x3 xdrive20d")
    assert name_match("Série 2 Gran Coupé", "bmw 218 i gran coupe")
    assert not name_match("Série 2 Gran Coupé", "bmw 218 i active tourer")


def test_robust_stats_ignore_a_ferrari_among_golfs():
    golfs = [17500, 18500, 19950, 21000, 22400, 24000, 26400]
    st = _compute_stats(golfs + [209950])
    assert st["p50"] < 25000 and st["p90"] < 30000 and st["n"] == len(golfs)


def test_publish_threshold_is_meaningful():
    assert MIN_PUBLISH_SAMPLE >= 6


# ── a thin model-year borrows its neighbours ────────────────────────────

def test_a_thin_year_is_priced_with_the_years_next_to_it():
    from app.services.market_aggregator import model_year_stats
    groups = {
        (1, 2014): [19000, 19500],                                 # 2 listings
        (1, 2015): [20500, 21000],                                 # 2
        (1, 2016): [22000, 22500, 23000],                          # 3
        (1, 2017): [24000, 25000, 25500, 26000, 26500, 27000, 27500],
    }
    stats = model_year_stats(groups)
    assert stats[(1, 2017)]["n"] == 7                              # enough on its own: not pooled
    assert stats[(1, 2017)]["p50"] == 26000
    assert stats[(1, 2015)]["n"] == 7                              # 2014 + 2015 + 2016
    assert 20500 <= stats[(1, 2015)]["p50"] <= 22000
    assert stats[(1, 2016)]["n"] == 12                             # 2015 + 2016 + 2017
    assert stats[(1, 2014)]["n"] == 7                              # 2014 + 2015 = 4, so two years out: + 2016


def test_a_year_too_thin_even_with_two_years_each_side_has_no_price():
    from app.services.market_aggregator import model_year_stats
    groups = {(1, 2014): [19000], (1, 2015): [20500, 21000], (1, 2016): [22000], (1, 2019): [30000] * 9}
    stats = model_year_stats(groups)
    assert stats[(1, 2014)] is None and stats[(1, 2015)] is None and stats[(1, 2016)] is None
    assert stats[(1, 2019)]["n"] == 9


def test_a_year_is_never_priced_from_neighbours_alone_or_from_another_model():
    from app.services.market_aggregator import model_year_stats
    groups = {
        (1, 2015): [20000] * 8,
        (1, 2017): [26000] * 8,       # no 2016 listing at all: no 2016 row is invented
        (2, 2016): [9000, 9500],      # another model's neighbours do not count
    }
    stats = model_year_stats(groups)
    assert (1, 2016) not in stats
    assert stats[(2, 2016)] is None
