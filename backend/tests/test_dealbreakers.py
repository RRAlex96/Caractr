"""Phase A — deal-breaker data layer.

These lock in the two things that protect user trust in the recall/known-failure
signal: (1) recalls are matched to models with high precision (no mis-attribution),
and (2) a serious recall is never silently downgraded, and (3) the curator's
free-form severity collapses to the deal-breaker tier correctly.
"""
from app.scrapers.safety_gate import _name_match_score, _canonical_severity
from app.services.curator_agent import normalize_severity


# ── high-precision model matching (precision over recall on purpose) ─────────
def test_model_matches_inside_verbose_product_text():
    # A whole-word hit of the DB model name inside a verbose recall product
    # string is a confident match.
    assert _name_match_score("Golf", "Volkswagen Golf VII 1.6 TDI") == 1.0
    assert _name_match_score("A3", "Audi A3 Sportback 35 TDI") == 1.0


def test_model_does_not_match_substring_of_another_name():
    # "A3" must NOT match inside "A30" — word boundaries guard against this.
    assert _name_match_score("A3", "Audi A30 concept") < 0.6


def test_unrelated_models_rejected():
    assert _name_match_score("Golf", "Vauxhall Astra") < 0.6
    assert _name_match_score("Clio", "Renault Captur") < 0.6


# ── severity normalisation (the Safety Gate bug fix) ─────────────────────────
def test_serious_risk_is_not_downgraded():
    # The API sends "Serious risk" (not "SERIOUS_RISK"); it must stay serious,
    # otherwise genuine safety recalls get the lowest evidence weight.
    assert _canonical_severity("Serious risk") == "serious"
    assert _canonical_severity("SERIOUS_RISK") == "serious"


def test_canonical_severity_buckets():
    assert _canonical_severity("High") == "high"
    assert _canonical_severity("Medium") == "medium"
    assert _canonical_severity("") == "low"
    assert _canonical_severity("anything else") == "low"


# ── curator deal-breaker tier ────────────────────────────────────────────────
def test_curator_severity_collapses_to_dealbreaker():
    for raw in ("critico", "Crítico", "deal-breaker", "grave", "critical"):
        assert normalize_severity(raw) == "critico"


def test_curator_severity_other_tiers():
    assert normalize_severity("high") == "alto"
    assert normalize_severity("low") == "baixo"
    assert normalize_severity("weird") == "medio"   # safe default
    assert normalize_severity(None) == "medio"
