"""
Caractr Recommendation Engine v4.0

V4 changes:
- Selector V4: 4 new sliders (relationship, driving_style, presence) + aversion choice
- Removed p4_passengers — family context derived from p1_context == "familia"
- Stage B: structured profile signals (identity_bias, anti_pattern, engagement_bias, latent_override)
- Stage E: aversion penalty layer — hard asymmetric suppression based on p6_aversion
- Budget fields renamed p8_budget_min / p8_budget_max (last question, not emotional anchor)
- Dream car renamed p7_dream_car

Pipeline: Profile -> Signals -> Constraints -> Score -> Aversion Penalty -> Diversity -> Explain -> Log
"""

from sqlalchemy.orm import Session
from sqlalchemy import text
import uuid
import json
import math

from app.services.dealbreakers import get_dealbreakers


def _attach_dealbreakers(db: Session, results: list) -> None:
    """Enrich each recommendation in place with its critical known failures.
    Recalls are left out: the card doesn't know the car's year, so a
    model-wide recall list would flag most of the catalogue — they belong on
    the listing-level checklist. Runs only for the shortlisted models."""
    for r in results:
        r["dealbreakers"] = get_dealbreakers(db, r.get("model_id"), include_recalls=False)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CONSTANTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

DIMENSIONS = ["economy", "comfort", "driving", "practical", "status", "reliability"]

# Ranking cost of a critical known failure (see score_model Stage F).
CRITICAL_ISSUE_FACTOR = 0.88
CRITICAL_ISSUE_FACTOR_AVERSE = 0.75

BODY_TYPE_ADJACENCY = {
    "citadino":  ["compacto"],
    "compacto":  ["citadino", "suv", "berlina"],
    "suv":       ["compacto", "berlina", "mpv", "carrinha"],
    "berlina":   ["compacto", "suv", "carrinha"],   # carrinhas are highway-natural
    "mpv":       ["suv", "berlina"],
    "carrinha":  ["berlina", "suv"],
}

BRAND_STATUS = {
    "BMW": 0.85, "Mercedes-Benz": 0.90, "Audi": 0.80, "Volvo": 0.70,
    "Porsche": 0.95, "Lexus": 0.75, "Alfa Romeo": 0.70, "Land Rover": 0.80,
    "MINI": 0.60, "Cupra": 0.55, "DS": 0.55, "Tesla": 0.65, "Alpine": 0.75,
    "Volkswagen": 0.40, "Peugeot": 0.35, "Renault": 0.30, "Toyota": 0.35,
    "Honda": 0.35, "Mazda": 0.45, "Skoda": 0.30, "Hyundai": 0.30,
    "Kia": 0.30, "Ford": 0.30, "Opel": 0.25, "SEAT": 0.25,
    "Citroen": 0.25, "Nissan": 0.30, "Fiat": 0.20, "Dacia": 0.10,
    "Suzuki": 0.20, "Subaru": 0.35, "MG": 0.15, "BYD": 0.15,
    "Smart": 0.30, "Omoda": 0.10,
}

DREAM_BRAND_TRAITS = {
    "porsche":    {"economy": 0.0, "comfort": 0.4, "driving": 0.9, "practical": 0.1, "status": 0.9, "reliability": 0.5},
    "bmw":        {"economy": 0.1, "comfort": 0.5, "driving": 0.8, "practical": 0.3, "status": 0.7, "reliability": 0.4},
    "mercedes":   {"economy": 0.0, "comfort": 0.9, "driving": 0.4, "practical": 0.5, "status": 0.8, "reliability": 0.5},
    "audi":       {"economy": 0.1, "comfort": 0.7, "driving": 0.6, "practical": 0.5, "status": 0.7, "reliability": 0.5},
    "tesla":      {"economy": 0.6, "comfort": 0.6, "driving": 0.5, "practical": 0.5, "status": 0.6, "reliability": 0.5},
    "volvo":      {"economy": 0.2, "comfort": 0.8, "driving": 0.3, "practical": 0.7, "status": 0.5, "reliability": 0.7},
    "toyota":     {"economy": 0.7, "comfort": 0.5, "driving": 0.3, "practical": 0.7, "status": 0.2, "reliability": 0.95},
    "land_rover": {"economy": 0.0, "comfort": 0.7, "driving": 0.4, "practical": 0.7, "status": 0.8, "reliability": 0.2},
    "alfa_romeo": {"economy": 0.0, "comfort": 0.4, "driving": 0.9, "practical": 0.2, "status": 0.5, "reliability": 0.2},
    "lexus":      {"economy": 0.2, "comfort": 0.9, "driving": 0.3, "practical": 0.5, "status": 0.7, "reliability": 0.9},
    "volkswagen": {"economy": 0.4, "comfort": 0.5, "driving": 0.4, "practical": 0.6, "status": 0.3, "reliability": 0.5},
    "mazda":      {"economy": 0.4, "comfort": 0.5, "driving": 0.7, "practical": 0.4, "status": 0.3, "reliability": 0.7},
    "dacia":      {"economy": 0.9, "comfort": 0.2, "driving": 0.2, "practical": 0.7, "status": 0.0, "reliability": 0.5},
    "mini":       {"economy": 0.3, "comfort": 0.3, "driving": 0.7, "practical": 0.2, "status": 0.4, "reliability": 0.4},
    "jeep":       {"economy": 0.1, "comfort": 0.4, "driving": 0.4, "practical": 0.6, "status": 0.5, "reliability": 0.3},
    "hyundai":    {"economy": 0.6, "comfort": 0.5, "driving": 0.3, "practical": 0.6, "status": 0.2, "reliability": 0.6},
    "nenhuma":    {"economy": 0.2, "comfort": 0.2, "driving": 0.2, "practical": 0.2, "status": 0.1, "reliability": 0.3},
}

# Backward compatibility alias
DREAM_CAR_TRAITS = DREAM_BRAND_TRAITS

_DREAM_BRAND_DISPLAY = {
    "porsche":    "Porsche",     "bmw":        "BMW",
    "mercedes":   "Mercedes",    "audi":       "Audi",
    "tesla":      "Tesla",       "volvo":      "Volvo",
    "toyota":     "Toyota",      "land_rover": "Land Rover",
    "alfa_romeo": "Alfa Romeo",  "lexus":      "Lexus",
    "volkswagen": "Volkswagen",  "mazda":      "Mazda",
    "dacia":      "Dacia",       "mini":       "MINI",
    "jeep":       "Jeep",        "hyundai":    "Hyundai",
}

_DREAM_BRAND_IDENTITY = {
    "porsche":    "Performance sem compromisso",
    "bmw":        "Prazer de conduzir, sempre",
    "mercedes":   "Luxo e refinamento",
    "audi":       "Tecnologia e elegância",
    "tesla":      "O futuro, agora",
    "volvo":      "Segurança e conforto escandinavo",
    "toyota":     "Fiável como nada",
    "land_rover": "Aventura e presença",
    "alfa_romeo": "Paixão italiana ao volante",
    "lexus":      "Perfeição silenciosa",
    "volkswagen": "O clássico que funciona",
    "mazda":      "Elegância com alma de condutor",
    "dacia":      "O essencial, sem teatro",
    "mini":       "Personalidade urbana",
    "jeep":       "Liberdade sem limites",
    "hyundai":    "Valor inteligente",
}

