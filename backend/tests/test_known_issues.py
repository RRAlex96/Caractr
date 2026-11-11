"""Curated engine-issue list: the seed file stays valid, and the matcher is
precise (a wrong red flag is worse than a missing one)."""
from app.services.known_issues import (
    applies_to_year, load_issues, matches_engine, validate, years_overlap,
)

ALL = {i["id"]: i for i in load_issues(include_drafts=True)}


def test_seed_file_is_valid():
    assert ALL, "seed file has no issues"
    errors = {k: validate(v) for k, v in ALL.items() if validate(v)}
    assert not errors, errors


def test_ids_are_unique():
    from app.services.known_issues import SEED_PATH
    import json
    ids = [i["id"] for i in json.loads(SEED_PATH.read_text(encoding="utf-8"))["issues"]]
    assert len(ids) == len(set(ids))


def test_drafts_never_reach_the_product():
    assert all(i["status"] == "approved" for i in load_issues())


def test_critico_without_authoritative_source_is_rejected():
    bad = dict(ALL["psa-puretech-12-belt"])
    bad["sources"] = [{"label": "x", "url": "https://forum.example", "kind": "forum"}]
    assert any("critico" in e for e in validate(bad))


def test_puretech_matches_catalogue_label():
    i = ALL["psa-puretech-12-belt"]
    assert matches_engine(i, brand="Peugeot", model="3008", label="1.2 PureTech 130 EAT8",
                          fuel="gasolina", displacement_cc=1199)
    # The BlueHDi diesel in the same car is not the PureTech
    assert not matches_engine(i, brand="Peugeot", model="3008", label="1.5 BlueHDi 130 EAT8",
                              fuel="diesel", displacement_cc=1499)
    # Plug-in hybrid 1.6 is not the PureTech 1.2
    assert not matches_engine(i, brand="Peugeot", model="3008", label="1.6 Hybrid 225 PHEV",
                              fuel="hibrido", displacement_cc=1598)


def test_brand_must_match():
    i = ALL["ford-ecoboost-10-wetbelt"]
    assert matches_engine(i, brand="Ford", label="1.0 EcoBoost 125", fuel="gasolina", displacement_cc=999)
    assert not matches_engine(i, brand="Volkswagen", label="1.0 TSI 110", fuel="gasolina", displacement_cc=999)


def test_unknown_attribute_fails_the_rule_that_needs_it():
    i = ALL["psa-puretech-12-belt"]
    assert not matches_engine(i, brand="Peugeot", label="1.2 PureTech", fuel="gasolina", displacement_cc=None)


def test_dq200_needs_low_torque_seven_speed():
    i = ALL["vag-dq200-dsg7"]
    assert matches_engine(i, brand="Volkswagen", label="1.4 TSI 122 DSG", transmission="auto 7", torque_nm=200)
    # DQ381/DQ250 territory: more torque, wet clutch
    assert not matches_engine(i, brand="Volkswagen", label="2.0 TDI 150 DSG", transmission="auto 7", torque_nm=340)
    assert not matches_engine(i, brand="Volkswagen", label="1.0 TSI 110", transmission="manual 6", torque_nm=200)


def test_years_gate_new_generations_out():
    n47 = ALL["bmw-n47-chain"]
    # The current 320d (B47, 2019+) shares cc and fuel with the N47 — years keep it out
    assert matches_engine(n47, brand="BMW", label="320d 190cv", fuel="diesel", displacement_cc=1995)
    assert not years_overlap(n47, 2019, None)
    assert years_overlap(n47, 2005, 2012)
    assert applies_to_year(n47, 2009) and not applies_to_year(n47, 2013)
    assert not applies_to_year(n47, None)
