"""Market snapshot: site model -> catalogue model, what a price may use, and
the stored-pool fallback of the ad analysis. No network, no database."""
import pytest

from app.services import ad_analysis_service as svc
from app.services.market_snapshot import (
    build_assigner, is_plausible, listing_from_node, observation_rows,
)


def _cat():
    rows = [
        ("Audi", "A3", "compacto"), ("Audi", "TT", "compacto"),
        ("BMW", "Série 3", "berlina"), ("BMW", "Série 2 Active Tourer", "mpv"),
        ("BMW", "Série 2 Gran Coupé", "compacto"), ("BMW", "X1", "suv"), ("BMW", "530", None),
        ("Mercedes-Benz", "Classe E", "berlina"), ("Mercedes-Benz", "E Coupé", "compacto"),
        ("Lexus", "NX", "suv"),
        ("Skoda", "Superb", "berlina"), ("Skoda", "Superb Combi", "carrinha"),
        ("MG", "ZS EV", "suv"), ("MINI", "Cooper", "citadino"),
        ("Hyundai", "Kona", "suv"), ("Volkswagen", "Golf", "compacto"),
        ("Citroën", "C3", "citadino"), ("Renault", "Mégane", "compacto"),
    ]
    return [{"id": i + 1, "brand_name": b, "model_name": m, "body_type": body}
            for i, (b, m, body) in enumerate(rows)]


@pytest.fixture(scope="module")
def assign():
    return build_assigner(_cat())


def _name(assign, make, site_id, title="", powertrain=""):
    hit = assign(make, site_id, title, powertrain)
    return hit["model_name"] if hit else None


@pytest.mark.parametrize("make, site_id, expected", [
    ("audi", "a3", "A3"),
    ("audi", "a3-sportback", "A3"),              # body variants are the same model
    ("audi", "a3-limousine", "A3"),
    ("vw", "golf-variant", "Golf"),
    ("renault", "megane-sport-tourer", "Mégane"),
    ("citroen", "c3", "C3"),
    ("citroen", "c3-aircross", None),            # another car
    ("bmw", "320", "Série 3"),                   # sub-model -> its series
    ("bmw", "530", None),                        # Série 5 is not in this catalogue; never the stub
    ("bmw", "218-active-tourer", "Série 2 Active Tourer"),
    ("bmw", "218-gran-coupe", "Série 2 Gran Coupé"),
    ("bmw", "218", None),                        # the 2-series coupé: neither
    ("bmw", "x1", "X1"),
    ("lexus", "nx-350h", "NX"),                  # falls back to the series
    ("skoda", "superb", "Superb"),
    ("skoda", "superb-break", "Superb Combi"),   # the alias beats the base model
    ("hyundai", "kauai", "Kona"),                # sold in Portugal as the Kauai
    ("mini", "mini-3p", "Cooper"),
    ("mini", "mini-5p", "Cooper"),
    ("tesla", "model-3", None),                  # make not in the catalogue
])
def test_site_model_to_catalogue_model(assign, make, site_id, expected):
    assert _name(assign, make, site_id) == expected


def test_mercedes_coupe_is_told_by_the_title(assign):
    assert _name(assign, "mercedes-benz", "e-220", "Mercedes-Benz E 220 d Avantgarde") == "Classe E"
    assert _name(assign, "mercedes-benz", "e-220", "Mercedes-Benz E 220 d Coupé AMG Line") == "E Coupé"


def test_electric_only_catalogue_model_takes_only_electric_listings(assign):
    assert _name(assign, "mg", "zs", "MG ZS EV Luxury", "electric") == "ZS EV"
    assert _name(assign, "mg", "zs", "MG ZS 1.5 VTi-Tech", "gaz") is None


def test_convertibles_are_flagged(assign):
    assert assign("audi", "a3-cabrio", "Audi A3 Cabrio 1.4 TFSI")["convertible"] is True
    assert assign("audi", "tt-roadster", "Audi TT Roadster")["convertible"] is True
    assert assign("audi", "a3-sportback", "Audi A3 Sportback 30 TFSI")["convertible"] is False
    assert assign("mercedes-benz", "e-220", "Mercedes-Benz E 220 d Cabrio")["convertible"] is True


def _node(**over):
    params = {"make": ("vw", "VW"), "model": ("golf", "Golf"),
              "version": ("ver-1-5-tsi", "1.5 TSI Life"), "fuel_type": ("gaz", "Gasolina"),
              "gearbox": ("manual", "Manual"), "mileage": ("89250", "89 250 km"),
              "engine_capacity": ("1498", "1 498 cm3"), "engine_power": ("130", "130 cv"),
              "first_registration_year": ("2020", "2020"), "origin": ("national", "Nacional")}
    node = {
        "id": "8097", "url": "https://www.standvirtual.com/carros/anuncio/vw-golf-ID8Q0ImG.html",
        "title": "VW Golf 1.5 TSI Life", "createdAt": "2026-11-11T13:25:15Z",
        "price": {"amount": {"units": 18900, "currencyCode": "EUR"}},
        "seller": {"__typename": "ProfessionalSeller", "name": "Stand X"},
        "parameters": [{"key": k, "value": v, "displayValue": d} for k, (v, d) in params.items()],
    }
    node.update(over)
    return node


