"""Our brand and model names -> Standvirtual's make and model ids.

The site drops an id it does not know and answers with every car of the make
(or of the site). Building the id by rule got 25 of the catalogue's 201 models
wrong, and every Citroën on the accent. Names are now matched against the
site's own list; all 201 catalogue searches were then checked against the live
site (scripts/audit_sv_slugs.py, 2026-11-13).
"""
import pytest

import asyncio

from app.scrapers import dispatcher
from app.scrapers.standvirtual import _build_search_url, _make_slug, search_needs_trim
from app.scrapers.sv_models import find_make, find_model, trim_label
from app.services import ad_analysis_service as svc
from app.services.ad_analysis_service import _market_trim
from app.scrapers.sv_models_data import SV_MAKES, SV_MODELS

BASE = "https://www.standvirtual.com/carros"


def test_snapshot_is_plausible():
    assert len(SV_MAKES) >= 100
    assert set(SV_MODELS) <= set(SV_MAKES)
    assert sum(len(models) for models in SV_MODELS.values()) >= 2000
    assert SV_MODELS["renault"]["clio"] == "Clio"


@pytest.mark.parametrize("brand, make", [
    ("Volkswagen", "vw"),
    ("VW", "vw"),
    ("Citroën", "citroen"),            # the catalogue's spelling; "citroën" is no make of the site
    ("Citroen", "citroen"),
    ("Mercedes-Benz", "mercedes-benz"),
    ("Mercedes", "mercedes-benz"),
    ("Mercedes Benz", "mercedes-benz"),
    ("MINI", "mini"),
    ("Land Rover", "land-rover"),
    ("Alfa Romeo", "alfa-romeo"),
    ("SEAT", "seat"),
    ("DS", "ds"),
    ("Not A Make", None),
    ("", None),
    (None, None),
])
def test_brand_names_map_to_the_sites_makes(brand, make):
    assert find_make(brand) == make


def test_unknown_brand_falls_back_to_a_plain_slug():
    assert _make_slug("Not A Make") == "not-a-make"
    assert _make_slug("Citroën") == "citroen"


@pytest.mark.parametrize("make, model, model_id", [
    # Punctuation and spacing the plain rule got wrong.
    ("volvo", "XC40", "xc-40"),
    ("volvo", "XC60", "xc-60"),
    ("volvo", "XC90", "xc-90"),
    ("volvo", "EX30", "ex-30"),
    ("vw", "ID.3", "id-3"),
    ("vw", "up!", "up"),
    ("mazda", "CX-30", "cx30"),
    ("mazda", "CX-5", "cx-5"),
    ("honda", "e:Ny1", "e-ny1"),
    ("smart", "#1", "smart-1"),
    ("smart", "#3", "smart-3"),
    ("renault", "Mégane", "megane"),
    ("renault", "Megane", "megane"),
    ("renault", "Scénic", "scenic"),
    # The site's id is not its name.
    ("cupra", "Leon", "cupra-leon"),
    ("seat", "Leon", "leon"),
    ("land-rover", "Range Rover Evoque", "evoque"),
    ("land-rover", "Range Rover Velar", "velar"),
    ("land-rover", "Range Rover", "range-rover"),
    # The site writes the make in front.
    ("mg", "4", "mg4"),
    ("mg", "5", "mg5"),
    # The site calls it something else.
    ("hyundai", "Kona", "kauai"),
    ("mg", "ZS EV", "zs"),
    ("opel", "Combo Life", "combo"),
    ("skoda", "Superb Combi", "superb-break"),
    # A "+" is part of the name.
    ("toyota", "C-HR", "c-hr"),
    ("toyota", "C-HR+", "c-hr-plus"),
    ("peugeot", "206", "206"),
    ("peugeot", "206+", "206-plus"),
    # Plain ones stay as they were.
    ("renault", "Clio", "clio"),
    ("vw", "Golf", "golf"),
    ("tesla", "Model 3", "model-3"),
    ("fiat", "500X", "500x"),
    # One car under two ids: both, in the site's form for several models.
    ("ds", "7", "ds7--ds7-crossback"),
    ("ds", "DS 7", "ds7--ds7-crossback"),
    ("ds", "DS7 Crossback", "ds7--ds7-crossback"),
    ("ds", "4", "ds4--number-4"),
    ("ds", "3", "ds3"),                               # the old DS3 is another car: not merged
    ("mini", "3 Portas", "mini-3p--mini-5p"),
    ("mini", "5 Portas", "mini-3p--mini-5p"),
    # The MINI hatch goes by its trims with us and in listings.
    ("mini", "Cooper", "mini-3p--mini-5p"),
    ("mini", "Cooper S", "mini-3p--mini-5p"),
    ("mini", "One D", "mini-3p--mini-5p"),
    ("mini", "John Cooper Works", "mini-3p--mini-5p"),
    ("mini", "Countryman", "countryman"),
    ("mini", "Clubman", "clubman"),
    # Not on the site's list.
    ("renault", "Not A Model", None),
    ("renault", "", None),
    (None, "Clio", None),
])
def test_model_names_map_to_the_sites_models(make, model, model_id):
    assert find_model(make, model) == model_id


