"""Size and scope of the live market pool.

The comparison worked from 20 cards of one Standvirtual results page, and that
page was often not the search that was meant: the year filter was ignored by
the site, petrol and hybrid searches came back empty, a Volkswagen search
returned every car on the site, and 1 card in 20 carried a wrong price. The
search must ask for what the site understands, refuse a page the site did not
scope to the make and model, and read further result pages when there are more.
"""
import asyncio
import json
import re

import pytest

from app.scrapers import dispatcher, olx, standvirtual
from app.scrapers.standvirtual import (
    _build_search_url,
    _parse_search_page,
    _search_is_scoped,
    _sv_fuel_values,
)
from app.services import ad_analysis_service as svc

SCOPED = ["category_id", "filter_enum_make", "filter_enum_model"]


def _edge(n, price=15000, year=2019, km=90000, seller="ProfessionalSeller"):
    return {"node": {
        "url": f"https://www.standvirtual.com/carros/anuncio/renault-clio-ID{n}.html",
        "title": f"Renault Clio 1.0 TCe Intens {n}",
        "shortDescription": "",
        "price": {"amount": {"units": price, "currencyCode": "EUR"}},
        "parameters": [
            {"key": "fuel_type", "value": "gaz", "displayValue": "Gasolina"},
            {"key": "mileage", "value": str(km), "displayValue": f"{km} km"},
            {"key": "first_registration_year", "value": str(year), "displayValue": str(year)},
        ],
        "seller": {"__typename": seller},
        "location": {"city": {"name": "Lisboa"}},
    }}


def _page(edges, total, applied=SCOPED, page_size=32):
    search = {"totalCount": total, "pageInfo": {"pageSize": page_size, "currentOffset": 0},
              "appliedFilters": [{"name": name, "value": "x"} for name in applied],
              "edges": edges}
    next_data = {"props": {"pageProps": {"urqlState": {
        "-1": {"data": json.dumps({"filters": {}})},
        "-2": {"data": json.dumps({"advertSearch": search})},
    }}}}
    return ('<html><body><script id="__NEXT_DATA__" type="application/json">'
            + json.dumps(next_data) + "</script></body></html>")


class _Response:
    def __init__(self, text):
        self.text = text

    def raise_for_status(self):
        pass


def _serve(monkeypatch, pages, delays=None):
    """Answer Standvirtual requests from `pages` ({page number: html or an
    exception to raise}); returns the list of requested URLs."""
    requested = []

    class Client:
        def __init__(self, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *exc):
            return False

        async def get(self, url):
            requested.append(url)
            m = re.search(r"[?&]page=(\d+)", url)
            page = int(m.group(1)) if m else 1
            if delays and page in delays:
                await asyncio.sleep(delays[page])
            if isinstance(pages[page], Exception):
                raise pages[page]
            return _Response(pages[page])

    monkeypatch.setattr(standvirtual.httpx, "AsyncClient", Client)
    monkeypatch.setattr(standvirtual.random, "uniform", lambda a, b: 0)
    monkeypatch.setattr(standvirtual, "_PAGE_GAP_SECONDS", 0)
    return requested


def _fetch(max_pages=4, max_results=160):
    return asyncio.run(standvirtual.fetch_listings(
        "Renault", "Clio", None, max_results, 2017, 2021, "Gasolina", None, max_pages))


def _ids(listings):
    return [int(re.search(r"ID(\d+)", l["source_url"]).group(1)) for l in listings]


# ── What the search asks for ─────────────────────────────────────────────────

def test_search_url_uses_the_filters_the_site_applies():
    url = _build_search_url("Renault", "Clio", None, 2017, 2021, "Gasolina")
    assert url.startswith("https://www.standvirtual.com/carros/renault/clio?")
    # "filter_float_year" is echoed back by the site but filters nothing.
    assert "search[filter_float_first_registration_year:from]=2017" in url
    assert "search[filter_float_first_registration_year:to]=2021" in url
    assert "filter_float_year" not in url
    assert "search[filter_enum_fuel_type][0]=gaz" in url
    assert "search[order]" not in url          # the site's default order
    assert "page=" not in url
    assert _build_search_url("Renault", "Clio", None, 2017, 2021, "Gasolina", None, 3).endswith("&page=3")
    assert _build_search_url("Renault", "Clio", page=2).endswith("/clio?page=2")