# Headline templates: (profile_top, model_best) -> [primary, alternate]
HEADLINE_TEMPLATES = {
    ("economy", "economy"):     ["Cada cêntimo conta — e o {name} faz contas como ninguém.", "{name}: orçamento apertado, escolha inteligente."],
    ("economy", "reliability"):  ["Gasta pouco e não avaria. O melhor dos dois mundos.", "Carteira tranquila, mecânico esquecido."],
    ("economy", "comfort"):      ["Conforto que não cobra extra no fim do mês.", "Viajar bem não tem de custar caro."],
    ("economy", "driving"):      ["Quem disse que económico tem de ser aborrecido?", "Poupas no depósito, ganhas na curva."],
    ("economy", "practical"):    ["Espaço e eficiência no mesmo pacote.", "Cabe tudo — inclusive no orçamento."],
    ("economy", "status"):       ["Mais do que parece, menos do que custa.", "Presença discreta, valor real."],
    ("comfort", "comfort"):     ["Quilómetros que simplesmente desaparecem.", "O silêncio dentro deste carro é a primeira coisa que notas."],
    ("comfort", "reliability"):  ["Conforto em que podes confiar ano após ano.", "Suave e previsível — exatamente como queres."],
    ("comfort", "economy"):      ["Viaja bem sem gastar muito.", "Refinamento acessível para o dia a dia."],
    ("comfort", "driving"):      ["Suave no dia a dia, vivo quando a estrada pede.", "Conforto com um toque de carácter escondido."],
    ("comfort", "practical"):    ["Espaço e silêncio para toda a viagem.", "Conforto familiar sem compromissos de espaço."],
    ("comfort", "status"):       ["Refinamento que se sente em cada detalhe.", "Luxo que não precisa de gritar."],
    ("driving", "driving"):     ["A estrada é tua. O {name} sabe disso.", "Cada curva é uma conversa entre ti e a máquina."],
    ("driving", "comfort"):      ["Rápido quando queres, civilizado quando precisas.", "Desportivo de fato e gravata — sabe ser ambos."],
    ("driving", "status"):       ["Para quem não se contenta com mero transporte.", "Presença na estrada, presença na curva."],
    ("driving", "economy"):      ["Diversão sem remorsos no depósito.", "Prazer de conduzir que não castiga a carteira."],
    ("driving", "reliability"):  ["Emoção que não te deixa ficar a pé.", "Divertido E fiável — raro, mas existe."],
    ("driving", "practical"):    ["Prático no dia a dia, vivo na curva.", "Leva a família e ainda sobra carácter."],
    ("practical", "practical"):  ["Cabe tudo e todos. Sem compromissos.", "Pensado para quem tem a vida cheia — literalmente."],
    ("practical", "economy"):    ["Famílias inteligentes fazem contas inteligentes.", "Espaço máximo, custo mínimo."],
    ("practical", "comfort"):    ["Espaço e conforto para quem carrega o mundo.", "A família viaja bem — e nota-se."],
    ("practical", "reliability"): ["O carro em que a família pode confiar.", "Fiável e espaçoso — o que mais precisas?"],
    ("practical", "driving"):    ["Prático sim, aborrecido não.", "Quem disse que um carro familiar não pode ter alma?"],
    ("practical", "status"):     ["Família com estilo. Existe e chama-se {name}.", "Espaço com presença — não é preciso escolher."],
    ("status", "status"):       ["Chegar num {name} já é uma declaração.", "Alguns carros falam por si. Este é um deles."],
    ("status", "driving"):       ["Prestígio com substância debaixo do capô.", "Não é só bonito — conduz tão bem como parece."],
    ("status", "comfort"):       ["Luxo que se sente, não só que se vê.", "O interior deste carro é o teu refúgio."],
    ("status", "economy"):       ["Premium sem o preço premium.", "Imagem de topo sem o custo de topo."],
    ("status", "reliability"):   ["Prestígio que não dá dores de cabeça.", "Uma marca séria num pacote sério."],
    ("status", "practical"):     ["Elegância que não sacrifica o dia a dia.", "Estilo e substância no mesmo carro."],
    ("reliability", "reliability"): ["Liga, conduz, esquece que existe. {brand} sabe fazer isto.", "A mecânica mais provada que vais encontrar neste segmento."],
    ("reliability", "economy"):  ["Paz de espírito e carteira cheia.", "Fiável e barato de manter — a dupla perfeita."],
    ("reliability", "comfort"):  ["Fiável e confortável — a combinação perfeita.", "Sem surpresas no mecânico, sem desconforto na estrada."],
    ("reliability", "driving"):  ["Fiável não tem de significar aborrecido.", "A prova de que solidez e diversão coexistem."],
    ("reliability", "practical"): ["O carro que a família merece. Sem surpresas.", "Espaço fiável — para a família que não quer dramas."],
    ("reliability", "status"):   ["Uma marca sólida num pacote com presença.", "Fiabilidade com um toque de classe."],
}

# Tradeoff templates per dimension: [template_a, template_b]
TRADEOFF_TEMPLATES = {
    "economy": [
        "Não é o mais económico do segmento — mas o que oferece justifica cada cêntimo extra.",
        "Os custos de posse não são os mais baixos — compensa noutras áreas que te interessam.",
    ],
    "comfort": [
        "O conforto não é o forte principal — prioriza outras qualidades que valorizas.",
        "Em viagens longas pode não ser o mais relaxante, mas no dia a dia cumpre bem.",
    ],
    "driving": [
        "Não é o mais emocionante de conduzir — mas nem todos os dias precisas de adrenalina.",
        "A condução é competente sem ser empolgante — o forte está noutras dimensões.",
    ],
    "practical": [
        "Espaço não é o ponto forte — ideal para quem não precisa de carregar o mundo.",
        "Para famílias grandes pode ficar justo, mas para o dia a dia resolve bem.",
    ],
    "status": [
        "Não é a marca que vira cabeças — mas quem percebe de carros, percebe o valor.",
        "Discreto na presença — o que ganha é em substância, não em aparência.",
    ],
    "reliability": [
        "Histórico com alguns pontos a vigiar — importante confirmar manutenção em dia.",
        "Não tem a fiabilidade de um Toyota — exige mais atenção à manutenção preventiva.",
    ],
}

# Reason templates: category -> [(condition_fn, template_a, template_b), ...]
# Built dynamically in _build_reasons since they depend on model data


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PHASE 1: BUILD PROFILE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _resolve_float(raw, mapping: dict | None, default: float) -> float:
    """Convert string choice to float, or pass through float values for backward compat."""
    if mapping and isinstance(raw, str) and raw in mapping:
        return mapping[raw]
    try:
        return float(raw)
    except (TypeError, ValueError):
        return default

# ── String → float mappings for card-based choices (V5) ──
_P2_MAP = {"apenas_transporte": 0.15, "gosto_conduzir": 0.50, "adoro_conduzir": 0.85}
_P3_MAP = {"suave_previsivel": 0.15, "confortavel_com_alma": 0.50, "dinamico_envolvente": 0.85}
_P5_MAP = {"discreto": 0.15, "bom_aspeto": 0.50, "vire_cabecas": 0.90}
_BUDGET_RANGE_MAP = {
    "8_15":  (8000, 15000),
    "15_25": (15000, 25000),
    "25_40": (25000, 40000),
    "40_plus": (40000, 80000),
}


def build_profile(answers: dict) -> tuple:
    """
    V5: Build 6D normalized profile + structured signals from wizard answers.
    Accepts both V4 float values and V5 string card choices.
    Returns (profile_dict, signals_dict).
    """
    profile = {d: 0.0 for d in DIMENSIONS}

    # ── P1: Context ──
    ctx = answers.get("p1_context", "misto")
    ctx_weights = {
        "cidade":  {"economy": 0.18, "practical": 0.10},
        "estrada": {"comfort": 0.18, "driving": 0.08},
        "familia": {"practical": 0.28, "reliability": 0.12},
        "misto":   {"economy": 0.08, "comfort": 0.08, "practical": 0.08},
    }
    for dim, w in ctx_weights.get(ctx, ctx_weights["misto"]).items():
        profile[dim] += w

    # ── P2: Relationship with car ──
    rel = _resolve_float(answers.get("p2_relationship", 0.5), _P2_MAP, 0.5)
    profile["driving"]     += rel * 0.18
    profile["economy"]     += (1.0 - rel) * 0.12
    profile["reliability"] += (1.0 - rel) * 0.08

    # ── P3: Driving style + risk (merged P3+P4 in V5) ──
    style = _resolve_float(answers.get("p3_driving_style", 0.5), _P3_MAP, 0.5)
    # Driving style weights (original P3)
    profile["driving"] += style * 0.18
    profile["comfort"] += (1.0 - style) * 0.18
    # Risk/character weights (originally P4, now derived from driving style)
    risk = _resolve_float(answers.get("p4_risk"), None, style)  # V5: None → derive from p3; V4: explicit float
    profile["reliability"] += (1.0 - risk) * 0.18
    profile["driving"]     += risk * 0.14
    profile["status"]      += risk * 0.06

    # ── P5: Presence ──
    presence = _resolve_float(answers.get("p5_presence", 0.5), _P5_MAP, 0.5)
    profile["status"]  += presence * 0.20
    profile["economy"] += (1.0 - presence) * 0.06

    # ── P8: Budget (indirect signal — last question, light influence) ──
    budget_range = answers.get("p8_budget_range")
    if budget_range and budget_range in _BUDGET_RANGE_MAP:
        budget_min, budget_max = _BUDGET_RANGE_MAP[budget_range]
        answers["p8_budget_min"] = budget_min
        answers["p8_budget_max"] = budget_max
    else:
        budget_max = int(answers.get("p8_budget_max", 20000))
    if budget_max < 12000:
        profile["economy"]     += 0.14
        profile["reliability"] += 0.08
    elif budget_max < 20000:
        pass  # neutral band
    elif budget_max < 35000:
        profile["comfort"] += 0.06
        profile["status"]  += 0.04
    else:
        profile["status"]  += 0.12
        profile["driving"] += 0.06

    # ── P7: Dream brand (30% influence — identity correction) ──
    dream = answers.get("p7_dream_brand") or answers.get("p7_dream_car")
    if dream and dream in DREAM_BRAND_TRAITS:
        for dim in DIMENSIONS:
            profile[dim] += DREAM_BRAND_TRAITS[dream].get(dim, 0.0) * 0.30

    # ── Normalize ──
    total = sum(profile.values())
    if total > 0:
        profile = {k: round(v / total, 4) for k, v in profile.items()}
    else:
        # Safety: if all dimensions are zero (e.g. unrecognized answers),
        # fall back to a uniform distribution so scoring doesn't collapse.
        uniform = round(1.0 / len(DIMENSIONS), 4)
        profile = {d: uniform for d in DIMENSIONS}

    # ── Stage B: Structured profile signals ──
    signals = _build_signals(profile, answers, dream)

    return profile, signals


