"""
Caractr — Rule-based Ad Analysis Engine
Produces the same structured JSON output as the LLM analyser,
but using deterministic rules + Portuguese template strings.

Zero API dependency. Zero latency. Works offline.
Covers: verdict, verdict_reason, green_flags, red_flags,
        seller_analysis, profile_fit, trim_level, spec_tier,
        key_extras, spec_value_assessment.

Used as the default when ANTHROPIC_API_KEY is not set,
or when USE_RULE_ANALYSIS=true in the environment.
"""

import re
from typing import Optional


# ── Keyword dictionaries ──────────────────────────────────────────────────────

# Extras keywords → display label
EXTRAS_KEYWORDS: list[tuple[list[str], str]] = [
    (["gps", "navegação", "navegacao", "navi"],                 "GPS"),
    (["câmara", "camara", "câmera", "camera", "reversing"],     "Câmara traseira"),
    (["teto panorâmico", "teto panoramico", "panoramic"],       "Teto panorâmico"),
    (["bancos aquecidos", "heated seats", "aquecimento de ban"],"Bancos aquecidos"),
    (["bancos elétricos", "bancos electricos", "electric seat"],"Bancos elétricos"),
    (["bancos em pele", "couro", "leather"],                    "Bancos em pele"),
    (["sensores de estacionamento", "sensor de park", "pdc"],   "Sensores de parque"),
    (["cruise control", "velocidade cruzeiro"],                  "Cruise control"),
    (["ar condicionado", "climatização", "climatronic", "a/c"], "Ar condicionado"),
    (["bi-zona", "bi zona", "dual zone"],                       "Climatização bi-zona"),
    (["bluetooth", "hands-free", "hands free"],                 "Bluetooth"),
    (["carregamento sem fios", "wireless charging", "qi "],     "Carregamento sem fios"),
    (["apple carplay", "carplay"],                              "Apple CarPlay"),
    (["android auto"],                                          "Android Auto"),
    (["faróis led", "farois led", "led headlights", "full led"],"Faróis LED"),
    (["faróis xenon", "farois xenon", "xenon"],                 "Faróis Xenon"),
    (["jantes", "rodas em liga", "alloy wheels"],               "Jantes liga leve"),
    (["tração integral", "awd", "4wd", "4motion", "xdrive", "quattro", "4x4"], "Tração integral"),
    (["suspensão adaptativa", "adaptive suspension", "dcc"],    "Suspensão adaptativa"),
    (["head-up display", "head up display", "hud"],             "Head-Up Display"),
    (["alerta de ângulo morto", "blind spot"],                  "Alerta ângulo morto"),
    (["teto de abrir", "teto amovível"],                        "Teto de abrir"),
    (["banco do condutor elétrico", "assento elétrico"],        "Banco condutor elétrico"),
    (["vidros elétricos", "electric windows"],                  "Vidros elétricos"),
    (["alarme", "sistema de alarme"],                           "Alarme"),
    (["garante", "garantia", "warranty"],                       "Com garantia"),
    (["livro de revisões", "revisões em dia", "historico de ma","manutenção em dia"], "Revisões em dia"),
    (["segunda chave", "chave extra"],                          "Segunda chave"),
    (["inspeção"],                                              "Inspeção recente"),
]

# Trim level keywords → trim name (first match wins)
TRIM_KEYWORDS: list[tuple[list[str], str]] = [
    (["amg", "m performance", "m3", "m5", "rs ", "r-line", "st ", "gti", "type r", "cupra"], None),  # Dynamic — use as-is
    (["exclusive", "exclusiv"],             "Exclusive"),
    (["prestige"],                          "Prestige"),
    (["executive"],                         "Executive"),
    (["elegance"],                          "Elegance"),
    (["luxury", "luxe"],                    "Luxury"),
    (["sport", "sportline", "sportback"],   "Sport"),
    (["style", "stylus"],                   "Style"),
    (["comfort", "confort", "comfortline"], "Comfort"),
    (["trend", "trendline"],                "Trend"),
    (["advance", "advanced"],               "Advance"),
    (["premium"],                           "Premium"),
    (["dynamic"],                           "Dynamic"),
    (["titanium"],                          "Titanium"),
    (["highline", "high line"],             "Highline"),
    (["business"],                          "Business"),
    (["black edition", "blackline"],        "Black Edition"),
    (["white edition"],                     "White Edition"),
    (["lounge"],                            "Lounge"),
    (["urban"],                             "Urban"),
    (["edition"],                           "Edition"),
]

