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
    assert worst == pytest.approx(0.40)


def test_reliability_aversion_bites_inside_the_real_score_range():
    # Real scores sit between 6.0 and 9.2: a 7.2 must lose clearly against an
    # 8.4 for someone who fears breakdowns (it kept 97% under the old curve).
    p = lambda r: _apply_aversion_penalty(_model(avg_reliability=r), "fiabilidade", "misto")  # noqa: E731
    assert p(8.4) == 1.0
    assert p(7.2) < 0.80
    assert p(6.0) == pytest.approx(0.40)


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


# ── template copy quality (what users see when the LLM is unavailable) ──

from app.services.recommend_service import _build_reasons, _fmt_eur, _fmt_score


def test_scores_never_leak_raw_floats():
    assert _fmt_score(8.333333333333334) == "8.3"
    assert _fmt_score(9.0) == "9"


def test_prices_use_portuguese_formatting():
    assert _fmt_eur(16000) == "16 000 €"


def test_reliability_reason_is_formatted():
    m = _model(id=2, brand_name="Suzuki", avg_reliability=8.333333333333334)
    reasons = _build_reasons(m, {}, "reliability", "economy", {"p8_budget_max": 15000})
    joined = " ".join(reasons)
    assert "8.333" not in joined and "8.3/10" in joined


def test_power_claim_is_framed_as_top_version():
    m = _model(id=1, driving_fun_score=9, max_power=510)
    reasons = _build_reasons(m, {}, "driving", "status", {"p8_budget_max": 35000})
    assert any("Versões até 510 cv" in r for r in reasons)


# ── Stage F: deal-breaker demotion ──────────────────────────────────────

from app.services.recommend_service import CRITICAL_ISSUE_FACTOR, CRITICAL_ISSUE_FACTOR_AVERSE


def test_critical_issue_demotes_but_never_zeroes():
    profile, _ = build_profile({"p1_context": "misto"})
    answers = {"p1_context": "misto"}
    clean = score_model(_model(id=1), profile, answers)
    flawed = score_model(_model(id=1, has_critical_issue=True), profile, answers)
    assert flawed == pytest.approx(clean * CRITICAL_ISSUE_FACTOR, rel=1e-3)
    assert flawed > 0


def test_critical_issue_hurts_more_when_user_hates_unreliability():
    profile, _ = build_profile({"p1_context": "misto"})
    averse = {"p1_context": "misto", "p6_aversion": "fiabilidade"}
    clean = score_model(_model(id=1, avg_reliability=8.0), profile, averse)
    flawed = score_model(_model(id=1, avg_reliability=8.0, has_critical_issue=True), profile, averse)
    assert flawed == pytest.approx(clean * CRITICAL_ISSUE_FACTOR_AVERSE, rel=1e-3)


def test_recalls_alone_do_not_affect_score():
    profile, _ = build_profile({"p1_context": "misto"})
    answers = {"p1_context": "misto"}
    base = score_model(_model(id=1), profile, answers)
    with_recall = score_model(_model(id=1, dealbreakers={"recall_count": 3}), profile, answers)
    assert with_recall == base


# ── a model is priced at the registration year the budget buys ──────────

def _years(*rows):
    return [{"year": y, "p50": p50, "p10": int(p50 * 0.85), "p90": int(p50 * 1.15), "n": 20,
             "as_of": "2026-11-13"} for y, p50 in rows]


GOLF = _years((2014, 9500), (2016, 12500), (2018, 15500), (2020, 19500), (2023, 26000))


def test_price_for_budget_picks_the_newest_year_that_fits():
    from app.services.recommend_service import price_for_budget
    row, over = price_for_budget(GOLF, 16000, 16000 * 1.15, this_year=2026)
    assert (row["year"], over) == (2018, False)
    row, over = price_for_budget(GOLF, 30000, 30000 * 1.15, this_year=2026)
    assert (row["year"], over) == (2023, False)


def test_price_for_budget_stretches_only_when_nothing_fits():
    from app.services.recommend_service import price_for_budget
    row, over = price_for_budget(GOLF, 9000, 9000 * 1.15, this_year=2026)   # the 2014 one, 5% over
    assert (row["year"], over) == (2014, True)
    assert price_for_budget(GOLF, 7000, 7000 * 1.15, this_year=2026) is None


def test_hard_constraints_price_the_model_at_that_year():
    golf = _model(id=1, avg_price=19500, prices_by_year=GOLF)       # 19 500: its most-listed year
    passed, stretch = apply_hard_constraints([golf], {"p8_budget_max": 13000})
    assert stretch == [] and len(passed) == 1
    m = passed[0]
    assert (m["price_year"], m["avg_price"]) == (2016, 12500)
    assert (m["min_price"], m["max_price"]) == (GOLF[1]["p10"], GOLF[1]["p90"])
    assert m["market_p50"] == 12500 and m["market_band"]["sample_count"] == 20
    assert golf["avg_price"] == 19500                                # the shared model is not changed


