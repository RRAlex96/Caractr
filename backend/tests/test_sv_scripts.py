"""
The Standvirtual maintenance scripts against pages of the site's November 2026
format (tests/fixtures/sv_search_2026_11.json, trimmed from real pages):

- scripts/refresh_sv_taxonomy.py reads the filter tree (filters.states), whose
  filter ids did not change: filter_enum_make / _model / _engine_code;
- scripts/audit_sv_slugs.py reads the filters applied to a search, where make
  and model are now one make_model_engine_code = "make|model".
"""
import json
import os
import re

import pytest

from scripts import audit_sv_slugs, refresh_sv_taxonomy

FIXTURE = os.path.join(os.path.dirname(__file__), "fixtures", "sv_search_2026_11.json")


@pytest.fixture(scope="module")
def fx() -> dict:
    with open(FIXTURE, encoding="utf-8") as fh:
        return json.load(fh)


def _page(*payloads: dict) -> str:
    """A results page as the site serves it: each urqlState entry holds its
    payload as a JSON string."""
    urql = {str(-1000 - i): {"hasNext": False, "data": json.dumps(p)} for i, p in enumerate(payloads)}
    next_data = {"props": {"pageProps": {"urqlState": urql}}, "page": "/[category]/[...filters]"}
    return f'<html><script id="__NEXT_DATA__" type="application/json">{json.dumps(next_data)}</script></html>'


# --- refresh_sv_taxonomy -----------------------------------------------------

def test_taxonomy_reads_the_november_2026_filter_tree(fx):
    html = _page({"advertSearch": fx["searches"]["/carros/peugeot"]}, {"filters": fx["filters"]})
    makes, models, series = refresh_sv_taxonomy._taxonomy(refresh_sv_taxonomy._filter_states(html))
    assert makes == {"bmw": "BMW", "byd": "BYD", "peugeot": "Peugeot"}
    assert models == {"bmw": {"serie-1": "Série 1", "serie-3": "Série 3"},
                      "peugeot": {"208": "208", "308": "308", "e-208": "e-208"}}
    assert series == {"bmw": {"serie-3": {"318": "318", "320": "320"}}}


def test_taxonomy_ignores_other_filters(fx):
    # The fuel filter has values but no make condition: not a make, model or series.
    assert any(s["filterId"] == "filter_enum_fuel_type" for s in fx["filters"]["states"])
    makes, models, series = refresh_sv_taxonomy._taxonomy(fx["filters"]["states"])
    assert "filter_enum_fuel_type" not in json.dumps([makes, models, series])


def test_taxonomy_page_without_filters_stops():
    with pytest.raises(SystemExit):
        refresh_sv_taxonomy._filter_states("<html>no next data</html>")
    with pytest.raises(SystemExit):
        refresh_sv_taxonomy._filter_states(_page({"advertSearch": {"totalCount": 0}}))


def test_generated_files_keep_their_format(fx):
    makes, models, series = refresh_sv_taxonomy._taxonomy(fx["filters"]["states"])
    text = refresh_sv_taxonomy.render_models(makes, models, "2026-11-17")
    assert "them on 2026-11-17 (3 makes, 5 models)." in text
    assert '    "bmw": "BMW",\n' in text
    assert '    "bmw": {"serie-1": "Série 1", "serie-3": "Série 3"},\n' in text
    ns = {}
    exec(text, ns)
    assert ns["SV_MAKES"] == makes and ns["SV_MODELS"] == models

    text = refresh_sv_taxonomy.render_series(series, models, "2026-11-17")
    assert "on 2026-11-17 (1 series, 2 sub-models)." in text
    assert '        "serie-3": ("Série 3", {"318": "318", "320": "320"}),\n' in text
    ns = {}
    exec(text, ns)
    assert ns["SV_SERIES"] == {"bmw": {"serie-3": ("Série 3", {"318": "318", "320": "320"})}}


def test_committed_data_files_parse_with_the_same_renderer():
    # The committed snapshot must round-trip through the renderer unchanged
    # (bar line endings): the generated format did not move.
    from app.scrapers.sv_models_data import SV_MAKES, SV_MODELS
    from app.scrapers.sv_series_data import SV_SERIES
    here = os.path.join(os.path.dirname(__file__), "..", "app", "scrapers")
    for name, render in (
        ("sv_models_data.py", lambda d: refresh_sv_taxonomy.render_models(SV_MAKES, SV_MODELS, d)),
        ("sv_series_data.py", lambda d: refresh_sv_taxonomy.render_series(
            {mk: {s: v for s, (_, v) in ser.items()} for mk, ser in SV_SERIES.items()}, SV_MODELS, d)),
    ):
        with open(os.path.join(here, name), encoding="utf-8") as fh:
            committed = fh.read().replace("\r\n", "\n")
        date = re.search(r"\bon (\d{4}-\d\d-\d\d) \(", committed).group(1)
        assert render(date) == committed, name


# --- audit_sv_slugs ----------------------------------------------------------

@pytest.mark.parametrize("path, make, model, result", [
    ("/carros/byd/atto-3", "byd", "atto-3", "scoped"),
    # A sub-model: the site applies "make|series|sub-model".
    ("/carros/bmw/320?search[filter_enum_engine_code]=serie-3", "bmw", "serie-3", "scoped"),
    ("/carros/peugeot", "peugeot", None, "unscoped"),
    # A model slug the site does not know is dropped silently: make only.
    ("/carros/peugeot/xyzzy", "peugeot", None, "unscoped"),
])
def test_audit_reads_the_combined_make_model_filter(fx, path, make, model, result):
    row = audit_sv_slugs._scope_row(fx["searches"][path])
    assert (row["applied_make"], row["applied_model"], row["result"]) == (make, model, result)
    assert row["total"] == fx["searches"][path]["totalCount"]


def test_audit_counts_the_models_on_the_page(fx):
    row = audit_sv_slugs._scope_row(fx["searches"]["/carros/byd/atto-3"])
    assert row["models_on_page"] == {"atto-3": 2}


def test_audit_still_reads_the_old_separate_filters():
    old = {"totalCount": 12, "edges": [], "appliedFilters": [
        {"name": "category_id", "value": "29"},
        {"name": "filter_enum_make", "value": "renault"},
        {"name": "filter_enum_model", "value": "clio"}]}
    row = audit_sv_slugs._scope_row(old)
    assert (row["applied_make"], row["applied_model"], row["result"]) == ("renault", "clio", "scoped")