def _build_signals(profile: dict, answers: dict, dream: str | None) -> dict:
    """Emit structured qualitative signals alongside the numeric vector."""
    presence = _resolve_float(answers.get("p5_presence", 0.5), _P5_MAP, 0.5)
    rel      = _resolve_float(answers.get("p2_relationship", 0.5), _P2_MAP, 0.5)

    # identity_bias
    if presence >= 0.65 and profile.get("status", 0) > 0.18:
        identity_bias = "prestige-oriented" if profile.get("status", 0) > 0.28 else "expressive"
    elif presence < 0.3 and rel < 0.4:
        identity_bias = "understated"
    elif dream and dream in ("porsche_911", "bmw_m3", "alfa_giulia_qv", "mercedes_amg_gt",
                              "porsche", "bmw", "alfa_romeo", "mercedes"):
        identity_bias = "aspirational"
    else:
        identity_bias = "balanced"

    # anti_pattern (from aversion)
    aversion = answers.get("p6_aversion", "nenhuma")
    anti_pattern_map = {
        "fiabilidade": "low_reliability_not_acceptable",
        "conforto":    "low_comfort_not_acceptable",
        "espaco":      "low_space_not_acceptable",
        "potencia":    "low_power_not_acceptable",
    }
    anti_pattern = anti_pattern_map.get(aversion, "none")

    # engagement_bias
    style = _resolve_float(answers.get("p3_driving_style", 0.5), _P3_MAP, 0.5)
    if rel > 0.65 and style > 0.55:
        engagement_bias = "wants_to_enjoy_driving"
    elif presence > 0.65:
        engagement_bias = "wants_status_expression"
    else:
        engagement_bias = "wants_low_cognitive_load"

    # latent_override: dream brand suggests higher status/driving than explicit answers
    latent_override = False
    if dream and dream in DREAM_BRAND_TRAITS:
        dream_traits = DREAM_BRAND_TRAITS[dream]
        explicit_driving = profile.get("driving", 0)
        explicit_status  = profile.get("status", 0)
        if (dream_traits.get("driving", 0) > explicit_driving + 0.15 or
                dream_traits.get("status", 0) > explicit_status + 0.15):
            latent_override = True

    return {
        "identity_bias":   identity_bias,
        "anti_pattern":    anti_pattern,
        "engagement_bias": engagement_bias,
        "latent_override": latent_override,
    }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PROFILE NARRATIVE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

_DIM_LABELS = {
    "economy": "economia", "comfort": "conforto", "driving": "condução",
    "practical": "praticidade", "status": "imagem", "reliability": "fiabilidade",
}

_DREAM_BRAND_NAMES = _DREAM_BRAND_DISPLAY
# Backward compat alias
_DREAM_CAR_NAMES = _DREAM_BRAND_NAMES


def generate_profile_narrative(profile: dict, signals: dict, answers: dict) -> dict:
    """
    Template-based profile narrative. Zero LLM dependency.
    Returns human-readable sentences about the user's profile.
    """
    sorted_dims = sorted(profile.items(), key=lambda x: x[1], reverse=True)
    top2 = [d[0] for d in sorted_dims[:2]]
    top2_labels = [_DIM_LABELS.get(d, d) for d in top2]

    # Priorities sentence
    if len(top2_labels) >= 2:
        priorities = f"{top2_labels[0].capitalize()} e {top2_labels[1]} estão no topo das tuas prioridades."
    elif top2_labels:
        priorities = f"{top2_labels[0].capitalize()} é a tua prioridade principal."
    else:
        priorities = "Perfil equilibrado entre as várias dimensões."

    # Tension sentence (only when latent_override — dream brand reveals hidden preference)
    tension = None
    dream = answers.get("p7_dream_car") or answers.get("p7_dream_brand")
    if signals.get("latent_override") and dream and dream in _DREAM_BRAND_DISPLAY:
        brand_name = _DREAM_BRAND_DISPLAY[dream]
        tension = f"A tua marca de sonho ({brand_name}) revela uma atração escondida por performance — levámos isso em conta."

    # Aversion sentence
    aversion = None
    p6 = answers.get("p6_aversion", "nenhuma")
    aversion_map = {
        "fiabilidade": "Ficou claro: problemas mecânicos são inaceitáveis para ti.",
        "conforto":    "Ficou claro: desconforto é inaceitável para ti.",
        "espaco":      "Ficou claro: falta de espaço é inaceitável para ti.",
        "potencia":    "Ficou claro: falta de potência é inaceitável para ti.",
    }
    if p6 and p6 != "nenhuma":
        aversion = aversion_map.get(p6)

    # Identity sentence
    identity_map = {
        "prestige-oriented": "Perfil orientado para prestígio — a marca e a imagem importam.",
        "expressive":        "Perfil expressivo — o carro é uma extensão da tua personalidade.",
        "understated":       "Perfil discreto — valorizas substância em vez de aparência.",
        "aspirational":      "Perfil aspiracional — sabes o que queres e não te contentas com menos.",
        "balanced":          "Perfil equilibrado — pragmático, sem abdicar do que importa.",
    }
    identity = identity_map.get(signals.get("identity_bias", "balanced"))

    # Context sentence
    context_map = {
        "cidade":  "Conduzes maioritariamente em cidade — agilidade e eficiência são essenciais.",
        "estrada": "Conduzes maioritariamente em estrada — conforto e autonomia são prioritários.",
        "familia": "O carro serve toda a família — espaço e segurança estão no centro.",
        "misto":   "O teu perfil é misto — o carro tem de funcionar bem em todos os contextos.",
    }
    ctx = answers.get("p1_context", "misto")
    context = context_map.get(ctx)

    # One-liner summary
    if len(top2_labels) >= 2:
        summary = f"{top2_labels[0].capitalize()} e {top2_labels[1]} como prioridades."
    else:
        summary = "Perfil equilibrado."

    return {
        "priorities": priorities,
        "tension":    tension,
        "aversion":   aversion,
        "identity":   identity,
        "context":    context,
        "summary":    summary,
    }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PHASE 2: LOAD & BUILD MODEL VECTORS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

LOAD_MODELS_SQL = text("""
    SELECT
        vm.id, vm.name AS model_name, b.name AS brand_name,
        vm.body_type, vm.segment,
        AVG(e.consumption_mixed)::float AS avg_consumption,
        AVG(e.reliability_score)::float AS avg_reliability,
        AVG(e.maintenance_cost_year)::float AS avg_maintenance,
        MIN(e.consumption_mixed)::float AS best_consumption,
        MAX(e.power_hp) AS max_power,
        dc.comfort_score, dc.driving_fun_score,
        dc.city_score, dc.highway_score, dc.family_score,
        dc.description AS character_desc,
        (SELECT mp.avg_price FROM market_price_stats mp WHERE mp.model_id = vm.id ORDER BY mp.year DESC LIMIT 1) AS avg_price,
        (SELECT mp.min_price FROM market_price_stats mp WHERE mp.model_id = vm.id ORDER BY mp.year DESC LIMIT 1) AS min_price,
        (SELECT mp.max_price FROM market_price_stats mp WHERE mp.model_id = vm.id ORDER BY mp.year DESC LIMIT 1) AS max_price,
        -- Reliability trust data: aggregate across generations (latest generation preferred)
        (
            SELECT ROUND(AVG(g.reliability_score)::numeric, 2)
            FROM generations g WHERE g.model_id = vm.id AND g.reliability_score IS NOT NULL
        ) AS reliability_score,
        (
            SELECT ROUND(MIN(g.reliability_ci_low)::numeric, 2)
            FROM generations g WHERE g.model_id = vm.id AND g.reliability_ci_low IS NOT NULL
        ) AS reliability_ci_low,
        (
            SELECT ROUND(MAX(g.reliability_ci_high)::numeric, 2)
            FROM generations g WHERE g.model_id = vm.id AND g.reliability_ci_high IS NOT NULL
        ) AS reliability_ci_high,
        (
            SELECT g.reliability_data_quality
            FROM generations g
            WHERE g.model_id = vm.id AND g.reliability_data_quality IS NOT NULL
            ORDER BY g.year_start DESC LIMIT 1
        ) AS reliability_data_quality,
        -- Market trust data: from newest generation
        (
            SELECT g.market_value_p50
            FROM generations g
            WHERE g.model_id = vm.id AND g.market_value_p50 IS NOT NULL
            ORDER BY g.year_start DESC LIMIT 1
        ) AS market_p50,
        (
            SELECT g.market_value_band
            FROM generations g
            WHERE g.model_id = vm.id AND g.market_value_band IS NOT NULL
              AND g.market_value_band != '{}'::jsonb
            ORDER BY g.year_start DESC LIMIT 1
        ) AS market_band,
        (
            SELECT g.market_value_as_of
            FROM generations g
            WHERE g.model_id = vm.id AND g.market_value_as_of IS NOT NULL
            ORDER BY g.year_start DESC LIMIT 1
        ) AS market_as_of
    FROM vehicle_models vm
    JOIN brands b ON b.id = vm.brand_id
    LEFT JOIN engines e ON e.model_id = vm.id
    LEFT JOIN driving_character dc ON dc.model_id = vm.id
    GROUP BY vm.id, vm.name, b.name, vm.body_type, vm.segment,
             dc.comfort_score, dc.driving_fun_score, dc.city_score,
             dc.highway_score, dc.family_score, dc.description
    HAVING COUNT(e.id) > 0
""")


