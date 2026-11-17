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
    assert matches_engine(i, brand="Volkswagen", label="1.4 TSI 122 DSG", transmission="auto 7",
                          torque_nm=200, displacement_cc=1395)
    # DQ381/DQ250 territory: more torque, wet clutch
    assert not matches_engine(i, brand="Volkswagen", label="2.0 TDI 150 DSG", transmission="auto 7",
                              torque_nm=340, displacement_cc=1968)
    assert not matches_engine(i, brand="Volkswagen", label="1.0 TSI 110", transmission="manual 6",
                              torque_nm=200, displacement_cc=999)


def test_years_gate_new_generations_out():
    n47 = ALL["bmw-n47-chain"]
    lo, hi = n47["years"]          # 2007-2014 after the audit of 2026-11-14
    assert matches_engine(n47, brand="BMW", label="320d 184cv", fuel="diesel", displacement_cc=1995)
    # The B47 that replaced it shares cc and fuel: its power outputs (190 cv)
    # are excluded by the rule, and its years by the years.
    assert not matches_engine(n47, brand="BMW", label="320d 190cv", fuel="diesel", displacement_cc=1995)
    assert not years_overlap(n47, 2019, None)
    assert years_overlap(n47, 2005, 2012)
    assert applies_to_year(n47, 2009) and not applies_to_year(n47, hi + 1)
    assert not applies_to_year(n47, None)


# ── Matching a scraped listing (ad analysis) ────────────────────────────────

from app.services.dealbreakers import merge_known_issues  # noqa: E402
from app.services.known_issues import (  # noqa: E402
    listing_engine_profile, match_listing, normalize_fuel, to_payload,
)

DRAFTS = list(ALL.values())


def _ids(listing):
    return [i["id"] for i in match_listing(listing, issues=DRAFTS)]


def _listing(**kw):
    base = {"brand_name": "Peugeot", "model_name": "208", "year": 2018, "fuel_type": "Gasolina",
            "version": "1.2 PureTech Allure", "engine_displacement_cc": None,
            "engine_power_hp": 110, "transmission": "Manual", "description": ""}
    return {**base, **kw}


def test_fuel_labels_from_marketplaces_normalise():
    assert normalize_fuel("Diesel") == "diesel"
    assert normalize_fuel("Gasóleo") == "diesel"
    assert normalize_fuel("Híbrido (Gasolina)") == "hibrido"
    assert normalize_fuel("Híbrido Plug-In") == "hibrido"
    assert normalize_fuel("Gasolina") == "gasolina"
    assert normalize_fuel(None) == ""


def test_puretech_208_2018_is_flagged_red():
    assert _ids(_listing()) == ["psa-puretech-12-belt"]
    assert match_listing(_listing(), issues=DRAFTS)[0]["severity"] == "critico"


def test_exact_cc_from_spec_sheet_also_matches():
    assert _ids(_listing(version="Allure", engine_displacement_cc=1199)) == ["psa-puretech-12-belt"]


def test_year_outside_the_affected_range_is_not_flagged():
    # PureTech 1.2: 2012-2022 after the audit of 2026-11-14 (the atmospheric
    # 1.2 from 2012 has the same wet belt)
    lo, hi = ALL["psa-puretech-12-belt"]["years"]
    assert _ids(_listing(year=hi + 2)) == []
    assert _ids(_listing(year=lo - 1)) == []


def test_no_year_means_no_flag():
    assert _ids(_listing(year=None)) == []


def test_hybrid_with_chain_is_not_the_wet_belt_puretech():
    assert _ids(_listing(year=2022, fuel_type="Híbrido (Gasolina)", version="1.2 Hybrid 136 e-DCS6")) == []


def test_engine_unknown_means_no_flag():
    # No version, no cc, nothing in the description: we don't guess.
    assert _ids(_listing(version="", description="Carro impecável, revisões na marca.")) == []


def test_description_numbers_that_are_not_engines_are_ignored():
    l = _listing(brand_name="Renault", model_name="Clio", year=2006, fuel_type="Diesel",
                 version="", description="Oferta de 1.5 anos de garantia. Motor dCi muito económico.")
    assert l and listing_engine_profile(l)["displacement_cc"] is None
    assert _ids(l) == []
    l2 = {**l, "description": "Motor 1.5 dCi de 86cv, revisões feitas."}
    assert _ids(l2) == ["renault-k9k-bearings"]