# High-spec indicators → spec_tier = "alto"
HIGH_SPEC_KEYWORDS = [
    "teto panorâmico", "teto panoramico", "head-up", "hud",
    "bancos em pele", "couro", "leather", "suspensão adaptativa",
    "faróis led", "full led", "matrix", "bi-zona", "climatronic",
    "carregamento sem fios", "apple carplay", "android auto",
    "jantes 18", "jantes 19", "jantes 20",
    "câmara 360", "camera 360", "surround view",
    "alerta de ângulo", "blind spot", "head up display",
]

LOW_SPEC_KEYWORDS = [
    "versão base", "entry", "básico", "sem extras", "simples",
    "ar condicionado manual", "rádio base",
]


# ── Extraction helpers ────────────────────────────────────────────────────────

def _extract_extras(description: str) -> list[str]:
    """Find known extras mentioned in the listing description."""
    desc_lower = description.lower()
    found = []
    for keywords, label in EXTRAS_KEYWORDS:
        if any(kw in desc_lower for kw in keywords):
            found.append(label)
    return found[:6]  # cap at 6 most relevant


def _detect_trim(description: str, title: str = "") -> Optional[str]:
    """Extract the trim/version name from description or title."""
    text = f"{title} {description}".lower()
    for keywords, label in TRIM_KEYWORDS:
        for kw in keywords:
            if kw in text:
                if label is None:
                    # Dynamic case: find the actual keyword in title
                    for k in keywords:
                        if k in (title or "").lower():
                            return k.upper().strip()
                return label
    return None


def _detect_spec_tier(description: str, extras: list[str]) -> str:
    desc_lower = description.lower()
    high_count = sum(1 for kw in HIGH_SPEC_KEYWORDS if kw in desc_lower)
    low_count  = sum(1 for kw in LOW_SPEC_KEYWORDS  if kw in desc_lower)
    if high_count >= 3 or len(extras) >= 5:
        return "alto"
    if low_count >= 2 or len(extras) <= 1:
        return "base"
    return "medio"


def _spec_value_assessment(spec_tier: str, price_delta: float) -> str:
    """Is the spec level good value for the asking price?"""
    if spec_tier == "alto" and price_delta >= 0.0:
        return "acima_do_esperado"
    if spec_tier == "alto" and price_delta < -0.3:
        return "abaixo_do_esperado"
    if spec_tier == "base" and price_delta >= 0.2:
        return "acima_do_esperado"
    if spec_tier == "base" and price_delta < -0.1:
        return "abaixo_do_esperado"
    return "adequado"


# ── Flag generators ───────────────────────────────────────────────────────────

