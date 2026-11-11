"""
Deterministic unit tests for the V5 recommendation engine.

These cover the parts of recommend_service that run without a database or
an LLM: profile building, hard constraints, scoring, the aversion penalty,
diverse selection, and the dismiss-reason adjustments. They lock in the
decision logic so future tuning can't silently regress it.

The LLM explanation path (_generate_explanations_llm) and the DB loaders
(load_models, _attach_dealbreakers) are intentionally out of scope — they
need a live Gemini key / Postgres and are exercised by the integration
scripts, not here.
"""

import pytest

from app.services.recommend_service import (
    DIMENSIONS,
    BRAND_STATUS,
    build_profile,
    apply_hard_constraints,
    score_model,
    _apply_aversion_penalty,
    _build_model_vector,
    select_diverse_top5,
    _apply_dismiss_adjustments,
)


# ── fixtures ────────────────────────────────────────────────────────────

def _model(**overrides):
    """A fully-formed model dict with its 6D vector computed."""
    m = {
        "id": overrides.get("id", 1),
        "model_name": "Test",
        "brand_name": "Volkswagen",
        "full_name": "Volkswagen Test",
        "body_type": "compacto",
        "segment": "medio",
        "avg_price": 18000,
        "min_price": 16000,
        "max_price": 20000,
        "avg_consumption": 6.0,
        "avg_reliability": 7.0,
        "avg_maintenance": 500.0,
        "best_consumption": 5.5,
        "max_power": 110,
        "comfort_score": 6,
        "driving_fun_score": 6,
        "city_score": 6,
        "highway_score": 6,
        "family_score": 6,
        "character_desc": "",
        "reliability_score": None,
    }
    m.update(overrides)
    m["vector"] = _build_model_vector(m)
    return m


# ── build_profile ───────────────────────────────────────────────────────

def test_profile_is_normalized_distribution():
    profile, _ = build_profile({"p1_context": "misto"})
    assert set(profile) == set(DIMENSIONS)
    assert all(0.0 <= v <= 1.0 for v in profile.values())
    assert abs(sum(profile.values()) - 1.0) < 1e-3


def test_family_context_prioritizes_practical_and_reliability():
    fam, _ = build_profile({"p1_context": "familia"})
    city, _ = build_profile({"p1_context": "cidade"})
    assert fam["practical"] > city["practical"]
    assert fam["reliability"] > 0.0


def test_dream_brand_shifts_profile_toward_its_traits():
    plain, _ = build_profile({"p1_context": "misto"})
    porsche, _ = build_profile({"p1_context": "misto", "p7_dream_brand": "porsche"})
    # Porsche traits are driving/status-heavy → those dims must rise.
    assert porsche["driving"] > plain["driving"]
    assert porsche["status"] > plain["status"]


def test_budget_range_sets_min_max_on_answers():
    answers = {"p1_context": "misto", "p8_budget_range": "15_25"}
    build_profile(answers)
    assert answers["p8_budget_min"] == 15000
    assert answers["p8_budget_max"] == 25000


def test_unknown_answers_fall_back_to_uniform_not_collapse():
    # Bogus context with no recognized signal → uniform, never all-zero.
    profile, _ = build_profile({"p1_context": "___nope___"})
    # misto fallback still gives weights, so just assert no collapse:
    assert abs(sum(profile.values()) - 1.0) < 1e-3
    assert all(v > 0 for v in profile.values())


def test_tiny_budget_boosts_economy():
    cheap, _ = build_profile({"p1_context": "misto", "p8_budget_max": 10000})
    rich, _ = build_profile({"p1_context": "misto", "p8_budget_max": 45000})
    assert cheap["economy"] > rich["economy"]
    assert rich["status"] > cheap["status"]


# ── apply_hard_constraints ──────────────────────────────────────────────

def test_over_stretch_limit_is_excluded():
    models = [_model(id=1, avg_price=40000)]  # budget 20k, stretch limit 23k
    passed, stretch = apply_hard_constraints(models, {"p8_budget_max": 20000})
    assert passed == [] and stretch == []


def test_stretch_band_is_separated_from_passed():
    models = [
        _model(id=1, avg_price=18000),  # within budget
        _model(id=2, avg_price=22000),  # over budget, within 15% stretch
    ]
    passed, stretch = apply_hard_constraints(models, {"p8_budget_max": 20000})
    assert [m["id"] for m in passed] == [1]
    assert [m["id"] for m in stretch] == [2]


def test_family_excludes_citadino():
    models = [_model(id=1, body_type="citadino", avg_price=15000)]
    passed, stretch = apply_hard_constraints(
        models, {"p1_context": "familia", "p8_budget_max": 20000}
    )
    assert passed == [] and stretch == []


def test_family_excludes_low_family_score_compacto():
    low = _model(id=1, body_type="compacto", family_score=5, avg_price=15000)
    high = _model(id=2, body_type="compacto", family_score=8, avg_price=15000)
    passed, _ = apply_hard_constraints(
        [low, high], {"p1_context": "familia", "p8_budget_max": 20000}
    )
    assert [m["id"] for m in passed] == [2]


def test_budget_floor_excludes_far_under_budget_when_real_budget():
    # budget_min 30000 → floor 0.58*30000 = 17400; a 10k car is a full tier below.
    cheap = _model(id=1, avg_price=10000)
    fit = _model(id=2, avg_price=30000)
    passed, _ = apply_hard_constraints(
        [cheap, fit], {"p8_budget_min": 30000, "p8_budget_max": 35000}
    )
    assert [m["id"] for m in passed] == [2]


