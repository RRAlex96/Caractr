"""
Recall → generation matcher. Every 'must NOT match' case below is a real false
positive found when auditing the first live Safety Gate ingest (Nov 2026).
"""
import pytest

from app.scrapers.model_match import best_generation, name_match, norm_model


@pytest.mark.parametrize("db_model, alert_model", [
    ("Classe A", "S-Klasse"),
    ("ID.3", "ID.4"),
    ("EV3", "EV5"),
    ("Ioniq 5", "IONIQ6 (CE)"),
    ("S-Max", "C-MAX"),
    ("Tourneo Connect", "Transit Connect"),
    ("Discovery Sport", "Discovery 3"),
    ("Discovery Sport", "Discovery"),
    ("Range Rover Velar", "Range Rover"),
    ("Polo", "ID.Polo"),
    ("500", "500X"),
    ("A3", "A30 concept"),
])
def test_known_false_positives_do_not_match(db_model, alert_model):
    assert not name_match(db_model, alert_model)


@pytest.mark.parametrize("db_model, alert_model", [
    ("Golf", "Golf Variant 7"),
    ("Kuga", "Kuga"),
    ("Q5", "Q5"),
    ("ID.3", "ID.3"),
    ("Range Rover Sport", "Range Rover Sport (LS)"),
    ("Classe A", "A-Klasse"),
    ("Classe A", "A-Class"),
    ("CLA", "CLA-Klasse"),
    ("GLE", "GLE-Class"),
    ("i30", "i30 & i30N (PDe & PDeN)"),
    ("Model 3", "Model 3"),
])
def test_true_matches_still_match(db_model, alert_model):
    assert name_match(db_model, alert_model)


def test_mercedes_class_normalisation():
    assert norm_model("A-Klasse") == norm_model("Classe A") == norm_model("A-Class") == "a"
    assert norm_model("S-Klasse") != norm_model("Classe A")


def _rows(*gens):
    return [{"id": i, "model_name": n, "year_start": s, "year_end": e}
            for i, (n, s, e) in enumerate(gens, 1)]


def test_year_mismatch_rejects_wrong_generation():
    # Astra H airbag recall (2005-2010) must not land on an Astra K (2015-2021).
    rows = _rows(("Astra", 2015, 2021))
    assert best_generation(rows, "Astra H", list(range(2005, 2011))) is None


def test_year_overlap_picks_the_right_generation():
    rows = _rows(("Kodiaq", 2016, 2023), ("Kodiaq", 2024, None))
    assert best_generation(rows, "Kodiaq I", [2016, 2017]) == 1
    assert best_generation(rows, "Kodiaq", [2025]) == 2


def test_unknown_years_still_match_on_name():
    rows = _rows(("Kuga", 2019, None))
    assert best_generation(rows, "Kuga", []) == 1


def test_more_specific_model_wins():
    rows = _rows(("Range Rover", 2013, None), ("Range Rover Sport", 2013, None))
    assert best_generation(rows, "Range Rover Sport (LS)", []) == 2


def test_shared_range_picks_generation_with_most_production_years():
    # "Octavia III, ..., Kodiaq I" — one shared batch range 2015-2024.
    yrs = list(range(2015, 2025))
    octavia = _rows(("Octavia", 2012, 2019), ("Octavia", 2020, None))
    kodiaq = _rows(("Kodiaq", 2016, 2023), ("Kodiaq", 2024, None))
    assert best_generation(octavia, "Octavia III", yrs) == 1   # tie → where production started
    assert best_generation(kodiaq, "Kodiaq I", yrs) == 1       # 8 years vs 1


def test_no_tolerance_on_exact_production_dates():
    # Astra H built until March 2014 is not a 2015+ Astra K.
    assert best_generation(_rows(("Astra", 2015, 2021)), "Astra H", list(range(2005, 2015))) is None


def _grows(*gens):
    return [{"id": i, "model_name": m, "gen_name": g, "year_start": s, "year_end": e}
            for i, (m, g, s, e) in enumerate(gens, 1)]


def test_designator_beats_year_count():
    # 'Astra L' recall with a shared 2017-2023 range must go to the Astra L, not the K.
    rows = _grows(("Astra", "Astra K", 2015, 2021), ("Astra", "Astra L", 2021, None))
    assert best_generation(rows, "Astra L", list(range(2017, 2024))) == 2


def test_designators_normalise_roman_and_mk():
    from app.scrapers.model_match import designators
    assert designators("Golf VII", "Golf") == designators("Mk7", "Golf") == {"7"}
    assert designators("Octavia III", "Octavia") == {"3"}
    assert designators("3 Series (F30)", "Série 3") >= {"f30"}


def test_designator_still_needs_year_overlap():
    rows = _grows(("Astra", "Astra L", 2021, None))
    assert best_generation(rows, "Astra L", [2010, 2011]) is None


def test_no_designator_falls_back_to_years():
    rows = _grows(("Golf", "Mk7", 2012, 2019), ("Golf", "Mk8", 2020, None))
    assert best_generation(rows, "Golf", [2021, 2022]) == 2


def test_convertible_variants_do_not_match_non_convertible_models():
    assert not name_match("A4", "A4 Cabrio")
    assert not name_match("Golf", "Golf Cabriolet")
    assert name_match("Golf", "Golf Variant 7")          # estates share the generation
    assert name_match("Tiguan", "Tiguan Allspace")
    assert name_match("MX-5 Roadster", "MX-5 Roadster")  # a convertible model still matches itself
