"""Series-level models and Standvirtual's sub-models.

Our catalogue files BMW, Mercedes and Lexus cars under the series ("Serie 3",
"Classe A", "NX"). The site only takes a sub-model ("320", "a-180", "nx-300h")
in the search path; "/carros/bmw/serie-3" is every BMW. A car that does not
come with the site's own slug must be searched under the sub-model its title
names, and must get no live reference when it names none: against the whole
series the reference is off by more than 20% for one car in four.
"""
import asyncio

import pytest

from app.scrapers import dispatcher
from app.scrapers.standvirtual import _build_search_url, is_series_model, sv_model_slug_for
from app.scrapers.sv_series import find_series, find_variant
from app.scrapers.sv_series_data import SV_SERIES
from app.services import ad_analysis_service as svc
from app.services.ad_analysis_service import _market_model_slug


def test_taxonomy_snapshot_is_whole():
    assert set(SV_SERIES) == {"bmw", "mercedes-benz", "lexus", "porsche"}
    assert sum(len(series) for series in SV_SERIES.values()) >= 50
    assert sum(len(variants) for series in SV_SERIES.values() for _, variants in series.values()) >= 450
    assert SV_SERIES["bmw"]["serie-5"][1]["530"] == "530"
    assert SV_SERIES["mercedes-benz"]["classe-a"][1]["a-180"] == "A 180"


@pytest.mark.parametrize("make, model, series", [
    ("bmw", "Serie 5", "serie-5"),
    ("bmw", "Série 3", "serie-3"),
    ("bmw", "3 Series", "serie-3"),
    ("bmw", "Série 2 Gran Coupé", "serie-2"),      # a body style of the series
    ("mercedes-benz", "Classe A", "classe-a"),
    ("mercedes-benz", "CLA", "classe-cla"),
    ("mercedes-benz", "Classe C", "classe-c"),       # not "classe-cla" / "classe-cl"
    ("mercedes-benz", "GLC Coupé", "classe-glc"),
    ("mercedes-benz", "SLK", "classe-slk"),          # not "classe-sl"
    ("lexus", "NX", "nx"),
    ("porsche", "911", "911-todos"),
    # Not series:
    ("bmw", "530", None),                            # a sub-model
    ("bmw", "X3", None),
    ("mercedes-benz", "A", None),                    # a bare letter is too little
    ("mercedes-benz", "E Coupé", "classe-e"),        # ... unless a body style follows
    ("mercedes-benz", "C Cabrio", "classe-c"),
    ("mercedes-benz", "A 180", None),                # a sub-model, not a series
    ("mercedes-benz", "EQA", None),                  # a model without sub-models
    ("porsche", "Cayenne", None),
    ("vw", "Golf", None),
    ("renault", "Clio", None),
    ("bmw", "", None),
    (None, "Serie 5", None),
])
def test_series_are_recognised(make, model, series):
    assert find_series(make, model) == series