def test_volkswagen_is_searched_under_the_sites_make_id():
    assert _build_search_url("Volkswagen", "Golf").endswith("/carros/vw/golf")


@pytest.mark.parametrize("fuel, values", [
    ("Gasolina", ["gaz"]),                       # "petrol" returned no results at all
    ("Diesel", ["diesel"]),
    ("Gasóleo", ["diesel"]),
    ("Elétrico", ["electric"]),
    ("Híbrido (Gasolina)", ["hibride-gaz"]),     # "hybrid" returned no results at all
    ("Híbrido (Diesel)", ["hibride-diesel"]),
    ("Híbrido", ["hibride-gaz", "hibride-diesel"]),
    ("Híbrido Plug-In", ["plugin-hybrid"]),
    ("Híbrido (Plug-in)", ["plugin-hybrid"]),
    ("GPL", ["gpl"]),
    ("Hidrogénio", []),
    (None, []),
])
def test_fuel_names_map_to_the_sites_filter_values(fuel, values):
    assert _sv_fuel_values(fuel) == values


def test_a_fuel_with_two_filter_values_asks_for_both():
    url = _build_search_url("Toyota", "Yaris", fuel_type="Híbrido")
    assert "search[filter_enum_fuel_type][0]=hibride-gaz" in url
    assert "search[filter_enum_fuel_type][1]=hibride-diesel" in url


# ── Reading one results page ─────────────────────────────────────────────────

def test_listings_are_read_from_the_search_data():
    listings, meta = _parse_search_page(
        _page([_edge(1, price=12799, year=2020, km=64108), _edge(2, seller="PrivateSeller")], total=272), "u")
    assert meta["total"] == 272 and meta["page_size"] == 32
    first = listings[0]
    assert first["source"] == "standvirtual"
    assert first["source_url"].endswith("renault-clio-ID1.html")
    assert (first["price"], first["year"], first["km"]) == (12799, 2020, 64108)
    assert first["fuel_type"] == "Gasolina"
    assert first["title"] == "Renault Clio 1.0 TCe Intens 1"
    assert [l["seller_type"] for l in listings] == ["stand", "privado"]


def test_a_price_in_another_currency_is_not_taken_as_euros():
    edge = _edge(1)
    edge["node"]["price"]["amount"]["currencyCode"] = "PLN"
    listings, _ = _parse_search_page(_page([edge], total=1), "u")
    assert listings[0]["price"] is None


def test_page_without_search_data_falls_back_to_the_cards():
    html = """<html><body><article data-id="1">
        <a href="/carros/anuncio/renault-clio-ID9.html"><h2>Renault Clio 1.0 TCe</h2></a>
        <span class="price">12 500 EUR</span><dl><dd>2019</dd><dd>80 000 km</dd><dd>Gasolina</dd></dl>
        </article></body></html>"""
    listings, meta = _parse_search_page(html, "u")
    assert meta is None
    assert [(l["price"], l["year"], l["km"]) for l in listings] == [(12500, 2019, 80000)]


def test_search_is_scoped_only_when_make_and_model_were_applied():
    assert _search_is_scoped({"applied": set(SCOPED)})
    # "/carros/mercedes-benz/classe-a": the make is applied, the model is not.
    assert not _search_is_scoped({"applied": {"category_id", "filter_enum_make", "filter_enum_fuel_type"}})
    # "/carros/volkswagen/golf": neither.
    assert not _search_is_scoped({"applied": {"category_id", "filter_enum_fuel_type"}})


# ── Reading several pages ────────────────────────────────────────────────────

