"""The 'paste the ad' fallback: an analysis never depends on our server being allowed to fetch the page."""
import asyncio

import pytest

from app.scrapers import generic
from app.services import ad_analysis_service as svc

URL = "https://www.standvirtual.com/carros/anuncio/peugeot-208-1-2-puretech-active-ID8Qabcd.html"

PASTED = """Standvirtual
Peugeot 208 1.2 PureTech Active
12 990 €
Preço negociável
Detalhes
Ano 2019
Quilómetros 74 500 km
Combustível Gasolina
Potência 82 cv
Caixa de velocidades Manual
Vendedor Profissional
Carro bem estimado, revisões na marca."""


@pytest.fixture(autouse=True)
def no_llm(monkeypatch):
    async def none(*a, **k):
        return {}
    monkeypatch.setattr(generic, "_extract_via_llm", none)


def test_pasted_text_gives_the_listing_facts():
    got = asyncio.run(generic.extract_from_pasted_text(PASTED, URL))
    assert got["brand"] == "Peugeot" and got["model"].startswith("208")
    assert got["price"] == 12990
    assert got["year"] == 2019
    assert got["km"] == 74500
    assert (got["fuel_type"] or "").lower().startswith("gasolina")
    assert got["_extraction_method"] == "pasted"
    assert "revisões na marca" in got["description"]


def test_very_long_paste_is_cut():
    got = asyncio.run(generic.extract_from_pasted_text(PASTED + ("x " * 50_000), URL))
    assert len(got["description"]) <= 4000


class _Db:
    def execute(self, *a, **k):
        return self

    def mappings(self):
        return self

    def fetchone(self):
        return None

    def commit(self):
        pass

    def rollback(self):
        pass


def _analyse(monkeypatch, scraped, pasted=None):
    seen = {}

    async def scrape(db, url, refetch=False, pasted_text=None):
        seen["pasted_text"] = pasted_text
        return scraped

    monkeypatch.setattr(svc, "_get_cached_analysis", lambda db, url: None)
    monkeypatch.setattr(svc, "_resolve_model_from_url", lambda db, url: None)
    monkeypatch.setattr(svc, "_scrape_and_store_listing", scrape)
    return asyncio.run(svc.analyse_listing(_Db(), URL, pasted_text=pasted)), seen


def test_a_page_that_could_not_be_read_asks_for_the_text(monkeypatch):
    out, _ = _analyse(monkeypatch, {"brand_name": "Peugeot", "model_name": "208", "price": None})
    assert out["error_code"] == "fetch_failed"


def test_a_paste_without_a_price_says_so(monkeypatch):
    out, seen = _analyse(monkeypatch, {"brand_name": "Peugeot", "model_name": "208", "price": None}, pasted="texto")
    assert out["error_code"] == "paste_incomplete"
    assert seen["pasted_text"] == "texto"


def test_a_failed_fetch_has_its_code(monkeypatch):
    out, _ = _analyse(monkeypatch, None)
    assert out["error_code"] == "fetch_failed"
