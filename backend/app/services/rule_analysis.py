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
    (["start/stop", "start stop", "start-stop"],                "Start/Stop"),
    (["keyless", "chave inteligente", "comfort access"],        "Keyless Entry"),
    (["cruise adaptativo", "adaptive cruise", "acc ", "distronic"], "Cruise adaptativo"),
    (["assistente de faixa", "lane assist", "lane keep"],       "Assistente de faixa"),
    (["travagem automática", "emergency braking", "aeb"],       "Travagem de emergência"),
    (["câmara 360", "camera 360", "surround view"],             "Câmara 360°"),
    (["dab", "rádio digital"],                                  "Rádio DAB"),
    (["matrix led", "matrix-led", "led matrix"],                "Faróis Matrix LED"),
    (["luz ambiente", "ambient light", "iluminação ambiente"],   "Iluminação ambiente"),
    (["park assist", "estacionamento automático"],               "Park Assist"),
    (["volante aquecido", "heated steering"],                    "Volante aquecido"),
    (["retrovisores elétricos", "espelhos elétricos"],           "Retrovisores elétricos"),
    (["isofix"],                                                 "ISOFIX"),
    (["único dono", "1 dono", "primeiro dono", "1.º dono"],     "Único dono"),
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

# ── Engine extraction ─────────────────────────────────────────────────────

_ENGINE_CODE_PATTERN = re.compile(
    r"\b([0-9]\.[0-9]{1,2})\s*"
    r"(TDI|TSI|TFSI|HDi|HDI|BlueHDi|BlueHDI|CDI|EcoBoost|EcoTec|"
    r"eTSI|eTDI|GTE|GTI|GTD|SCe|TCe|dCi|VTi|THP|PureTech|"
    r"T-GDi|CRDI|D4D|Turbo|MHEV|HEV|PHEV|Skyactiv|MultiJet|JTD|"
    r"EcoBlue|TGDi|MPI|GDi|Zetec)?",
    re.IGNORECASE,
)

# Known engine code patterns that appear directly in descriptions
_KNOWN_ENGINE_CODES = re.compile(
    r"\b(N47D20|N20B20|B47D20|B48B20|EA888|EA211|EA189|"
    r"K9K|M9T|H5F|F4R|"
    r"OM651|OM654|M264|M274|"
    r"DV6|DW10|EB2|EP6|"
    r"D4204T|D5244T|B4204T|"
    r"1KD|2GR|1NZ|2ZR|"
    r"G4FC|G4FJ|D4FB|"
    r"CRLB|CXDA|DFGA|DGDA)\b",
    re.IGNORECASE,
)


def _extract_engine_code(description: str) -> Optional[str]:
    """Extract engine code or displacement+type from description."""
    if not description:
        return None
    # First try known engine codes (most specific)
    m = _KNOWN_ENGINE_CODES.search(description)
    if m:
        return m.group(1).upper()
    # Then try displacement + type pattern (e.g. "2.0 TDI")
    m = _ENGINE_CODE_PATTERN.search(description)
    if m:
        disp = m.group(1)
        code = (m.group(2) or "").upper()
        return f"{disp} {code}".strip() if code else disp
    # BMW/Merc model designation fallback: "320d" → "2.0 Diesel", "116i" → "1.6 Gasolina"
    # Only match when displacement digits are sensible (first digit 0-5 → 0.X to 5.X litres)
    m = re.search(r"\b(\d)([0-5]\d)\s*([dDiIeE])?\b", description)
    if m:
        disp_raw = m.group(2)  # "20" from "320d"
        suffix = (m.group(3) or "").lower()
        disp = f"{disp_raw[0]}.{disp_raw[1]}"  # "20" → "2.0"
        fuel = {"d": "Diesel", "i": "Gasolina", "e": "Híbrido"}.get(suffix, "")
        return f"{disp} {fuel}".strip() if fuel else disp
    return None


