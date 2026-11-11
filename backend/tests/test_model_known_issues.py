"""Model-level known issues (engine_issues) are filtered to the car being
analysed: its production year, and no diesel/petrol mismatch. They used to be
aggregated model-wide — a 2024 Peugeot 208 was told about a PureTech recall
from 2021."""
from app.services.ad_analysis_service import _filter_model_issues


def _row(desc, years=None, sev="alto", fuel="gasolina", cost=None):
    return {"description": desc, "affected_years": years, "severity": sev,
            "fuel_type": fuel, "fix_cost_estimate": cost}


PURETECH = _row("Correia húmida do 1.2 PureTech", "2014-2022", "alto", "gasolina", "€700-1200")
BLUEHDI = _row("Corrente das árvores de cames 1.5 BlueHDi", "2017-2022", "alto", "diesel", "€500-1400")
RATTLES = _row("Ruídos parasitas no tablier", "2019+", "baixo", "gasolina")
OPEN = _row("Bomba de água com fugas", None, "medio", "gasolina", "€300-500")


def test_issue_outside_the_cars_year_is_dropped():
    known, _ = _filter_model_issues([PURETECH], year=2024, fuel="Gasolina")
    assert known is None
    known, _ = _filter_model_issues([PURETECH], year=2018, fuel="Gasolina")
    assert known == "Correia húmida do 1.2 PureTech"


def test_open_ended_range_applies_from_its_start():
    later = _row("Sensor NOx", "2020+", "medio")
    assert _filter_model_issues([later], year=2019, fuel=None)[0] is None
    assert _filter_model_issues([later], year=2023, fuel=None)[0] == "Sensor NOx"


def test_unknown_or_unparseable_years_never_exclude():
    weird = _row("Embraiagem", "primeiras unidades", "medio")
    known, _ = _filter_model_issues([OPEN, weird], year=2024, fuel="Gasolina")
    assert known == "Bomba de água com fugas; Embraiagem"


def test_unknown_listing_year_keeps_everything():
    known, _ = _filter_model_issues([PURETECH, OPEN], year=None, fuel=None)
    assert "PureTech" in known and "Bomba de água" in known


def test_diesel_issue_dropped_for_petrol_car_and_vice_versa():
    assert _filter_model_issues([PURETECH, BLUEHDI], year=2019, fuel="Gasolina")[0] == PURETECH["description"]
    assert _filter_model_issues([PURETECH, BLUEHDI], year=2019, fuel="Diesel")[0] == BLUEHDI["description"]


def test_hybrid_and_lpg_are_petrol_family_never_split_on_fuel():
    for fuel in ("Híbrido (Gasolina)", "Híbrido Plug-In", "GPL"):
        assert _filter_model_issues([PURETECH], year=2019, fuel=fuel)[0] == PURETECH["description"], fuel


def test_unknown_fuel_keeps_both():
    known, _ = _filter_model_issues([PURETECH, BLUEHDI], year=2019, fuel=None)
    assert "PureTech" in known and "BlueHDi" in known


def test_most_serious_first_and_costs_follow_kept_issues():
    crit = _row("Motor gripa", "2015-2020", "critico", "gasolina", "€4000")
    known, costs = _filter_model_issues([OPEN, PURETECH, crit], year=2018, fuel="Gasolina")
    assert known.split("; ")[0] == "Motor gripa"           # the rule engine quotes the first one
    assert costs == "€4000; €700-1200; €300-500"
    _, costs = _filter_model_issues([PURETECH, BLUEHDI], year=2019, fuel="Gasolina")
    assert costs == "€700-1200"                             # the dropped diesel issue's cost goes too


def test_duplicates_across_engines_collapse():
    known, _ = _filter_model_issues([PURETECH, dict(PURETECH)], year=2018, fuel="Gasolina")
    assert known == PURETECH["description"]


def test_baixo_rows_are_not_selected_upstream_but_harmless_here():
    # The SQL only selects alto/critico/medio; if one slips through it sorts last.
    known, _ = _filter_model_issues([RATTLES, PURETECH], year=2020, fuel="Gasolina")
    assert known.split("; ")[0] == PURETECH["description"]