def test_further_pages_are_fetched_up_to_what_the_search_holds(monkeypatch):
    pages = {1: _page([_edge(n) for n in range(0, 32)], total=70),
             2: _page([_edge(n) for n in range(32, 64)], total=70),
             3: _page([_edge(n) for n in range(64, 70)], total=70)}
    requested = _serve(monkeypatch, pages)
    listings = _fetch(max_pages=4)
    assert _ids(listings) == list(range(70))          # page order kept
    assert len(requested) == 3                        # 70 results are 3 pages, not 4
    assert sorted(int(re.search(r"page=(\d+)", u).group(1)) for u in requested[1:]) == [2, 3]
    assert all("filter_float_first_registration_year:from]=2017" in u for u in requested)


def test_no_more_pages_than_the_cap(monkeypatch):
    pages = {p: _page([_edge(p * 100 + n) for n in range(32)], total=5000) for p in range(1, 10)}
    requested = _serve(monkeypatch, pages)
    listings = _fetch(max_pages=4)
    assert len(requested) == 4
    assert len(listings) == 128


def test_single_page_search_makes_one_request(monkeypatch):
    requested = _serve(monkeypatch, {1: _page([_edge(n) for n in range(18)], total=18)})
    assert len(_fetch(max_pages=4)) == 18
    assert len(requested) == 1


def test_one_page_is_read_unless_more_are_asked_for(monkeypatch):
    pages = {p: _page([_edge(p * 100 + n) for n in range(32)], total=500) for p in range(1, 5)}
    requested = _serve(monkeypatch, pages)
    listings = asyncio.run(standvirtual.fetch_listings("Renault", "Clio", max_results=60))
    assert len(requested) == 1 and len(listings) == 32


def test_a_listing_seen_on_two_pages_is_counted_once(monkeypatch):
    pages = {1: _page([_edge(n) for n in range(0, 32)], total=60),
             2: _page([_edge(n) for n in range(28, 60)], total=60)}   # 28–31 moved down a page
    _serve(monkeypatch, pages)
    assert _ids(_fetch()) == list(range(60))


def test_a_failed_page_is_skipped_not_fatal(monkeypatch):
    pages = {1: _page([_edge(n) for n in range(0, 32)], total=96),
             2: RuntimeError("503"),
             3: _page([_edge(n) for n in range(64, 96)], total=96)}
    _serve(monkeypatch, pages)
    assert _ids(_fetch()) == list(range(0, 32)) + list(range(64, 96))


def test_a_page_that_is_late_is_left_out(monkeypatch):
    pages = {1: _page([_edge(n) for n in range(0, 32)], total=96),
             2: _page([_edge(n) for n in range(32, 64)], total=96),
             3: _page([_edge(n) for n in range(64, 96)], total=96)}
    _serve(monkeypatch, pages, delays={3: 5})
    monkeypatch.setattr(standvirtual, "_MORE_PAGES_BUDGET_SECONDS", 0.2)
    assert _ids(_fetch()) == list(range(0, 64))


def test_unscoped_search_returns_nothing_and_reads_no_further(monkeypatch):
    """The site dropped the model (or the make): the page is priced listings of
    other cars. 17 626 diesel cars must not become a Golf's comparables."""
    applied = ["category_id", "filter_enum_fuel_type"]
    pages = {p: _page([_edge(p * 100 + n) for n in range(32)], total=17626, applied=applied)
             for p in range(1, 5)}
    requested = _serve(monkeypatch, pages)
    assert _fetch(max_pages=4) == []
    assert len(requested) == 1


def test_empty_search_returns_nothing(monkeypatch):
    requested = _serve(monkeypatch, {1: _page([], total=0)})
    assert _fetch() == []
    assert len(requested) == 1


# ── Dispatcher and the analysis ──────────────────────────────────────────────

def test_dispatcher_passes_the_page_cap_to_standvirtual_only(monkeypatch):
    seen = {}

    async def sv(*args):
        seen["sv"] = args
        return [{"source_url": "https://sv/1", "price": 10000}]

    async def ox(*args):
        seen["olx"] = args
        return [{"source_url": "https://olx/1", "price": 11000}]

    monkeypatch.setattr(standvirtual, "fetch_listings", sv)
    monkeypatch.setattr(olx, "fetch_listings", ox)
    merged = asyncio.run(dispatcher.fetch_listings_all_sources(
        "Renault", "Clio", max_per_source=160, year_from=2017, year_to=2021,
        fuel_type="Gasolina", max_pages=4))
    assert len(merged) == 2
    assert seen["sv"] == ("Renault", "Clio", None, 160, 2017, 2021, "Gasolina", None, 4, None)
    assert seen["olx"] == ("Renault", "Clio", None, 160, 2017, 2021, "Gasolina")