def load_models(db: Session) -> list:
    """Load all models with aggregated data, grouped by model."""
    rows = db.execute(LOAD_MODELS_SQL).fetchall()
    # Models with a critical known failure (the deal-breaker tier — only sourced
    # research or a human can set it). Recalls are deliberately NOT here: they
    # are normally fixed free at the dealer, so they warn but never demote.
    critical_ids = {r[0] for r in db.execute(text("""
        SELECT DISTINCT e.model_id FROM engine_issues ei
        JOIN engines e ON e.id = ei.engine_id
        WHERE lower(ei.severity) = 'critico'
    """)).fetchall()}
    models = []
    for row in rows:
        avg_price = int(row.avg_price) if row.avg_price else None
        if not avg_price:
            continue  # skip models without price data (hard constraint)
        
        m = {
            "id": row.id,
            "model_name": row.model_name,
            "brand_name": row.brand_name,
            "full_name": f"{row.brand_name} {row.model_name}",
            "body_type": row.body_type or "compacto",
            "segment": row.segment or "medio",
            "avg_price": avg_price,
            "min_price": int(row.min_price) if row.min_price else avg_price,
            "max_price": int(row.max_price) if row.max_price else avg_price,
            "avg_consumption": float(row.avg_consumption) if row.avg_consumption else 7.0,
            "avg_reliability": float(row.avg_reliability) if row.avg_reliability else 5.0,
            "avg_maintenance": float(row.avg_maintenance) if row.avg_maintenance else 500.0,
            "best_consumption": float(row.best_consumption) if row.best_consumption else None,
            "max_power": int(row.max_power) if row.max_power else None,
            "comfort_score": int(row.comfort_score) if row.comfort_score else 5,
            "driving_fun_score": int(row.driving_fun_score) if row.driving_fun_score else 5,
            "city_score": int(row.city_score) if row.city_score else 5,
            "highway_score": int(row.highway_score) if row.highway_score else 5,
            "family_score": int(row.family_score) if row.family_score else 5,
            "character_desc": row.character_desc or "",
            # Trust data — from generations table
            "reliability_score":        float(row.reliability_score) if row.reliability_score else None,
            "reliability_ci_low":       float(row.reliability_ci_low) if row.reliability_ci_low else None,
            "reliability_ci_high":      float(row.reliability_ci_high) if row.reliability_ci_high else None,
            "reliability_data_quality": row.reliability_data_quality or "prior_only",
            "market_p50":               int(row.market_p50) if row.market_p50 else None,
            "market_band":              dict(row.market_band) if row.market_band else None,
            "market_as_of":             str(row.market_as_of) if row.market_as_of else None,
            "has_critical_issue":       row.id in critical_ids,
        }
        m["vector"] = _build_model_vector(m)
        models.append(m)
    return models


def _build_model_vector(m: dict) -> dict:
    """Compute 6D vector (0-1) for a model from its aggregated data."""
    # Economy: 60% consumption inverse + 40% maintenance inverse
    # EVs store consumption in kWh/100km (typically 14-22); petrol/diesel in L/100km (<= 12).
    # Anything above 10 is treated as an EV — convert to petrol-equivalent cost at
    # ~0.20 €/kWh vs ~1.70 €/L: effective_L = kWh * 0.20 / 1.70
    avg_c = m["avg_consumption"]
    if avg_c > 10.0:
        avg_c = avg_c * 0.20 / 1.70  # kWh → petrol-cost-equivalent L/100km
    eco_c = max(0, min(1, (12.0 - avg_c) / 9.0))
    eco_m = max(0, min(1, (1200 - m["avg_maintenance"]) / 1000.0))
    economy = eco_c * 0.6 + eco_m * 0.4

    comfort = m["comfort_score"] / 10.0
    driving = m["driving_fun_score"] / 10.0
    practical = (m["family_score"] / 10.0) * 0.6 + (m["city_score"] / 10.0) * 0.4

    brand_s = BRAND_STATUS.get(m["brand_name"], 0.25)
    seg_bonus = {"economico": 0.0, "medio": 0.15, "premium": 0.40, "luxo": 0.60}.get(m["segment"], 0.1)
    status = min(1.0, brand_s * 0.7 + seg_bonus * 0.3)

    reliability = m["avg_reliability"] / 10.0

    return {d: round(v, 3) for d, v in zip(
        DIMENSIONS, [economy, comfort, driving, practical, status, reliability]
    )}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PHASE 3: HARD CONSTRAINTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def apply_hard_constraints(models: list, answers: dict) -> tuple:
    """V5: Returns (passed, stretch) lists. Family derived from p1_context."""
    budget_max    = int(answers.get("p8_budget_max", 25000))
    budget_min    = int(answers.get("p8_budget_min", 0))
    stretch_limit = budget_max * 1.15
    ctx           = answers.get("p1_context", "misto")
    is_family     = ctx == "familia"

    passed, stretch = [], []
    for m in models:
        if m["avg_price"] > stretch_limit:
            continue
        # Budget floor: when the user has real budget (>=25k), exclude deeply-under-budget models
        # avg_price < 58% of budget_min means the user is a full tier above what this model offers
        if budget_min >= 25000 and m["avg_price"] < budget_min * 0.58:
            continue
        # Family context: no city cars; compactos/berlinas need solid family score
        if is_family:
            if m["body_type"] == "citadino":
                continue
            if m["body_type"] in ("compacto", "berlina") and m["family_score"] < 7:
                continue
        # Highway context: city cars have no place on a road trip
        if ctx == "estrada" and m["body_type"] == "citadino":
            continue
        # City context: MPVs need good city score
        if ctx == "cidade" and m["body_type"] == "mpv" and m["city_score"] < 5:
            continue

        if m["avg_price"] > budget_max:
            stretch.append(m)
        else:
            passed.append(m)
    return passed, stretch


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PHASE 4: SCORING
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def score_model(model: dict, profile: dict, answers: dict) -> float:
    """V4: Score = base × penalty × interactions × context × aversion_multiplier."""
    mv  = model["vector"]
    ctx = answers.get("p1_context", "misto")

    # ── Stage D: Base dot product ──
    # For profiles where the user is explicitly non-status-oriented (presence < 0.30),
    # compress the status dimension's contribution — prevents premium brand "bleed"
    # from pulling their models into slots they don't deserve on profile fit alone.
    presence = _resolve_float(answers.get("p5_presence", 0.5), _P5_MAP, 0.5)
    if presence < 0.30:
        mv = dict(mv)
        # Pull status score toward the mean (0.35) — softens the premium gap
        mv["status"] = mv["status"] * 0.50 + 0.35 * 0.50
    base = sum(profile[d] * mv[d] for d in DIMENSIONS)

    # ── Stage D: Soft penalties (profile need vs. model offer) ──
    penalty = 1.0
    penalty_checks = [
        ("economy",     0.25, 0.30, 3.0, 0.30),
        ("reliability", 0.20, 0.40, 2.5, 0.40),
        ("practical",   0.25, 0.30, 3.0, 0.30),
        ("driving",     0.25, 0.30, 2.0, 0.50),
    ]
    for dim, prof_thresh, model_thresh, severity, floor in penalty_checks:
        if profile[dim] > prof_thresh and mv[dim] < model_thresh:
            gap = model_thresh - mv[dim]
            penalty *= max(floor, 1.0 - gap * severity)

    # ── Stage D: Feature cross bonuses ──
    interaction = 1.0
    crosses = [
        ("economy",  0.20, "reliability", 0.18, "economy",  0.5, "reliability", 0.7, 0.15),
        ("driving",  0.20, "status",      0.10, "driving",  0.6, "status",      0.4, 0.12),
        ("comfort",  0.20, "status",      0.15, "comfort",  0.7, "status",      0.5, 0.10),
        ("practical",0.20, "economy",     0.18, "practical",0.5, "economy",     0.4, 0.12),
        ("driving",  0.18, "economy",     0.18, "driving",  0.5, "economy",     0.4, 0.10),
    ]
    for pd1, pt1, pd2, pt2, md1, mt1, md2, mt2, bonus in crosses:
        if profile[pd1] > pt1 and profile[pd2] > pt2 and mv[md1] > mt1 and mv[md2] > mt2:
            interaction += bonus

    # ── Context boost — stronger signal so context shapes results meaningfully ──
    if ctx == "cidade":
        interaction += (model["city_score"] / 10.0) * 0.12
    elif ctx == "estrada":
        interaction += (model["highway_score"] / 10.0) * 0.14

    # Reliability cross bonus: highway drivers who value reliability get rewarded
    # for choosing a model that actually delivers on that axis (Toyota/Volvo types).
    # Stronger signal needed to break through the base-score advantage of sporty berliners.
    if ctx == "estrada" and profile.get("reliability", 0) > 0.18 and model["avg_reliability"] > 8.0:
        interaction += 0.10

    # EV/hybrid boost for city + economy context
    # Detects EVs (best_consumption stored in kWh > 10) and efficient hybrids (< 5 L/100km)
    if profile.get("economy", 0) > 0.18:
        best_c = model.get("best_consumption")
        if best_c and (best_c > 10.0 or best_c < 5.0):  # EV (kWh) or efficient hybrid
            boost = 0.08 if ctx == "cidade" else 0.04
            interaction += boost

    # Soft penalty for non-SUV/MPV body types in familia context.
    # Penalty is steeper when the profile also has a high driving dimension —
    # driving enthusiasts who say "familia" are picking a car, not a taxi.
    if ctx == "familia" and model["body_type"] in ("berlina", "compacto"):
        penalty_factor = 0.72 if profile.get("driving", 0) > 0.20 else 0.82
        interaction *= penalty_factor

    base_score = base * penalty * interaction

    # ── Stage E: Aversion penalty — hard asymmetric suppression ──
    aversion = answers.get("p6_aversion", "nenhuma")
    aversion_multiplier = _apply_aversion_penalty(model, aversion, ctx)

    # ── Stage F: Deal-breaker demotion — a critical known failure (design flaw,
    # not fixed by a recall) costs ranking but never removes the car; the
    # warning banner still explains why. Stronger when the user is averse to
    # unreliability.
    critical = 1.0
    if model.get("has_critical_issue"):
        critical = CRITICAL_ISSUE_FACTOR_AVERSE if aversion == "fiabilidade" else CRITICAL_ISSUE_FACTOR

    return round(base_score * aversion_multiplier * critical, 4)


