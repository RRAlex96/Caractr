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


# ── Recalls are a checklist, not a deal-breaker ─────────────────────────────

from datetime import date as _date

from app.services.dealbreakers import get_dealbreakers


class _Res:
    def __init__(self, rows): self._rows = rows
    def mappings(self): return self
    def fetchall(self): return self._rows


class _FakeDB:
    """First execute() → recall rows, second → critical-issue rows."""
    def __init__(self, recall_rows, critical_rows=()):
        self.sql: list[str] = []
        self.recall_rows = recall_rows
        self.critical_rows = list(critical_rows)
    def execute(self, stmt, *_a, **_k):
        self.sql.append(str(stmt))
        is_recall_query = "reliability_evidence" in self.sql[-1]
        return _Res(self.recall_rows if is_recall_query else self.critical_rows)


def _recall(source, title, desc=None, month=1):
    return {"source": source, "source_url": "https://example.test/" + title, "severity": "serious",
            "observed_month": _date(2026, month, 1),
            "payload": {"title": title, "description": desc or title},
            "year_start": 2015, "year_end": None}


_CRIT = {"engine": "1.2 PureTech 130", "description": "Correia de distribuição em óleo degrada-se",
         "affected_years": "2014-2022", "fix_cost_estimate": "€900-1500", "source": "Stellantis"}


def test_eu_recall_alone_is_not_a_dealbreaker():
    d = get_dealbreakers(_FakeDB([_recall("eu_safety_gate", "X1: Risco de ferimentos")]), model_id=1)
    assert d["has_dealbreaker"] is False
    assert d["recall_count"] == 1
    assert d["recalls"][0]["risk"] == "Risco de ferimentos"


def test_us_recalls_are_never_shown():
    db = _FakeDB([])
    d = get_dealbreakers(db, model_id=1)
    assert "us_recalls" not in d
    # Filtered in SQL: only EU sources are selected.
    assert "'eu_safety_gate'" in db.sql[0] and "nhtsa" not in db.sql[0]


def test_critical_known_failure_is_the_dealbreaker():
    d = get_dealbreakers(_FakeDB([], [_CRIT]), model_id=1)
    assert d["has_dealbreaker"] is True
    assert d["critical_issues"][0]["engine"] == "1.2 PureTech 130"


def test_critical_failure_filtered_by_listing_year():
    d = get_dealbreakers(_FakeDB([], [_CRIT]), model_id=1, year=2023)
    assert d["has_dealbreaker"] is False


def test_airbag_inflator_recall_is_priority_and_first():
    rows = [_recall("eu_safety_gate", f"Golf: Risco de ferimentos {i}", month=12) for i in range(7)]
    rows.append(_recall("eu_safety_gate", "Golf: Risco de ferimentos",
                        "O propulsor no airbag do condutor pode deteriorar-se ao longo do tempo.", month=1))
    d = get_dealbreakers(_FakeDB(rows), model_id=1)
    assert d["recall_count"] == 6                # capped
    assert d["recalls"][0]["priority"] is True   # sorted before the cap, never cut
    assert all(not r["priority"] for r in d["recalls"][1:])


def test_airbag_sensor_recall_is_not_priority():
    from app.services.dealbreakers import _is_priority
    assert not _is_priority("Golf: Risco de ferimentos", "O sensor do airbag do passageiro pode falhar.")
    assert _is_priority("X1", "O insuflador do airbag do condutor pode funcionar mal")


def test_long_text_is_clipped_at_a_word():
    from app.services.dealbreakers import _clip
    out = _clip("palavra " * 100, 50)
    assert out.endswith("…") and len(out) <= 51 and "palav…" not in out
    assert _clip("curto", 50) == "curto"


def test_cards_skip_recalls():
    db = _FakeDB([_recall("eu_safety_gate", "anything")], [_CRIT])
    d = get_dealbreakers(db, model_id=1, include_recalls=False)
    assert d["recall_count"] == 0 and d["has_dealbreaker"] is True
    assert not any("reliability_evidence" in s for s in db.sql)


def test_nhtsa_component_code_becomes_readable_title():
    from app.services.dealbreakers import _component_title
    assert _component_title("SERVICE BRAKES, HYDRAULIC:POWER ASSIST:ELECTRIC") == "Recall: service brakes"
    assert _component_title(None) is None
