"""The negotiation guide: polite maintenance-first opening, precise offers,
a narrowing ladder, facts with euros, and nothing invented without data."""
import re

from app.services.known_issues import load_issues, to_payload
from app.services.negotiation import _precise, build_plan

PURETECH = next(to_payload(i) for i in load_issues() if i["id"] == "psa-puretech-12-belt")
LISTING = {"brand_name": "Peugeot", "model_name": "208", "year": 2018, "km": 110000, "price": 8990,
           "seller_type": "particular", "listing_age_days": 40}
NUMBERS = {"asking_price": 8990, "opening_offer": 8100, "fair_value": 8550, "walk_away": 8550,
           "sample_count": 107, "confidence": "alta"}
DEALBREAKERS = {"critical_issues": [PURETECH], "watch_items": [], "recall_count": 2}


def plan(**kw):
    return build_plan({**LISTING, **kw.get("listing", {})}, kw.get("numbers", NUMBERS),
                      kw.get("dealbreakers", DEALBREAKERS), kw.get("history"))


def stage(p, key):
    return next(s for s in p["stages"] if s["key"] == key)


def test_five_moments_in_order():
    assert [s["key"] for s in plan()["stages"]] == ["primeira", "visita", "proposta", "contrapropostas", "fecho"]
    assert all(s["why"] for s in plan()["stages"])


def test_first_message_asks_about_maintenance_never_about_the_engine_fault():
    m = stage(plan(), "primeira")["message"]
    assert "histórico de manutenção" in m and "mecânico de confiança à visita" in m
    for bad in ("correia", "PureTech", "problema", "€"):
        assert bad not in m
    assert m.count("– ") == 4


def test_newer_or_dearer_car_at_a_stand_gets_a_brand_diagnostic():
    m = stage(plan(listing={"seller_type": "stand", "year": 2022, "price": 24000}), "primeira")["message"]
    assert "diagnóstico na marca" in m and "garantia" in m


def test_offers_are_precise_never_round():
    assert _precise(10000) == 9850 and _precise(10500) == 10450 and _precise(10550) == 10550
    n = plan()["numbers"]
    assert n["opening"] % 500 != 0


def test_offer_cites_facts_with_the_same_number():
    m = stage(plan(), "proposta")["message"]
    assert "8.550 €" in m and f"{plan()['numbers']['opening']:,}".replace(",", ".") in m
    assert "correia" not in m                       # not asserted before the visit


def test_no_invoice_offer_is_lower_and_names_the_cost():
    m = stage(plan(), "proposta")["message_no_invoice"]
    assert "não tem fatura de troca" in m and "700 € a 1.200 €" in m and "7.600 €" in m


def test_ladder_concessions_shrink_and_stop_at_target():
    p = plan()
    prices = [p["numbers"]["opening"]] + [l["price"] for l in stage(p, "contrapropostas")["ladder"]]
    steps = [b - a for a, b in zip(prices, prices[1:])]
    assert steps == sorted(steps, reverse=True) and prices[-1] == p["numbers"]["target"]


def test_stand_price_is_fixed_asks_for_the_legal_three_year_warranty():
    c = {x["if"]: x["reply"] for x in stage(plan(listing={"seller_type": "stand"}), "contrapropostas")["counters"]}
    assert "garantia de 3 anos" in c["«O preço é fixo»"] and "18 meses" in c["«O preço é fixo»"]


def test_private_sale_visit_checks_ownership_and_liens():
    tips = " ".join(stage(plan(), "visita")["tips"])
    assert "penhoras" in tips and "inspeção periódica" in tips


def test_exit_names_the_target_not_the_asking_price():
    p = plan(listing={"price": 8000})
    assert f"{p['numbers']['target']:,}".replace(",", ".") in stage(p, "fecho")["message"]


def test_no_market_data_means_no_numbers_and_an_honest_note():
    p = plan(numbers=None, dealbreakers={})
    assert p["numbers"] is None and p["walk_away"] is None and p["note"]
    assert "melhor preço" in stage(p, "proposta")["message"] and not re.search(r"\d €", stage(p, "proposta")["message"])


def test_portuguese_contractions():
    p = plan()
    assert "fatura da correia" in p["walk_away"]["text"] and "de a " not in p["walk_away"]["text"]