def _green_flags(
    price_delta: float,
    km_per_year: Optional[float],
    seller_type: str,
    extras: list[str],
    description: str,
    photo_count: int,
    listing_age_days: Optional[int],
    user_profile: Optional[dict] = None,
    model_info: Optional[dict] = None,
) -> list[str]:
    flags = []
    desc = description.lower()

    if price_delta >= 0.3:
        flags.append(f"Preço {round(price_delta * 20, 0):.0f}% abaixo da média de mercado")
    elif price_delta >= 0.1:
        flags.append(f"Preço ligeiramente abaixo do mercado")

    if km_per_year and km_per_year < 10_000:
        flags.append(f"Quilometragem baixa para a idade ({km_per_year:,.0f} km/ano)")
    elif km_per_year and km_per_year < 14_000:
        flags.append(f"Quilometragem dentro da média ({km_per_year:,.0f} km/ano)")

    if seller_type == "privado":
        flags.append("Vendedor particular — margem de negociação típica")

    if any(kw in desc for kw in ["revisões em dia", "livro de revisões", "manutenção em dia", "histórico"]):
        flags.append("Histórico de manutenção documentado")

    if any(kw in desc for kw in ["garantia", "garante"]):
        flags.append("Garantia incluída")

    if any(kw in desc for kw in ["inspeção válida", "inspeção recente"]):
        flags.append("Inspeção recente válida")

    if photo_count >= 10:
        flags.append(f"Boas fotos do anúncio ({photo_count} imagens)")

    if len(extras) >= 4:
        flags.append(f"Bem equipado ({len(extras)} extras identificados)")

    if listing_age_days is not None and listing_age_days <= 7:
        flags.append("Anúncio recente — provavelmente não vendido ainda")

    # Profile-aware green flags
    if user_profile and model_info:
        _dim_labels = {
            "economy": "economia", "comfort": "conforto", "driving": "condução",
            "practical": "praticidade", "status": "imagem", "reliability": "fiabilidade",
        }
        top_dim = max(user_profile.items(), key=lambda x: x[1])[0] if user_profile else ""
        top_label = _dim_labels.get(top_dim, top_dim)
        mi_comfort = (model_info.get("comfort_score") or 5)
        mi_reliability = (model_info.get("avg_reliability") or model_info.get("reliability_score") or 5)

        if top_dim == "reliability" and mi_reliability >= 8:
            flags.append(f"Fiabilidade excelente — exatamente o que o teu perfil pede")
        elif top_dim == "comfort" and mi_comfort >= 8:
            flags.append(f"Conforto de referência no segmento — ideal para o teu perfil")
        elif top_dim in ("economy", "reliability") and mi_reliability >= 7.5:
            flags.append(f"Alinha com a tua prioridade de {top_label}")

    return flags[:5]


def _red_flags(
    price_delta: float,
    km_per_year: Optional[float],
    listing_price: Optional[int],
    avg_price: Optional[float],
    seller_type: str,
    description: str,
    photo_count: int,
    listing_age_days: Optional[int],
    model_info: Optional[dict],
    user_profile: Optional[dict] = None,
) -> list[str]:
    flags = []
    desc = description.lower()

    if listing_price and avg_price and listing_price < avg_price * 0.75:
        flags.append("Preço muito abaixo do mercado — verificar cuidadosamente antes de contatar")

    if km_per_year and km_per_year > 25_000:
        flags.append(f"Quilometragem muito elevada ({km_per_year:,.0f} km/ano — uso intensivo)")
    elif km_per_year and km_per_year > 20_000:
        flags.append(f"Quilometragem acima da média ({km_per_year:,.0f} km/ano)")

    if price_delta < -0.3:
        flags.append("Preço acima do mercado — margem de negociação recomendada")

    if seller_type == "stand" and avg_price and listing_price and listing_price > avg_price * 1.15:
        flags.append("Stand a pedir mais de 15% acima da média de mercado")

    if listing_age_days is not None and listing_age_days > 90:
        flags.append(f"Anúncio publicado há mais de 90 dias — possível problema de escoamento")

    if photo_count < 3:
        flags.append("Poucas fotos — difícil avaliar o estado do veículo")

    if len(description) < 80:
        flags.append("Descrição muito curta — pedir informação adicional ao vendedor")

    # Model-specific known issues
    if model_info:
        issues = model_info.get("known_issues") or ""
        if issues and model_info.get("avg_reliability") and model_info["avg_reliability"] < 6.5:
            # Only surface the most important issue
            first_issue = issues.split(";")[0].strip()
            if first_issue:
                flags.append(f"Verificar: {first_issue[:80]}")

    if any(kw in desc for kw in ["vendo por motivo de saúde", "vendo urgente", "necessito vender"]):
        flags.append("Linguagem de urgência — verificar autenticidade do anúncio")

    # Profile-aware red flags
    if user_profile and model_info:
        _dim_labels = {
            "economy": "economia", "comfort": "conforto", "driving": "condução",
            "practical": "praticidade", "status": "imagem", "reliability": "fiabilidade",
        }
        top_dim = max(user_profile.items(), key=lambda x: x[1])[0] if user_profile else ""
        mi_comfort = (model_info.get("comfort_score") or 5)
        mi_reliability = (model_info.get("avg_reliability") or model_info.get("reliability_score") or 5)
        mi_driving = (model_info.get("driving_fun_score") or 5)
        mi_practical = (model_info.get("family_score") or 5)

        if top_dim == "reliability" and mi_reliability < 7:
            flags.append("O teu perfil prioriza fiabilidade — este modelo tem histórico misto")
        if top_dim == "comfort" and mi_comfort < 5:
            flags.append("Conforto abaixo do que o teu perfil pede")
        if top_dim == "economy" and km_per_year and km_per_year > 18_000:
            flags.append("Consumo elevado para o teu perfil de economia")

    return flags[:5]


