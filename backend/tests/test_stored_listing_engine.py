"""Engine facts of a listing read back from the database.

A listing analysed before is not scraped again: its row is read back. The row
has no column for the engine power, version, displacement or gearbox; they are
saved in the analysis blob (`_listing_engine`). Read back without them, the car
was compared across every engine of its model. They now come back with the row.

So does the row's id: the analysis redone from a stored listing is saved on that
row, as the analysis of a fresh scrape is. It used to be thrown away.
"""
import asyncio
import json

import pytest

from app.services import ad_analysis_service as svc
from app.services.ad_analysis_service import _power_range, _resolve_model_from_url, _with_stored_engine

URL = "https://www.standvirtual.com/carros/anuncio/vw-golf-1-6-tdi-ID8PabCd.html"

ENGINE = {"version": "1.6 TDI Confortline", "engine_displacement_cc": 1598, "engine_power_hp": 115,
          "transmission": "Manual", "fuel_type": "Diesel"}


def _row(**over):
    row = {"id": 42, "model_id": 7, "brand_name": "Volkswagen", "model_name": "Golf", "year": 2017, "km": 120000,
           "price": 14500, "km_per_year": 13000, "price_delta": 0.0, "deal_tier": "razoavel",
           "deal_score": 0.5, "seller_type": "profissional", "description": "Golf 1.6 TDI",
           "photo_count": 12, "fuel_type": "Diesel", "source_url": URL,
           "llm_analysis": {"verdict": "razoavel", "_listing_engine": dict(ENGINE)}}
    row.update(over)
    return row


class _Db:
    """Stands in for the session: one stored listing, or none."""

    def __init__(self, row):
        self.row, self.sql, self.params = row, [], []

    def execute(self, sql, params=None):
        self.sql.append(str(sql))
        self.params.append(params)
        return self

    def mappings(self):
        return self

    def fetchone(self):
        return self.row


def test_stored_listing_comes_back_with_its_engine():
    listing = _with_stored_engine(_row())
    assert listing["engine_power_hp"] == 115
    assert listing["version"] == "1.6 TDI Confortline"
    assert listing["engine_displacement_cc"] == 1598
    assert listing["transmission"] == "Manual"
    assert _power_range(listing["engine_power_hp"]) == (97, 133)
    # The blob itself is not part of the listing.
    assert "llm_analysis" not in listing
    assert listing["price"] == 14500 and listing["source_url"] == URL


def test_blob_stored_as_text_is_read_too():
    listing = _with_stored_engine(_row(llm_analysis=json.dumps({"_listing_engine": ENGINE})))
    assert listing["engine_power_hp"] == 115


@pytest.mark.parametrize("blob", [
    None,                                   # never analysed
    {},                                     # analysed, nothing saved
    {"verdict": "bom"},                     # analysed before the engine was saved
    {"_listing_engine": None},
    {"_listing_engine": "115 cv"},          # not the shape saved
    {"_listing_engine": {k: None for k in ENGINE}},
    "not json",
    "[1, 2]",
    ["_listing_engine"],
])
def test_listing_without_saved_engine_comes_back_as_it_is(blob):
    listing = _with_stored_engine(_row(llm_analysis=blob))
    assert listing.get("engine_power_hp") is None
    assert _power_range(listing.get("engine_power_hp")) is None
    assert "llm_analysis" not in listing
    assert listing["fuel_type"] == "Diesel" and listing["year"] == 2017


def test_row_without_the_blob_column_is_left_alone():
    row = _row()
    del row["llm_analysis"]
    assert _with_stored_engine(row) == row


def test_the_rows_own_fuel_is_not_overridden():
    blob = {"_listing_engine": {**ENGINE, "fuel_type": "Gasolina"}}
    assert _with_stored_engine(_row(llm_analysis=blob))["fuel_type"] == "Diesel"
    # ... and is filled in when the row has none.
    assert _with_stored_engine(_row(fuel_type=None, llm_analysis=blob))["fuel_type"] == "Gasolina"


def test_the_row_is_not_changed_in_place():
    row = _row()
    _with_stored_engine(row)
    assert "llm_analysis" in row and "engine_power_hp" not in row


def test_read_back_asks_for_the_blob_and_returns_the_power():
    db = _Db(_row())
    listing = _resolve_model_from_url(db, URL)
    assert "n.llm_analysis" in db.sql[0]
    assert "n.id," in db.sql[0] and "ORDER BY n.id DESC" in db.sql[0]   # the row the cache check reads
    assert listing["id"] == 42
    assert db.params[0] == {"url": URL}
    assert listing["engine_power_hp"] == 115 and listing["model_id"] == 7


def test_read_back_of_an_unknown_listing_is_none():
    assert _resolve_model_from_url(_Db(None), URL) is None


class _Reached(BaseException):
    """Stops the analysis at the market comparison (not caught as an Exception)."""