def test_listing_from_node_keeps_the_car_and_nothing_about_the_seller():
    rec = listing_from_node(_node())
    assert rec["price"] == 18900 and rec["year"] == 2020 and rec["km"] == 89250
    assert rec["cc"] == 1498 and rec["hp"] == 130 and rec["gearbox"] == "manual"
    assert rec["sv_model"] == "golf" and rec["powertrain"] == "gaz" and rec["origin"] == "national"
    assert rec["version"] == "1.5 TSI Life" and rec["seller_type"] == "stand"
    assert "Stand X" not in str(rec)


def test_listing_from_node_needs_a_url_and_a_euro_price():
    assert listing_from_node(_node(url="")) is None
    assert listing_from_node(_node(price={"amount": {"units": 18900, "currencyCode": "USD"}})) is None
    assert listing_from_node(_node(price=None)) is None


@pytest.mark.parametrize("rec, ok", [
    ({"price": 18900, "year": 2020, "km": 89000}, True),
    ({"price": 1000, "year": 2020, "km": 89000}, False),      # "preço sob consulta"
    ({"price": 750000, "year": 2020, "km": 89000}, False),
    ({"price": 18900, "year": None, "km": 89000}, False),
    ({"price": 18900, "year": 2020, "km": None}, False),
    ({"price": 18900, "year": 2015, "km": 0}, False),         # a used car showing 0 km
    ({"price": 18900, "year": 2026, "km": 0}, True),          # a new one may
    ({"price": 18900, "year": 2020, "km": 900000}, False),
])
def test_is_plausible(rec, ok):
    assert is_plausible(rec, this_year=2026) is ok


def test_observation_rows_pick_the_generation_and_skip_what_cannot_price():
    gens = [
        {"id": 1, "model_id": 10, "year_start": 2012, "year_end": 2019, "fuel_type": None},
        {"id": 2, "model_id": 10, "year_start": 2020, "year_end": None, "fuel_type": None},
        {"id": 3, "model_id": 10, "year_start": 2020, "year_end": None, "fuel_type": "eletrico"},
    ]
    base = {"model_id": 10, "convertible": False, "price": 15000, "km": 90000,
            "powertrain": "diesel", "seller_type": "stand", "sv_model": "golf",
            "version": "1.6 TDI", "hp": 115, "cc": 1598, "gearbox": "manual",
            "origin": "national", "listed_at": None, "read_at": "2026-11-13T20:00:00+00:00"}
    recs = [
        {**base, "url": "u1", "year": 2017},
        {**base, "url": "u2", "year": 2021},
        {**base, "url": "u3", "year": 2021, "powertrain": "electric"},
        {**base, "url": "u4", "year": 2005},                      # before any generation
        {**base, "url": "u5", "year": 2017, "model_id": None},    # not in the catalogue
        {**base, "url": "u6", "year": 2017, "convertible": True},
        {**base, "url": "u7", "year": 2017, "price": 1},
        {**base, "url": "u1", "year": 2017},                      # the same listing twice
    ]
    rows, counts = observation_rows(recs, gens)
    by_url = {r["source_url"]: r for r in rows}
    assert set(by_url) == {"u1", "u2", "u3", "u4"}
    assert by_url["u1"]["generation_id"] == 1
    assert by_url["u2"]["generation_id"] == 2            # not the electric-only generation
    assert by_url["u3"]["generation_id"] == 3 and by_url["u3"]["fuel_type"] == "eletrico"
    assert by_url["u4"]["generation_id"] is None
    assert by_url["u1"]["fuel_type"] == "diesel" and by_url["u1"]["engine_power_hp"] == 115
    assert counts["not_in_catalogue"] == 1 and counts["convertible"] == 1
    assert counts["implausible"] == 2 and counts["no_generation"] == 1 and counts["rows"] == 4


# ── the ad analysis' fallback on stored listings ─────────────────────────────

class _Result:
    def __init__(self, rows):
        self._rows = rows

    def fetchall(self):
        return self._rows

    def mappings(self):
        return self._rows


class _FakeDb:
    def __init__(self, rows):
        self.rows, self.sql, self.params = rows, "", {}

    def execute(self, statement, params=None):
        self.sql, self.params = str(statement), params or {}
        return _Result(self.rows)

    def rollback(self):
        pass