def _seller_analysis(
    seller_type: str,
    description: str,
    photo_count: int,
) -> str:
    desc = description.lower()
    has_history = any(kw in desc for kw in ["revisões", "manutenção", "histórico", "livro"])
    has_guarantee = any(kw in desc for kw in ["garantia", "garante"])
    has_contact_urgency = any(kw in desc for kw in ["urgente", "oportunidade", "único dono"])

    if seller_type == "privado":
        base = "Vendedor particular."
        if has_history:
            base += " Menciona histórico de manutenção — pedir comprovativos."
        else:
            base += " Sem menção de histórico — solicitar caderneta de revisões."
        if has_guarantee:
            base += " Garantia mencionada — clarificar condições."
    elif seller_type == "stand":
        base = "Stand profissional."
        if has_guarantee:
            base += " Garantia incluída — verificar período e cobertura."
        else:
            base += " Sem menção de garantia — negociar inclusão."
        if photo_count >= 8:
            base += " Apresentação cuidada."
    else:
        base = "Tipo de vendedor não identificado — confirmar antes de avançar."

    if has_contact_urgency:
        base += " Linguagem de urgência no anúncio — manter objetividade na negociação."

    return base[:300]


def _profile_fit(
    user_profile: Optional[dict],
    model_info: Optional[dict],
    deal_tier: str,
    brand_name: str,
    model_name: str,
) -> str:
    """Generate a one-sentence profile fit comment."""
    if not user_profile:
        return f"Análise baseada nas características do {brand_name} {model_name}."

    top_dim = max(user_profile.items(), key=lambda x: x[1])[0] if user_profile else ""
    dim_labels = {
        "economy": "economia", "comfort": "conforto", "driving": "prazer ao volante",
        "practical": "praticidade", "status": "imagem", "reliability": "fiabilidade",
    }
    dim_label = dim_labels.get(top_dim, top_dim)

    reliability = (model_info or {}).get("avg_reliability", 0) or 0
    comfort = (model_info or {}).get("comfort_score", 0) or 0

    if deal_tier == "forte":
        return f"Boa oportunidade para o teu perfil — prioridade {dim_label}, e este anúncio está bem posicionado no mercado."
    elif deal_tier == "razoavel":
        return f"Enquadra-se bem com a tua prioridade de {dim_label}, a preço de mercado."
    elif deal_tier == "cuidado":
        if top_dim == "economy":
            return f"Para o teu perfil de {dim_label}, o preço acima do mercado é um ponto a negociar."
        return f"Adequado ao teu perfil de {dim_label}, mas o preço merece negociação."
    else:
        return f"Com o teu perfil de {dim_label}, há provavelmente melhores opções no mercado por este valor."


# ── Verdict templates ─────────────────────────────────────────────────────────

VERDICT_REASON_TEMPLATES: dict[str, list[str]] = {
    "forte": [
        "Bom preço e quilometragem controlada — anúncio sólido.",
        "Abaixo do mercado com km razoável — vale investigar.",
        "Preço competitivo e vendedor particular — margem para negociar.",
        "Bem posicionado no mercado, poucas ressalvas identificadas.",
    ],
    "razoavel": [
        "Preço alinhado com o mercado, sem grandes alertas.",
        "Anúncio dentro da norma — nem oferta nem exagero.",
        "Condições normais de mercado, verificar estado físico.",
        "Preço justo, mas há espaço para negociar ligeiramente.",
    ],
    "cuidado": [
        "Acima do mercado ou quilometragem elevada — negociar.",
        "Alguns pontos merecem atenção antes de avançar.",
        "Preço ou uso acima do esperado — verificar com cautela.",
        "Anúncio com ressalvas — clarificar detalhes antes de contactar.",
    ],
    "evitar": [
        "Preço ou condições fora do mercado — procurar alternativas.",
        "Múltiplos sinais de alerta — investigar com muito cuidado.",
        "Quilometragem muito elevada ou preço suspeito.",
        "Anúncio com alertas sérios — não avançar sem inspeção física.",
    ],
}

