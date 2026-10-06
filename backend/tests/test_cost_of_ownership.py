"""Cost of ownership (fuel + IUC + maintenance) and the Portuguese IUC estimate."""
from app.services.ad_analysis_service import (
    _build_cost_of_ownership as tco,
    _estimate_iuc,
)


def test_diesel_with_model_and_depreciation():
    r = tco(
        {"fuel_type": "Diesel", "price": 18000, "year": 2018, "engine_power_hp": 190,
         "engine_displacement_cc": 1995},
        {"maintenance_cost_year": 900},
        {"annual_pct": 0.12},
        "2.0 TDI",
    )
    assert r is not None
    assert r["annual_fuel"] > 0
    assert r["annual_iuc"] and r["annual_iuc"] > 0          # displacement known -> IUC computed
    assert r["monthly_running"] > 0
    assert r["monthly_true"] > r["monthly_running"]          # true cost adds depreciation


def test_displacement_from_listing_feeds_iuc():
    # The captured engine_capacity (cc) should drive IUC even without an engine hint.
    r = tco({"fuel_type": "Gasolina", "price": 15000, "year": 2019, "engine_displacement_cc": 1498},
            None, None, None)
    assert r is not None and r["annual_iuc"] is not None


def test_thin_data_degrades_gracefully():
    r = tco({"fuel_type": "Gasolina", "price": 9000, "year": 2015, "description": ""}, None, None, None)
    assert r is not None
    assert r["annual_fuel"] > 0          # fuel still estimable
    assert r["monthly_true"] is None     # no depreciation -> no "true" figure


def test_iuc_estimate_rules():
    assert _estimate_iuc(None, "gasolina", 2020) is None                 # no displacement -> unknown
    assert _estimate_iuc(1600, "elétrico", 2022) == 0                    # EV exempt / nominal
    assert _estimate_iuc(1999, "diesel", 2018) > 0                       # a normal car has a real cost
    # a bigger engine costs more
    assert _estimate_iuc(2999, "diesel", 2018) > _estimate_iuc(1200, "diesel", 2018)