def test_bluehdi_2019_gets_the_camchain_recall_issue():
    l = _listing(model_name="3008", year=2019, fuel_type="Diesel", version="1.5 BlueHDi 130 EAT8 GT Line")
    assert _ids(l) == ["psa-bluehdi-15-camchain"]


def test_dq200_from_listing_text_uses_power_as_torque_stand_in():
    golf = {"brand_name": "Volkswagen", "model_name": "Golf", "year": 2011, "fuel_type": "Gasolina",
            "version": "1.4 TSI DSG Highline", "engine_power_hp": 122, "transmission": "Automática",
            "description": ""}
    ids = _ids(golf)
    assert "vag-dq200-dsg7" in ids and "vw-ea111-tsi-chain" in ids
    # Red (DQ200) sorts before amber (EA111)
    assert ids[0] == "vag-dq200-dsg7"
    # A 6-speed DSG (DQ250) is a different gearbox
    assert "vag-dq200-dsg7" not in _ids({**golf, "version": "1.4 TSI DSG6"})
    # 2.0 TDI DSG is never the DQ200
    assert "vag-dq200-dsg7" not in _ids({**golf, "fuel_type": "Diesel", "version": "2.0 TDI DSG",
                                          "engine_power_hp": 140})


def test_multiline_description_still_matches_lookahead_rules():
    mini = {"brand_name": "MINI", "model_name": "Cooper", "year": 2009, "fuel_type": "Gasolina",
            "version": "", "engine_displacement_cc": 1598,
            "description": "Vendo MINI\nMotor 1.6\nCooper S em bom estado"}
    assert "prince-16-chain" in _ids(mini)


def test_merge_puts_curated_red_first_and_amber_in_watch_items():
    golf = match_listing({"brand_name": "Volkswagen", "model_name": "Golf", "year": 2011,
                          "fuel_type": "Gasolina", "version": "1.4 TSI DSG", "engine_power_hp": 122},
                         issues=DRAFTS)
    existing = {"has_dealbreaker": False, "recall_count": 1, "critical_issue_count": 0,
                "recalls": [{"title": "r"}], "critical_issues": []}
    out = merge_known_issues(existing, golf)
    assert out["has_dealbreaker"] is True
    assert out["critical_issues"][0]["id"] == "vag-dq200-dsg7"
    assert [w["id"] for w in out["watch_items"]] == ["vw-ea111-tsi-chain"]
    assert out["recalls"] == [{"title": "r"}]   # recalls untouched
    assert merge_known_issues(None, [])["has_dealbreaker"] is False


def test_payload_shape_for_frontend():
    p = to_payload(ALL["psa-puretech-12-belt"])
    assert p["curated"] and p["engine"] and p["problem"] and p["check"]
    lo, hi = ALL["psa-puretech-12-belt"]["years"]
    assert p["affected_years"] == f"{lo}–{hi}"
    assert "preventivo" in p["fix_cost_estimate"] and "se falhar" in p["fix_cost_estimate"]
    assert all(s["url"].startswith("https://") for s in p["sources"])


def test_exact_cc_alone_only_counts_where_it_is_unique():
    # Nissan Micra 1.2 atmosférico (HR12DE, 1198 cc) is NOT the 1.2 DIG-T —
    # the TCe entry doesn't opt into exact_cc_suffices, so the name is required.
    micra = {"brand_name": "Nissan", "model_name": "Micra", "year": 2014, "fuel_type": "Gasolina",
             "version": "Acenta", "engine_displacement_cc": 1198, "description": ""}
    assert _ids(micra) == []
    assert _ids({**micra, "model_name": "Juke", "version": "1.2 DIG-T Tekna"}) == ["renault-tce12-oil"]