def _generate_engine_analysis(
    engine_hint: Optional[str],
    fuel_type: str,
    km: int,
    known_issues: str,
    brand_name: str,
    model_name: str,
) -> Optional[str]:
    """Generate engine-specific analysis from available data."""
    parts = []
    fuel_lower = (fuel_type or "").lower()

    if engine_hint:
        parts.append(f"Motorização {engine_hint}")
        if fuel_type:
            parts[-1] += f" ({fuel_type})"
        parts[-1] += "."
    elif fuel_type:
        parts.append(f"Motor a {fuel_type.lower()}.")
    else:
        return None

    # Known issues → engine-specific warning
    if known_issues and known_issues not in ("", "Sem problemas conhecidos registados."):
        first_issue = known_issues.split(";")[0].strip()
        if first_issue and len(first_issue) > 5:
            parts.append(f"Problema registado neste modelo: {first_issue[:100]}.")

    # Km-based advice
    if km > 200000:
        parts.append(
            "Com mais de 200.000 km, os componentes de desgaste maior "
            "(turbo, injetores, caixa) devem ser verificados com cuidado."
        )
    elif km > 150000:
        parts.append("Acima de 150.000 km — pedir comprovativo das últimas revisões de maior intervalo.")
    elif km > 100000:
        parts.append("A partir dos 100.000 km, verificar histórico de correia/corrente de distribuição.")

    # Fuel-specific notes
    if "diesel" in fuel_lower or any(
        x in (engine_hint or "").lower() for x in ("tdi", "hdi", "bluehdi", "cdi", "dci", "d4d", "ecobl")
    ):
        if km > 120000:
            parts.append("Motor diesel com km elevados — verificar DPF, EGR e injetores.")
        elif km > 80000:
            parts.append("Motor diesel — verificar se o DPF está limpo e se faz percursos longos regularmente.")
    elif "híbrido" in fuel_lower or "hybrid" in fuel_lower:
        parts.append("Híbrido — verificar estado da bateria de alta tensão e ciclos de carga registados.")
    elif "elétrico" in fuel_lower or "electric" in fuel_lower:
        parts.append("Elétrico — confirmar saúde da bateria (SOH) e capacidade residual.")

    return " ".join(parts) if len(parts) >= 2 else (parts[0] if parts else None)


def _generate_extras_analysis(
    extras: list[str],
    spec_tier: str,
    price_delta: float,
    price: int,
    brand_name: str,
    model_name: str,
) -> str:
    """Generate an assessment of the equipment level vs. price."""
    if not extras:
        return (
            f"Não foram identificados extras na descrição do {brand_name} {model_name}. "
            "Isto pode indicar uma versão base, ou o vendedor simplesmente não listou o equipamento. "
            "Confirma diretamente antes de avaliar."
        )

    extras_str = ", ".join(extras[:8])
    parts = [f"Extras identificados: {extras_str}."]

    if spec_tier == "alto":
        parts.append("Equipamento acima da média para este modelo — valoriza o anúncio.")
        if price_delta >= 0.1:
            parts.append("Com o preço abaixo do mercado e bom equipamento, é uma proposta competitiva.")
        elif price_delta < -0.1:
            parts.append("Apesar do bom equipamento, o preço acima do mercado sugere margem para negociar.")
    elif spec_tier == "base":
        parts.append("Equipamento de nível base — versão de entrada.")
        if price_delta < -0.05 and price:
            parts.append("Para uma versão base, o preço pedido é elevado.")
    else:
        parts.append("Equipamento de nível médio, dentro do esperado para esta gama.")

    # Hint at valuable missing extras
    extras_lower = {e.lower() for e in extras}
    missing = []
    if not any("pele" in e or "couro" in e for e in extras_lower):
        missing.append("bancos em pele")
    if not any("panorâmico" in e or "panoramico" in e for e in extras_lower):
        missing.append("teto panorâmico")
    if not any("led" in e for e in extras_lower):
        missing.append("faróis LED")
    if not any("câmara" in e or "camara" in e or "camera" in e for e in extras_lower):
        missing.append("câmara traseira")

    if missing and spec_tier != "alto":
        parts.append(f"Não detetados: {', '.join(missing[:3])} — se presentes, valorizariam o carro.")

    return " ".join(parts)