@pytest.mark.parametrize("make, model, text, slug", [
    # BMW: the number is the sub-model, whatever engine letter follows it.
    ("bmw", "Serie 3", "BMW 320d Touring Pack M", "320"),
    ("bmw", "Serie 3", "BMW Série 3 320 d Auto 190cv", "320"),
    ("bmw", "Serie 3", "BMW 330e iPerformance 252 cv", "330"),
    ("bmw", "Serie 3", "BMW M340i xDrive", "m340"),
    ("bmw", "Serie 3", "BMW M3 Competition", "m3"),
    ("bmw", "Serie 5", "https://www.olx.pt/d/anuncio/bmw-530e-iperformance-IDabc12.html", "530"),
    # Body styles the site files apart.
    ("bmw", "Serie 3", "BMW 320d Gran Turismo", "320-gran-turismo"),
    ("bmw", "Serie 3", "BMW 320d GT Line Sport", "320-gran-turismo"),
    ("bmw", "Serie 4", "BMW 420d Gran Coupé", "420-gran-coupe"),
    ("bmw", "Serie 4", "BMW 420d Coupé", "420"),
    ("bmw", "Série 2 Gran Coupé", "BMW 218i", "218-gran-coupe"),   # body style from the catalogue name
    ("bmw", "Serie 2", "BMW 225xe Active Tourer", "225xe-active-tourer"),
    # Numbers that are not a sub-model.
    ("bmw", "Serie 3", "BMW Série 3 320 cv", None),
    ("bmw", "Serie 3", "BMW Série 3 Touring 2019 150.000 km", None),
    ("bmw", "Serie 1", "BMW 116d 2018 118.000km", "116"),
    ("bmw", "Serie 5", "BMW 520d 190cv 520 000 km", "520"),
    ("bmw", "Serie 2", "BMW Série 2 2020 Active Tourer", None),
    # The first one named wins.
    ("bmw", "Serie 3", "BMW 320d, troco por 318d", "320"),
    # Mercedes: letters and number, written together or apart.
    ("mercedes-benz", "Classe A", "Mercedes-Benz A 180 d Style", "a-180"),
    ("mercedes-benz", "Classe A", "Mercedes A180d AMG Line", "a-180"),
    ("mercedes-benz", "Classe A", "Mercedes-Benz A 180 d Limousine", "a-180-limousine"),
    ("mercedes-benz", "Classe A", "Mercedes A 35", "a-35-amg"),            # "AMG" left out
    ("mercedes-benz", "Classe A", "Mercedes-AMG A 45 S 4Matic+", "a-45-amg"),
    ("mercedes-benz", "Classe C", "Mercedes-Benz C 220 d Avantgarde", "c-220"),
    ("mercedes-benz", "Classe C", "Mercedes C 63 S", "c-63"),
    ("mercedes-benz", "Classe M", "Mercedes ML 320 CDI", "ml-320"),
    ("mercedes-benz", "CLA", "Mercedes CLA 250 e", "cla-250"),
    ("mercedes-benz", "CLA", "Mercedes CLA 250+ AMG", "cla-250-plus"),
    ("mercedes-benz", "Classe E", "Mercedes Classe E 300 de 200 cv", "e-300"),
    # Another class's sub-model is never taken.
    ("mercedes-benz", "Classe C", "Mercedes CLA 220 d", None),
    ("mercedes-benz", "Classe C", "Mercedes GLC 220 d", None),
    ("mercedes-benz", "Classe A", "Mercedes Classe A 2019 Diesel", None),
    # Lexus, Porsche 911.
    ("lexus", "NX", "Lexus NX 350h Executive", "nx-350h"),
    ("lexus", "NX", "Lexus NX 450h+ F Sport", "nx-450hplus"),
    ("lexus", "IS", "Lexus IS 300h", "is-300h"),                           # not "is-300"
    ("porsche", "911", "Porsche 911 Carrera 4S (991)", "991"),
    ("porsche", "911", "Porsche 911 Carrera", None),
    # The catalogue name is itself a sub-model: no text needed.
    ("bmw", "530", None, "530"),
    ("bmw", "X3", None, "x3"),
    ("mercedes-benz", "A 180", None, "a-180"),
    ("lexus", "IS 300h", None, "is-300h"),
    # Makes and models the site does not file by series.
    ("vw", "Golf", "VW Golf 1.6 TDI", None),
    ("bmw", "Serie 3", None, None),
])
def test_sub_model_is_read_from_the_listing(make, model, text, slug):
    assert find_variant(make, model, text) == slug


def test_search_url_for_a_series_and_for_a_sub_model():
    base = "https://www.standvirtual.com/carros"
    # A series only works as a filter on the make.
    url = _build_search_url("BMW", "Serie 5", None, 2017, 2023, "Híbrido Plug-In")
    assert url.startswith(f"{base}/bmw?search[filter_enum_model]=serie-5&")
    assert "search[filter_float_first_registration_year:from]=2017" in url
    assert "search[filter_enum_fuel_type][0]=plugin-hybrid" in url
    assert _build_search_url("Mercedes-Benz", "Classe A") == f"{base}/mercedes-benz?search[filter_enum_model]=classe-a"
    assert _build_search_url("BMW", "Série 3", page=2) == f"{base}/bmw?search[filter_enum_model]=serie-3&page=2"
    # A sub-model goes in the path: from the catalogue name or the given slug.
    assert _build_search_url("BMW", "530") == f"{base}/bmw/530"
    assert _build_search_url("Mercedes-Benz", "A 180") == f"{base}/mercedes-benz/a-180"
    assert _build_search_url("Mercedes-Benz", "Classe A", model_slug_override="a-180") == f"{base}/mercedes-benz/a-180"
    # Everything else is unchanged.
    assert _build_search_url("Renault", "Clio") == f"{base}/renault/clio"
    assert _build_search_url("Mercedes-Benz", "EQA") == f"{base}/mercedes-benz/eqa"