def test_ad_analysis_attaches_matches_and_briefs_the_llm():
    from app.services import ad_analysis_service as svc
    listing = _listing()
    base = {"dealbreakers": {"has_dealbreaker": False, "recall_count": 0, "critical_issue_count": 0,
                             "recalls": [], "critical_issues": []}}
    orig = svc.match_listing
    svc.match_listing = lambda l: match_listing(l, issues=DRAFTS)
    try:
        payload, matched = svc._known_issue_dealbreakers(base, listing)
        assert payload["has_dealbreaker"] and [i["id"] for i in matched] == ["psa-puretech-12-belt"]
        note = svc._known_issues_prompt_note(matched)
        assert "FALHA GRAVE" in note and "1.2 PureTech" in note
        # Nothing matched → the model's own payload is returned untouched
        same, none = svc._known_issue_dealbreakers(base, _listing(year=2024))
        assert same is base["dealbreakers"] and none == []
        # A matcher crash never breaks an analysis
        svc.match_listing = lambda l: (_ for _ in ()).throw(RuntimeError("boom"))
        same, none = svc._known_issue_dealbreakers(base, listing)
        assert same is base["dealbreakers"] and none == []
    finally:
        svc.match_listing = orig


def test_m32_flags_six_speed_opels_but_not_other_gearboxes():
    astra = {"brand_name": "Opel", "model_name": "Astra", "year": 2008, "fuel_type": "Diesel",
             "version": "1.7 CDTi Cosmo", "engine_displacement_cc": 1686, "engine_power_hp": 125,
             "transmission": "Manual", "description": ""}
    assert "opel-m32-bearings" in _ids(astra)
    # An ad that says it is the 5-speed is not the M32
    assert "opel-m32-bearings" not in _ids({**astra, "version": "1.7 CDTI Cosmo M5"})
    # The 160 cv 2.0 CDTi has the F40 gearbox: excluded by power even when the text doesn't say it
    insignia = {**astra, "model_name": "Insignia", "version": "2.0 CDTi Cosmo",
                "engine_displacement_cc": 1956, "engine_power_hp": 160}
    assert "opel-m32-bearings" not in _ids(insignia)
    assert "opel-m32-bearings" in _ids({**insignia, "engine_power_hp": 130})
    # Fiat 1.3 Multijet ("70 JTD") is a 5-speed small diesel
    punto = {**astra, "brand_name": "Fiat", "model_name": "Punto", "version": "70 JTD Multijet",
             "engine_displacement_cc": 1248, "engine_power_hp": 70}
    assert "opel-m32-bearings" not in _ids(punto)
    # Old 2.0 DTi (Zafira A) has another gearbox
    assert "opel-m32-bearings" not in _ids({**astra, "model_name": "Zafira", "year": 2004,
                                             "version": "2.0 DTi Elegance", "engine_displacement_cc": 1995})


def test_xtronic_only_for_j11_t32_automatics():
    q = {"brand_name": "Nissan", "model_name": "Qashqai", "year": 2016, "fuel_type": "Gasolina",
         "version": "1.2 DIG-T N-Connecta", "engine_displacement_cc": 1197, "engine_power_hp": 115,
         "transmission": "Automática", "description": ""}
    # (the 1.2 DIG-T engine itself also carries the TCe 1.2 entry)
    assert "nissan-xtronic-cvt" in _ids(q)
    assert "nissan-xtronic-cvt" not in _ids({**q, "transmission": "Manual"})
    # The 2019+ automatics are DCT, and 2013 is still the J10
    assert "nissan-xtronic-cvt" not in _ids({**q, "year": 2019, "version": "1.3 DIG-T N-Connecta DCT"})
    assert "nissan-xtronic-cvt" not in _ids({**q, "year": 2013})


def test_exclude_power_band_needs_known_power():
    from app.services.known_issues import matches_engine
    i = ALL["opel-m32-bearings"]
    kw = dict(brand="Opel", model="Insignia", label="2.0 CDTi", fuel="diesel", displacement_cc=1956,
              transmission="manual 6")
    assert not matches_engine(i, power_hp=160, **kw)
    assert matches_engine(i, power_hp=None, **kw)


# ── BMW codes written apart (Standvirtual: "20 d xDrive", "d Pack M" + slug "320") ──

def _bmw(**kw):
    base = {"brand_name": "BMW", "model_name": "X3", "year": 2012, "fuel_type": "Diesel",
            "version": "20 d xDrive Pack M Auto", "engine_displacement_cc": 1995,
            "engine_power_hp": 184, "transmission": "Automática", "description": "",
            "sv_model_slug": "x3"}
    return {**base, **kw}