# ── score_model ─────────────────────────────────────────────────────────

def test_score_is_non_negative_float():
    profile, _ = build_profile({"p1_context": "misto"})
    s = score_model(_model(), profile, {"p1_context": "misto"})
    assert isinstance(s, float) and s >= 0.0


def test_reliability_aversion_suppresses_unreliable_model():
    profile, _ = build_profile({"p1_context": "misto"})
    reliable = _model(id=1, avg_reliability=9.0)
    flaky = _model(id=2, avg_reliability=4.0)
    answers = {"p1_context": "misto", "p6_aversion": "fiabilidade"}
    assert score_model(reliable, profile, answers) > score_model(flaky, profile, answers)


def test_profile_alignment_raises_score():
    # An economy-heavy profile should score an economical model above a thirsty one.
    answers = {"p1_context": "cidade", "p2_relationship": "apenas_transporte",
               "p8_budget_max": 12000}
    profile, _ = build_profile(answers)
    frugal = _model(id=1, avg_consumption=4.5, avg_maintenance=350)
    thirsty = _model(id=2, avg_consumption=11.0, avg_maintenance=900)
    assert score_model(frugal, profile, answers) > score_model(thirsty, profile, answers)


# ── _apply_aversion_penalty ─────────────────────────────────────────────

def test_aversion_none_is_neutral():
    assert _apply_aversion_penalty(_model(), "nenhuma", "misto") == 1.0


def test_aversion_penalty_is_monotonic_no_cliff_inversions():
    # The design claim: a worse model never gets a *better* penalty.
    prev = 0.0
    for rel in [0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 7.5, 8.0, 9.0, 10.0]:
        p = _apply_aversion_penalty(_model(avg_reliability=rel), "fiabilidade", "misto")
        assert p >= prev - 1e-9, f"penalty dropped at reliability={rel}"
        prev = p
    assert prev == 1.0  # at/above threshold → no penalty


def test_aversion_penalty_respects_floor():
    worst = _apply_aversion_penalty(_model(avg_reliability=0.0), "fiabilidade", "misto")
    assert worst == pytest.approx(0.30)


# ── select_diverse_top5 ─────────────────────────────────────────────────

def _scored(models):
    for i, m in enumerate(models):
        m["_score"] = m.pop("_force_score", 1.0 - i * 0.01)
        m["is_stretch"] = False
        m["is_wildcard"] = False
    return models


def test_select_returns_at_most_five():
    models = _scored([_model(id=i, avg_price=18000) for i in range(10)])
    out = select_diverse_top5(models, [], {"p1_context": "misto"})
    assert len(out) <= 5


def test_select_no_duplicate_ids():
    models = _scored([_model(id=i, avg_price=18000, body_type="suv") for i in range(8)])
    out = select_diverse_top5(models, [], {"p1_context": "familia"})
    assert len({m["id"] for m in out}) == len(out)


def test_mainstream_brand_capped_at_one():
    # 6 Renaults (mid/low brand) should never fill more than 1 slot.
    models = _scored([
        _model(id=i, brand_name="Renault", body_type="compacto", avg_price=18000)
        for i in range(6)
    ])
    out = select_diverse_top5(models, [], {"p1_context": "misto"})
    renaults = [m for m in out if m["brand_name"] == "Renault"]
    assert len(renaults) == 1


def test_premium_brand_capped_at_two():
    models = _scored([
        _model(id=i, brand_name="BMW", segment="premium", body_type="berlina",
               avg_price=22000)
        for i in range(6)
    ])
    out = select_diverse_top5(models, [], {"p1_context": "misto"})
    bmws = [m for m in out if m["brand_name"] == "BMW"]
    assert len(bmws) <= 2


def test_stretch_only_admitted_when_close_to_top():
    passed = _scored([_model(id=1, avg_price=18000, _force_score=1.0)])
    # Stretch model scoring far below top (0.50 < 0.85*1.0) must be rejected.
    weak_stretch = _scored([_model(id=99, avg_price=22000, _force_score=0.50)])
    out = select_diverse_top5(passed, weak_stretch, {"p1_context": "misto"})
    assert 99 not in {m["id"] for m in out}


# ── _apply_dismiss_adjustments ──────────────────────────────────────────

def test_dismiss_sportier_raises_driving():
    base = {d: 0.2 for d in DIMENSIONS}
    adj = _apply_dismiss_adjustments(base, ["Quero algo mais desportivo"])
    assert adj["driving"] > base["driving"]


def test_dismiss_adjustments_clamp_to_unit_interval():
    base = {d: 0.95 for d in DIMENSIONS}
    adj = _apply_dismiss_adjustments(base, ["mais luxuoso", "mais desportivo"])
    assert all(0.0 <= v <= 1.0 for v in adj.values())


# ── _build_model_vector ─────────────────────────────────────────────────

def test_vector_dims_in_unit_interval():
    v = _build_model_vector(_model())
    assert set(v) == set(DIMENSIONS)
    assert all(0.0 <= x <= 1.0 for x in v.values())


def test_ev_consumption_converted_not_penalized_as_thirsty():
    # EV at 18 kWh/100km must not read as a 18 L/100km gas-guzzler.
    ev = _build_model_vector(_model(avg_consumption=18.0))
    gas = _build_model_vector(_model(avg_consumption=9.0))
    assert ev["economy"] > gas["economy"]