def _generate_negotiation_script(
    price: int,
    avg_price: Optional[float],
    price_delta: float,
    km: int,
    listing_age: Optional[int],
    seller_type: str,
    engine_hint: Optional[str],
    known_issues: str,
    brand_name: str,
    model_name: str,
) -> Optional[str]:
    """Generate a concrete negotiation approach with first offer and arguments."""
    if not price:
        return None

    parts = []

    # ── First offer ──
    if avg_price and price > avg_price * 1.02:
        target = round(avg_price * 0.97 / 100) * 100
        parts.append(f"Começa por oferecer €{target:,}.")
    elif price_delta < -0.05:
        target = round(price * 0.93 / 100) * 100
        parts.append(f"Começa por oferecer €{target:,} (≈7% abaixo do pedido).")
    elif price_delta > 0.1:
        target = round(price * 0.97 / 100) * 100
        parts.append(f"O preço já é competitivo, mas tenta €{target:,} — nunca pagues o primeiro preço.")
    else:
        target = round(price * 0.95 / 100) * 100
        parts.append(f"Propõe €{target:,} como ponto de partida (≈5% de desconto).")

    # ── Arguments ──
    arguments = []
    if avg_price and price > avg_price:
        diff = int(price - avg_price)
        arguments.append(f"o preço está €{diff:,} acima da média de mercado")
    if km > 150000:
        arguments.append(f"com {km:,} km, há custos de manutenção previsíveis")
    elif km > 100000:
        arguments.append(f"{km:,} km implica atenção à manutenção de maior intervalo")
    if listing_age and listing_age > 30:
        arguments.append(f"o anúncio está publicado há {listing_age} dias")
    if known_issues and known_issues not in ("", "Sem problemas conhecidos registados."):
        first_issue = known_issues.split(";")[0].strip()[:60]
        if first_issue:
            arguments.append(f"problema do modelo ({first_issue}) justifica desconto preventivo")

    if arguments:
        parts.append(f"Argumentos: {'; '.join(arguments)}.")

    if seller_type in ("privado", "particular"):
        parts.append("Vendedor particular é tipicamente mais flexível — levanta dinheiro como argumento de fecho rápido.")
    elif seller_type in ("stand", "profissional"):
        parts.append("Num stand, pede garantia estendida ou revisão incluída como contrapartida.")

    return " ".join(parts) if parts else None


def _generate_verdict_narrative(
    verdict: str,
    brand_name: str,
    model_name: str,
    year: Optional[int],
    price: int,
    avg_price: Optional[float],
    km: int,
    km_per_year: Optional[float],
    extras: list[str],
    spec_tier: str,
    known_issues: str,
    seller_type: str,
) -> str:
    """Generate a 3-4 sentence final synthesis combining all data points."""
    parts = []
    car = f"{brand_name} {model_name}" + (f" de {year}" if year else "")

    # ── Opening — overall call ──
    if verdict == "forte":
        if km_per_year and km_per_year < 12000:
            parts.append(f"Este {car} apresenta quilometragem baixa e preço competitivo — boa oportunidade.")
        else:
            parts.append(f"Este {car} está bem posicionado no mercado — merece atenção séria.")
    elif verdict == "razoavel":
        parts.append(f"Este {car} está dentro do normal para o mercado — não é oferta, mas também não é caro.")
    elif verdict == "cuidado":
        parts.append(f"Este {car} requer cautela — há pontos que merecem investigação antes de avançar.")
    else:
        parts.append(f"Este {car} não se recomenda nas condições atuais — procura alternativas semelhantes.")

    # ── Price context ──
    if avg_price and price:
        diff_pct = abs((avg_price - price) / avg_price * 100)
        if price < avg_price * 0.95:
            parts.append(f"A €{price:,}, está cerca de {diff_pct:.0f}% abaixo da média de mercado (€{int(avg_price):,}).")
        elif price > avg_price * 1.05:
            parts.append(f"A €{price:,}, está {diff_pct:.0f}% acima da média (€{int(avg_price):,}) — há margem para negociar.")
        else:
            parts.append(f"O preço de €{price:,} está alinhado com a média de mercado (€{int(avg_price):,}).")

    # ── Equipment / km context ──
    if len(extras) >= 4 and spec_tier == "alto":
        parts.append(f"Equipamento acima da média ({len(extras)} extras), o que valoriza este exemplar.")
    elif len(extras) <= 1:
        parts.append("Equipamento limitado ou não listado — confirma com o vendedor o que inclui.")

    if km_per_year and km_per_year > 20000:
        parts.append("A quilometragem anual é elevada — espera mais desgaste nos componentes habituais.")

    # ── Known issues warning ──
    if known_issues and known_issues not in ("", "Sem problemas conhecidos registados.") and km > 100000:
        parts.append("Este modelo tem problemas conhecidos — faz inspeção mecânica independente antes de fechar negócio.")

    return " ".join(parts[:4])


