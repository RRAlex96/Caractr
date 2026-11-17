"""The negotiation plan: numbers and messages agree, arguments carry euros,
the first message never accuses, and nothing is invented without data."""
from app.services.known_issues import load_issues, to_payload
from app.services.negotiation import build_plan

PURETECH = next(to_payload(i) for i in load_issues() if i["id"] == "psa-puretech-12-belt")
LISTING = {"brand_name": "Peugeot", "model_name": "208", "year": 2018, "km": 110000, "price": 8990,
           "seller_type": "particular", "listing_age_days": 40}
NUMBERS = {"asking_price": 8990, "opening_offer": 8100, "fair_value": 8550, "walk_away": 8550,
           "sample_count": 107, "confidence": "alta"}
DEALBREAKERS = {"critical_issues": [PURETECH], "watch_items": [], "recall_count": 2}


def plan(**kw):
    return build_plan({**LISTING, **kw.get("listing", {})}, kw.get("numbers", NUMBERS),
                      kw.get("dealbreakers", DEALBREAKERS), kw.get("history"))


def test_offer_message_uses_the_opening_number_not_another():
    p = plan()
    assert p["numbers"] == {"asking": 8990, "opening": 8100, "target": 8300, "ceiling": 8550,
                            "comparables": 107, "confidence": "alta"}
    assert "8.100 €" in p["messages"]["offer"] and "8.500" not in p["messages"]["offer"]


def test_arguments_carry_euros_market_and_maintenance():
    kinds = {a["kind"]: a for a in plan()["arguments"]}
    assert "8.550 €" in kinds["mercado"]["text"] and kinds["mercado"]["eur"] == 440
    assert kinds["manutencao"]["eur"] == 700 and "700 €–1.200 €" in kinds["manutencao"]["text"]
    assert "tempo" in kinds            # 40 days on the market


def test_ceiling_drops_without_the_invoice():
    w = plan()["walk_away"]
    assert w["ceiling"] == 8550 and w["ceiling_unproven"] == 7850


def test_first_message_asks_politely_and_never_says_known_problem():
    m = plan()["messages"]["first_contact"]
    assert "correia de distribuição já foi substituída" in m
    assert "problema conhecido" not in m and "€" not in m          # no accusation, no price
    assert m.count("– ") <= 4


def test_stand_gets_extras_not_cash():
    p = plan(listing={"seller_type": "stand"})
    assert "revisão feita" in p["messages"]["offer"] and "pronto" not in p["messages"]["offer"]
    assert any("incluir" in c["reply"] for c in p["messages"]["counters"])
    assert "despesas administrativas" in p["messages"]["first_contact"]


def test_no_market_data_means_no_numbers_and_an_honest_note():
    p = plan(numbers=None, dealbreakers={})
    assert p["numbers"] is None and p["walk_away"] is None and p["note"]
    assert "melhor preço" in p["messages"]["offer"] and "€" not in p["messages"]["offer"]


def test_a_car_already_below_market_is_not_haggled_hard():
    p = plan(listing={"price": 8000})
    assert p["numbers"]["ceiling"] == 8000 and p["numbers"]["opening"] == 7750
    assert not any(a["kind"] == "mercado" for a in p["arguments"])


def test_default_offer_only_states_facts_and_no_invoice_variant_starts_lower():
    m = plan()["messages"]
    assert "correia" not in m["offer"]                       # not asserted before the seller answers
    assert "8.100 €" in m["offer"]
    assert "a correia de distribuição não tem fatura" in m["offer_no_invoice"]
    assert "7.600 €" in m["offer_no_invoice"]                 # 97% of the 7 850 ceiling without invoice
    assert m["no_invoice_topic"] == "a correia de distribuição"


def test_portuguese_contractions():
    p = plan()
    assert "fatura da correia" in p["walk_away"]["text"] and "de a " not in p["walk_away"]["text"]
    assert any(c["if"] == "Não há fatura da correia de distribuição" for c in p["messages"]["counters"])