def _apply_aversion_penalty(model: dict, aversion: str, ctx: str) -> float:
    """
    Stage E: Smooth asymmetric penalties for declared aversion.
    Uses linear decay below a threshold so penalties are monotonic —
    a model with a slightly worse score always gets a worse penalty
    (no cliff inversions between adjacent tiers).
    """

    def _smooth_penalty(score: float, threshold: float, floor: float) -> float:
        """Linear decay from 1.0 at threshold to floor at 0."""
        if score >= threshold:
            return 1.0
        return max(floor, floor + (1.0 - floor) * (score / threshold))

    if aversion == "fiabilidade":
        # Below 7.5 → smooth decay to 0.30 at score=0
        return _smooth_penalty(model["avg_reliability"], 7.5, 0.30)

    elif aversion == "conforto":
        return _smooth_penalty(model["comfort_score"], 7.0, 0.35)

    elif aversion == "espaco":
        threshold = 6.0 if ctx == "familia" else 5.0
        return _smooth_penalty(model["family_score"], threshold, 0.35)

    elif aversion == "potencia":
        return _smooth_penalty(model["driving_fun_score"], 6.0, 0.40)

    return 1.0  # no penalty


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PHASE 5: DIVERSE SELECTION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def select_diverse_top5(scored: list, stretch_scored: list, answers: dict) -> list:
    """
    V5: Pick 5 with diversity rules.
    - Brand cap: premium brands (status>=0.60) max 2; mid/low max 1
    - Segment cap: max 3 premium/luxo — but NOT applied in passes 1-2 so body-type
      diversity (e.g. Volvo V60 carrinha) isn't blocked before variety is established
    - Citadinos excluded from misto adjacent pass (only reach the list as wildcard)
    """
    ctx = answers.get("p1_context", "misto")
    primary_body = _infer_primary_body(ctx)
    adjacent = BODY_TYPE_ADJACENCY.get(primary_body, [])

    all_ranked = sorted(scored, key=lambda x: x["_score"], reverse=True)
    stretch_ranked = sorted(stretch_scored, key=lambda x: x["_score"], reverse=True)
    top_score = all_ranked[0]["_score"] if all_ranked else 0

    selected = []
    brands = {}
    segments: dict = {}  # segment → count; premium/luxo capped at 3

    def _can_add(m, apply_seg_cap: bool = True):
        seg = m.get("segment", "medio")
        seg_premium = seg in ("premium", "luxo")
        # Segment cap is optional: skip it in early passes so body-type diversity
        # isn't crowded out by segment saturation before variety is established.
        seg_ok = (segments.get(seg, 0) < 3) if (seg_premium and apply_seg_cap) else True
        # Premium brands (status >= 0.60): max 2 per brand — their lineup is diverse
        # Mid/low brands: max 1 — two same-brand models in the same list feels like one choice
        brand_status = BRAND_STATUS.get(m["brand_name"], 0.25)
        brand_cap = 2 if brand_status >= 0.60 else 1
        return (
            brands.get(m["brand_name"], 0) < brand_cap
            and m["id"] not in {s["id"] for s in selected}
            and seg_ok
        )

    def _record(m):
        brands[m["brand_name"]] = brands.get(m["brand_name"], 0) + 1
        seg = m.get("segment", "medio")
        segments[seg] = segments.get(seg, 0) + 1

    # Pass 1: best from primary + adjacent body types (no seg cap — body variety first)
    for m in all_ranked:
        if len(selected) >= 4:
            break
        if m["body_type"] == primary_body or m["body_type"] in adjacent:
            # Citadinos are too small for misto; reserve them for wildcard only
            if ctx == "misto" and m["body_type"] == "citadino":
                continue
            if _can_add(m, apply_seg_cap=False):
                selected.append(m)
                _record(m)

    # Pass 2: ensure at least 1 adjacent body type is represented (no seg cap)
    has_adjacent = any(m["body_type"] in adjacent for m in selected)
    if not has_adjacent:
        for m in all_ranked:
            if m["body_type"] in adjacent:
                if ctx == "misto" and m["body_type"] == "citadino":
                    continue
                if _can_add(m, apply_seg_cap=False):
                    selected.append(m)
                    _record(m)
                    break

    # Pass 2b: for estrada, guarantee a carrinha slot if one exists within 30% of top score.
    # Carrinhas are the natural highway companion but are rare in the DB; without this,
    # berliners and SUVs fill all 4+1 slots before the estate body type gets a look.
    if ctx == "estrada" and len(selected) < 5:
        has_carrinha = any(m["body_type"] == "carrinha" for m in selected)
        if not has_carrinha:
            for m in all_ranked:
                if m["body_type"] == "carrinha" and m["_score"] >= top_score * 0.70:
                    if _can_add(m, apply_seg_cap=False):
                        selected.append(m)
                        _record(m)
                        break

    # Pass 3: stretch (max 1, only if score >= 85% of best)
    if len(selected) < 5 and stretch_ranked:
        best_stretch = stretch_ranked[0]
        if best_stretch["_score"] >= (top_score * 0.85) and _can_add(best_stretch):
            best_stretch["is_stretch"] = True
            selected.append(best_stretch)
            _record(best_stretch)

    # Pass 4: wildcard (unexpected body type, score > 65% of best; seg cap applies)
    if len(selected) < 5:
        wildcard_threshold = top_score * 0.65
        for m in all_ranked:
            if _can_add(m):
                is_unexpected = m["body_type"] not in [primary_body] + adjacent
                if is_unexpected and m["_score"] >= wildcard_threshold:
                    m["is_wildcard"] = True
                    selected.append(m)
                    _record(m)
                    break

    # Pass 5: fill remaining (seg cap applies)
    # Citadinos are only excluded from misto in passes 1-2 where they would crowd out
    # compactos/SUVs/berlinas as the primary recommendations. In pass 5 they are allowed
    # as legitimate fallback — otherwise tiny-budget profiles end up with < 5 results.
    for m in all_ranked:
        if len(selected) >= 5:
            break
        if _can_add(m):
            selected.append(m)
            _record(m)

    return selected[:5]


def _infer_primary_body(ctx: str) -> str:
    """V4: infer primary body type from context alone (passengers removed)."""
    if ctx == "familia":
        return "suv"
    if ctx == "cidade":
        return "compacto"
    if ctx == "estrada":
        return "berlina"
    return "compacto"  # misto default


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# LLM EXPLANATION GENERATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

_P2_LABEL = {
    "apenas_transporte": "apenas transporte, sem envolvimento",
    "gosto_conduzir":    "gosta de conduzir, aprecia uma boa viagem",
    "adoro_conduzir":    "adora conduzir, o carro é uma extensão de si",
}
_P3_LABEL = {
    "suave_previsivel":     "prefere condução suave e previsível",
    "confortavel_com_alma": "quer conforto com alguma alma ao volante",
    "dinamico_envolvente":  "quer dinamismo e envolvimento total",
}
_P5_LABEL = {
    "discreto":     "quer um carro discreto, sem chamar atenção",
    "bom_aspeto":   "quer bom aspeto sem ostentação",
    "vire_cabecas": "quer presença e impacto visual",
}
_P6_LABEL = {
    "fiabilidade": "problemas mecânicos/avarias",
    "conforto":    "desconforto/suspensão dura",
    "espaco":      "falta de espaço",
    "potencia":    "falta de resposta do motor",
}
_CTX_LABEL = {
    "cidade":  "maioritariamente cidade (trânsito, estacionamento)",
    "estrada": "maioritariamente estrada (autoestrada, viagens longas)",
    "familia": "uso familiar (escola, compras, todos a bordo)",
    "misto":   "uso misto (cidade e estrada)",
}