@pytest.mark.parametrize("brand, model, path", [
    ("Volkswagen", "ID.3", "/vw/id-3"),
    ("Volkswagen", "up!", "/vw/up"),
    ("Volvo", "XC40", "/volvo/xc-40"),
    ("Citroën", "C3 Aircross", "/citroen/c3-aircross"),
    ("Cupra", "Leon", "/cupra/cupra-leon"),
    ("Hyundai", "Kona", "/hyundai/kauai"),
    ("Land Rover", "Range Rover Evoque", "/land-rover/evoque"),
    ("DS", "7", "/ds/ds7--ds7-crossback"),
    ("DS", "4", "/ds/ds4--number-4"),
    ("MINI", "Cooper", "/mini/mini-3p--mini-5p"),
    ("Smart", "#1", "/smart/smart-1"),
    ("Renault", "Mégane", "/renault/megane"),
    ("Renault", "Clio", "/renault/clio"),
    # A series or a sub-model is still decided first (sv_series).
    ("BMW", "Serie 3", "/bmw?search[filter_enum_model]=serie-3"),
    ("Mercedes-Benz", "E Coupé", "/mercedes-benz?search[filter_enum_model]=classe-e"),
    ("BMW", "X3", "/bmw/x3"),
    # Unknown to the site's list: a plain slug, without accents.
    ("Renault", "Modèle Nouveau", "/renault/modele-nouveau"),
])
def test_search_url_uses_the_sites_ids(brand, model, path):
    assert _build_search_url(brand, model) == BASE + path


def test_the_listings_own_slug_still_wins():
    assert _build_search_url("Volvo", "XC40", model_slug_override="xc-40-recharge") == f"{BASE}/volvo/xc-40-recharge"


def test_the_listings_own_slug_is_widened_to_the_cars_other_id():
    """A Standvirtual DS 7 Crossback comes with "ds7-crossback"; the same car
    is also filed as "ds7"."""
    assert _build_search_url("DS", "7", model_slug_override="ds7-crossback") == f"{BASE}/ds/ds7--ds7-crossback"
    assert _build_search_url("DS", "7", model_slug_override="ds7") == f"{BASE}/ds/ds7--ds7-crossback"
    assert _build_search_url("MINI", "Cooper", model_slug_override="mini-5p") == f"{BASE}/mini/mini-3p--mini-5p"
    assert _build_search_url("MINI", "Countryman", model_slug_override="countryman") == f"{BASE}/mini/countryman"
    url = _build_search_url("MINI", "Cooper", None, 2014, 2023, "Gasolina", "mini-3p", 2)
    assert url == (f"{BASE}/mini/mini-3p--mini-5p?search[filter_float_first_registration_year:from]=2014"
                   "&search[filter_float_first_registration_year:to]=2023&search[filter_enum_fuel_type][0]=gaz&page=2")


# ── Trims: the MINI hatch ────────────────────────────────────────────────────
# Every MINI hatch is a "Cooper" in the catalogue, be it a One or a John Cooper
# Works. Against all trims the reference is off by more than 20% for half the
# petrol cars; within the trim, for one in seven.

@pytest.mark.parametrize("text, trim", [
    ("MINI 3 Portas Cooper S Auto", "cooper s"),
    ("MINI 5 Portas Cooper", "cooper"),
    ("MINI 5 Portas One", "one"),
    ("MINI 3 Portas One D", "one"),                    # diesels: kept apart by the fuel filter
    ("MINI Cooper D 5 portas", "cooper"),
    ("MINI Cooper SD", "cooper s"),
    ("MINI 3 Portas Cooper SE", "cooper se"),
    ("MINI 3 Portas John Cooper Works Auto Desportiva", "jcw"),
    ("Mini JCW 231cv", "jcw"),
    ("MINI 3 Portas Cooper Sport Edition", "cooper"),  # "Sport" is not an "S"
    ("https://www.standvirtual.com/carros/anuncio/mini-3-portas-ver-cooper-s-auto-ID8Q1.html", "cooper s"),
    ("Mini 3 portas 2018 gasolina", None),
    ("", None),
    (None, None),
])
def test_mini_trim_is_read_from_the_listing(text, trim):
    assert trim_label(text) == trim


