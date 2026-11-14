"""A cached or shared analysis keeps its position against the market."""


# ── a cached or shared analysis keeps its price position ─────────────────────

def test_price_position_is_rebuilt_for_a_cached_analysis():
    from app.services.ad_analysis_service import _price_position
    stats = {"median_price": 10000, "sample_count": 40}
    pos = _price_position({"price": 12990}, stats)
    assert pos["price_delta_pct"] == 29.9 and pos["price_delta"] < 0          # above the market
    assert _price_position({"price": 9000}, stats)["price_delta"] > 0          # below
    assert _price_position({"price": 12990}, {"median_price": 10000, "sample_count": 2}) == {}
    assert _price_position({"price": None}, stats) == {}


def test_build_response_fills_the_position_from_the_market(monkeypatch):
    from app.services.ad_analysis_service import _build_response
    out = _build_response({"price": 12990, "brand_name": "Peugeot", "model_name": "208", "year": 2019},
                          {}, from_cache=True, market_stats={"median_price": 10000, "sample_count": 40})
    assert out["deal"]["price_delta_pct"] == 29.9
