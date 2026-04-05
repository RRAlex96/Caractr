"""
Tests for the Bayesian reliability scorer.

Required properties:
1. Validity:      0 < p_mean < 1, CI contains mean, scores in [1, 10]
2. Monotonicity:  adding a high-severity recall must decrease the score
3. CI narrowing:  more evidence → CI width shrinks (consistency)
4. Data quality:  labels reflect evidence count correctly
5. Stability:     score change from one additional weak signal < 0.15
6. Fuel/age:      different priors produce meaningfully different baselines
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.bayesian_reliability import compute_reliability_score, scores_are_valid


# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────

def _recall(severity_fail: float, weight: float, source: str = "eu_safety_gate") -> dict:
    return {"fail_eff": severity_fail, "succ_eff": 0, "weight": weight, "source": source}

def _positive(succ: float, source: str = "inspection") -> dict:
    return {"fail_eff": 0, "succ_eff": succ, "weight": 0.3, "source": source}


# ─────────────────────────────────────────────────────────────
# 1. Validity
# ─────────────────────────────────────────────────────────────

def test_no_evidence_is_valid():
    result = compute_reliability_score([], fuel_type="gasolina", age_years=5)
    assert scores_are_valid(result), f"Invalid result: {result}"

def test_with_evidence_is_valid():
    ev = [_recall(6.0, 1.0), _recall(3.0, 0.6, "standvirtual_nlp")]
    result = compute_reliability_score(ev, fuel_type="diesel", age_years=10)
    assert scores_are_valid(result), f"Invalid result: {result}"

def test_score_bounds():
    result = compute_reliability_score([], fuel_type="gasolina", age_years=3)
    assert 1.0 <= result["score_1_10"] <= 10.0
    assert 1.0 <= result["ci_low_1_10"] <= result["score_1_10"]
    assert result["score_1_10"] <= result["ci_high_1_10"] <= 10.0


# ─────────────────────────────────────────────────────────────
# 2. Monotonicity — adding a serious recall must decrease score
# ─────────────────────────────────────────────────────────────

def test_serious_recall_decreases_score():
    base    = compute_reliability_score([], fuel_type="gasolina", age_years=5)
    updated = compute_reliability_score(
        [_recall(6.0, 1.0)], fuel_type="gasolina", age_years=5
    )
    assert updated["score_1_10"] < base["score_1_10"], (
        f"Score should drop after serious recall: {base['score_1_10']} -> {updated['score_1_10']}"
    )

def test_medium_recall_decreases_score():
    base    = compute_reliability_score([], fuel_type="diesel", age_years=8)
    updated = compute_reliability_score(
        [_recall(1.5, 0.3)], fuel_type="diesel", age_years=8
    )
    assert updated["score_1_10"] < base["score_1_10"]

def test_multiple_recalls_decrease_monotonically():
    ev0 = compute_reliability_score([], fuel_type="gasolina", age_years=6)
    ev1 = compute_reliability_score([_recall(3.0, 0.6)], fuel_type="gasolina", age_years=6)
    ev2 = compute_reliability_score([_recall(3.0, 0.6), _recall(6.0, 1.0)], fuel_type="gasolina", age_years=6)
    assert ev0["score_1_10"] > ev1["score_1_10"] > ev2["score_1_10"]


# ─────────────────────────────────────────────────────────────
# 3. CI narrowing — more evidence → narrower CI
# ─────────────────────────────────────────────────────────────

def test_more_evidence_narrows_ci():
    def ci_width(evidence):
        r = compute_reliability_score(evidence, fuel_type="gasolina", age_years=5)
        return r["ci_high_1_10"] - r["ci_low_1_10"]

    w0 = ci_width([])
    w1 = ci_width([_recall(3.0, 0.6), _positive(10, "eu_safety_gate")])
    w3 = ci_width([
        _recall(3.0, 0.6), _positive(10, "eu_safety_gate"),
        _recall(1.5, 0.3, "standvirtual_nlp"), _positive(20, "breakdown"),
        _recall(0.5, 0.1, "tsb"),
    ])
    assert w3 < w1, f"More evidence should narrow CI: {w1:.3f} -> {w3:.3f}"
    # Prior-only CI can be narrow or wide depending on n0, so just check consistency
    assert w0 > 0, "CI should always have positive width"


# ─────────────────────────────────────────────────────────────
# 4. Data quality labels
# ─────────────────────────────────────────────────────────────

def test_no_evidence_is_prior_only():
    result = compute_reliability_score([], fuel_type="gasolina", age_years=5)
    assert result["data_quality"] == "prior_only"
    assert result["evidence_count"] == 0

def test_one_source_is_limited():
    result = compute_reliability_score(
        [_recall(3.0, 0.6), _recall(1.5, 0.3)],  # same source
        fuel_type="gasolina", age_years=5
    )
    assert result["data_quality"] == "limited"

def test_multiple_sources_is_robust():
    ev = [
        _recall(3.0, 0.6, "eu_safety_gate"),
        _recall(1.5, 0.3, "standvirtual_nlp"),
        _positive(5, "breakdown"),
    ]
    result = compute_reliability_score(ev, fuel_type="gasolina", age_years=5)
    assert result["data_quality"] == "robust"
    assert result["evidence_count"] == 3


# ─────────────────────────────────────────────────────────────
# 5. Stability — one weak signal should not move score > 0.15
# ─────────────────────────────────────────────────────────────

def test_stability_weak_signal():
    base_ev = [_recall(3.0, 0.6, "eu_safety_gate"), _positive(10, "breakdown")]
    base    = compute_reliability_score(base_ev, fuel_type="gasolina", age_years=5)

    updated_ev = base_ev + [_recall(0.5, 0.1, "tsb")]
    updated    = compute_reliability_score(updated_ev, fuel_type="gasolina", age_years=5)

    delta = abs(updated["score_1_10"] - base["score_1_10"])
    assert delta < 0.15, f"Weak signal moved score too much: {delta:.3f}"


# ─────────────────────────────────────────────────────────────
# 6. Priors differ by fuel type and age
# ─────────────────────────────────────────────────────────────

def test_older_car_lower_baseline():
    young = compute_reliability_score([], fuel_type="gasolina", age_years=2)
    old   = compute_reliability_score([], fuel_type="gasolina", age_years=15)
    assert young["score_1_10"] > old["score_1_10"], (
        f"Older cars should have lower prior: {young['score_1_10']} vs {old['score_1_10']}"
    )

def test_ev_has_different_baseline_than_diesel():
    ev_score     = compute_reliability_score([], fuel_type="eletrico", age_years=5)
    diesel_score = compute_reliability_score([], fuel_type="diesel", age_years=10)
    # EV young vs diesel old — just verify they differ
    assert ev_score["score_1_10"] != diesel_score["score_1_10"]

def test_unknown_fuel_uses_default():
    result = compute_reliability_score([], fuel_type=None, age_years=5)
    assert scores_are_valid(result)
    result2 = compute_reliability_score([], fuel_type="rocket_fuel", age_years=5)
    assert scores_are_valid(result2)


# ─────────────────────────────────────────────────────────────
# 7. Sources list
# ─────────────────────────────────────────────────────────────

def test_sources_deduplicated():
    ev = [
        _recall(3.0, 0.6, "eu_safety_gate"),
        _recall(1.5, 0.3, "eu_safety_gate"),
        _positive(5, "breakdown"),
    ]
    result = compute_reliability_score(ev, fuel_type="gasolina", age_years=5)
    assert len(result["sources"]) == 2
    assert "eu_safety_gate" in result["sources"]
    assert "breakdown" in result["sources"]


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