import random as _random
def _verdict_reason(verdict: str, price_delta: float, km_per_year: Optional[float]) -> str:
    """Pick the most contextually accurate template."""
    templates = VERDICT_REASON_TEMPLATES.get(verdict, VERDICT_REASON_TEMPLATES["razoavel"])

    if verdict == "forte":
        if price_delta >= 0.4:
            return "Preço significativamente abaixo do mercado — anúncio muito competitivo."
        if km_per_year and km_per_year < 10_000:
            return "Baixa quilometragem anual e bom preço — vale claramente a pena investigar."
    elif verdict == "cuidado":
        if price_delta < -0.2:
            return "Preço acima do mercado — negociar antes de avançar."
        if km_per_year and km_per_year > 20_000:
            return "Quilometragem anual elevada — desgaste acima da média."
    elif verdict == "evitar":
        if km_per_year and km_per_year > 25_000:
            return "Quilometragem muito elevada — veículo com desgaste intensivo."
        if price_delta < -0.5:
            return "Preço acima do mercado em mais de 10% — existem alternativas melhores."

    return _random.choice(templates)


# ── Main entry point ──────────────────────────────────────────────────────────

def analyse(
    listing: dict,
    model_info: Optional[dict] = None,
    market_stats: Optional[dict] = None,
    user_profile: Optional[dict] = None,
) -> dict:
    """
    Run the rule-based analysis engine.

    listing: normalised listing dict from DB / scraper
        Expected keys: brand_name, model_name, year, km, price, seller_type,
                       description, photo_count, listing_age_days,
                       price_delta, km_per_year, deal_tier, deal_score
    model_info: from _get_model_info() — reliability, known_issues
    market_stats: from _get_market_stats() — avg_price
    user_profile: {economy, comfort, driving, practical, status, reliability}

    Returns the same JSON shape as the LLM analyser.
    """
    description  = listing.get("description", "") or ""
    title        = listing.get("title", "") or f"{listing.get('brand_name', '')} {listing.get('model_name', '')}".strip()
    seller_type  = listing.get("seller_type", "desconhecido") or "desconhecido"
    photo_count  = int(listing.get("photo_count") or 0)
    price_delta  = float(listing.get("price_delta") or 0.0)
    km_per_year  = listing.get("km_per_year")
    deal_tier    = listing.get("deal_tier", "razoavel")
    listing_price = listing.get("price")
    listing_age  = listing.get("listing_age_days")
    avg_price    = (market_stats or {}).get("avg_price")
    brand_name   = listing.get("brand_name", "")
    model_name   = listing.get("model_name", "")

    # ── Extras and spec detection ──
    extras    = _extract_extras(description)
    trim      = _detect_trim(description, title)
    spec_tier = _detect_spec_tier(description, extras)
    spec_val  = _spec_value_assessment(spec_tier, price_delta)

    # ── Flags ──
    green = _green_flags(price_delta, km_per_year, seller_type, extras, description, photo_count, listing_age, user_profile, model_info)
    red   = _red_flags(price_delta, km_per_year, listing_price, avg_price, seller_type, description, photo_count, listing_age, model_info, user_profile)

    # ── Verdict ──
    verdict        = deal_tier  # already computed by deal scoring
    verdict_reason = _verdict_reason(verdict, price_delta, km_per_year)

    # ── Seller analysis ──
    seller_analysis_text = _seller_analysis(seller_type, description, photo_count)

    # ── Profile fit ──
    profile_fit_text = _profile_fit(user_profile, model_info, deal_tier, brand_name, model_name)

    return {
        "verdict":                verdict,
        "verdict_reason":         verdict_reason,
        "green_flags":            green,
        "red_flags":              red,
        "seller_analysis":        seller_analysis_text,
        "profile_fit":            profile_fit_text,
        "trim_level":             trim,
        "spec_tier":              spec_tier,
        "key_extras":             extras,
        "spec_value_assessment":  spec_val,
        "_engine":                "rule-based",  # internal tag, stripped before sending to frontend
    }
