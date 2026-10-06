"""Negotiation numbers: the concrete offer figures shown to the buyer."""
from app.services.ad_analysis_service import _build_negotiation_numbers as neg


def test_overpriced_old_private_gives_aggressive_opening():
    r = neg(
        {"price": 19000, "listing_age_days": 45, "seller_type": "particular", "km": 160000, "year": 2017},
        {"median_price": 17000, "sample_count": 24},
    )
    assert r is not None
    assert r["opening_offer"] < r["fair_value"] <= r["walk_away"]
    assert r["potential_saving"] > 0
    assert r["confidence"] == "alta"
    assert any("dias" in l.lower() for l in r["leverage"])  # listing-age leverage surfaced


def test_fair_price_small_margin():
    r = neg(
        {"price": 17200, "listing_age_days": 5, "seller_type": "profissional", "km": 90000, "year": 2019},
        {"median_price": 17000, "sample_count": 12},
    )
    assert r is not None
    assert r["fair_value"] == 17000
    assert r["confidence"] == "media"  # 8..19 comparables


def test_thin_sample_is_suppressed():
    # Below the minimum comparables, numbers would be noise -> None.
    assert neg({"price": 14500, "year": 2016}, {"median_price": 19900, "sample_count": 3}) is None


def test_no_market_data_is_none():
    assert neg({"price": 15000}, {}) is None


def test_implausible_ratio_is_suppressed():
    # A €5.000 car against a €15.750 market (ratio .32) = wrong pool / scam -> None.
    assert neg({"price": 5000, "year": 2017}, {"median_price": 15750, "sample_count": 14}) is None
    # Wildly above (ratio 2.3), e.g. a Velar mis-matched to an Evoque -> None.
    assert neg({"price": 39500, "year": 2018}, {"median_price": 16990, "sample_count": 20}) is None


def test_rounding_and_ordering_invariants():
    r = neg(
        {"price": 20500, "listing_age_days": 20, "seller_type": "stand", "km": 100000, "year": 2018},
        {"median_price": 18400, "sample_count": 22},
    )
    assert r is not None
    for k in ("opening_offer", "fair_value", "walk_away"):
        assert r[k] % 50 == 0                    # rounded to €50
    assert r["opening_offer"] <= r["walk_away"]  # never nonsensical