def _market_call(monkeypatch, row):
    """What analyse_listing asks of the market comparison for a stored listing."""
    seen = {}

    async def market(brand, model, year, **kw):
        seen.update(kw, brand=brand, model=model, year=year)
        raise _Reached()

    async def no_scrape(db, url):
        raise AssertionError("a stored listing is not scraped again")

    monkeypatch.setattr(svc, "_get_cached_analysis", lambda db, url: None)   # analysis gone stale
    monkeypatch.setattr(svc, "_scrape_and_store_listing", no_scrape)
    monkeypatch.setattr(svc, "_get_generation_window", lambda *args, **kwargs: None)
    monkeypatch.setattr(svc, "_fetch_live_market_data", market)
    monkeypatch.setattr(svc, "DISABLE_LIVE_MARKET", False)
    with pytest.raises(_Reached):
        asyncio.run(svc.analyse_listing(_Db(row), URL))
    return seen


def test_stale_analysis_is_redone_within_the_cars_power_band(monkeypatch):
    seen = _market_call(monkeypatch, _row())
    assert (seen["brand"], seen["model"], seen["year"]) == ("Volkswagen", "Golf", 2017)
    assert seen["power_hp"] == 115
    assert seen["fuel_type"] == "Diesel" and seen["km"] == 120000


def test_stored_listing_without_a_saved_power_is_redone_as_before(monkeypatch):
    seen = _market_call(monkeypatch, _row(llm_analysis={"verdict": "bom"}))
    assert seen["power_hp"] is None


def test_stored_mini_gets_its_trim_from_the_saved_version(monkeypatch):
    # The catalogue calls every MINI hatch a "Cooper"; the version saved with
    # the analysis says which one this is.
    row = _row(brand_name="MINI", model_name="Cooper", fuel_type="Gasolina", description="",
               source_url="https://example.pt/viatura/12345",
               llm_analysis={"_listing_engine": {"version": "John Cooper Works", "engine_power_hp": 231}})
    seen = _market_call(monkeypatch, row)
    assert seen["power_hp"] == 231
    assert seen["trim"] == "jcw"


def _stored_analysis(monkeypatch, row, market=None):
    """What analyse_listing saves after redoing the analysis of a stored listing."""
    saved = {}

    async def no_market(*args, **kwargs):
        return dict(market or {})

    async def analysis(listing, model_info, market_stats, user_profile):
        return {"verdict": "razoavel", "summary": "redone"}

    async def no_scrape(db, url):
        raise AssertionError("a stored listing is not scraped again")

    def store(db, normalized_id, blob, deal_tier, deal_score):
        saved.update(id=normalized_id, blob=blob, tier=deal_tier, score=deal_score)
        raise _Reached()

    monkeypatch.setattr(svc, "_get_cached_analysis", lambda db, url: None)   # analysis gone stale
    monkeypatch.setattr(svc, "_scrape_and_store_listing", no_scrape)
    monkeypatch.setattr(svc, "_get_generation_window", lambda *args, **kwargs: None)
    monkeypatch.setattr(svc, "_fetch_live_market_data", no_market)
    monkeypatch.setattr(svc, "_stored_market_data", lambda *args, **kwargs: None)
    monkeypatch.setattr(svc, "_get_model_info", lambda *args, **kwargs: {})
    monkeypatch.setattr(svc, "_analyse", analysis)
    monkeypatch.setattr(svc, "_store_analysis", store)
    monkeypatch.setattr(svc, "DISABLE_LIVE_MARKET", False)
    with pytest.raises(_Reached):
        asyncio.run(svc.analyse_listing(_Db(row), URL))
    return saved


def test_redone_analysis_is_stored_on_the_listings_row(monkeypatch):
    saved = _stored_analysis(monkeypatch, _row())
    assert saved["id"] == 42
    assert saved["blob"]["summary"] == "redone"


def test_storing_the_redone_analysis_keeps_the_engine_facts(monkeypatch):
    # The new blob replaces the old one: what the old one knew of the engine
    # must be in it, or the next read-back and every cache hit would lose it.
    saved = _stored_analysis(monkeypatch, _row())
    assert saved["blob"]["_listing_engine"] == ENGINE


def test_redone_analysis_stores_the_reference_it_was_judged_against(monkeypatch):
    market = {"median_price": 14721, "avg_price": 14800, "sample_count": 58, "source": "live",
              "power_comparison": {"car_power_hp": 115, "power_from": 97, "power_to": 133, "pool_count": 60}}
    saved = _stored_analysis(monkeypatch, _row(), market)
    ref = saved["blob"]["_market_ref"]
    assert ref["median_price"] == 14721 and ref["sample_count"] == 58
    assert ref["power_comparison"]["power_from"] == 97


def test_listing_without_saved_engine_is_stored_too(monkeypatch):
    saved = _stored_analysis(monkeypatch, _row(llm_analysis={"verdict": "bom"}))
    assert saved["id"] == 42
    assert saved["blob"]["_listing_engine"]["engine_power_hp"] is None
    assert saved["blob"]["_listing_engine"]["fuel_type"] == "Diesel"
