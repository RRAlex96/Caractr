"""Scam/anomaly detection — the 'too good to be true' protection."""
from app.services.ad_analysis_service import _build_anomaly as anomaly


def test_implausibly_cheap_is_danger():
    r = anomaly({"price": 5000}, {"median_price": 15750}, [])
    assert r and r["level"] == "danger"


def test_notably_below_market_is_warning():
    r = anomaly({"price": 11000}, {"median_price": 18000}, [])  # ~0.61 ratio
    assert r and r["level"] == "warning"


def test_at_market_is_clean():
    assert anomaly({"price": 18000}, {"median_price": 18400}, []) is None


def test_validation_flag_forces_danger():
    r = anomaly({"price": 1500}, {"median_price": 2000}, ["new_car_too_cheap:2024,EUR1500"])
    assert r and r["level"] == "danger"


def test_km_year_mismatch_is_warning():
    r = anomaly({"price": 15000}, {"median_price": 15500}, ["km_vs_year_mismatch:km=400000,year=2021"])
    assert r and r["level"] == "warning"
