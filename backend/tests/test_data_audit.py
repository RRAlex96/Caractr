"""The data audit (app/services/data_audit.py) and the reference files it relies on.

No database here: the checks' SQL runs against a real database in the CI job
"Database · build from seeds". These tests cover the scoring and the
consistency of the hand-written reference files.
"""
import glob
import os
import re

import pytest

from app.services.data_audit import (
    CHECKS, DIMENSIONS, Check, Result, _score_rule, as_json, as_markdown, run_audit,
)

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_every_check_has_a_known_dimension_and_one_kind():
    ids = [c.id for c in CHECKS]
    assert len(ids) == len(set(ids))
    for c in CHECKS:
        assert c.dim in DIMENSIONS, c.id
        assert c.severity in ("critical", "major", "minor"), c.id
        assert bool(c.measure) != bool(c.sql), c.id            # a rule or a measure, not both
        assert not c.sql or c.total, c.id                      # a rule says what it is out of


def test_dimension_weights_add_up_to_one():
    assert abs(sum(w for _t, w in DIMENSIONS.values()) - 1.0) < 1e-9


def test_rule_score_falls_faster_the_more_serious_the_rule():
    assert _score_rule(0, 500, "critical") == 1.0
    assert _score_rule(5, 500, "minor") > _score_rule(5, 500, "major") > _score_rule(5, 500, "critical")
    assert _score_rule(100, 100, "critical") == 0.0
    assert _score_rule(3, 0, "major") == 0.0                   # offenders out of nothing: the worst


class _FakeDb:
    """Answers every check: rules find nothing, measures are full, totals are 10."""

    def __init__(self, fail_id=None):
        self.fail_id = fail_id

    def execute(self, sql):
        text_ = str(sql)
        fail = self.fail_id and any(text_ == str(c.sql) for c in CHECKS if c.id == self.fail_id)
        return _Res(fail)

    def rollback(self):
        pass


class _Res:
    def __init__(self, fail):
        self.fail = fail

    def fetchone(self):
        return (10, 10)

    def fetchall(self):
        return [("bad row",)] * 10 if self.fail else []

    def scalar(self):
        return 10


def test_a_clean_database_scores_100_and_a_broken_rule_is_reported():
    audit = run_audit(_FakeDb())
    assert audit["score"] == 100.0 and not audit["critical_failures"]
    broken = run_audit(_FakeDb(fail_id="INT-04"))
    assert broken["critical_failures"] == ["INT-04"]
    assert broken["dimensions"]["integrity"] < 100
    md = as_markdown(broken)
    assert "INT-04" in md and "FAIL" in md and "bad row" in md
    assert as_json(broken)["critical_failures"] == ["INT-04"]


def test_only_some_dimensions_can_be_run():
    audit = run_audit(_FakeDb(), only=["integrity", "safeties"])
    assert set(audit["dimensions"]) == {"integrity", "safeties"}
    assert {r.check.dim for r in audit["results"]} == {"integrity", "safeties"}
    with pytest.raises(ValueError):
        run_audit(_FakeDb(), only=["integrity", "vibes"])


def test_a_check_that_cannot_run_scores_zero_and_says_why():
    class Broken(_FakeDb):
        def execute(self, sql):
            raise RuntimeError('relation "brand_reliability" does not exist\nmore')
    audit = run_audit(Broken(), only=["safeties"])
    r = audit["results"][0]
    assert r.score == 0 and not r.passed and "brand_reliability" in r.error


def test_the_constraints_the_audit_expects_are_created_by_a_migration():
    sql = "\n".join(open(p, encoding="utf-8").read() for p in glob.glob(os.path.join(BACKEND, "seeds", "migration_v6*.sql")))
    saf = next(c for c in CHECKS if c.id == "SAF-01")
    for name in re.findall(r"\('([a-z_]+)'\)", saf.measure):
        assert name in sql, name


# ── the site-model map points at models the catalogue has ────────────────────

@pytest.mark.skipif(not os.getenv("CATALOGUE_DB_URL"),
                    reason="needs a database built from the seeds (CI job: Database · build from seeds)")
def test_every_mapped_site_model_points_at_a_catalogue_model():
    from sqlalchemy import create_engine, text

    from app.scrapers.sv_catalogue_map import OUT_OF_SCOPE, SITE_MODEL_MAP
    with create_engine(os.environ["CATALOGUE_DB_URL"]).connect() as c:
        have = {tuple(r) for r in c.execute(text(
            "SELECT b.name, vm.name FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id"))}
    missing = sorted(set(SITE_MODEL_MAP.values()) - have)
    assert not missing, missing[:10]
    assert not set(SITE_MODEL_MAP) & set(OUT_OF_SCOPE)


def test_the_map_finds_a_body_style_by_the_name_the_site_gives_it():
    from app.scrapers.sv_models import catalogue_target
    assert catalogue_target("Opel", "Insignia Sports Tourer") == ("Opel", "Insignia")
    assert catalogue_target("Citroën", "DS3") == ("DS", "3")
    assert catalogue_target("MG", "ZS") is None               # petrol ZS or ZS EV: the fuel decides
    assert catalogue_target("Renault", "Clio") is None        # named like its catalogue model