def _generate_seller_read(
    seller_type: str,
    description: str,
    photo_count: int,
    listing_age: Optional[int],
) -> Optional[str]:
    """Analyze seller behavior from description and listing signals."""
    if not description and photo_count == 0:
        return None

    parts = []
    desc = description.lower()
    desc_len = len(description)

    # Description length signals
    if desc_len > 500:
        parts.append("Descrição detalhada — sinal positivo de transparência por parte do vendedor.")
    elif desc_len > 200:
        parts.append("Descrição com informação razoável, mas não exaustiva.")
    elif desc_len > 50:
        parts.append("Descrição curta — pode indicar pouca experiência ou tentativa de omitir informação.")
    else:
        parts.append("Descrição muito curta — pedir toda a informação por mensagem antes de visitar.")

    # Photo count signals
    if photo_count >= 15:
        parts.append(f"Com {photo_count} fotos, mostra o carro em detalhe — bom indicador de confiança.")
    elif photo_count >= 8:
        parts.append(f"{photo_count} fotos — apresentação adequada.")
    elif photo_count > 0:
        parts.append(f"Poucas fotos ({photo_count}) — pedir imagens do interior, motor e eventuais marcas.")

    # Keyword signals
    if any(w in desc for w in ["urgente", "oportunidade única", "necessito vender", "última semana"]):
        parts.append(
            "Linguagem de urgência — o vendedor quer despachar, o que pode ser vantagem "
            "na negociação mas exige verificar as razões da pressa."
        )
    elif any(w in desc for w in ["impecável", "imaculado", "como novo", "zero defeitos", "sem marcas"]):
        parts.append(
            "Termos como 'impecável' são comuns mas raramente verdadeiros num usado "
            "— verificar pessoalmente com olho crítico."
        )

    # Listing age context
    if listing_age and listing_age > 60:
        parts.append(
            f"Anúncio há {listing_age} dias — se fosse tão bom como descrito, já teria vendido."
        )
    elif listing_age and listing_age > 30:
        parts.append(f"Há {listing_age} dias no mercado — vendedor provavelmente mais recetivo a propostas.")

    return " ".join(parts[:3]) if parts else None


# ── Verdict templates ─────────────────────────────────────────────────────

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

    # ── Engine identification ──
    engine_code = _extract_engine_code(description)
    fuel_type   = listing.get("fuel_type", "") or ""
    km          = int(listing.get("km") or 0)
    known_issues = (model_info or {}).get("known_issues") or ""

    engine_analysis = _generate_engine_analysis(
        engine_code, fuel_type, km, known_issues, brand_name, model_name,
    )

    # ── Narrative enrichments (replace null sections when Gemini is down) ──
    extras_analysis = _generate_extras_analysis(
        extras, spec_tier, price_delta, int(listing_price or 0), brand_name, model_name,
    )

    negotiation_script = _generate_negotiation_script(
        int(listing_price or 0), avg_price, price_delta, km,
        listing_age, seller_type, engine_code, known_issues, brand_name, model_name,
    )

    year = listing.get("year")
    verdict_narrative = _generate_verdict_narrative(
        verdict, brand_name, model_name, year,
        int(listing_price or 0), avg_price, km, km_per_year,
        extras, spec_tier, known_issues, seller_type,
    )

    seller_read = _generate_seller_read(
        seller_type, description, photo_count, listing_age,
    )

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
        "engine_code":            engine_code,
        "engine_analysis":        engine_analysis,
        "extras_analysis":        extras_analysis,
        "negotiation_script":     negotiation_script,
        "verdict_narrative":      verdict_narrative,
        "seller_read":            seller_read,
        "_engine":                "rule-based",  # internal tag, stripped before sending to frontend
    }