def _stored(db, **over):
    args = dict(model_id=26, brand_name="Volkswagen", model_name="Golf", year=2018,
                fuel_type="Diesel", gen_year_start=2012, gen_year_end=2019,
                km=120000, power_hp=115)
    args.update(over)
    return svc._stored_market_data(db, **args)


def test_stored_pool_is_scoped_like_the_live_comparison():
    rows = [(14000 + 200 * i, 100000 + 4000 * i, 2017 + i % 3, 12.4) for i in range(12)]
    db = _FakeDb(rows)
    stats = _stored(db)
    assert stats["source"] == "snapshot" and stats["age_days"] == 12
    assert stats["sample_count"] >= 3 and stats["median_price"]
    assert db.params["year_from"] == 2012 and db.params["year_to"] == 2019
    assert db.params["powertrains"] == ["diesel"]
    assert (db.params["p_from"], db.params["p_to"]) == svc._power_range(115)
    assert "extraction_method = 'search_snapshot'" in db.sql
    assert stats["power_comparison"]["car_power_hp"] == 115
    assert "variants" not in db.params                      # no site model known: every body variant


def test_stored_pool_keeps_to_the_listings_own_body_variant():
    rows = [(14000 + 200 * i, 100000 + 4000 * i, 2017 + i % 3, 2.0) for i in range(12)]
    db = _FakeDb(rows)
    assert _stored(db, sv_model_slug="golf-variant")
    assert db.params["variants"] == ["golf-variant"] and "p_from" in db.params
    assert _stored(db, model_name="Cooper", brand_name="MINI", sv_model_slug="mini-3p--mini-5p")
    assert db.params["variants"] == ["mini-3p", "mini-5p"]


def test_stored_pool_needs_three_listings():
    assert _stored(_FakeDb([(14000, 100000, 2018, 3.0)] * 2)) == {}


def test_stored_pool_without_power_uses_the_site_variant_or_nothing():
    rows = [(30000 + 300 * i, 90000, 2018, 5.0) for i in range(6)]
    db = _FakeDb(rows)
    # a series whose sub-model is unknown is not compared
    assert _stored(db, model_id=101, brand_name="BMW", model_name="Série 3",
                   power_hp=None, sv_model_slug=None) == {}
    # with the sub-model it is, within that sub-model
    stats = _stored(db, model_id=101, brand_name="BMW", model_name="Série 3",
                    power_hp=None, sv_model_slug="320")
    assert stats and db.params["variants"] == ["320"] and "p_from" not in db.params
    # a MINI hatch needs its trim, which stored listings do not carry
    assert _stored(db, model_id=5, brand_name="MINI", model_name="Cooper",
                   power_hp=None, sv_model_slug="mini-3p") == {}


def test_catalogue_model_id_ignores_accents_on_both_sides():
    rows = [{"id": 101, "brand_name": "BMW", "model_name": "Série 3"},
            {"id": 3, "brand_name": "Citroën", "model_name": "C3"},
            {"id": 28, "brand_name": "Renault", "model_name": "Mégane"}]
    db = _FakeDb(rows)
    assert svc._catalogue_model_id(db, "BMW", "Série 3") == 101
    assert svc._catalogue_model_id(db, "bmw", "Serie 3") == 101
    assert svc._catalogue_model_id(db, "Citroen", "C3") == 3
    assert svc._catalogue_model_id(db, "Renault", "MEGANE") == 28
    assert svc._catalogue_model_id(db, "Renault", "Clio") is None
    assert svc._catalogue_model_id(db, "", "C3") is None


def test_reassign_works_out_the_model_again_for_this_catalogue():
    from app.services.market_snapshot import reassign
    recs = [{"make": "audi", "sv_model": "a3-sportback", "title": "Audi A3 Sportback", "powertrain": "gaz",
             "model_id": 999, "convertible": True, "url": "u1"},
            {"make": "peugeot", "sv_model": "e-208", "title": "Peugeot e-208", "powertrain": "electric",
             "model_id": None, "url": "u2"},
            {"make": "hyundai", "sv_model": "kauai", "title": "Hyundai Kauai", "powertrain": "gaz",
             "model_id": 5, "url": "u3"}]
    cat = _cat() + [{"id": 77, "brand_name": "Peugeot", "model_name": "208", "body_type": "citadino"}]
    out = reassign(recs, cat)
    ids = {c["model_name"]: c["id"] for c in cat}
    assert out[0]["model_id"] == ids["A3"] and out[0]["convertible"] is False   # the file's id is not trusted
    assert out[1]["model_id"] == 77                                             # the electric 208
    assert out[2]["model_id"] == ids["Kona"]
    assert recs[0]["model_id"] == 999                                           # the input is not changed
