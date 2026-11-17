"""Refined shortlists, powertrain / new-or-used filters and running costs."""
from app.services import energy_costs as ec
from app.services.recommend_service import (
    _build_model_vector, _nudge_profile, apply_hard_constraints, apply_refinement, build_profile, running_cost,
)


def _model(**kw):
    m = {
        "id": 1, "model_name": "T", "brand_name": "Kia", "full_name": "Kia T", "body_type": "suv",
        "segment": "medio", "avg_price": 20000, "min_price": 18000, "max_price": 22000,
        "avg_consumption": 6.0, "avg_reliability": 8.0, "avg_maintenance": 350.0, "best_consumption": 5.5,
        "max_power": 130, "comfort_score": 6, "driving_fun_score": 6, "city_score": 6, "highway_score": 6,
        "family_score": 7, "character_desc": "", "reliability_score": None,
        "engines": [
            {"fuel_type": "gasolina", "plug_in": False, "consumption": 6.0, "power_hp": 120,
             "year_from": 2018, "year_to": 2026, "listings_seen": 100},
            {"fuel_type": "eletrico", "plug_in": False, "consumption": 16.0, "power_hp": 200,
             "year_from": 2020, "year_to": 2026, "listings_seen": 40},
        ],
        "prices_by_year": [{"year": 2021, "p50": 17000, "p10": 15000, "p90": 19000, "n": 30, "as_of": None},
                           {"year": 2026, "p50": 26000, "p10": 25000, "p90": 27000, "n": 10, "as_of": None}],
        "prices_by_fuel": {
            "gasolina": [{"year": 2021, "p50": 15500, "p10": 14000, "p90": 17000, "n": 20, "as_of": None}],
            "eletrico": [{"year": 2021, "p50": 21500, "p10": 20000, "p90": 23000, "n": 8, "as_of": None}],
        },
        "new_prices": {"eletrico": {"year": 2026, "p50": 31000, "p10": 30000, "p90": 32000, "n": 4, "as_of": None}},
    }
    m.update(kw)
    m["vector"] = _build_model_vector(m)
    return m


BASE = {"p1_context": "misto", "p8_budget_min": 15000, "p8_budget_max": 25000}


def test_electric_choice_prices_the_electric_version():
    passed, stretch = apply_hard_constraints([_model()], {**BASE, "powertrain": "eletrico"})
    assert passed and passed[0]["avg_price"] == 21500           # not the mixed 17 000
    assert all(e["fuel_type"] == "eletrico" for e in passed[0]["engines"])


def test_a_model_without_that_powertrain_is_left_out():
    m = _model(engines=[{"fuel_type": "diesel", "consumption": 5, "year_from": 2018, "year_to": 2026}],
               prices_by_fuel={"diesel": [{"year": 2021, "p50": 15000, "p10": 1, "p90": 1, "n": 9, "as_of": None}]})
    passed, stretch = apply_hard_constraints([m], {**BASE, "powertrain": "eletrico"})
    assert not passed and not stretch


def test_new_condition_uses_new_stock_prices_and_respects_budget():
    passed, stretch = apply_hard_constraints([_model()], {**BASE, "p8_budget_max": 35000, "condition": "novo"})
    assert passed and passed[0]["avg_price"] == 31000
    # 31 000 is beyond a 25 000 budget's stretch limit (28 750): no car
    passed, stretch = apply_hard_constraints([_model()], {**BASE, "condition": "novo"})
    assert not passed and not stretch


def test_used_condition_drops_current_year_stock():
    passed, _ = apply_hard_constraints([_model()], {**BASE, "p8_budget_max": 30000, "condition": "usado"})
    assert passed and passed[0]["price_year"] == 2021


def test_refinement_cheaper_scales_budget_and_more_reliable_sets_aversion():
    a, nudges = apply_refinement({**BASE, "p8_budget_range": "15_25"}, ["mais_barato", "mais_fiavel"], "eletrico", "usado")
    assert a["p8_budget_max"] == 20000 and a["p8_budget_min"] == 12000 and "p8_budget_range" not in a
    assert a["p6_aversion"] == "fiabilidade" and a["powertrain"] == "eletrico" and a["condition"] == "usado"
    assert nudges["reliability"] > 0


def test_refinement_takes_at_most_two_wants_and_keeps_a_show_off():
    a, nudges = apply_refinement({**BASE, "p5_presence": "vire_cabecas"},
                                 ["mais_premium", "mais_espaco", "mais_desportivo"], None, None)
    assert a["p5_presence"] == "vire_cabecas"          # "more premium" never lowers presence
    assert "driving" not in nudges                     # third want ignored


def test_nudged_profile_stays_a_distribution():
    profile, _ = build_profile(dict(BASE))
    out = _nudge_profile(profile, {"reliability": 0.3, "status": -1.0})
    assert abs(sum(out.values()) - 1.0) < 1e-3 and min(out.values()) >= 0


def test_running_cost_uses_the_main_engine_of_the_year():
    m = _model(price_year=2019)           # only the petrol engine was on sale in 2019
    rc = running_cost(m, {"p1_context": "estrada"})
    assert rc["fuel"] == "gasolina" and rc["km_month"] == 2000
    assert rc["eur_month"] == round(6.0 * 2000 / 100 * ec.PRICES["gasolina"]["eur"])


def test_electric_running_cost_shows_home_and_public():
    rc = ec.monthly_energy_cost("eletrico", 16.0, 1000)
    assert rc["eur_month_home"] < rc["eur_month"] < rc["eur_month_public"]


def test_no_running_cost_for_plug_in_hybrids_or_unknown_consumption():
    assert ec.monthly_energy_cost("hibrido", 1.5, 1000, plug_in=True) is None
    assert ec.monthly_energy_cost("gasolina", None, 1000) is None


# ── New-car list prices (seeds/new_car_list_prices.json) ──────────────────

from app.services.recommend_service import _list_price_rows, load_list_prices  # noqa: E402


def test_list_price_rows_take_the_cheapest_version_as_desde():
    rows = _list_price_rows([
        {"fuel": "eletrico", "pvp_eur": 34490, "source": "a", "date": "2026-11-16"},
        {"fuel": "eletrico", "pvp_eur": 29990, "source": "b", "date": "2026-11-16"},
        {"fuel": "hibrido", "pvp_eur": 30900, "source": "c", "date": "2026-11-16"},
    ], 2026)
    assert rows["eletrico"]["p50"] == 29990 and rows["eletrico"]["p90"] == 34490
    assert rows["eletrico"]["list_price"] and rows["eletrico"]["source"] == "b"
    assert rows["hibrido"]["n"] == 0


def test_a_list_price_alone_never_passes_as_a_used_car():
    listed = {"year": 2026, "p50": 30000, "p10": 30000, "p90": 30000, "n": 0, "as_of": None, "list_price": True}
    m = _model(prices_by_year=[listed], prices_by_fuel={}, new_prices={"eletrico": listed})
    passed, stretch = apply_hard_constraints([m], {**BASE, "p8_budget_max": 35000, "condition": "usado"})
    assert not passed and not stretch
    passed, _ = apply_hard_constraints([m], {**BASE, "p8_budget_max": 35000, "condition": "novo"})
    assert passed and passed[0]["price_basis"] == "list"


def test_list_price_seed_file_is_sourced():
    prices = load_list_prices()
    assert prices, "seeds/new_car_list_prices.json is empty"
    for key, versions in prices.items():
        assert "|" in key
        for v in versions:
            assert v["pvp_eur"] > 5000 and str(v.get("source", "")).startswith("https://"), (key, v)