def test_hard_constraints_exclude_a_model_no_year_of_which_fits():
    golf = _model(id=1, avg_price=19500, prices_by_year=GOLF)
    assert apply_hard_constraints([golf], {"p8_budget_max": 6000}) == ([], [])


def test_budget_floor_uses_the_year_the_budget_buys():
    # 40–60k: the newest Golf (26 000) is still a tier below what the user is shopping for.
    golf = _model(id=1, avg_price=19500, prices_by_year=GOLF)
    passed, stretch = apply_hard_constraints([golf], {"p8_budget_min": 46000, "p8_budget_max": 60000})
    assert passed == [] and stretch == []


def test_a_model_is_not_recommended_at_a_year_older_than_the_age_limit():
    from app.services.recommend_service import price_for_budget
    cayenne = _years((2008, 22000), (2012, 31000), (2016, 39000), (2021, 70000))
    # 25 000 buys a 2008 Cayenne — 18 years old in 2026. Not advice: no pick.
    assert price_for_budget(cayenne, 25000, 25000 * 1.15, this_year=2026) is None
    row, over = price_for_budget(cayenne, 40000, 40000 * 1.15, this_year=2026)
    assert (row["year"], over) == (2016, False)
    # 12 years old is still inside the limit
    row, _ = price_for_budget(_years((2014, 9500)), 10000, 11500, this_year=2026)
    assert row["year"] == 2014


def test_a_small_budget_may_buy_an_older_car():
    from app.services.recommend_service import price_for_budget
    old = _years((2009, 4500), (2012, 6500))
    row, _ = price_for_budget(old, 5000, 5750, this_year=2026)       # 17 years old: allowed under 8 000
    assert row["year"] == 2009
    assert price_for_budget(_years((2006, 4500)), 5000, 5750, this_year=2026) is None   # 20 years: not even then


def test_load_models_sql_keeps_litres_and_kwh_apart():
    from app.services.recommend_service import LOAD_MODELS_SQL
    sql = str(LOAD_MODELS_SQL)
    assert "avg_kwh" in sql and "best_kwh" in sql
    # plug-in lab figures and electric kWh are not in the litres average
    assert sql.count("e.fuel_type <> 'eletrico'") == 2
    assert sql.count("e.consumption_mixed < 3.5") == 2
    # nothing that needs a column older databases do not have
    assert "plug_in" not in sql


# ── a trade-off never denies what the headline or the reasons just said ──
from app.services.recommend_service import (
    DIMENSIONS, TRADEOFF_TEMPLATES, _build_tradeoff, generate_all_explanations,
)

_FLAT = {d: v for d, v in zip(DIMENSIONS, (0.10, 0.16, 0.20, 0.24, 0.10, 0.20))}


def _with_vector(model_id, **vector):
    m = _model(id=model_id, full_name=f"Marca Modelo{model_id}", family_score=7, driving_fun_score=7)
    m["vector"] = {d: vector.get(d, 0.15) for d in DIMENSIONS}
    return m


def test_reasons_report_which_dimensions_they_praised():
    praised = set()
    _build_reasons(_model(id=1, family_score=7, comfort_score=5), {}, "practical", "comfort",
                   {"p8_budget_max": 25000}, praised)
    # a reason was written about space; none about comfort (score below 7)
    assert praised == {"practical"}


def test_tradeoff_skips_a_praised_dimension_when_no_other_car_is_clearly_better():
    profile = dict(_FLAT)
    # the biggest gap is on space, and no other car is clearly roomier
    car = _with_vector(1, practical=0.10, comfort=0.15)
    others = [_with_vector(i, practical=0.12) for i in (2, 3, 4, 5)]
    flat = TRADEOFF_TEMPLATES["practical"]
    assert _build_tradeoff(car, profile, [car] + others, {}, set()) in flat
    said = _build_tradeoff(car, profile, [car] + others, {}, set(), {"practical"})
    assert said not in flat and "espaço" not in said.lower()


def test_tradeoff_may_still_compare_a_praised_dimension_with_a_clearly_better_car():
    profile = dict(_FLAT)
    car = _with_vector(1, practical=0.10, reliability=0.30)
    roomy = _with_vector(2, practical=0.40)
    roomy["full_name"] = "Skoda Octavia"
    said = _build_tradeoff(car, profile, [car, roomy], {}, set(), {"practical"})
    assert said == "Não é tão espaçoso como o Skoda Octavia, mas compensa em fiabilidade."


def test_comparison_never_offers_the_compared_dimension_as_the_compensation():
    profile = dict(_FLAT)
    # space is this car's own strongest side, and another car has more of it
    car = _with_vector(1, economy=0.10, comfort=0.21, driving=0.20, practical=0.22, status=0.10,
                       reliability=0.20)
    roomy = _with_vector(2, practical=0.45)
    said = _build_tradeoff(car, profile, [car, roomy], {}, set())
    assert "mas compensa em conforto" in said


def test_template_explanations_do_not_contradict_themselves():
    profile = dict(_FLAT)
    cars = [_with_vector(i, practical=0.10 + i * 0.005) for i in range(1, 6)]
    for out in generate_all_explanations(cars, profile, {"p8_budget_max": 25000}):
        # every car here gets "Nota 7/10 para famílias" as a reason
        assert any("famílias" in r or "familiar" in r for r in out["reasons"])
        assert out["tradeoff"] not in TRADEOFF_TEMPLATES["practical"]


