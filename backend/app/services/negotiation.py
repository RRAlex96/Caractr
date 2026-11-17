"""
The negotiation guide shown under an ad analysis: five moments — first
message, the visit, the offer, the counter-offers, the close or the exit —
each with a ready message in European Portuguese and one line on why it works.
Built from the analysis' own numbers, so a message never offers more than the
plan says.

What it rests on (2026-11-18 research):
- Precise first offers anchor harder: recipients adjust less from 10 350 than
  from 10 000 (Mason, Lee, Wiley & Ames 2013, JESP) — but a hyper-precise or
  aggressive number can backfire with experienced counterparts, so offers are
  rounded to 50 and kept off round 500s.
- Decreasing concessions signal you are near your limit and win better deals
  (Tey, Schaerer, Madan & Swaab 2021, OBHDP): the ladder narrows each step.
- Fix the target before talking — the defence against the seller's own
  tapering (same paper).
- Portugal: a used car from a professional carries the legal warranty of
  3 years, reducible to 18 months only by written agreement (DL 84/2021) —
  something to ask a stand for instead of money. A private sale has none.
  The last periodic inspection (IPO) sheet records the kilometres.

Tone: polite, curious, human. The first message asks about maintenance the
way any careful buyer would — never "this engine has a known problem".
"""
from datetime import datetime
from typing import Optional


def _eur(n) -> str:
    return f"{int(round(n)):,} €".replace(",", ".")


def _round50(x: float) -> int:
    return int(round(x / 50.0) * 50)


def _round10(x: float) -> int:
    return int(round(x / 10.0) * 10)


def _precise(x: float) -> int:
    """A first offer that looks worked out, not pulled from the air:
    to the 50, never on a round 500 (10 000 -> 9 850, 10 500 -> 10 450)."""
    r = _round50(x)
    if r % 1000 == 0:
        return r - 150
    if r % 500 == 0:
        return r - 50
    return r


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


def _first_sentence(t: Optional[str]) -> str:
    t = (t or "").strip()
    for end in (". ", "! ", "? "):
        if end in t:
            return t.split(end)[0] + end.strip()
    return t