def _build_llm_prompt(top5: list, profile: dict, answers: dict) -> str:
    """Build the Gemini prompt for batch recommendation generation."""
    dim_pt = {
        "economy": "economia/custo", "comfort": "conforto",
        "driving": "prazer de condução", "practical": "praticidade",
        "status": "imagem/presença", "reliability": "fiabilidade",
    }
    sorted_profile = sorted(profile.items(), key=lambda x: x[1], reverse=True)
    profile_str = ", ".join(
        f"{dim_pt.get(k, k)} {int(v*100)}%" for k, v in sorted_profile
    )

    p1 = _CTX_LABEL.get(answers.get("p1_context", "misto"), "uso misto")
    p2 = _P2_LABEL.get(str(answers.get("p2_relationship", "")), "gosta de conduzir")
    p3 = _P3_LABEL.get(str(answers.get("p3_driving_style", "")), "conforto com alma")
    p5 = _P5_LABEL.get(str(answers.get("p5_presence", "")), "bom aspeto")
    p6 = _P6_LABEL.get(answers.get("p6_aversion", "nenhuma"), "nenhuma")
    dream = answers.get("p7_dream_brand") or answers.get("p7_dream_car")
    dream_str = f"{_DREAM_BRAND_DISPLAY.get(dream, dream)}" if dream else "nenhuma"
    budget_min = int(answers.get("p8_budget_min", 8000))
    budget_max = int(answers.get("p8_budget_max", 25000))

    models_json = []
    for rank, m in enumerate(top5, 1):
        mv = m["vector"]
        models_json.append({
            "rank": rank,
            "name": m["full_name"],
            "brand": m["brand_name"],
            "body_type": m["body_type"],
            "segment": m["segment"],
            "score": round(m["_score"], 3),
            "dimensions": {dim_pt.get(k, k): round(v, 2) for k, v in mv.items()},
            "price_range": f"€{m['min_price']:,}–€{m['max_price']:,}" if m.get("min_price") else "N/D",
            "is_wildcard": m.get("is_wildcard", False),
        })

    import json as _json
    models_str = _json.dumps(models_json, ensure_ascii=False, indent=2)

    return f"""És um especialista em automóveis a ajudar um comprador português. Fala em português de Portugal (não brasileiro). Usa "tu" e linguagem direta, como um amigo especialista — não um vendedor.

PERFIL DO UTILIZADOR:
- Contexto: {p1}
- Relação com o carro: {p2}
- Estilo de condução: {p3}
- Imagem: {p5}
- Inaceitável: {p6}
- Marca de sonho: {dream_str}
- Orçamento: €{budget_min:,}–€{budget_max:,}
- Perfil calculado: {profile_str}

MODELOS RECOMENDADOS (por ordem de compatibilidade):
{models_str}

TAREFA: Para cada modelo, gera um headline curto (máximo 12 palavras) e 2-3 razões (cada uma 1 frase, máximo 20 palavras) e um tradeoff honesto (1 frase, máximo 15 palavras).

REGRAS CRÍTICAS:
1. Cada headline DEVE ser diferente em tom e ângulo — proibido repetir estruturas
2. Cada razão DEVE referenciar algo específico do perfil do utilizador (contexto, estilo, budget, intolerâncias)
3. Nunca uses chavões genéricos como "excelente relação qualidade/preço" ou "ótima opção"
4. O tradeoff deve ser honesto e específico ao perfil — o que este utilizador em particular pode não gostar
5. Para wildcards (is_wildcard: true), menciona que é uma opção fora da zona habitual mas que vale a pena considerar
6. Tom: direto, conversacional, confiante — como um amigo que percebe de carros

Responde APENAS com JSON válido neste formato exato:
{{
  "recommendations": [
    {{
      "rank": 1,
      "headline": "...",
      "reasons": ["...", "...", "..."],
      "tradeoff": "..."
    }},
    ...
  ],
  "profile_narrative": {{
    "summary": "...",
    "priorities": "...",
    "tension": null,
    "aversion": "...",
    "identity": "...",
    "context": "..."
  }}
}}

Para profile_narrative: summary é 1 frase curta sobre o perfil, priorities descreve as dimensões dominantes, tension só se a marca de sonho revela uma atração escondida (senão null), aversion sobre o que é inaceitável, identity sobre o tipo de condutor, context sobre o uso do carro."""


def _generate_explanations_llm(top5: list, profile: dict, answers: dict) -> dict | None:
    """
    Try to generate all explanations + profile narrative via Gemini.
    Returns dict with 'recommendations' list and 'profile_narrative', or None on failure.
    """
    try:
        from app.services.llm_client import generate_json, LLMError, llm_available
        if not llm_available():
            return None

        prompt = _build_llm_prompt(top5, profile, answers)
        result = generate_json(prompt, max_tokens=1200)

        recs = result.get("recommendations", [])
        if len(recs) != len(top5):
            return None

        return result
    except Exception as e:
        import logging as _logging
        _logging.getLogger(__name__).warning(f"LLM generation failed, falling back to templates: {e}")
        return None


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PHASE 6: EXPLANATIONS (with full context of all 5)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def generate_all_explanations(top5: list, profile: dict, answers: dict, llm_result: dict | None = None) -> list:
    """
    Generate explanations for ALL 5 models at once.
    Uses pre-computed llm_result if provided; falls back to template engine per model.
    """
    sorted_profile = sorted(profile.items(), key=lambda x: x[1], reverse=True)
    profile_top1 = sorted_profile[0][0]
    profile_top2 = sorted_profile[1][0]

    used_headline_keys = []
    used_tradeoff_dims = set()
    results = []

    for rank, m in enumerate(top5, 1):
        mv = m["vector"]
        model_sorted = sorted(mv.items(), key=lambda x: x[1], reverse=True)
        model_best = model_sorted[0][0]
        model_2nd = model_sorted[1][0]
        model_3rd = model_sorted[2][0] if len(model_sorted) > 2 else model_best

        # Use LLM output if available for this rank
        llm_rec = None
        if llm_result:
            llm_recs = llm_result.get("recommendations", [])
            matching = [r for r in llm_recs if r.get("rank") == rank]
            if matching:
                llm_rec = matching[0]

        if llm_rec:
            headline = llm_rec.get("headline", "")
            reasons  = llm_rec.get("reasons", [])[:3]
            tradeoff = llm_rec.get("tradeoff", "")
        else:
            # ── Template fallback ──
            headline = _pick_headline(m, profile_top1, profile_top2, model_best, model_2nd, model_3rd, used_headline_keys)
            reasons  = _build_reasons(m, profile, profile_top1, profile_top2, answers)
            if m.get("is_wildcard"):
                reasons.append("Fora da tua zona habitual, mas vale a pena olhar.")
            tradeoff = _build_tradeoff(m, profile, top5, answers, used_tradeoff_dims)

        # Build trust panel data
        reliability_trust = None
        if m.get("reliability_score") is not None:
            reliability_trust = {
                "score":        m["reliability_score"],
                "ci_low":       m["reliability_ci_low"],
                "ci_high":      m["reliability_ci_high"],
                "data_quality": m["reliability_data_quality"],
            }

        market_trust = None
        if m.get("market_p50"):
            market_trust = {
                "p50":          m["market_p50"],
                "band":         m["market_band"],
                "as_of":        m["market_as_of"],
            }

        results.append({
            "rank": rank,
            "model_id": m["id"],
            "model_name": m["model_name"],
            "brand_name": m["brand_name"],
            "full_name": m["full_name"],
            "body_type": m["body_type"],
            "segment": m["segment"],
            "headline": headline,
            "reasons": reasons[:3],
            "tradeoff": tradeoff,
            "price_range": {"min": m["min_price"], "max": m["max_price"]},
            "is_stretch": m.get("is_stretch", False),
            "is_wildcard": m.get("is_wildcard", False),
            "reliability": reliability_trust,
            "market": market_trust,
        })

    return results


def _pick_headline(model: dict, prof_top1: str, prof_top2: str,
                   model_best: str, model_2nd: str, model_3rd: str,
                   used_keys: list) -> str:
    """
    Pick a unique headline by tracking template KEYS, not rendered strings.
    Each model must use a different (profile_dim, model_dim, variant) combo.
    """
    name = model["full_name"]
    brand = model["brand_name"]

    model_segment = model.get("segment", "medio")
    is_premium_model = model_segment in ("premium", "luxo")

    # For premium/luxury models, don't let "economy" be the profile anchor in the headline.
    # "Cada cêntimo conta — e o Lexus NX faz contas como ninguém" is tonally wrong.
    # Instead, use the model's own strongest dimension as the headline angle.
    if is_premium_model and prof_top1 == "economy":
        # Prioritise model strengths over the user's economy focus for premium frame
        effective_top1 = model_best if model_best != "economy" else model_2nd
        effective_top2 = prof_top2
    else:
        effective_top1 = prof_top1
        effective_top2 = prof_top2

    # Candidates in priority order: best angles to try
    candidates = [
        (effective_top1, model_best),   # primary angle
        (effective_top1, model_2nd),    # model's 2nd strength
        (effective_top2, model_best),   # user's 2nd need x model best
        (effective_top2, model_2nd),    # user 2nd x model 2nd
        (effective_top1, model_3rd),    # model's 3rd strength
        (effective_top2, model_3rd),    # user 2nd x model 3rd
        (prof_top1, model_2nd),         # fallback to original profile axis
        (prof_top1, model_3rd),
    ]

    for key in candidates:
        # Final guard: don't frame a premium/luxury car through an "economy" headline.
        # This applies whether "economy" is the profile dimension (key[0]) OR the model
        # dimension (key[1]) — "Viaja bem sem gastar muito" for a Lexus is also wrong.
        if is_premium_model and "economy" in key:
            continue
        templates = HEADLINE_TEMPLATES.get(key)
        if not templates:
            continue
        for variant_idx, template in enumerate(templates):
            used_tuple = (key, variant_idx)
            if used_tuple not in used_keys:
                used_keys.append(used_tuple)
                return template.format(name=name, brand=brand)

    # Absolute last resort — should never happen with 36 template keys x 2 variants
    return f"O {name} encaixa no teu perfil de formas que vao surpreender-te."