def _listing(n, title, price=15000, year=2019, km=90000):
    return {"year": year, "km": km, "price": price, "fuel_type": "Gasolina", "title": title,
            "source_url": f"https://x/carros/anuncio/renault-clio-ID{n}.html"}


def _market(monkeypatch, listings, engine_hint=None, asked=None):
    async def fake_fetch(**kwargs):
        if asked is not None:
            asked.update(kwargs)
        return listings

    monkeypatch.setattr(dispatcher, "fetch_listings_all_sources", fake_fetch)
    monkeypatch.setattr(svc, "_market_cache", {})
    return asyncio.run(svc._fetch_live_market_data(
        "Renault", "Clio", 2019, fuel_type="Gasolina", engine_hint=engine_hint,
        gen_year_start=2019, gen_year_end=None))


def test_market_comparison_asks_for_several_pages(monkeypatch):
    asked = {}
    _market(monkeypatch, [_listing(n, "Renault Clio 1.0 TCe") for n in range(6)], asked=asked)
    assert asked["max_pages"] == svc._MARKET_MAX_PAGES == 4
    assert asked["max_per_source"] >= 4 * 32


def test_whole_fetched_pool_is_compared(monkeypatch):
    listings = [_listing(n, "Renault Clio 1.0 TCe", price=12000 + 10 * n) for n in range(120)]
    assert _market(monkeypatch, listings)["sample_count"] == 120


def test_engine_hint_cut_applies_from_three_matches(monkeypatch):
    """Kept on purpose: with 3–4 listings of the car's engine the price verdict
    is withheld (fewer than _MIN_RELIABLE_MARKET_SAMPLE) rather than computed
    against the other engines."""
    others = [_listing(n, "Renault Clio 1.0 TCe", price=13000) for n in range(20)]
    same = [_listing(100 + n, "Renault Clio 1.3 TCe RS Line", price=19000) for n in range(3)]
    stats = _market(monkeypatch, others + same, engine_hint="1.3 TCe")
    assert stats["sample_count"] == 3
    assert stats["sample_count"] < svc._MIN_RELIABLE_MARKET_SAMPLE
    assert stats["median_price"] == 19000


def test_engine_hint_matching_fewer_than_three_keeps_the_pool(monkeypatch):
    others = [_listing(n, "Renault Clio 1.0 TCe", price=13000) for n in range(20)]
    same = [_listing(100 + n, "Renault Clio 1.3 TCe RS Line", price=19000) for n in range(2)]
    assert _market(monkeypatch, others + same, engine_hint="1.3 TCe")["sample_count"] == 22


def test_combined_make_model_filter_of_november_2026_is_scoped():
    # The site now applies make and model as one filter: "byd|atto-3".
    from app.scrapers.standvirtual import applied_make_model
    meta = {"applied": {"category_id", "make_model_engine_code"},
            "applied_values": {"category_id": "29", "make_model_engine_code": "byd|atto-3"}}
    assert applied_make_model(meta) == ("byd", "atto-3")
    assert _search_is_scoped(meta)
    # A slug the site did not know keeps only the make: never comparables
    make_only = {"applied": {"category_id", "make_model_engine_code"},
                 "applied_values": {"make_model_engine_code": "volkswagen"}}
    assert applied_make_model(make_only) == ("volkswagen", None)
    assert not _search_is_scoped(make_only)
    # A sub-model searched with its series (live 2026-11-17, 463 results)
    sub_model = {"applied": {"category_id", "make_model_engine_code"},
                 "applied_values": {"make_model_engine_code": "bmw|serie-3|320"}}
    assert applied_make_model(sub_model) == ("bmw", "serie-3")
    assert _search_is_scoped(sub_model)
