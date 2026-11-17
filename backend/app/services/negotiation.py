"""
The negotiation plan shown under an ad analysis: three numbers, the arguments
that move the price (with euros attached), and the messages to send — all
built from the same facts, so a message never offers more than the plan says.

It replaces an AI-written script that ignored the computed offer (it proposed
8 500 EUR on a 208 whose opening offer was 8 100) and tips with no figures
("com jeitinho costuma resultar").

European Portuguese, plain, friendly; never accuses the seller.
"""
from datetime import datetime
from typing import Optional


def _eur(n) -> str:
    return f"{int(round(n)):,} €".replace(",", ".")


def _round50(x: float) -> int:
    return int(round(x / 50.0) * 50)


def _thousands_km(km) -> str:
    return f"{int(round(km / 1000))} mil km" if km else ""


def _is_stand(seller_type: str) -> bool:
    s = (seller_type or "").lower()
    return "stand" in s or "profiss" in s


def _curated_issues(dealbreakers: Optional[dict]) -> list:
    d = dealbreakers or {}
    out = [i for i in (d.get("critical_issues") or []) + (d.get("watch_items") or []) if i.get("curated")]
    # red first, then the one with the dearest preventive fix
    return sorted(out, key=lambda i: (i.get("severity") != "critico",
                                      -((i.get("cost_eur") or {}).get("preventive") or [0, 0])[0]))


def _issue_topic(i: dict) -> str:
    if i.get("component") == "caixa":
        return "a caixa"
    p = (i.get("problem") or "").lower()
    if "correia" in p:
        return "a correia de distribuição"
    if "corrente" in p:
        return "a corrente de distribuição"
    if "turbo" in p:
        return "o turbo"
    if "injetor" in p:
        return "os injetores"
    return "o motor"


def _de(topic: str) -> str:
    """'de' + article, contracted as Portuguese does: da correia, do turbo, dos injetores."""
    for art, contracted in (("a ", "da "), ("o ", "do "), ("as ", "das "), ("os ", "dos ")):
        if topic.startswith(art):
            return contracted + topic[len(art):]
    return "de " + topic


def _short_engine(name: Optional[str]) -> str:
    return (name or "").split(" (")[0].strip()