def _fmt_score(x) -> str:
    """8.333333 → '8.3', 9.0 → '9' — never leak raw floats into copy."""
    v = round(float(x), 1)
    return str(int(v)) if v == int(v) else f"{v}"


def _fmt_eur(n) -> str:
    """16000 → '16 000 €' (Portuguese thousands separator)."""
    return f"{int(n):,}".replace(",", " ") + " €"


def _build_reasons(model: dict, profile: dict, top1: str, top2: str, answers: dict) -> list:
    """Build 2-3 concrete reasons from templates with variation."""
    reasons = []
    m = model
    mid = m["id"]  # used to pick template A vs B

    # Priority dimensions to cover
    dims_to_cover = [top1, top2]

    for dim in dims_to_cover:
        if dim == "economy":
            if m["best_consumption"]:
                t = [
                    f"Consumo real a partir de {m['best_consumption']}L/100km.",
                    f"Gasta {m['best_consumption']}L/100km em uso misto — dos melhores da classe.",
                ]
                reasons.append(t[mid % 2])
            elif m["avg_maintenance"]:
                t = [
                    f"Manutenção média de {_fmt_eur(m['avg_maintenance'])}/ano.",
                    f"Custa {_fmt_eur(m['avg_maintenance'])}/ano a manter — sem surpresas.",
                ]
                reasons.append(t[mid % 2])

        elif dim == "comfort":
            if m["comfort_score"] >= 7:
                t = [
                    f"Nota {m['comfort_score']}/10 em conforto — referência no segmento.",
                    f"Conforto {m['comfort_score']}/10 — quilómetros longos passam a voar.",
                ]
                reasons.append(t[mid % 2])

        elif dim == "driving":
            if m["driving_fun_score"] >= 7:
                t = [
                    f"Nota {m['driving_fun_score']}/10 em prazer de condução.",
                    f"Chassis com {m['driving_fun_score']}/10 — sentes a estrada, controlas tudo.",
                ]
                reasons.append(t[mid % 2])
            # max_power is the most powerful version of the model (e.g. a Giulia
            # Quadrifoglio), not what this budget buys — say so honestly.
            if m["max_power"] and m["max_power"] >= 150 and len(reasons) < 3:
                reasons.append(f"Versões até {m['max_power']} cv, para quando a estrada pede.")

        elif dim == "practical":
            if m["family_score"] >= 6:
                t = [
                    f"Nota {m['family_score']}/10 para famílias — espaço real.",
                    f"Nota familiar de {m['family_score']}/10 — cabe tudo e todos.",
                ]
                reasons.append(t[mid % 2])
            if m["city_score"] >= 8 and len(reasons) < 3:
                t = [
                    f"Nota {m['city_score']}/10 em cidade — ágil e fácil de estacionar.",
                    f"Nota {m['city_score']}/10 em cidade — pensado para o dia a dia urbano.",
                ]
                reasons.append(t[mid % 2])

        elif dim == "reliability":
            if m["avg_reliability"] >= 7.0:
                rel = _fmt_score(m["avg_reliability"])
                t = [
                    f"Fiabilidade {rel}/10 — historial sólido.",
                    f"A {m['brand_name']} é sinónimo de fiabilidade: {rel}/10.",
                ]
                reasons.append(t[mid % 2])

        elif dim == "status":
            reasons.append(f"{m['brand_name']} — uma marca que dispensa apresentações neste segmento.")

    # Fill with price context if < 3 reasons
    if len(reasons) < 3 and m["avg_price"]:
        budget_max = int(answers.get("p8_budget_max", 25000))
        price = _fmt_eur(m["avg_price"])
        if m["avg_price"] <= budget_max * 0.85:
            t = [
                f"Preço médio de {price} — bem abaixo do teu limite.",
                f"A {price}, sobra margem no orçamento.",
            ]
            reasons.append(t[mid % 2])
        elif m["avg_price"] <= budget_max:
            t = [
                f"Preço médio de {price} — dentro do teu orçamento.",
                f"A {price}, encaixa no que definiste.",
            ]
            reasons.append(t[mid % 2])

    # Last fill: character description
    if len(reasons) < 2 and m["character_desc"]:
        reasons.append(m["character_desc"])

    return reasons[:3]


def _build_tradeoff(model: dict, profile: dict, all5: list, answers: dict, used_dims: set) -> str:
    """
    Build tradeoff with comparative reference when gap is significant.
    Tracks used dimensions to avoid identical tradeoffs across models.
    """
    mv = model["vector"]
    m = model

    # Stretch: always gets price-based tradeoff
    if m.get("is_stretch"):
        budget_max = int(answers.get("p8_budget_max", 25000))
        over = m["avg_price"] - budget_max
        return f"Ultrapassa o teu orçamento em ~{_fmt_eur(over)} — mas o que oferece justifica olhar."

    # Rank all dimensions by gap (profile need minus model offer)
    # Include ALL dimensions, even small profile weights
    gaps = []
    for d in DIMENSIONS:
        if profile[d] > 0.02:  # almost any dimension the user has
            gaps.append((d, profile[d] - mv[d]))
    gaps.sort(key=lambda x: x[1], reverse=True)  # biggest gap first

    # Pick the first gap dimension not already used by another model
    chosen_dim = None
    chosen_gap = 0
    for dim, gap in gaps:
        if dim not in used_dims:
            chosen_dim = dim
            chosen_gap = gap
            break

    # If all dims used (5 models, 6 dims — shouldn't happen), pick biggest gap
    if not chosen_dim and gaps:
        chosen_dim = gaps[0][0]
        chosen_gap = gaps[0][1]

    if not chosen_dim:
        return "Compromissos mínimos para o teu perfil."

    used_dims.add(chosen_dim)

    # Comparative tradeoff: find best model in this dimension among the other 4
    best_in_dim = None
    best_val = 0
    for other in all5:
        if other["id"] == model["id"]:
            continue
        oval = other["vector"].get(chosen_dim, 0)
        if oval > best_val:
            best_val = oval
            best_in_dim = other

    dim_pt = {
        "economy": "económico", "comfort": "confortável", "driving": "emocionante",
        "practical": "espaçoso", "status": "vistoso", "reliability": "fiável",
    }.get(chosen_dim, "forte")

    # If there's a meaningfully better model, do comparative
    if best_in_dim and best_val > mv.get(chosen_dim, 0) + 0.08:
        model_best_dim = max(mv, key=mv.get)
        comp_pt = {
            "economy": "economia", "comfort": "conforto", "driving": "condução",
            "practical": "espaço", "status": "presença", "reliability": "fiabilidade",
        }.get(model_best_dim, "outras áreas")
        return f"Não é tão {dim_pt} como o {best_in_dim['full_name']}, mas compensa em {comp_pt}."

    # Generic tradeoff for this dimension
    templates = TRADEOFF_TEMPLATES.get(chosen_dim, [
        "Como todos os carros, tem compromissos — mas os que importam para ti estão cobertos."
    ])
    return templates[model["id"] % len(templates)]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PHASE 7: SESSION LOGGING
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def log_session(db: Session, session_id: str, answers: dict, profile: dict,
                top5: list, pool_size: int) -> None:
    """Log the recommendation session to DB."""
    models_shown = [
        {
            "model_id": m["id"],
            "rank": i + 1,
            "score": m.get("_score", 0),
            "is_stretch": m.get("is_stretch", False),
            "is_wildcard": m.get("is_wildcard", False),
        }
        for i, m in enumerate(top5)
    ]
    try:
        db.execute(text("""
            INSERT INTO recommendation_sessions
                (id, answers_raw, profile_computed, models_shown, models_pool_size,
                 budget_range, had_stretch, had_wildcard)
            VALUES (:id, :answers, :profile, :models, :pool,
                    :budget, :stretch, :wildcard)
        """), {
            "id": session_id,
            "answers": json.dumps(answers),
            "profile": json.dumps(profile),
            "models": json.dumps(models_shown),
            "pool": pool_size,
            "budget": json.dumps({
                "min": answers.get("p8_budget_min", 5000),
                "max": answers.get("p8_budget_max", 25000),
            }),
            "stretch": any(m.get("is_stretch") for m in top5),
            "wildcard": any(m.get("is_wildcard") for m in top5),
        })
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"[CARACTR] Session log failed: {e}")


