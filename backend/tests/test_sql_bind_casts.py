"""
Regression guard: SQLAlchemy text() silently refuses to bind a parameter that
is immediately followed by a Postgres `::` cast — `:payload::jsonb` is sent to
the DB unbound and fails with `syntax error at or near ":"`. This bug broke
every recall scraper and the curator's save path. Use CAST(:x AS type).
"""
import pathlib
import re

from sqlalchemy import text

APP = pathlib.Path(__file__).resolve().parent.parent / "app"
BIND_THEN_CAST = re.compile(r"(?<![:\w]):[A-Za-z_]\w*::")


def test_sqlalchemy_does_not_bind_param_before_double_colon_cast():
    # Documents *why* the pattern is banned.
    assert list(text("SELECT :a::jsonb")._bindparams) == []
    assert list(text("SELECT CAST(:a AS jsonb)")._bindparams) == ["a"]


def test_no_bind_param_followed_by_cast_in_app_code():
    offenders = []
    for f in APP.rglob("*.py"):
        for i, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            if BIND_THEN_CAST.search(line):
                offenders.append(f"{f.relative_to(APP.parent)}:{i}: {line.strip()}")
    assert not offenders, "Use CAST(:x AS type) instead of :x::type\n" + "\n".join(offenders)