def build_plan(listing: dict, numbers: Optional[dict], dealbreakers: Optional[dict],
               price_history: Optional[dict] = None) -> dict:
    """{numbers, arguments, messages:{first_contact, offer, counters}, walk_away}."""
    price = listing.get("price") or 0
    year = listing.get("year")
    km = listing.get("km") or 0
    stand = _is_stand(listing.get("seller_type"))
    days = listing.get("listing_age_days") or 0
    car = " ".join(str(x) for x in (listing.get("brand_name"), listing.get("model_name"), year) if x)
    issues = _curated_issues(dealbreakers)
    recalls = (dealbreakers or {}).get("recall_count") or 0

    # ── Numbers: open, aim, ceiling ─────────────────────────────────────────
    plan_numbers = None
    if numbers:
        opening, ceiling = numbers["opening_offer"], numbers["walk_away"]
        target = _round50((opening + ceiling) / 2)
        plan_numbers = {"asking": price, "opening": opening, "target": target, "ceiling": ceiling,
                        "comparables": numbers.get("sample_count"), "confidence": numbers.get("confidence")}
        if price <= ceiling:
            # Already at or below what similar cars ask: don't haggle hard, check the car.
            plan_numbers.update(opening=_round50(price * 0.97), target=_round50(price * 0.985), ceiling=price)

    # ── Arguments, strongest first, each with what it is worth ──────────────
    args: list[dict] = []
    if numbers and plan_numbers and price > numbers["walk_away"] and (numbers.get("sample_count") or 0) >= 8:
        gap = price - numbers["walk_away"]
        args.append({"kind": "mercado", "eur": gap,
                     "text": f"Carros iguais ({year}, à volta de {_thousands_km(km)}) pedem cerca de "
                             f"{_eur(numbers['walk_away'])} — {numbers['sample_count']} anúncios comparáveis.",
                     "say": f"carros iguais, com quilómetros parecidos, estão a pedir à volta de {_eur(numbers['walk_away'])}"})
    top = issues[0] if issues else None
    prev = ((top or {}).get("cost_eur") or {}).get("preventive")
    if top and prev:
        topic = _issue_topic(top)
        args.append({"kind": "manutencao", "eur": prev[0], "conditional": True,
                     "text": f"Se não houver fatura {_de(topic)}: são {_eur(prev[0])}–{_eur(prev[1])} que vais ter de gastar "
                             f"({_short_engine(top.get('engine'))}).",
                     "say": f"{topic} não tem fatura de troca, e isso são {_eur(prev[0])}–{_eur(prev[1])} que vou ter de gastar"})
    if days >= 30:
        args.append({"kind": "tempo", "eur": None, "text": f"Está anunciado há {days} dias — quem espera tanto costuma ceder.",
                     "say": None})
    drop = (price_history or {}).get("drop_total") or 0
    if drop >= 200:
        args.append({"kind": "historico", "eur": None,
                     "text": f"Já baixou {_eur(drop)} desde que o acompanhamos — há margem.", "say": None})
    if year and km:
        age = max(1, datetime.now().year - int(year))
        if km >= 200000:
            args.append({"kind": "km", "eur": None,
                         "text": f"Com {_thousands_km(km)}, conta com manutenção pesada a curto prazo "
                                 "(embraiagem, suspensão, distribuição): pede as faturas do que já foi feito.",
                         "say": f"já tem {_thousands_km(km)} e vai precisar de manutenção a curto prazo"})
        elif km > age * 18000:
            args.append({"kind": "km", "eur": None,
                         "text": f"Tem {km // age:,} km por ano, acima do normal (~15.000).".replace(",", "."),
                         "say": "tem bastantes quilómetros para o ano"})

    # ── Ceiling when the expensive job has no invoice ───────────────────────
    walk = None
    if plan_numbers:
        walk = {"ceiling": plan_numbers["ceiling"],
                "text": f"Acima de {_eur(plan_numbers['ceiling'])} não compensa"
                        + (f": há {plan_numbers['comparables']} carros comparáveis por esse preço." if plan_numbers.get("comparables") else ".")}
        if top and prev and plan_numbers["ceiling"] - prev[0] > plan_numbers["opening"] * 0.85:
            walk["ceiling_unproven"] = _round50(plan_numbers["ceiling"] - prev[0])
            walk["text"] += (f" Sem fatura {_de(_issue_topic(top))}, o teu teto desce para "
                             f"{_eur(walk['ceiling_unproven'])}.")

    # ── Messages ────────────────────────────────────────────────────────────
    questions: list[str] = []
    for i in issues[:2]:
        if i.get("seller_question"):
            questions.append(i["seller_question"])
    if not any("revis" in q.lower() or "óleo" in q.lower() for q in questions):
        questions.append("As revisões estão em dia? Tem as faturas ou o livro?")
    if stand:
        questions.append("O preço inclui tudo (legalização, despesas administrativas) e que garantia dão?")
    else:
        questions.append("Quantos donos teve? O carro está em seu nome?")
    if recalls and len(questions) < 4:
        questions.append("Pode enviar-me a matrícula ou o VIN? Queria confirmar as campanhas de recolha.")
    first_contact = "\n".join(
        [f"Olá, boa tarde! Vi o anúncio do {car} e tenho interesse. Antes de marcar uma visita, posso fazer-lhe umas perguntas?", ""]
        + [f"– {q}" for q in questions[:4]]
        + ["", "Obrigado!"])

    # The default offer states only facts already true (market, time, km); the
    # no-invoice variant adds the job's cost and starts lower.
    says = [a["say"] for a in args if a.get("say") and not a.get("conditional")][:2]
    known_private = "particular" in (listing.get("seller_type") or "").lower()
    offer_no_invoice = None
    if plan_numbers:
        sweetener = ("Fecho rapidamente, com a revisão feita antes da entrega." if stand
                     else "Pago a pronto e fecho rapidamente." if known_private else "Consigo fechar rapidamente.")
        liked = f"Gostei do carro, mas {' e '.join(says)}." if says else "Gostei do carro."
        offer = f"Olá! Obrigado pelas respostas. {liked} Posso oferecer {_eur(plan_numbers['opening'])}. {sweetener}"
        if top and prev and walk and walk.get("ceiling_unproven"):
            cond = next(a["say"] for a in args if a.get("conditional"))
            low_open = _round50(min(plan_numbers["opening"], walk["ceiling_unproven"] * 0.97))
            if stand:
                # One or the other, never both: the job done, or the price down.
                offer_no_invoice = (f"Olá! Obrigado pelas respostas. Gostei do carro, mas {cond}. "
                                    f"Posso fechar por {_eur(plan_numbers['opening'])} com a troca feita antes da entrega, "
                                    f"ou por {_eur(low_open)} sem ela.")
            else:
                offer_no_invoice = (f"Olá! Obrigado pelas respostas. Gostei do carro, mas {cond}. "
                                    f"Posso oferecer {_eur(low_open)}. Fecho rapidamente.")
    else:
        offer = (f"Olá! Obrigado pelas respostas. Gostei do carro{', mas ' + says[0] if says else ''}. "
                 f"Qual é o melhor preço que consegue fazer{' a pronto' if not stand else ''}?")

    counters = []
    if plan_numbers:
        counters.append({"if": "Faz uma contraproposta",
                         "reply": f"Se ficar até {_eur(plan_numbers['target'])}, aceita. Entre isso e "
                                  f"{_eur(plan_numbers['ceiling'])}, responde: «Fazemos {_eur(plan_numbers['target'])} e fecho hoje.» "
                                  f"Acima de {_eur(plan_numbers['ceiling'])}, agradece e sai."})
    if stand:
        counters.append({"if": "«O preço é fixo»",
                         "reply": "«Percebo. Então consegue incluir a revisão completa, pneus novos ou uma garantia mais longa? "
                                  "Com isso fechamos.» Nos stands, os extras costumam ceder antes do preço."})
    else:
        counters.append({"if": "«O preço é fixo»",
                         "reply": f"«Percebo. Fico a pensar — se mudar de ideias, a minha proposta mantém-se esta semana.» "
                                  f"{'Um particular com o carro há ' + str(days) + ' dias à venda costuma voltar a ligar.' if days >= 21 else 'Muitas vezes o vendedor volta a ligar.'}"})
    counters.append({"if": "«Tenho mais interessados»",
                     "reply": "«Sem problema. A minha proposta fica de pé; se não se concretizar, diga-me.» Não subas por pressão."})
    if top and prev:
        counters.append({"if": f"Não há fatura {_de(_issue_topic(top))}",
                         "reply": f"«Então peço que seja feito antes da entrega, ou que desconte {_eur(prev[0])}.» "
                                  f"É o custo mínimo da reparação preventiva."})

    return {
        "numbers": plan_numbers,
        "note": None if plan_numbers else (
            "Ainda há poucos carros comparáveis à venda para te darmos números com confiança: "
            "negoceia com os argumentos e pede ao vendedor o melhor preço."),
        "arguments": args[:4],
        "walk_away": walk,
        "messages": {"first_contact": first_contact, "offer": offer, "offer_no_invoice": offer_no_invoice,
                     "no_invoice_topic": _issue_topic(top) if offer_no_invoice else None, "counters": counters},
        "seller": "stand" if stand else "particular",
    }