def test_split_20_d_xdrive_matches_n47():
    assert "bmw-n47-chain" in _ids(_bmw())
    assert "bmw-n47-chain" in _ids(_bmw(model_name="X1", version="18 d sDrive Line Sport",
                                        engine_power_hp=143, sv_model_slug="x1"))


def test_split_code_keeps_the_power_exclusion():
    # The 190 cv 20d is the B47 — excluded by the entry through the power,
    # which a listing states only in its spec sheet.
    assert "bmw-n47-chain" not in _ids(_bmw(version="20 d xDrive", engine_power_hp=190, year=2014))
    assert "bmw-n47-chain" not in _ids(_bmw(model_name="X5", version="25 d sDrive",
                                            engine_power_hp=231, year=2014, sv_model_slug="x5"))


def test_series_number_from_the_model_slug():
    s3 = _bmw(model_name="Série 3", year=2010, version="d Pack M", engine_power_hp=184,
              transmission="Manual", sv_model_slug="320")
    assert "bmw-n47-chain" in _ids(s3)
    assert "bmw-n47-chain" in _ids({**s3, "version": "320 d"})
    assert "bmw-n47-chain" in _ids({**s3, "sv_model_slug": "420-gran-coupe", "year": 2014})
    assert "bmw-n47-chain" in _ids({**s3, "version": "dA Pack M", "sv_model_slug": "520", "year": 2012})
    # No number to read: no flag (precision over recall)
    assert "bmw-n47-chain" not in _ids({**s3, "sv_model_slug": None})
    assert "bmw-n47-chain" not in _ids({**s3, "sv_model_slug": "serie-3"})


def test_split_petrol_code_matches_n20():
    x1 = _bmw(model_name="X1", fuel_type="Gasolina", year=2013, version="20 i xDrive",
              engine_displacement_cc=1997, engine_power_hp=184, sv_model_slug="x1")
    assert "bmw-n20-chain-guide" in _ids(x1)
    assert "bmw-n20-chain-guide" in _ids({**x1, "model_name": "Série 3", "version": "i Line Sport",
                                          "sv_model_slug": "320"})


def test_litre_figures_and_years_never_become_codes():
    p = listing_engine_profile
    for text in ("1.5 d", "2.0 i Sport", "2,0 d", "2018 d", "20 dias de garantia", "130 dCi",
                 "revisão aos 20 da marca"):
        assert p({"version": text})["label"] == text
    # A bare "d" version with a 4-digit or non-numeric slug gets nothing joined
    assert p({"version": "d Pack M", "sv_model_slug": "3008"})["label"] == "d Pack M"
    assert p({"version": "d Pack M", "sv_model_slug": "320--318"})["label"] == "d Pack M"
    # The slug joins only a version that starts with the letter, never free text
    assert p({"version": "Pack M", "description": "d", "sv_model_slug": "320"})["label"] == "Pack M d"
    assert p({"version": "dA", "sv_model_slug": "520"})["label"] == "dA | 520dA"


def test_non_bmw_text_unchanged_and_power_kept_apart():
    p = listing_engine_profile
    assert p({"version": "1.2 PureTech Allure"})["label"] == "1.2 PureTech Allure"
    assert p({"version": "1.6 THP"})["label"] == "1.6 THP"
    # Power goes at the end, apart from the text: "1.6" + "150cv" can't read as "1.6 150"
    assert p({"version": "1.6", "engine_power_hp": 150})["label"] == "1.6 | 150cv"
    # A Mercedes "220 d" joins too, but no Mercedes entry reads "220d"
    assert _ids({"brand_name": "Mercedes-Benz", "model_name": "Classe C", "year": 2010,
                 "fuel_type": "Diesel", "version": "220 d", "engine_displacement_cc": 2143,
                 "engine_power_hp": 170, "transmission": "Manual", "description": ""}) == []


def test_power_never_reads_as_part_of_the_gearbox():
    # The matcher reads "transmission + label": a power in front of the label
    # turned "1.0 Groove Auto" + "75cv" into "auto 7" (the DQ200's "auto 7").
    up = {"brand_name": "Volkswagen", "model_name": "up!", "year": 2013, "fuel_type": "Gasolina",
          "version": "1.0 Groove Auto", "engine_displacement_cc": 999, "engine_power_hp": 75,
          "transmission": "Automática", "description": ""}
    assert "vag-dq200-dsg7" not in _ids(up)
