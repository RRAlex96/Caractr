"""Our brand and model names -> Standvirtual's make and model ids.

The site drops an id it does not know and answers with every car of the make
(or of the site). Building the id by rule got 25 of the catalogue's 201 models
wrong, and every Citroën on the accent. Names are now matched against the
site's own list; all 201 catalogue searches were then checked against the live
site (scripts/audit_sv_slugs.py, 2026-11-13).
"""
import pytest

from app.scrapers.standvirtual import _build_search_url, _make_slug
from app.scrapers.sv_models import find_make, find_model
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
    ("ds", "4", "ds4"),
    ("ds", "7", "ds7"),
    ("ds", "DS 7", "ds7"),
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
    # Not on the site's list.
    ("mini", "Cooper", None),
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
    ("DS", "7", "/ds/ds7"),
    ("Smart", "#1", "/smart/smart-1"),
    ("Renault", "Mégane", "/renault/megane"),
    ("Renault", "Clio", "/renault/clio"),
    # A series or a sub-model is still decided first (sv_series).
    ("BMW", "Serie 3", "/bmw?search[filter_enum_model]=serie-3"),
    ("Mercedes-Benz", "E Coupé", "/mercedes-benz?search[filter_enum_model]=classe-e"),
    ("BMW", "X3", "/bmw/x3"),
    # Unknown to the site's list: a plain slug, without accents.
    ("MINI", "Cooper", "/mini/cooper"),
    ("Renault", "Modèle Nouveau", "/renault/modele-nouveau"),
])
def test_search_url_uses_the_sites_ids(brand, model, path):
    assert _build_search_url(brand, model) == BASE + path


def test_the_listings_own_slug_still_wins():
    assert _build_search_url("Volvo", "XC40", model_slug_override="xc-40-recharge") == f"{BASE}/volvo/xc-40-recharge"