def test_trim_comes_from_the_first_text_that_names_one():
    assert trim_label(None, "MINI 3 Portas", "Cooper S Auto", "MINI One") == "cooper s"


def test_trim_is_taken_from_title_version_model_or_url():
    assert _market_trim({"source_title": "MINI 3 Portas Cooper S Auto"}, None) == "cooper s"
    assert _market_trim({"version": "One D"}, None) == "one"
    assert _market_trim({"source_model_name": "John Cooper Works"}, None) == "jcw"
    assert _market_trim({}, "https://www.olx.pt/d/anuncio/mini-cooper-d-5-portas-IDabc.html") == "cooper"
    assert _market_trim({"source_title": "Mini 3 portas"}, None) is None


def test_only_the_mini_hatch_search_needs_a_trim():
    assert search_needs_trim("MINI", "Cooper")
    assert search_needs_trim("MINI", "Cooper", "mini-3p") and search_needs_trim("MINI", "Cooper", "mini-5p")
    assert not search_needs_trim("MINI", "Countryman") and not search_needs_trim("MINI", "Cooper", "countryman")
    assert not search_needs_trim("DS", "7") and not search_needs_trim("Renault", "Clio")


def _mini(n, title, price, slug="mini-3p"):
    return {"year": 2018, "km": 60000 + 1000 * n, "price": price, "fuel_type": "Gasolina", "title": title,
            "sv_model_slug": slug, "source_url": f"https://x/carros/anuncio/mini-ID{n}.html"}


MINI_POOL = (
    [_mini(n, "MINI 3 Portas One", 14000 + 10 * n) for n in range(8)]
    + [_mini(20 + n, "MINI 5 Portas Cooper", 18000 + 10 * n, "mini-5p") for n in range(8)]
    + [_mini(40 + n, "MINI 3 Portas Cooper S Auto", 23000 + 10 * n) for n in range(8)]
    + [_mini(60 + n, "MINI 3 Portas John Cooper Works", 30000 + 10 * n) for n in range(4)]
    + [_mini(80 + n, "MINI 3 Portas", 20000) for n in range(3)]
)


def _mini_market(monkeypatch, calls, trim, slug=None, model="Cooper", listings=MINI_POOL):
    async def fake_fetch(**kwargs):
        calls.append(kwargs)
        return listings

    monkeypatch.setattr(dispatcher, "fetch_listings_all_sources", fake_fetch)
    return asyncio.run(svc._fetch_live_market_data(
        "MINI", model, 2018, fuel_type="Gasolina", gen_year_start=2014, gen_year_end=2023,
        sv_model_slug=slug, trim=trim))


def test_mini_is_compared_within_its_trim(monkeypatch):
    calls = []
    monkeypatch.setattr(svc, "_market_cache", {})
    assert _mini_market(monkeypatch, calls, "one")["median_price"] == 14035
    cooper = _mini_market(monkeypatch, calls, "cooper", slug="mini-5p")
    assert cooper["sample_count"] == 8 and cooper["median_price"] == 18035   # not the Cooper S or the JCW
    assert _mini_market(monkeypatch, calls, "cooper s", slug="mini-3p")["median_price"] == 23035
    assert len(calls) == 3                                                   # one cached pool per trim


def test_mini_with_few_of_its_trim_gets_no_verdict_and_never_the_other_trims(monkeypatch):
    monkeypatch.setattr(svc, "_market_cache", {})
    jcw = _mini_market(monkeypatch, [], "jcw")
    assert jcw["sample_count"] == 4 < svc._MIN_RELIABLE_MARKET_SAMPLE
    assert jcw["median_price"] == 30015
    assert _mini_market(monkeypatch, [], "cooper se") == {}                  # none of that trim: nothing


def test_mini_without_a_trim_is_not_compared(monkeypatch):
    calls = []
    monkeypatch.setattr(svc, "_market_cache", {})
    assert _mini_market(monkeypatch, calls, None) == {}
    assert _mini_market(monkeypatch, calls, None, slug="mini-3p") == {}
    assert calls == []


def test_trim_is_ignored_for_models_that_do_not_need_it(monkeypatch):
    monkeypatch.setattr(svc, "_market_cache", {})
    listings = [dict(l, title=l["title"].replace("3 Portas", "Countryman").replace("5 Portas", "Countryman"),
                     sv_model_slug="countryman") for l in MINI_POOL]
    stats = _mini_market(monkeypatch, [], "cooper", slug="countryman", model="Countryman", listings=listings)
    assert stats["sample_count"] == len(MINI_POOL)