def test_series_model_helpers_take_our_brand_names():
    assert is_series_model("BMW", "Serie 3") and is_series_model("Mercedes-Benz", "Classe A")
    assert not is_series_model("BMW", "530") and not is_series_model("Renault", "Clio")
    assert sv_model_slug_for("Mercedes-Benz", "Classe C", "Mercedes-Benz C 220 d") == "c-220"


def test_market_slug_prefers_the_listings_own_then_title_model_url():
    own = {"sv_model_slug": "a-200", "source_title": "Mercedes-Benz A 180 d"}
    assert _market_model_slug(own, "Mercedes-Benz", "Classe A", None) == "a-200"
    assert _market_model_slug({"source_title": "BMW 320d Touring"}, "BMW", "Serie 3", None) == "320"
    assert _market_model_slug({"source_model_name": "A 180"}, "Mercedes-Benz", "Classe A", None) == "a-180"
    assert _market_model_slug({}, "BMW", "Serie 5",
                              "https://www.standvirtual.com/carros/anuncio/bmw-530-ver-e-pack-m-ID8Q1gmK.html") == "530"
    assert _market_model_slug({"source_title": "BMW Série 3 Touring"}, "BMW", "Serie 3", None) is None
    assert _market_model_slug({"source_title": "Renault Clio 1.0 TCe"}, "Renault", "Clio", None) is None


def _listing(n, price):
    return {"year": 2019, "km": 90000 + n, "price": price, "fuel_type": "Diesel", "title": "Mercedes-Benz A",
            "source_url": f"https://x/carros/anuncio/mercedes-benz-a-ID{n}{price}.html"}


def _market(monkeypatch, calls, slug, prices=None):
    async def fake_fetch(**kwargs):
        calls.append(kwargs)
        by_slug = prices or {}
        return [_listing(n, by_slug.get(kwargs["sv_model_slug"], 20000)) for n in range(8)]

    monkeypatch.setattr(dispatcher, "fetch_listings_all_sources", fake_fetch)
    return asyncio.run(svc._fetch_live_market_data(
        "Mercedes-Benz", "Classe A", 2019, fuel_type="Diesel",
        gen_year_start=2018, gen_year_end=None, sv_model_slug=slug))


def test_series_without_a_sub_model_gets_no_live_reference(monkeypatch):
    calls = []
    monkeypatch.setattr(svc, "_market_cache", {})
    assert _market(monkeypatch, calls, None) == {}
    assert calls == []                      # not even searched


def test_series_with_a_sub_model_is_searched_under_it(monkeypatch):
    calls = []
    monkeypatch.setattr(svc, "_market_cache", {})
    stats = _market(monkeypatch, calls, "a-180")
    assert stats["sample_count"] == 8
    assert [c["sv_model_slug"] for c in calls] == ["a-180"]


def test_two_sub_models_of_one_series_do_not_share_a_cached_pool(monkeypatch):
    calls = []
    monkeypatch.setattr(svc, "_market_cache", {})
    prices = {"a-180": 20000, "a-250": 30000}
    assert _market(monkeypatch, calls, "a-180", prices)["median_price"] == 20000
    assert _market(monkeypatch, calls, "a-250", prices)["median_price"] == 30000
    assert _market(monkeypatch, calls, "a-180", prices)["median_price"] == 20000   # from the cache
    assert [c["sv_model_slug"] for c in calls] == ["a-180", "a-250"]