def log_feedback(db: Session, session_id: str, satisfaction: str,
                 preferred_model_id: int, email: str) -> None:
    """Log user feedback."""
    try:
        db.execute(text("""
            INSERT INTO user_feedback (session_id, satisfaction, preferred_model_id, email)
            VALUES (:sid, :sat, :mid, :email)
        """), {
            "sid": session_id,
            "sat": satisfaction,
            "mid": preferred_model_id,
            "email": email,
        })
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"[CARACTR] Feedback log failed: {e}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MAIN ENTRY POINT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def get_recommendations(db: Session, answers: dict) -> dict:
    """V4 pipeline: answers -> profile + signals -> filter -> score -> select -> explain -> log."""
    session_id = str(uuid.uuid4())

    # Phase 1: Build profile + structured signals
    profile, signals = build_profile(answers)

    # Phase 2: Load models
    all_models = load_models(db)

    # Phase 3: Hard constraints
    passed, stretch = apply_hard_constraints(all_models, answers)
    pool_size = len(passed)

    # Phase 4 + Stage E: Score (includes aversion penalty)
    for m in passed:
        m["_score"] = score_model(m, profile, answers)
        m["is_stretch"] = False
        m["is_wildcard"] = False
    for m in stretch:
        m["_score"] = score_model(m, profile, answers) * 0.90
        m["is_stretch"] = False
        m["is_wildcard"] = False

    # Phase 5: Diverse selection
    top5 = select_diverse_top5(passed, stretch, answers)

    # Re-sort by score so rank 1 always has the highest score.
    # select_diverse_top5 adds models in pass order (body-type diversity),
    # which can place a high-scoring adjacent-body model at position 4 or 5
    # even when it outscores models added earlier.
    top5 = sorted(top5, key=lambda x: x["_score"], reverse=True)

    # Phase 6: Explanations (LLM-first, template fallback)
    llm_result = _generate_explanations_llm(top5, profile, answers)
    results = generate_all_explanations(top5, profile, answers, llm_result=llm_result)
    _attach_dealbreakers(db, results)

    # Phase 7: Log session
    log_session(db, session_id, answers, profile, top5, pool_size)

    # Suggestions if fewer than 5 results
    suggestions = None
    if len(top5) < 5:
        budget_max = int(answers.get("p8_budget_max", 25000))
        all_prices = sorted([m["avg_price"] for m in all_models if m["avg_price"]])
        if len(all_prices) >= 5:
            suggested = all_prices[4]
            if suggested > budget_max:
                suggestions = {"stretch_budget": suggested, "models_available": pool_size}

    # Profile narrative: use LLM version if available, else template
    llm_narrative = llm_result.get("profile_narrative") if llm_result else None
    narrative = llm_narrative if llm_narrative else generate_profile_narrative(profile, signals, answers)

    return {
        "session_id": session_id,
        "profile": profile,
        "profile_signals": signals,
        "profile_summary": _summarize_profile(profile),
        "profile_narrative": narrative,
        "answers": answers,
        "recommendations": results,
        "suggestions": suggestions,
    }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# REFRESH RECOMMENDATIONS (dislike → get alternatives)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Maps dismiss reason keywords → profile dimension adjustments
_DISMISS_ADJUSTMENTS: list[tuple[str, dict]] = [
    ("desportivo",  {"driving": +0.15, "economy": -0.05}),
    ("sportier",    {"driving": +0.15, "economy": -0.05}),
    ("luxuoso",     {"status": +0.15, "comfort": +0.05, "economy": -0.10}),
    ("premium",     {"status": +0.12, "comfort": +0.05, "economy": -0.08}),
    ("prático",     {"practical": +0.15, "driving": -0.05}),
    ("pratico",     {"practical": +0.15, "driving": -0.05}),
    ("espaço",      {"practical": +0.12}),
    ("espaco",      {"practical": +0.12}),
    ("conforto",    {"comfort": +0.12, "driving": -0.05}),
    ("discreto",    {"status": -0.12}),
    ("marca",       {}),   # brand dislike — no profile change, just exclude
    ("orçamento",   {"economy": +0.10}),
    ("orcamento",   {"economy": +0.10}),
    ("estilo",      {}),   # style mismatch — no numeric adjustment
]


def _apply_dismiss_adjustments(profile: dict, dismiss_reasons: list[str]) -> dict:
    """
    Nudge the profile based on dismiss reasons.
    Clamps all dimensions to [0.0, 1.0].
    """
    adjusted = dict(profile)
    for reason in dismiss_reasons:
        reason_lower = reason.lower()
        for keyword, deltas in _DISMISS_ADJUSTMENTS:
            if keyword in reason_lower:
                for dim, delta in deltas.items():
                    adjusted[dim] = max(0.0, min(1.0, adjusted.get(dim, 0.0) + delta))
                break
    return adjusted


def get_alternative_recommendations(
    db: Session,
    session_id: str,
    dismissed_model_ids: list[int],
    dismiss_reasons: list[str],
    count: int = 3,
) -> dict:
    """
    Re-run the recommendation pipeline excluding dismissed models,
    with profile nudged based on why the user dismissed them.

    Returns a compact response: {alternatives: [...], profile_adjusted: bool}
    """
    import json as _json

    try:
        # Load original session answers + profile
        row = db.execute(text("""
            SELECT answers_raw, profile_computed
            FROM recommendation_sessions
            WHERE id = :sid
            LIMIT 1
        """), {"sid": session_id}).mappings().fetchone()

        if not row or not row["answers_raw"]:
            return {"alternatives": [], "profile_adjusted": False}

        answers = _json.loads(row["answers_raw"]) if isinstance(row["answers_raw"], str) else dict(row["answers_raw"])
        original_profile = (
            _json.loads(row["profile_computed"]) if isinstance(row["profile_computed"], str)
            else dict(row["profile_computed"])
        ) if row["profile_computed"] else None

        # Build fresh profile from answers (or use stored one)
        profile, _ = build_profile(answers)
        if original_profile:
            profile = original_profile

        # Nudge profile based on dismiss reasons
        profile_adjusted = bool(dismiss_reasons)
        if profile_adjusted:
            profile = _apply_dismiss_adjustments(profile, dismiss_reasons)

        # Load + score all models (excluding dismissed)
        all_models = load_models(db)
        passed, stretch = apply_hard_constraints(all_models, answers)

        excluded = set(dismissed_model_ids)
        passed  = [m for m in passed  if m["id"] not in excluded]
        stretch = [m for m in stretch if m["id"] not in excluded]

        for m in passed:
            m["_score"] = score_model(m, profile, answers)
            m["is_stretch"] = False
            m["is_wildcard"] = False
        for m in stretch:
            m["_score"] = score_model(m, profile, answers) * 0.90
            m["is_stretch"] = True
            m["is_wildcard"] = False

        # Take top N diverse alternatives
        candidates = sorted(passed + stretch, key=lambda x: x["_score"], reverse=True)

        # Light body-type diversity: avoid duplicating body types already in dismissed set
        # (we don't know dismissed body types, so just pick top N unique-by-body-type)
        seen_bodies: set[str] = set()
        alternatives: list[dict] = []
        for m in candidates:
            bt = m.get("body_type", "")
            if bt not in seen_bodies or len(alternatives) >= count - 1:
                alternatives.append(m)
                seen_bodies.add(bt)
            if len(alternatives) >= count:
                break

        if not alternatives:
            return {"alternatives": [], "profile_adjusted": profile_adjusted}

        # Generate explanations (LLM-first, template fallback)
        llm_result = None
        try:
            llm_result = _generate_explanations_llm(alternatives, profile, answers)
        except Exception as e:
            import logging as _logging
            _logging.getLogger(__name__).warning(f"LLM explanations failed in refresh: {e}")

        results = generate_all_explanations(alternatives, profile, answers, llm_result=llm_result)
        _attach_dealbreakers(db, results)

        return {
            "alternatives": results,
            "profile_adjusted": profile_adjusted,
            "adjusted_profile": profile if profile_adjusted else None,
        }

    except Exception as e:
        import logging as _logging
        _logging.getLogger(__name__).error(f"get_alternative_recommendations failed: {e}", exc_info=True)
        return {"alternatives": [], "profile_adjusted": False, "error": str(e)}


def _summarize_profile(profile: dict) -> str:
    s = sorted(profile.items(), key=lambda x: x[1], reverse=True)
    pt = {"economy": "economia", "comfort": "conforto", "driving": "condução",
          "practical": "praticidade", "status": "imagem", "reliability": "fiabilidade"}
    return f"Perfil dominado por {pt.get(s[0][0], s[0][0])} ({int(s[0][1]*100)}%) e {pt.get(s[1][0], s[1][0])} ({int(s[1][1]*100)}%)."


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DREAM CARS HELPER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def get_dream_cars(answers: dict) -> list:
    """Return top 6 dream brands for P7 based on partial profile similarity."""
    partial, _ = build_profile(answers)
    scored = []
    for key, traits in DREAM_BRAND_TRAITS.items():
        if key == "nenhuma":
            continue
        sim = sum(partial.get(d, 0) * traits.get(d, 0) for d in DIMENSIONS)
        scored.append({
            "id": key,
            "name": _DREAM_BRAND_DISPLAY.get(key, key.replace("_", " ").title()),
            "identity": _DREAM_BRAND_IDENTITY.get(key, ""),
            "score": round(sim, 3),
        })
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:6]
