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


# ── trust rule: unsourced critico can't become a deal-breaker ──────────────

from app.services.curator_agent import effective_severity, _issue_source_label


def test_closed_book_critico_is_capped_at_alto():
    assert effective_severity("critico", grounded=False) == "alto"
    assert effective_severity("deal-breaker", grounded=False) == "alto"


def test_grounded_critico_is_kept():
    assert effective_severity("critico", grounded=True) == "critico"


def test_non_critico_severities_unaffected_by_grounding():
    for raw, expect in [("alto", "alto"), ("medio", "medio"), ("baixo", "baixo")]:
        assert effective_severity(raw, grounded=False) == expect
        assert effective_severity(raw, grounded=True) == expect


def test_issue_source_label_states_provenance():
    assert "sem fontes" in _issue_source_label(False)
    assert "pesquisa web" in _issue_source_label(True)


# ── year-aware deal-breakers ────────────────────────────────────────────────

from datetime import date

from app.services.dealbreakers import (
    _applies, _parse_affected_years, _recall_years, _years_label,
)


def test_recall_years_prefer_production_range_over_generation():
    assert _recall_years({"years": [2024, 2025, 2026]}, 2019, None) == (2024, 2026)
    # NHTSA: single de-duplicated "year" is not a range → use the generation.
    assert _recall_years({"year": 2021}, 2019, None) == (2019, None)


def test_kuga_2020_is_not_warned_about_2024_only_recall():
    lo, hi = _recall_years({"years": [2024, 2025, 2026]}, 2019, None)
    assert not _applies(2020, lo, hi)
    assert _applies(2025, lo, hi)


def test_unknown_year_or_bounds_never_exclude():
    assert _applies(None, 2024, 2026)          # recommendation view: no year
    assert _applies(2020, None, None)          # recall with no known period


def test_affected_years_parsing():
    assert _parse_affected_years("2010-2014") == (2010, 2014)
    assert _parse_affected_years("2020+") == (2020, None)
    assert _parse_affected_years("variável") is None
    assert _parse_affected_years("20101") is None


def test_years_label():
    assert _years_label(2013, 2024) == "2013-2024"
    assert _years_label(2024, None) == "2024+"
    assert _years_label(2019, date.today().year) == "2019+"
    assert _years_label(None, None) is None
