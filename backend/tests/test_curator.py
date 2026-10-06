"""The Curator agent's deterministic guard — the gate before anything hits the DB."""
from app.services.curator_agent import validate_draft


def _good():
    return {
        "reliability_score": 7.5, "maintenance_cost_year": 900, "year_start": 2015,
        "confidence": 0.8, "known_issues": [{"severity": "medio", "description": "x"}],
    }


def test_valid_draft_passes():
    ok, issues = validate_draft(_good())
    assert ok and issues == []


def test_bad_score_rejected():
    d = _good(); d["reliability_score"] = 42
    ok, issues = validate_draft(d)
    assert not ok and any("reliability_score" in i for i in issues)


def test_bad_confidence_rejected():
    d = _good(); d["confidence"] = 5
    assert validate_draft(d)[0] is False


def test_implausible_maintenance_rejected():
    d = _good(); d["maintenance_cost_year"] = 99999
    assert validate_draft(d)[0] is False


def test_known_issues_must_be_list():
    d = _good(); d["known_issues"] = "lots"
    assert validate_draft(d)[0] is False
