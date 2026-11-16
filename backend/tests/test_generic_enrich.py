"""Dealer sites keep fuel, power and version in the title, heading or address;
the generic reader fills those gaps without overwriting structured data."""
from bs4 import BeautifulSoup

from app.scrapers.generic import _detect_fuel, _enrich_from_title_and_url


def _run(result, html="<html><body></body></html>", url="https://dealer.example/carros/x"):
    _enrich_from_title_and_url(result, BeautifulSoup(html, "lxml"), url)
    return result


def test_fills_fuel_power_version_from_title():
    r = _run({"title": "Peugeot 3008 GT 1.5 BlueHdi 130cv EAT8", "brand": "Peugeot", "model": "3008"})
    assert "fuel_type" not in r          # "BlueHdi" alone is not a fuel word: left for other layers
    assert r["engine_power_hp"] == 130
    assert r["version"] == "GT 1.5 BlueHdi 130cv EAT8"


def test_reads_the_address_when_the_page_says_little():
    url = "https://benecar.pt/carros/Peugeot/3008/gt-15-bluehdi-eat8-diesel-2020-156598"
    r = _run({"title": "", "brand": "", "model": ""}, url=url)
    assert r["brand"] == "Peugeot" and r["model"] == "3008"
    assert r["fuel_type"] == "diesel"
    assert "1.5" in r["version"] and "2020" not in r["version"] and "156598" not in r["version"]


def test_brand_from_the_address_abarth():
    r = _run({"title": "500 1.4 16v T-JET 145CV 595", "brand": "", "model": ""},
             url="https://www.carplus.pt/carros-usados/abarth/500-14-16v-a00742/")
    assert r["brand"] == "Abarth"
    assert r["engine_power_hp"] == 145


def test_never_overwrites_structured_fields():
    r = _run({"title": "Fiat 500L 1.3 Multijet 95cv", "brand": "Fiat", "model": "500L",
              "fuel_type": "gasolina", "engine_power_hp": 99})
    assert r["fuel_type"] == "gasolina" and r["engine_power_hp"] == 99


def test_full_title_version_loses_brand_and_model():
    r = _run({"title": "x", "brand": "Abarth", "model": "500", "version": "Abarth 500 1.4 16v T-JET 145CV 595"})
    assert r["version"] == "1.4 16v T-JET 145CV 595"


def test_hybrid_words_only_as_words():
    assert _detect_fuel("Chevrolet Aveo 1.2 LS") is None
    assert _detect_fuel("Toyota C-HR 1.8 HEV") == "híbrido"
    assert _detect_fuel("Ford Kuga 2.5 PHEV") == "híbrido plug-in"
    assert _detect_fuel("Vidros elétricos, jantes") is None
