"""Model resolution guard, variant codes, and the OLX detail label parsing."""
from app.services.ad_analysis_service import _models_compatible, _sv_variant_code
from app.scrapers.olx import _extract_pt_label_values, _norm_fuel, _norm_transmission
from app.scrapers.standvirtual import _sv_fuel_values


def test_models_compatible_blocks_wrong_match():
    # The Velar/Evoque bug: different last token, no containment -> incompatible.
    assert _models_compatible("Range Rover Velar", "Range Rover Evoque") is False
    # Genuine matches stay compatible.
    assert _models_compatible("Golf", "Golf") is True
    assert _models_compatible("Serie 3", "BMW Serie 3") is True   # containment


def test_sv_variant_code_from_url():
    assert _sv_variant_code("https://x/carros/anuncio/bmw-320-ver-d-auto-ID8Q0uI8.html") == "320"
    assert _sv_variant_code("https://x/carros/anuncio/bmw-116-ver-d-pack-ID8PYhxl.html") == "116"
    assert _sv_variant_code("https://x/carros/anuncio/renault-captur-IDabc.html") is None  # no 3-digit variant


def test_olx_label_parsing_fixes_fuel_and_power():
    # Regression: fuel used to bleed into the next label ("Diesel Potência") and
    # power was stored under the wrong field. Both must be clean now.
    text = ("Marca: BMW Ano: 2015 Quilómetros: 178 000 km "
            "Combustível: Diesel Potência: 218 cv Tipo de Caixa: Automática Cor: Preto")
    r = {}
    _extract_pt_label_values(text, r)
    assert r["fuel_type"] == "Diesel"
    assert r["engine_power_hp"] == 218
    assert r["year"] == 2015
    assert r["km"] == 178000
    assert r["transmission"] == "Automática"


def test_fuel_normalisers():
    assert _norm_fuel("Gasóleo") == "Diesel"
    assert _norm_fuel("Híbrido Plug-in") == "Híbrido (Plug-in)"
    assert _norm_transmission("Automática") == "Automática"
    assert _sv_fuel_values("Diesel") == ["diesel"]
    assert _sv_fuel_values("Híbrido (Plug-in)") == ["plugin-hybrid"]