def build_plan(listing: dict, numbers: Optional[dict], dealbreakers: Optional[dict],
               price_history: Optional[dict] = None) -> dict:
    """{numbers, arguments, walk_away, stages[], messages{...}} — see module doc."""
    price = listing.get("price") or 0
    year = listing.get("year")
    km = listing.get("km") or 0
    stand = _is_stand(listing.get("seller_type"))
    private = "particular" in (listing.get("seller_type") or "").lower()
    days = listing.get("listing_age_days") or 0
    car = " ".join(str(x) for x in (listing.get("brand_name"), listing.get("model_name")) if x)
    issues = _curated_issues(dealbreakers)
    top = issues[0] if issues else None
    prev = ((top or {}).get("cost_eur") or {}).get("preventive")
    topic = _issue_topic(top) if top else None
    age = max(0, datetime.now().year - int(year)) if year else None
    # A newer or dearer car justifies a diagnostic at the brand's workshop.
    brand_check = bool((age is not None and age <= 6) or price >= 20000)

    # ── Numbers: start, aim, ceiling ────────────────────────────────────────
    n = None
    if numbers:
        opening, ceiling = _precise(numbers["opening_offer"]), numbers["walk_away"]
        if price <= ceiling:
            # Already at or below what similar cars ask: a light touch.
            opening, ceiling = _precise(price * 0.97), price
        target = _round50((opening + ceiling) / 2)
        n = {"asking": price, "opening": opening, "target": target, "ceiling": ceiling,
             "comparables": numbers.get("sample_count"), "confidence": numbers.get("confidence")}

    # ── Arguments, strongest first, each with what it is worth ──────────────
    args: list[dict] = []
    if numbers and n and price > numbers["walk_away"] and (numbers.get("sample_count") or 0) >= 8:
        args.append({"kind": "mercado", "eur": price - numbers["walk_away"],
                     "text": f"Carros iguais ({year}, à volta de {_thousands_km(km)}) pedem cerca de "
                             f"{_eur(numbers['walk_away'])} — {numbers['sample_count']} anúncios comparáveis.",
                     "say": f"vi outros {car} parecidos, com quilómetros semelhantes, à volta de {_eur(numbers['walk_away'])}"})
    if top and prev:
        args.append({"kind": "manutencao", "eur": prev[0], "conditional": True,
                     "text": f"Se não houver fatura {_de(topic)}: são {_eur(prev[0])}–{_eur(prev[1])} que vais ter de gastar "
                             f"({_short_engine(top.get('engine'))}).",
                     "say": f"não há fatura {_de(topic)} e são {_eur(prev[0])} a {_eur(prev[1])} que vou ter de gastar logo"})
    if days >= 30:
        args.append({"kind": "tempo", "eur": None, "text": f"Está anunciado há {days} dias — quem espera tanto costuma ceder.",
                     "say": None})
    drop = (price_history or {}).get("drop_total") or 0
    if drop >= 200:
        args.append({"kind": "historico", "eur": None,
                     "text": f"Já baixou {_eur(drop)} desde que o acompanhamos — há margem.", "say": None})
    if year and km and age:
        if km >= 200000:
            args.append({"kind": "km", "eur": None,
                         "text": f"Com {_thousands_km(km)}, conta com manutenção pesada a curto prazo "
                                 "(embraiagem, suspensão, distribuição).",
                         "say": f"com {_thousands_km(km)} vai precisar de manutenção a curto prazo"})
        elif km > age * 18000:
            args.append({"kind": "km", "eur": None,
                         "text": f"Tem {km // age:,} km por ano, acima do normal (~15.000).".replace(",", "."),
                         "say": "tem bastantes quilómetros para o ano"})

    walk = None
    if n:
        walk = {"ceiling": n["ceiling"],
                "text": f"Acima de {_eur(n['ceiling'])} não compensa"
                        + (f": há {n['comparables']} carros comparáveis por esse preço." if n.get("comparables") else ".")}
        if top and prev and n["ceiling"] - prev[0] > n["opening"] * 0.85:
            walk["ceiling_unproven"] = _round50(n["ceiling"] - prev[0])
            walk["text"] += f" Sem fatura {_de(topic)}, o teu teto desce para {_eur(walk['ceiling_unproven'])}."

    # ── 1. First message: maintenance, history, a mechanic — nothing else ───
    qs = ["Tem o histórico de manutenção — livro ou faturas? Quando foi a última revisão?",
          "Já teve alguma intervenção maior, como distribuição, embraiagem, travões ou pneus?"]
    if stand:
        qs.append("O preço anunciado é o final, com legalização e despesas incluídas? E que garantia dão?")
    else:
        qs.append("É o primeiro dono? E, se não for indiscrição, porque está a vender?")
    qs.append("Seria possível fazer um diagnóstico na marca antes de fecharmos?" if brand_check and stand
              else "Importa-se que leve um mecânico de confiança à visita?")
    first_contact = "\n".join(
        [f"Olá, boa tarde! Vi o anúncio do {car} e fiquei interessado. Antes de combinarmos uma visita, "
         "posso fazer-lhe umas perguntas?", ""]
        + [f"– {q}" for q in qs] + ["", "Obrigado!"])

    # ── 2. At the visit: what to look for, what to say ──────────────────────
    visit = ["Confirma os quilómetros no papel da última inspeção periódica e nas faturas — devem bater certo."]
    if top:
        visit.append(f"Entre os documentos da manutenção, procura a fatura {_de(topic)}. "
                     f"Se não houver, é o teu principal argumento.")
        check = _first_sentence(top.get("check"))
        if check and "fatura" not in check.lower() and "prova" not in check.lower():
            visit.append(check)
    visit.append("Faz o test-drive com o motor frio: arranque, ruídos, caixa, travões.")
    if private:
        visit.append("Confirma que o vendedor é o dono e pede a certidão do registo automóvel: "
                     "não pode haver penhoras nem reserva de propriedade.")
    if stand:
        visit.append("Pede o preço final por escrito, com tudo incluído.")
    visit.append("Não fales de preço no local se não tiveres de o fazer. Agradece e diz que vais pensar — "
                 "a proposta faz-se depois, com calma.")

    # ── 3. The offer ─────────────────────────────────────────────────────────
    facts = [a["say"] for a in args if a.get("say") and not a.get("conditional")][:2]
    seen = ("Fiz as contas: " + " e ".join(facts) + ". ") if facts else "É o valor que me parece justo pelo que vi. "
    sweet = ("Se ficarmos neste valor, fecho esta semana." if stand
             else "Pago na totalidade por transferência e trato da documentação esta semana." if private
             else "Consigo fechar esta semana.")
    offer = offer_no_invoice = None
    if n:
        if facts:
            offer = (f"Olá! Obrigado pelo tempo e pela visita. Gostei do carro e estou mesmo interessado. {seen}"
                     f"A minha proposta é {_eur(n['opening'])}. {sweet} Diga-me o que acha.")
        else:
            offer = (f"Olá! Obrigado pelo tempo e pela visita. Gostei do carro e estou mesmo interessado. "
                     f"A minha proposta é {_eur(n['opening'])} — é o valor que me parece justo pelo que vi. "
                     f"{sweet} Diga-me o que acha.")
        if walk and walk.get("ceiling_unproven"):
            low = _precise(min(n["opening"], walk["ceiling_unproven"] * 0.97))
            if stand:
                offer_no_invoice = (f"Olá! Obrigado pela visita. Gostei do carro, mas {topic} "
                                    f"não tem fatura de troca e são {_eur(prev[0])} a {_eur(prev[1])} logo à cabeça. "
                                    f"Proponho {_eur(n['opening'])} com a troca feita antes da entrega, ou "
                                    f"{_eur(low)} se eu tratar dela. O que prefere?")
            else:
                offer_no_invoice = (f"Olá! Obrigado pela visita. Gostei do carro, mas {topic} não tem fatura de troca "
                                    f"e são {_eur(prev[0])} a {_eur(prev[1])} que vou ter de gastar logo. "
                                    f"Por isso, a minha proposta é {_eur(low)}. {sweet}")
    else:
        offer = (f"Olá! Obrigado pelo tempo e pela visita. Gostei do carro e estou interessado. "
                 f"Qual é o melhor preço que consegue fazer{' com tudo incluído' if stand else ''}?")

    # ── 4. Counter-offers: a narrowing ladder ────────────────────────────────
    ladder = []
    counters = []
    if n:
        gap = max(0, n["target"] - n["opening"])
        steps = [n["opening"] + _round10(gap * 0.55), n["opening"] + _round10(gap * 0.85), n["target"]]
        steps = sorted(set(s for s in steps if s > n["opening"]))
        ladder = [{"price": steps[0], "say": f"Percebo. Consigo chegar aos {_eur(steps[0])}, mas já é um esforço."}]
        if len(steps) > 1:
            ladder.append({"price": steps[1], "say": f"Posso ir aos {_eur(steps[1])}. Mais do que isso fica difícil."})
        if len(steps) > 2:
            ladder.append({"price": steps[2], "say": f"{_eur(steps[2])} é mesmo o meu limite. Se fizer sentido, fechamos."})
        counters.append({"if": "Faz uma contraproposta",
                         "reply": "Sobe pelos degraus abaixo, um de cada vez e cada vez menos — mostra que estás "
                                  f"a chegar ao limite. Nunca passes de {_eur(n['ceiling'])}."})
        counters.append({"if": "«Fazemos a meio caminho?»",
                         "reply": (f"Só se o meio ficar até {_eur(n['target'])}. Se ficar acima: "
                                   f"«Gostava, mas o meu limite é {_eur(n['target'])}.»")})
    if stand:
        counters.append({"if": "«O preço é fixo»",
                         "reply": "«Percebo. Então, pelo mesmo valor, consegue a garantia de 3 anos, a revisão feita "
                                  "e pneus novos?» A lei dá 3 anos de garantia a usados de stand; só desce para 18 meses "
                                  "por acordo escrito — pedir os 3 anos não lhe custa dinheiro."})
    else:
        counters.append({"if": "«O preço é fixo»",
                         "reply": "«Percebo, obrigado. A minha proposta mantém-se esta semana, caso mude de ideias.» "
                                  "E deixa-o pensar — muitos voltam a ligar."})
    counters.append({"if": "«Tenho mais interessados»",
                     "reply": "«Compreendo. Se não se concretizar, a minha proposta fica de pé.» Não subas por pressão."})
    if top and prev:
        counters.append({"if": f"Não há fatura {_de(topic)}",
                         "reply": f"«Então peço que seja feita antes da entrega, ou que desconte {_eur(prev[0])}.» "
                                  "É o custo mínimo da reparação preventiva."})

    # ── 5. The close, or a dignified exit ───────────────────────────────────
    close = ("Antes de assinar, um último pedido simples: «Pode entregá-lo com a revisão feita e o depósito cheio?» "
             "Nos stands, os extras cedem mais facilmente do que o preço." if stand else
             "No fecho, pede o que não custa dinheiro ao vendedor: as duas chaves, o livro de revisões e todas as "
             "faturas. Faz o pagamento por transferência, com recibo e a declaração de venda assinada.")
    exit_msg = (f"Obrigado pela disponibilidade. Para mim, o limite é {_eur(n['target'])}. "
                "Se mudar de ideias, a minha proposta mantém-se até sexta-feira." if n else
                "Obrigado pela disponibilidade. Vou pensar e, se fizer sentido, volto a contactar.")

    stages = [
        {"key": "primeira", "title": "Antes de ir ver o carro", "message": first_contact,
         "why": "Perguntas abertas sobre a manutenção dão-te a informação de que precisas sem pôr o vendedor na "
                "defensiva. O preço só se fala depois de veres o carro."},
        {"key": "visita", "title": "Na visita", "tips": visit,
         "why": "O que encontras na visita é a tua melhor razão para baixar o preço — e é difícil de contestar."},
        {"key": "proposta", "title": "A proposta", "message": offer, "message_no_invoice": offer_no_invoice,
         "no_invoice_topic": topic if offer_no_invoice else None,
         "why": "Um valor exato (10.350 € em vez de 10.000 €) mostra que fizeste contas e leva a contrapropostas "
                "mais próximas da tua (Mason et al., 2013). Justifica com factos, não com opinião."},
        {"key": "contrapropostas", "title": "Se o vendedor contrapropuser", "ladder": ladder, "counters": counters,
         "why": "Concessões cada vez menores mostram que estás perto do teu limite e levam a melhores acordos "
                "(Tey et al., 2021). Decide o teu objetivo antes de começar."},
        {"key": "fecho", "title": "Fechar — ou sair bem", "tips": [close], "message": exit_msg,
         "why": "Sair com educação e uma proposta de pé é muitas vezes o que traz o vendedor de volta."},
    ]

    return {
        "numbers": n,
        "note": None if n else ("Ainda há poucos carros comparáveis à venda para te darmos números com confiança: "
                                "negoceia com os argumentos e pede ao vendedor o melhor preço."),
        "arguments": args[:4],
        "walk_away": walk,
        "stages": stages,
        # kept for pages built before the stages existed
        "messages": {"first_contact": first_contact, "offer": offer, "offer_no_invoice": offer_no_invoice,
                     "no_invoice_topic": topic if offer_no_invoice else None, "counters": counters},
        "seller": "stand" if stand else "particular",
    }