# ── a model recommended at a year is described by the engines of that year ──
from app.services.recommend_service import _with_price, engine_figures

_ENGINES = [
    {"fuel_type": "diesel", "plug_in": False, "consumption": 5.0, "power_hp": 190, "reliability": 7.5,
     "maintenance": 800, "year_from": 2010, "year_to": 2016},
    {"fuel_type": "hibrido", "plug_in": True, "consumption": 1.8, "power_hp": 292, "reliability": 7.0,
     "maintenance": 950, "year_from": 2019, "year_to": 2023},
    {"fuel_type": "gasolina", "plug_in": False, "consumption": 9.5, "power_hp": 510, "reliability": 7.2,
     "maintenance": 1400, "year_from": 2021, "year_to": 2023},
]


def test_engine_figures_are_those_of_the_year():
    f = engine_figures(_ENGINES, 2015)
    assert f["max_power"] == 190 and f["best_consumption"] == 5.0
    assert f["avg_reliability"] == 7.5 and f["avg_maintenance"] == 800
    later = engine_figures(_ENGINES, 2022)
    assert later["max_power"] == 510
    assert later["best_consumption"] == 9.5        # the plug-in's 1.8 L is not a real consumption
    assert later["reliability_score"] == 7.1


def test_engine_figures_stand_aside_when_they_cannot_tell():
    assert engine_figures(_ENGINES, None) == {}
    assert engine_figures([], 2015) == {}
    assert engine_figures(_ENGINES, 2005) == {}                       # no engine known for that year
    undated = [{**e, "year_from": None, "year_to": None} for e in _ENGINES]
    assert engine_figures(undated, 2015) == {}                        # all engines, as before


def test_pricing_a_model_at_a_year_takes_that_years_engines():
    m = _model(id=7, max_power=510, best_consumption=1.8)
    m["engines"] = _ENGINES
    row = {"p50": 21000, "p10": 18000, "p90": 25000, "year": 2015, "n": 20, "as_of": "2026-11-13"}
    priced = _with_price(m, row)
    assert priced["max_power"] == 190 and priced["best_consumption"] == 5.0
    assert priced["price_year"] == 2015 and priced["avg_price"] == 21000
    assert m["max_power"] == 510                                      # the model itself is untouched


# ── Ownership: age, running cost, image fit (2026-11-17) ──────────────────

from app.services.recommend_service import curated_fault_share, ownership_factor  # noqa: E402


def _transport_answers(**kw):
    a = {"p1_context": "cidade", "p2_relationship": "apenas_transporte", "p3_driving_style": "suave_previsivel",
         "p5_presence": "discreto", "p6_aversion": "fiabilidade", "p8_budget_min": 8000, "p8_budget_max": 12000}
    a.update(kw)
    return a


def test_an_older_car_costs_more_for_a_no_hassle_buyer():
    answers = _transport_answers()
    profile, _ = build_profile(dict(answers))
    new = _model(id=1, price_year=2022)
    old = _model(id=2, price_year=2014)
    assert ownership_factor(new, profile, answers) > ownership_factor(old, profile, answers)


def test_discreet_transport_buyer_prefers_mainstream_to_premium():
    answers = _transport_answers(p6_aversion="nenhuma")
    profile, _ = build_profile(dict(answers))
    bmw = _model(id=1, brand_name="BMW", price_year=2020)
    kia = _model(id=2, brand_name="Kia", price_year=2020)
    assert ownership_factor(kia, profile, answers) > ownership_factor(bmw, profile, answers)
    # ...but a buyer who wants presence is not pushed away from BMW
    show = _transport_answers(p5_presence="vire_cabecas", p2_relationship="adoro_conduzir", p6_aversion="nenhuma")
    p2, _ = build_profile(dict(show))
    assert ownership_factor(bmw, p2, show) == ownership_factor(kia, p2, show)


def test_high_maintenance_costs_a_breakdown_averse_buyer():
    answers = _transport_answers(p5_presence="bom_aspeto")
    profile, _ = build_profile(dict(answers))
    cheap = _model(id=1, avg_maintenance=320, price_year=2021)
    dear = _model(id=2, avg_maintenance=650, price_year=2021)
    assert ownership_factor(cheap, profile, answers) > ownership_factor(dear, profile, answers)


def test_curated_fault_share_weights_engines_on_sale_that_year():
    m = _model(engines=[
        {"year_from": 2014, "year_to": 2022, "listings_seen": 300, "critical_years": [(2012, 2022)]},
        {"year_from": 2014, "year_to": 2022, "listings_seen": 100, "critical_years": []},
        {"year_from": 2023, "year_to": 2026, "listings_seen": 200, "critical_years": []},
    ])
    assert curated_fault_share(m, 2018) == 0.75
    assert curated_fault_share(m, 2024) == 0.0
    assert curated_fault_share(m, None) == 0.0
