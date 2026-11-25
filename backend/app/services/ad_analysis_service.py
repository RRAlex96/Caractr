"""
Caractr — Ad Analysis Service
Analyses a specific listing URL using:
1. Deal scoring (price delta, km/year, red flags)
2. Analysis engine — Gemini 2.5 Flash when GEMINI_API_KEY is set, rule-based otherwise

Analysis routing:
- If GEMINI_API_KEY is set AND USE_RULE_ANALYSIS != "true" → Gemini 2.5 Flash (main analysis)
- Otherwise → deterministic rule-based engine (zero cost, zero latency)
- Gemini also generates narrative enrichments (extras_analysis, negotiation_script,
  verdict_narrative, seller_read) in a second pass regardless of main engine.

Cache strategy: analyse once per listing URL, serve from DB cache.
Refresh if analysis_cached_at > 7 days.
"""

import os
import re
import math
import json
import asyncio
import hashlib
import unicodedata
from datetime import datetime, timezone, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import text


def _strip_accents(s: str) -> str:
    """Remove diacritics/accents: 'Citroën' → 'Citroen', 'Série' → 'Serie'."""
    return "".join(
        c for c in unicodedata.normalize("NFD", s)
        if unicodedata.category(c) != "Mn"
    )

from app.scrapers.dispatcher import fetch_detail_for_url, detect_source, extract_slugs_from_url, is_supported_url, source_label
from app.services.dealbreakers import get_dealbreakers, merge_known_issues
from app.services.known_issues import match_listing, normalize_fuel
from app.scrapers.normalizer import (
    _compute_price_delta,
    _compute_km_per_year,
    _classify_deal_tier,
    _compute_deal_score,
)

import time

# In-memory market data cache: key → {pool, cached_at}, pool being the filtered
# comparables as {"price", "km", "year"} dicts. Keyed per variant — refreshed every 6h
_market_cache: dict = {}
_MARKET_CACHE_TTL = 6 * 3600  # 6 hours
_MAX_MARKET_CACHE_KEYS = 500  # evict oldest entries if cache grows beyond this

USE_RULE_ANALYSIS = os.getenv("USE_RULE_ANALYSIS", "false").lower() == "true"
DISABLE_LIVE_MARKET = os.getenv("DISABLE_LIVE_MARKET", "false").lower() == "true"  # scraping is now httpx-based (no Playwright OOM)
_MIN_NEGOTIATION_SAMPLE = 5  # below this many comparables, suppress precise offer figures
_MIN_RELIABLE_MARKET_SAMPLE = 5  # below this, the market median is too noisy to drive the price verdict
# The live comparison reads up to 4 Standvirtual result pages (32 listings
# each). One page, cut to 20, left a model with 5–15 comparables at best.
_MARKET_MAX_PAGES = 4
_MARKET_MAX_LISTINGS = 160
# Comparables are listings within 15% of the car's engine power, when the
# listing states it: a Golf 1.6 TDI is not priced against a GTD, a MINI One not
# against a Cooper S. Leave-one-out over 2 615 live listings of 25 searches
# (2026-11-13), pricing each from the others:
#   - references off by more than 20%: 10% of cars with the rules it replaces
#     (engine named in the title, MINI trim), 8% within the band; by more than
#     30%: 3% and 2%. Where engines differ most the gap is large (Golf diesel
#     28% -> 17%, Golf petrol 14% -> 6%), elsewhere there is none to close.
#   - a whole series (BMW Série 3, Mercedes Classe C) within the band is as
#     good as the car's own sub-model (10% and 10%), so a series car whose
#     sub-model is not named can be compared after all.
#   - ±15% does as well as ±10% and ±5% and withholds fewer verdicts (88%
#     against 87% and 84% of cars get one; 90% with the old rules).
_POWER_BAND = 0.15
CACHE_TTL_HOURS = 168  # 7 days

def _compute_profile_fit(
    user_profile: dict,
    model_info: dict,
    aversion: str = "nenhuma",
) -> dict:
    """
    Compute alignment between user 6D profile and a model's known characteristics.
    Returns {fit_score, fit_tier, fit_label, fit_reason}.
    """
    _dim_labels = {
        "economy": "economia", "comfort": "conforto", "driving": "condução",
        "practical": "praticidade", "status": "imagem", "reliability": "fiabilidade",
    }

    comfort     = (model_info.get("comfort_score") or 5) / 10.0
    driving     = (model_info.get("driving_fun_score") or 5) / 10.0
    practical   = (model_info.get("family_score") or 5) / 10.0
    reliability = (model_info.get("avg_reliability") or model_info.get("reliability_score") or 5) / 10.0
    economy     = max(0.0, min(1.0, (1.0 - (model_info.get("avg_reliability") or 5) / 30.0)))
    status      = 0.4  # neutral default (not available in model_info)

    model_vector = {
        "economy": economy, "comfort": comfort, "driving": driving,
        "practical": practical, "status": status, "reliability": reliability,
    }

    raw = sum(user_profile.get(d, 0) * model_vector.get(d, 0) for d in model_vector)

    # Aversion penalty — hard suppression when model conflicts with declared aversion
    aversion_penalty = 1.0
    if aversion == "fiabilidade" and (model_info.get("avg_reliability") or 5) < 6.5:
        aversion_penalty = 0.4
    elif aversion == "conforto" and comfort < 0.45:
        aversion_penalty = 0.6
    elif aversion == "espaco" and practical < 0.4:
        aversion_penalty = 0.6
    elif aversion == "potencia" and driving < 0.4:
        aversion_penalty = 0.6

    fit_score = round(min(1.0, raw * aversion_penalty), 3)

    if fit_score >= 0.75:
        fit_tier, fit_label = "excelente", "Excelente alinhamento"
    elif fit_score >= 0.55:
        fit_tier, fit_label = "bom", "Bom alinhamento"
    elif fit_score >= 0.35:
        fit_tier, fit_label = "parcial", "Alinhamento parcial"
    else:
        fit_tier, fit_label = "fraco", "Pouco alinhado"

    top_dim = max(user_profile.items(), key=lambda x: x[1])[0] if user_profile else "comfort"
    top_label = _dim_labels.get(top_dim, top_dim)

    if aversion_penalty < 1.0:
        _aversion_reason = {
            "fiabilidade": "fiabilidade abaixo do teu limite de tolerância",
            "conforto":    "conforto abaixo do que o teu perfil exige",
            "espaco":      "espaço insuficiente para as tuas necessidades",
            "potencia":    "potência insuficiente para o teu perfil",
        }
        fit_reason = f"Atenção: {_aversion_reason.get(aversion, 'conflito com a tua aversão declarada')}."
    elif fit_score >= 0.65:
        fit_reason = f"Alinha bem com a tua prioridade de {top_label}."
    elif fit_score >= 0.45:
        fit_reason = f"Alinhamento razoável com o teu perfil de {top_label}."
    else:
        fit_reason = f"Este modelo prioriza outras dimensões — pouco alinhado com o teu perfil de {top_label}."

    return {"fit_score": fit_score, "fit_tier": fit_tier, "fit_label": fit_label, "fit_reason": fit_reason}


def _build_analysis_prompt(
    listing: dict,
    model_info: dict,
    market_stats: dict,
    user_profile: Optional[dict] = None,
) -> str:
    profile_note = ""
    if user_profile:
        _dim_labels = {
            "economy": "Economia", "comfort": "Conforto", "driving": "Condução",
            "practical": "Praticidade", "status": "Imagem", "reliability": "Fiabilidade",
        }
        sorted_dims = sorted(user_profile.items(), key=lambda x: x[1], reverse=True)
        top2 = [_dim_labels.get(d[0], d[0]) for d in sorted_dims[:2]]
        profile_note = f"""
Perfil do comprador (6 dimensões):
  Economia: {user_profile.get('economy',0):.2f}  |  Conforto: {user_profile.get('comfort',0):.2f}
  Condução: {user_profile.get('driving',0):.2f}  |  Praticidade: {user_profile.get('practical',0):.2f}
  Imagem: {user_profile.get('status',0):.2f}      |  Fiabilidade: {user_profile.get('reliability',0):.2f}
Prioridades do comprador: {', '.join(top2)}

Avalia também se este carro é adequado para ESTE comprador específico."""

    km_per_year = listing.get("km_per_year")
    try:
        age_years = max(1, datetime.now().year - int(listing.get("year")))
    except (TypeError, ValueError):
        age_years = None
    km_note = (f"{km_per_year:.0f} km/ano em {age_years} anos" if km_per_year and age_years
               else f"{km_per_year:.0f} km/ano" if km_per_year else "desconhecido")

    known_issues = model_info.get("known_issues", "Sem problemas conhecidos registados.")

    fuel_type = listing.get('fuel_type', '')
    engine_hp = listing.get('engine_power_hp', '')
    colour = listing.get('colour', '')
    transmission = listing.get('transmission', '')

    listing_age = listing.get("listing_age_days")
    listing_age_str = f"{listing_age} dias" if listing_age else "desconhecido"
    maintenance = model_info.get("maintenance_cost_year")
    maintenance_str = f"~€{int(maintenance):,}/ano" if maintenance else "N/D"
    ref_price = market_stats.get('median_price') or market_stats.get('avg_price') or 0
    price = listing.get('price', 0) or 0
    price_delta_pct = listing.get('price_delta_pct', '?')
    price_pos = 'abaixo' if (listing.get('price_delta', 0) or 0) > 0 else 'acima'
    market_sample = market_stats.get('sample_count') or 0
    # Only present a confident price-vs-market line when the pool is big enough.
    if ref_price and market_sample >= _MIN_RELIABLE_MARKET_SAMPLE and price_delta_pct not in (None, '?'):
        adjusted = (market_stats.get('year_comparison') or {}).get('basis') == 'adjusted'
        basis_note = ", preços ajustados ao ano e aos km deste carro" if adjusted else ""
        market_line = (f"Mediana de mercado: €{int(ref_price):,} ({market_sample} anúncios{basis_note}) | "
                       f"Este carro está {price_delta_pct}% {price_pos} do mercado")
    elif ref_price and market_sample:
        market_line = (f"Dados de mercado LIMITADOS (apenas {market_sample} anúncios comparáveis) — "
                       f"NÃO tires conclusões fortes sobre o preço; baseia o veredicto em km, "
                       f"motor, estado e equipamento.")
    else:
        market_line = "Sem dados de mercado fiáveis — avalia pelo km, motor, estado e equipamento."

    return f"""És um consultor especialista em carros usados em Portugal com 20 anos de experiência. Conheces TODOS os modelos, gerações, motores, versões e problemas típicos. Fala em PT-PT. Tom direto e honesto como um amigo que percebe muito de carros. Responde APENAS com JSON válido, sem texto extra.

O teu trabalho: analisar este anúncio como se o comprador te estivesse a pagar para o aconselhar. Sê ESPECÍFICO — nunca genérico.

ANÚNCIO:
Modelo: {listing.get('brand_name', '')} {listing.get('model_name', '')}
Versão de fábrica (trim): {listing.get('version') or 'não indicada — infere da descrição'}
Ano: {listing.get('year', 'desconhecido')}
Km: {listing.get('km', 'desconhecido')} ({km_note})
Preço pedido: {price:,} EUR
Tipo de vendedor: {listing.get('seller_type', 'desconhecido')}
Combustível: {fuel_type or 'desconhecido'}
Potência: {engine_hp or 'desconhecida'} cv
Transmissão: {transmission or 'desconhecida'}
Cor: {colour or 'desconhecida'}
Anúncio há: {listing_age_str}
Descrição do anúncio: {listing.get('description', 'Sem descrição disponível.')[:2000]}

CONTEXTO DE MERCADO:
{market_line}
Custo manutenção estimado: {maintenance_str}
Problemas conhecidos do modelo: {known_issues}
{profile_note}

INSTRUÇÕES IMPORTANTES:
1. IDENTIFICA O MOTOR EXATO: com base na cilindrada, potência e combustível, identifica o código do motor (ex: "Motor N47D20 no BMW", "Motor K9K no Renault", "OM651 no Mercedes"). Isto é crítico para os problemas conhecidos.
2. IDENTIFICA A VERSÃO/TRIM: Avantgarde, Comfort, Sport, R-Line, GT-Line, R-Dynamic, Pack M, etc. Cada versão traz equipamento de série diferente.
3. SEPARA EQUIPAMENTO DE SÉRIE vs EXTRAS OPCIONAIS — isto é crucial para quem não percebe de carros:
   - "trim_includes": o que ESTA versão de fábrica já traz de série (ex: R-Line → jantes, faróis LED, bancos desportivos, multimédia). Conhecimento do modelo, não só da descrição.
   - "optional_extras": o que foi ADICIONADO além da versão (ex: teto panorâmico, som premium, bola de reboque, pack de assistência). Só o que a descrição revela como extra.
   Não repitas o mesmo item nos dois. Se não souberes a versão, deixa trim_includes vazio e lista tudo em optional_extras.
4. AVALIA O PREÇO COM BASE NO EQUIPAMENTO: Um carro "base" e um "full extras" do mesmo modelo podem ter €3-5k de diferença. Reflecte isso no veredicto.
5. NÃO ACUSES O VENDEDOR: nunca classifiques um custo ou uma prática como ilegal, abusivo, fraude ou burla, nem afirmes má-fé — não tens como o provar e o texto é público. Descreve o facto (ex: "há 300 € de despesas administrativas além do preço anunciado") e diz o que o comprador deve perguntar ou negociar.
6. USA OS NÚMEROS DADOS, NÃO RECALCULES: km/ano, idade, mediana de mercado e a % face ao mercado já estão calculados acima e aparecem ao comprador noutros cartões. Se os referires, usa exatamente esses valores — nunca faças as tuas próprias contas (um texto que contradiz os números destrói a confiança).
7. INFORMAR, NUNCA ASSUSTAR: sem linguagem alarmista ('bomba-relógio', 'foge', 'pesadelo', 'evita a todo o custo'). Diz o risco, quanto custa e como o confirmar. Se um problema conhecido tiver uma garantia ou extensão do fabricante que o cubra (está indicada nos problemas conhecidos acima), menciona-a.

Responde APENAS com este JSON (sem texto extra, sem markdown):
{{
  "verdict": "forte|razoavel|cuidado|evitar",
  "verdict_reason": "Uma frase em português, máximo 20 palavras. Sê ESPECÍFICO — referencia o motor, extras ou km.",
  "green_flags": ["MÁXIMO 4. Cada flag deve ser específica a ESTE carro. Ex: 'Motor 2.0 TDI CR (150cv) — um dos mais fiáveis do grupo VAG'. NUNCA ponhas flags genéricas como 'Bom preço'."],
  "red_flags": ["MÁXIMO 4. Cada flag deve ser específica. Ex: 'Motor N47 com >150k km — corrente de distribuição traseira, verificar urgentemente'. NUNCA flags genéricas."],
  "seller_analysis": "2-3 frases: o que a descrição REVELA sobre o vendedor. Profissional ou particular? O que omite? O tom é confiante ou vago? Há sinais de urgência na venda?",
  "profile_fit": "Como este anúncio específico se adequa ao perfil do comprador (1-2 frases)",
  "trim_level": "Nome exato da versão/trim detectado (ex: 'Avantgarde', 'R-Line', 'R-Dynamic S', 'Pack M') ou null se não identificável",
  "spec_tier": "base|medio|alto — baseado no equipamento total (série + extras)",
  "trim_includes": ["3-7 itens que ESTA versão de fábrica traz de série. Ex para R-Line: 'Jantes 18\"', 'Faróis LED', 'Bancos desportivos', 'Volante multifunções'. Vazio se a versão for desconhecida."],
  "optional_extras": ["Extras OPCIONAIS adicionados além da versão, com valor quando relevante. Ex: 'Teto panorâmico', 'Som Harman Kardon', 'Bola de reboque'. Máximo 8."],
  "equipment_note": "1 frase simples para quem não percebe de carros: este carro está bem ou mal equipado para a versão/preço, e porquê. Ex: 'Bem equipado — além do R-Line de série, tem teto e som premium que valem o preço.'",
  "key_extras": ["Lista TODOS os extras mencionados na descrição. Ex: 'Bancos em pele', 'Teto panorâmico', 'Navegação', 'Câmara traseira', 'Jantes 19', 'Sensores estacionamento', 'LED'. Máximo 12."],
  "spec_value_assessment": "acima_do_esperado|adequado|abaixo_do_esperado — considerando os extras para esta versão e preço",
  "engine_code": "Código do motor se identificável (ex: 'EA888', 'N47D20', 'K9K 636', 'OM651') ou null",
  "engine_analysis": "1-2 frases sobre ESTE motor específico: fiabilidade conhecida, pontos fracos, o que verificar. Ex: 'O EA888 Gen3 é sólido mas consome óleo — verificar nível entre revisões. Correia aos 210k km.'",
  "extras_analysis": "2-3 frases: que extras tem, o que valem no mercado, e o que FALTA em relação ao esperado para esta versão.",
  "verdict_narrative": "3-4 frases: síntese final como amigo especialista. Honesto e direto. Contextualiza preço, km, motor, extras — vale ou não? Para quem é ideal?",
  "seller_read": "2-3 frases: psicologia do vendedor baseada na descrição. Descrição detalhada = transparência, vaga = possível ocultação. Palavras como 'urgente', 'impecável' — o que significam.",
  "inspection_checklist": ["5-7 pontos de inspeção ESPECÍFICOS para ESTE motor e modelo. Ex: 'Verificar corrente de distribuição — problema conhecido acima de 120k km'. Não ponhas coisas genéricas como 'verificar pneus'."]
}}"""


# ── Analysis engine routing ────────────────────────────────────────────────

def _run_rule_engine(
    listing: dict,
    model_info: dict,
    market_stats: dict,
    user_profile: Optional[dict],
) -> dict:
    """Run the deterministic rule-based analysis engine."""
    from app.services.rule_analysis import analyse as rule_analyse
    result = rule_analyse(listing, model_info, market_stats, user_profile)
    # Strip internal tag before returning
    result.pop("_engine", None)
    return result


async def _call_gemini_analysis(prompt: str) -> dict:
    """
    Call Gemini for unified structured ad analysis + enrichment.
    Returns {} on failure (triggers rule engine fallback).
    Returns {"_quota_exhausted": True, ...} on quota errors so frontend can show message.
    """
    try:
        from app.services.llm_client import generate_json, LLMError, QuotaExhaustedError
        usage: dict = {}
        result = await asyncio.wait_for(
            asyncio.to_thread(generate_json, prompt, 8192, usage),
            timeout=90,
        )
        if not isinstance(result, dict) or not result.get("verdict"):
            print(f"[AD_ANALYSIS] Gemini returned unexpected structure: {str(result)[:200]}")
            return {}
        if usage:
            result["_llm_usage"] = usage   # cached with the analysis: real cost per analysis
        print(f"[AD_ANALYSIS] Gemini OK — verdict={result.get('verdict')}, "
              f"engine={result.get('engine_code')}, extras={len(result.get('key_extras', []))}")
        return result
    except asyncio.TimeoutError:
        print("[AD_ANALYSIS] Gemini analysis timed out after 90s")
        return {"_llm_error": "timeout:90s"}
    except Exception as e:
        err_name = type(e).__name__
        err_msg = str(e)[:300]
        print(f"[AD_ANALYSIS] Gemini analysis failed: {err_name}: {err_msg}")
        # Surface quota error so frontend can show appropriate message
        if "Quota" in err_name or "quota" in err_msg.lower() or "429" in err_msg:
            return {"_quota_exhausted": True, "_llm_error": f"quota:{err_msg[:150]}"}
        return {"_llm_error": f"{err_name}:{err_msg[:150]}"}


async def _analyse(
    listing: dict,
    model_info: dict,
    market_stats: dict,
    user_profile: Optional[dict],
) -> dict:
    """
    Route to the correct analysis engine:
    - Gemini (LLM_MODEL): when GEMINI_API_KEY is set and USE_RULE_ANALYSIS != true
    - Rule engine: fallback when no API key, flag set, or Gemini fails
    """
    from app.services.llm_client import llm_available

    if USE_RULE_ANALYSIS or not llm_available():
        reason = f"USE_RULE={USE_RULE_ANALYSIS}|llm_avail={llm_available()}"
        print(f"[AD_ANALYSIS] Using rule engine ({reason})")
        result = _run_rule_engine(listing, model_info, market_stats, user_profile)
        result["_analysis_engine"] = f"rule:{reason}"
        return result

    print("[AD_ANALYSIS] Using Gemini for analysis")
    prompt = _build_analysis_prompt(listing, model_info, market_stats, user_profile)
    result = await _call_gemini_analysis(prompt)

    llm_error = result.get("_llm_error") if result else None
    if not result or not result.get("verdict"):
        quota = result.get("_quota_exhausted", False) if result else False
        reason = "quota_exhausted" if quota else ("gemini_error" if llm_error else "gemini_empty")
        print(f"[AD_ANALYSIS] Gemini failed ({reason}: {llm_error}), falling back to rule engine")
        result = _run_rule_engine(listing, model_info, market_stats, user_profile)
        result["_analysis_engine"] = f"rule:{reason}"
        if llm_error:
            result["_llm_error"] = llm_error
        return result

    result["_analysis_engine"] = "gemini"
    return result


# ── DB helpers ─────────────────────────────────────────────────────────────

def _get_cached_analysis(db: Session, listing_url: str) -> Optional[dict]:
    """Return cached analysis if it exists and is fresh."""
    row = db.execute(text("""
        SELECT n.id, n.price, n.year, n.km, n.km_per_year, n.price_delta, n.deal_tier,
               n.deal_score, n.seller_type, n.brand_name, n.model_name, n.description,
               n.llm_analysis, n.analysis_cached_at, n.photo_count, n.listing_age_days,
               n.fuel_type
        FROM normalized_listings n
        JOIN raw_listings r ON r.id = n.raw_listing_id
        WHERE r.source_url = :url
        ORDER BY n.id DESC
        LIMIT 1
    """), {"url": listing_url}).mappings().fetchone()

    if not row:
        return None

    # Check cache freshness
    cached_at = row["analysis_cached_at"]
    if cached_at and row["llm_analysis"]:
        age = datetime.now(timezone.utc) - (cached_at if cached_at.tzinfo else cached_at.replace(tzinfo=timezone.utc))
        if age < timedelta(hours=CACHE_TTL_HOURS):
            return dict(row)

    return None


_SEVERITY_RANK = {"critico": 0, "alto": 1, "medio": 2}
# Diesel vs petrol-family. Hybrids and LPG run petrol engines, so they're never
# split from petrol on fuel alone — only a clear diesel/petrol mismatch drops.
_FUEL_FAMILY = {"diesel": "diesel", "gasolina": "petrol", "gpl": "petrol",
                "hibrido": "petrol", "eletrico": "electric"}


def _filter_model_issues(rows, year: Optional[int], fuel: Optional[str]) -> tuple[Optional[str], Optional[str]]:
    """Model-level engine_issues → the text shown/fed to the LLM, keeping only
    issues that can apply to THIS car: its production year inside the issue's
    affected_years, and no diesel/petrol mismatch. Unknown or unparseable
    years/fuels never exclude. Most serious first (the rule engine quotes the
    first one). Returns (known_issues, fix_cost_estimates)."""
    from app.services.dealbreakers import _applies, _parse_affected_years
    from app.services.known_issues import normalize_fuel

    car_family = _FUEL_FAMILY.get(normalize_fuel(fuel))
    kept = []
    for r in rows:
        desc = (r.get("description") or "").strip()
        if not desc:
            continue
        span = _parse_affected_years(r.get("affected_years"))
        if span and not _applies(year, *span):
            continue
        engine_family = _FUEL_FAMILY.get(normalize_fuel(r.get("fuel_type")))
        if car_family and engine_family and car_family != engine_family:
            continue
        kept.append(r)
    kept.sort(key=lambda r: (_SEVERITY_RANK.get((r.get("severity") or "").lower(), 9), r["description"]))

    descs = list(dict.fromkeys(r["description"].strip() for r in kept))
    costs = list(dict.fromkeys(str(r["fix_cost_estimate"]).strip() for r in kept if r.get("fix_cost_estimate")))
    return ("; ".join(descs) or None), ("; ".join(costs) or None)


def _catalogue_model_id(db: Session, brand_name: str, model_name: str) -> Optional[int]:
    """The catalogue model with this brand and name, compared without accents
    or case on BOTH sides. The SQL this replaces lower-cased the catalogue
    name but stripped accents from the given one only, so "Série 3", "Citroën"
    and "Mégane" never found their own row: those cars were analysed with no
    reliability score, maintenance estimate, known issues or recalls."""
    brand, model = _norm_name(brand_name), _norm_name(model_name)
    if not brand or not model:
        return None
    for row in db.execute(text("""
        SELECT vm.id, b.name AS brand_name, vm.name AS model_name
        FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
        ORDER BY vm.id
    """)).mappings():
        if _norm_name(row["brand_name"]) == brand and _norm_name(row["model_name"]) == model:
            return row["id"]
    return None


def _get_model_info(db: Session, brand_name: str, model_name: str,
                    year: int | None = None, fuel: str | None = None) -> dict:
    """Fetch model reliability info, known issues, maintenance cost, and Bayesian trust data.

    `year`/`fuel` (the listing's, when known) filter the known issues and
    recalls to ones that can apply to this car."""
    catalogue_id = _catalogue_model_id(db, brand_name, model_name)
    if catalogue_id is None:
        return {"reliability_score": None, "known_issues": None}
    row = db.execute(text("""
        SELECT vm.id,
               AVG(e.reliability_score)::float           AS avg_reliability,
               AVG(e.maintenance_cost_year)::float       AS maintenance_cost_year,
               MAX(dc.comfort_score)                     AS comfort_score,
               MAX(dc.driving_fun_score)                 AS driving_fun_score,
               MAX(dc.family_score)                      AS family_score,
               (SELECT ROUND(AVG(g.reliability_score)::numeric, 2)
                FROM generations g WHERE g.model_id = vm.id
                AND g.reliability_score IS NOT NULL)     AS reliability_score
        FROM vehicle_models vm
        JOIN brands b ON b.id = vm.brand_id
        LEFT JOIN engines e ON e.model_id = vm.id
        LEFT JOIN driving_character dc ON dc.model_id = vm.id
        WHERE vm.id = :id
        GROUP BY vm.id
    """), {"id": catalogue_id}).mappings().fetchone()

    if not row:
        return {"reliability_score": None, "known_issues": None}

    info = dict(row)
    model_id = info.get("id")

    # Known issues, filtered to this car's year and fuel (they used to be
    # aggregated model-wide: a 2024 208 was told about a 2021 PureTech recall).
    issue_rows = db.execute(text("""
        SELECT DISTINCT ei.description, ei.affected_years, ei.fix_cost_estimate,
               ei.severity, e.fuel_type
        FROM engine_issues ei
        JOIN engines e ON e.id = ei.engine_id
        WHERE e.model_id = :mid AND ei.severity IN ('alto', 'critico', 'medio')
          -- rows the AI curator wrote with no source to check are never
          -- passed on as known faults (see curator_agent._issue_source_label)
          AND COALESCE(ei.source, '') NOT LIKE 'IA (%sem fontes%'
    """), {"mid": model_id}).mappings().fetchall()
    info["known_issues"], info["fix_cost_estimates"] = _filter_model_issues(issue_rows, year, fuel)

    # Reliability shown in the trust panel: the curated per-engine score for
    # this model (the same one the recommender ranks on), with the spread
    # across its engines as the range, labelled as an estimate. The count-based
    # generations.reliability_score is not shown — every recall or complaint
    # record counted as a failure with no exposure, so well-documented cars
    # scored worst (Honda CR-V 1.4/10) and undocumented ones best.
    if model_id:
        trust_row = db.execute(text("""
            SELECT
                ROUND(AVG(reliability_score)::numeric, 1)                      AS score,
                ROUND(GREATEST(1, MIN(reliability_score) - 0.5)::numeric, 1)   AS ci_low,
                ROUND(LEAST(10, MAX(reliability_score) + 0.5)::numeric, 1)     AS ci_high,
                'prior_only'                                                   AS data_quality
            FROM engines
            WHERE model_id = :mid AND reliability_score IS NOT NULL
        """), {"mid": model_id}).mappings().fetchone()

        if trust_row and trust_row["score"] is not None:
            info["bayesian_reliability_score"]   = float(trust_row["score"])
            info["bayesian_reliability_ci_low"]  = float(trust_row["ci_low"]) if trust_row["ci_low"] else None
            info["bayesian_reliability_ci_high"] = float(trust_row["ci_high"]) if trust_row["ci_high"] else None
            info["bayesian_reliability_quality"] = trust_row["data_quality"] or "prior_only"

        # Loud "would this put a buyer off?" signal: recalls + critical failures.
        info["dealbreakers"] = get_dealbreakers(db, model_id, year=year)

    return info


# Engine facts kept in the cached analysis blob, so a cache hit can re-match
# curated known issues against whatever is approved *now*.
_LISTING_ENGINE_KEYS = ("version", "engine_displacement_cc", "engine_power_hp", "transmission", "fuel_type",
                        "sv_model_slug")


def known_issue_dealbreakers_for_cached(model_info: Optional[dict], row: dict, llm: dict) -> Optional[dict]:
    """Cache hits and permalinks: re-match against the engine facts saved with
    the analysis, so approvals made since then take effect."""
    listing = {**row, **{k: v for k, v in (llm.get("_listing_engine") or {}).items() if v is not None}}
    payload, matched = _known_issue_dealbreakers(model_info, listing)
    saved = set(llm.get("_known_issue_ids") or []) - {i["id"] for i in matched}
    if saved:
        # Matched when analysed but not now: keep them while still approved.
        from app.services.known_issues import load_issues
        extra = [i for i in load_issues() if i["id"] in saved]
        if extra:
            payload = merge_known_issues(payload, matched + extra)
    return payload


def _known_issue_dealbreakers(model_info: Optional[dict], listing: dict) -> tuple[Optional[dict], list]:
    """Deal-breaker payload with the curated engine issues that match THIS
    listing (its year, fuel, displacement and version) folded in."""
    base = (model_info or {}).get("dealbreakers")
    try:
        matched = match_listing(listing)
    except Exception as e:  # never let curation data break an analysis
        print(f"[AD_ANALYSIS] Known-issue match error: {e}")
        return base, []
    if not matched:
        return base, []
    print(f"[AD_ANALYSIS] Known issues matched: {[i['id'] for i in matched]}")
    return merge_known_issues(base, matched), matched


def _known_issues_prompt_note(matched: list) -> str:
    """Curated, sourced findings for the LLM — so the narrative can't call an
    engine 'bulletproof' while the page shows it in red."""
    if not matched:
        return ""
    parts = []
    for i in matched:
        lo, hi = i["years"]
        tier = "FALHA GRAVE" if i["severity"] == "critico" else "ponto fraco"
        cover = f" Garantia/extensão: {i['mitigation']}" if i.get("mitigation") else ""
        parts.append(f"[{tier}] {i['name']} ({lo}-{hi}): {i['problem']}. Verificar: {i['check']}{cover}")
    return ("FALHAS CONHECIDAS VERIFICADAS (com fontes) para a motorização deste anúncio — "
            "menciona-as nos red_flags, engine_analysis e inspection_checklist: " + " | ".join(parts))


def _pick_generation(rows: list, fuel_type: Optional[str] = None):
    """
    Choose among generation rows that all contain the car's year.

    Usually there is one. Two cars sold side by side under one model name
    overlap (the petrol Fiat 500 ran to 2024, the electric 500e started in
    2020); such a row carries `fuel_type`. A fuel-specific generation is chosen
    only for a car of that fuel; otherwise a generation with no fuel restriction
    wins, and a fuel-specific one is the last resort. Ties go to the newest.
    """
    from app.services.known_issues import normalize_fuel

    car_fuel = normalize_fuel(fuel_type)

    def rank(row) -> int:
        gen_fuel = normalize_fuel(row.get("fuel_type"))
        if not gen_fuel:
            return 1
        return 0 if gen_fuel == car_fuel else 2

    ordered = sorted(rows, key=lambda r: (rank(r), -(r["year_start"] or 0)))
    return ordered[0] if ordered else None


def _get_generation_window(db: Session, model_id: int, year: int,
                           fuel_type: Optional[str] = None) -> Optional[tuple]:
    """
    Return (year_start, year_end, generation_id) for the generation that contains `year`.
    year_end may be NULL (current gen) — treated as present year.
    When more than one generation contains the year, the car's fuel decides
    (see _pick_generation). Returns None if no generation record found.
    """
    rows = db.execute(text("""
        SELECT id, year_start, year_end, fuel_type
        FROM generations
        WHERE model_id = :model_id
          AND year_start <= :year
          AND (year_end IS NULL OR year_end >= :year)
        ORDER BY year_start DESC
    """), {"model_id": model_id, "year": year}).mappings().fetchall()

    row = _pick_generation([dict(r) for r in rows], fuel_type)
    if row:
        return (row["year_start"], row["year_end"], row["id"])
    return None


# A generation row wider than this is a long-lived or catch-all generation (a
# curator "Geração principal" 1988–now row put a 2018 BMW 530e up against
# 2017–2024 cars). Above it the comparison is narrowed around the car's own year.
_WIDE_GENERATION_YEARS = 8
_WIDE_GENERATION_TOLERANCE = 2
_NO_GENERATION_TOLERANCE = 3


def _comparison_year_window(
    year: Optional[int],
    gen_year_start: Optional[int],
    gen_year_end: Optional[int],
    current_year: Optional[int] = None,
) -> tuple:
    """
    (year_from, year_to, label) the market comparison is restricted to.
    year_to None = open-ended (still-current generation).

      - normal generation      -> the generation window
      - generation > 8 years   -> car's year ±2, kept inside the generation
      - no generation record   -> car's year ±3
      - nothing known          -> (None, None, "")
    """
    if gen_year_start is None:
        if not year:
            return (None, None, "")
        t = _NO_GENERATION_TOLERANCE
        return (int(year) - t, int(year) + t, f"±{t} years")

    label = f"gen {gen_year_start}-{gen_year_end or 'now'}"
    span = (gen_year_end or current_year or datetime.now().year) - gen_year_start
    if not year or span <= _WIDE_GENERATION_YEARS:
        return (gen_year_start, gen_year_end, label)

    t = _WIDE_GENERATION_TOLERANCE
    year_from = max(gen_year_start, int(year) - t)
    year_to = int(year) + t if gen_year_end is None else min(gen_year_end, int(year) + t)
    return (year_from, year_to, f"±{t} years within wide {label}")


# ── Mileage comparability ────────────────────────────────────────────────────
# A 2018 BMW 530e with 170 000 km was shown as 15% below a median built mostly
# from cars with far fewer kilometres. The comparison is now made against
# listings whose mileage is close to the car's, and the price verdict is
# withheld when there are none and the rest of the pool is not comparable.
_KM_BAND_FRACTION = 0.30          # ±30% of the car's km ...
_KM_BAND_MIN_HALF_WIDTH = 25_000  # ... but never narrower than ±25 000 km
_MARKET_PRICE_KEYS = ("avg_price", "median_price", "min_price", "max_price", "sample_count")


def _km_band(km: int) -> tuple:
    """(km_from, km_to) of listings considered comparable in mileage, rounded
    outwards to whole thousands. 170 000 km -> (119 000, 221 000)."""
    half = max(_KM_BAND_MIN_HALF_WIDTH, km * _KM_BAND_FRACTION)
    km_from = max(0, int((km - half) // 1000) * 1000)
    km_to = int(-((km + half) // -1000)) * 1000
    return (km_from, km_to)


def _median(values: list) -> float:
    s = sorted(values)
    n = len(s)
    return s[n // 2] if n % 2 == 1 else (s[n // 2 - 1] + s[n // 2]) / 2


def _price_stats(prices: list) -> dict:
    """Median, trimmed average (top and bottom 10% dropped), range and count."""
    all_prices = sorted(prices)
    n = len(all_prices)
    trim_n = max(1, n // 10)
    trimmed = all_prices[trim_n:-trim_n] if n > 4 else all_prices
    return {
        "avg_price":    round(sum(trimmed) / len(trimmed)),
        "median_price": round(_median(all_prices)),
        "min_price":    all_prices[0],
        "max_price":    all_prices[-1],
        "sample_count": n,
    }


def _select_km_comparables(pool: list, km: Optional[int]) -> tuple:
    """
    (listings to compare against, km_comparison) for a car with `km` kilometres.
    km_comparison says what was compared, so it can be shown to the user:

      basis "band"      at least 5 listings sit inside the car's km band: only
                        those are compared.
      basis "pool"      fewer than 5 in the band, but the pool's median km is
                        inside it: the car's mileage is typical of the pool, so
                        the whole pool is a fair comparison.
      basis "mismatch"  fewer than 5 in the band and the pool's typical mileage
                        is outside it: nothing comparable. The whole pool is
                        returned (its stats are still valid market data) but the
                        caller must not judge the price against it
                        (see _withhold_if_not_comparable).
      None              the car's km is unknown, or fewer than 5 listings state
                        their km: mileage cannot be taken into account.

    Listings without km are never counted inside the band — unlike the year,
    the search URL does not scope results by mileage.
    """
    try:
        km = int(km) if km else 0
    except (TypeError, ValueError):
        km = 0
    if km <= 0:
        return pool, None
    known = [l for l in pool if isinstance(l.get("km"), (int, float)) and l["km"] > 0]
    if len(known) < _MIN_RELIABLE_MARKET_SAMPLE:
        return pool, None

    km_from, km_to = _km_band(km)
    in_band = [l for l in known if km_from <= l["km"] <= km_to]
    info = {
        "car_km":         km,
        "km_from":        km_from,
        "km_to":          km_to,
        "in_band_count":  len(in_band),
        "pool_count":     len(pool),
        "pool_median_km": round(_median([l["km"] for l in known])),
    }
    if len(in_band) >= _MIN_RELIABLE_MARKET_SAMPLE:
        return in_band, {**info, "basis": "band"}
    if km_from <= info["pool_median_km"] <= km_to:
        return pool, {**info, "basis": "pool"}
    return pool, {**info, "basis": "mismatch"}


# ── Model-year mix ───────────────────────────────────────────────────────────
# The mileage band alone left the 2018 530e "12% below market": 6 of the 9
# listings in its band were 2020–2022 cars. Inside one generation a model year
# is worth about as much as 50 000 km, so the year mix has to be handled too.
#
# Preferred: fit log(price) on model year and km over the pool and move every
# listing's price to the car's own year and km ("adjusted" comparables). On the
# 16 real 530e listings, leave-one-out, this is off by 3.4% on average (worst
# 8.9%) against each listing's own asking price, where the km band is off by
# 9.8% (worst 38.8%). The fit is only used when it is well supported:
_FIT_MIN_SAMPLE = 8           # listings stating year and km (3 parameters)
_FIT_MAX_YEAR_EFFECT = 0.20   # a model year newer is worth 0–20% more ...
_FIT_MAX_KM_EFFECT = 0.006    # ... and 1 000 km more is worth 0–0.6% less
_FIT_MAX_LEVERAGE = 0.5       # the car must sit inside the cloud of listings
_FIT_MAX_MARGIN = 0.06        # 90% confidence half-width of the reference
_FIT_OUTLIER_MIN = 0.15       # a listing within ~15% of the fit is never dropped
# Otherwise: listings of the car's year ±1 when at least 5 are, else what the
# mileage step selected if the car's year is the middle of it, else no
# reference. (Accepting a median year one off let a 2018 car through against
# five 2017–2021 listings, 20% away from the fitted value.)
_YEAR_NEAR = 1
_YEAR_TYPICAL = 0.5

# Two-sided 90% Student t quantiles by degrees of freedom (no scipy in prod).
_T90 = {5: 2.015, 6: 1.943, 7: 1.895, 8: 1.860, 9: 1.833, 10: 1.812, 11: 1.796,
        12: 1.782, 13: 1.771, 14: 1.761, 15: 1.753, 16: 1.746, 17: 1.740,
        18: 1.734, 19: 1.729, 20: 1.725, 21: 1.721, 22: 1.717, 23: 1.714,
        24: 1.711, 25: 1.708, 26: 1.706, 27: 1.703, 28: 1.701, 29: 1.699}


def _int_or_none(value) -> Optional[int]:
    try:
        return int(value) if value else None
    except (TypeError, ValueError):
        return None


def _fit_log_price(rows: list) -> Optional[dict]:
    """Least squares of log(price) on model year and km (in thousands) over
    (year, km, price) rows. None when the two effects cannot be told apart
    (one model year only, one mileage only, or year and km moving together)."""
    n = len(rows)
    if n < 4:
        return None
    y_mean = sum(r[0] for r in rows) / n
    k_mean = sum(r[1] for r in rows) / n / 1000.0
    p_mean = sum(math.log(r[2]) for r in rows) / n
    dy = [r[0] - y_mean for r in rows]
    dk = [r[1] / 1000.0 - k_mean for r in rows]
    dp = [math.log(r[2]) - p_mean for r in rows]
    syy = sum(a * a for a in dy)
    skk = sum(a * a for a in dk)
    syk = sum(a * b for a, b in zip(dy, dk))
    det = syy * skk - syk * syk
    if syy <= 0 or skk <= 0 or det <= 1e-9 * syy * skk:
        return None
    syp = sum(a * b for a, b in zip(dy, dp))
    skp = sum(a * b for a, b in zip(dk, dp))
    b_year = (skk * syp - syk * skp) / det
    b_km = (syy * skp - syk * syp) / det
    resid = [p - b_year * a - b_km * b for a, b, p in zip(dy, dk, dp)]
    return {
        "n": n, "y_mean": y_mean, "k_mean": k_mean, "p_mean": p_mean,
        "b_year": b_year, "b_km": b_km, "resid": resid,
        "sigma": math.sqrt(sum(r * r for r in resid) / (n - 3)),
        "inv": (skk / det, -syk / det, syy / det),
    }


def _fit_without_outliers(rows: list) -> tuple:
    """(fit, rows used). One least-squares fit is not robust to a salvage car or
    a deposit-only price the way a median is, so the listings furthest from a
    first fit — more than 3 robust standard deviations and more than ~15% — are
    left out, at most one in eight, and the fit is redone."""
    fit = _fit_log_price(rows)
    if not fit:
        return None, rows
    centre = _median(fit["resid"])
    spread = 1.4826 * _median([abs(r - centre) for r in fit["resid"]])
    limit = max(3 * spread, _FIT_OUTLIER_MIN)
    worst = sorted(range(len(rows)), key=lambda i: -abs(fit["resid"][i] - centre))
    drop = {i for i in worst[:max(1, len(rows) // 8)] if abs(fit["resid"][i] - centre) > limit}
    if not drop or len(rows) - len(drop) < _FIT_MIN_SAMPLE:
        return fit, rows
    kept = [r for i, r in enumerate(rows) if i not in drop]
    refit = _fit_log_price(kept)
    return (refit, kept) if refit else (fit, rows)


def _adjust_pool_to_car(pool: list, year: Optional[int], km: Optional[int]) -> tuple:
    """
    (prices adjusted to the car's year and km, year_comparison) when a fit of
    price on model year and km is well supported, else (None, reason):

      "unknown"   the car's year or km is not known
      "few"       fewer than 8 listings state both year and km
      "single"    the listings do not vary enough in year and km to fit
      "outside"   the car's year or km is beyond the listings', or the car sits
                  away from them (an old car with few km among young ones with
                  many): that would be extrapolating
      "unstable"  a coefficient has the wrong sign or an implausible size, or
                  the 90% confidence margin of the reference is wider than 6%
    """
    year, km = _int_or_none(year), _int_or_none(km)
    if not year or not km or km <= 0:
        return None, "unknown"
    rows = [(int(l["year"]), l["km"], l["price"]) for l in pool
            if _int_or_none(l.get("year")) and isinstance(l.get("km"), (int, float)) and l["km"] > 0]
    if len(rows) < _FIT_MIN_SAMPLE:
        return None, "few"
    fit, used = _fit_without_outliers(rows)
    if not fit:
        return None, "single"
    years = [r[0] for r in used]
    kms = [r[1] for r in used]
    if not (min(years) <= year <= max(years)) or not (min(kms) <= km <= max(kms)):
        return None, "outside"
    d_year = year - fit["y_mean"]
    d_km = km / 1000.0 - fit["k_mean"]
    i_yy, i_yk, i_kk = fit["inv"]
    leverage = 1.0 / fit["n"] + i_yy * d_year ** 2 + 2 * i_yk * d_year * d_km + i_kk * d_km ** 2
    if leverage > _FIT_MAX_LEVERAGE:
        return None, "outside"
    if not (0 <= fit["b_year"] <= _FIT_MAX_YEAR_EFFECT) or not (-_FIT_MAX_KM_EFFECT <= fit["b_km"] <= 0):
        return None, "unstable"
    t90 = _T90.get(fit["n"] - 3, 1.697)
    margin = math.exp(t90 * fit["sigma"] * math.sqrt(leverage)) - 1
    if margin > _FIT_MAX_MARGIN:
        return None, "unstable"

    value = fit["p_mean"] + fit["b_year"] * d_year + fit["b_km"] * d_km
    adjusted = [round(math.exp(value + r)) for r in fit["resid"]]
    return adjusted, {
        "basis":          "adjusted",
        "car_year":       year,
        "car_km":         km,
        "median_year":    _median(years),
        "year_from":      min(years),
        "year_to":        max(years),
        "km_from":        min(kms),
        "km_to":          max(kms),
        "count":          len(used),
        "excluded_count": len(rows) - len(used),
        "pool_count":     len(pool),
        # What the fit found for this model: price change per model year and
        # per 10 000 km, and the 90% margin of the reference price.
        "per_year_pct":   round((math.exp(fit["b_year"]) - 1) * 100, 1),
        "per_10k_km_pct": round((math.exp(fit["b_km"] * 10) - 1) * 100, 1),
        "margin_pct":     round(margin * 100, 1),
    }


def _select_year_comparables(compared: list, year: Optional[int]) -> tuple:
    """
    Year step when prices could not be adjusted: (listings to compare against,
    year_comparison).

      basis "near"      at least 5 listings are of the car's year ±1: only
                        those are compared.
      basis "typical"   every listing is within ±1 year, or fewer than 5 are
                        but the car's year is their median year: `compared`
                        is a fair comparison.
      basis "mismatch"  neither: the listings are mostly of other years. The
                        caller must not judge the price against them
                        (see _withhold_if_not_comparable).
      None              the car's year is unknown, or fewer than 5 listings
                        state theirs (the search is scoped to the comparison
                        window, so they are kept as before).
    """
    year = _int_or_none(year)
    known = [l for l in compared if _int_or_none(l.get("year"))]
    if not year or len(known) < _MIN_RELIABLE_MARKET_SAMPLE:
        return compared, None
    years = [int(l["year"]) for l in known]
    info = {
        "car_year":    year,
        "median_year": _median(years),
        "year_from":   min(years),
        "year_to":     max(years),
        "count":       len(compared),
    }
    near = [l for l in known if abs(int(l["year"]) - year) <= _YEAR_NEAR]
    if len(near) == len(known):
        return compared, {**info, "basis": "typical"}
    if len(near) >= _MIN_RELIABLE_MARKET_SAMPLE:
        near_years = [int(l["year"]) for l in near]
        return near, {**info, "basis": "near", "year_from": min(near_years),
                      "year_to": max(near_years), "count": len(near)}
    if abs(info["median_year"] - year) <= _YEAR_TYPICAL:
        return compared, {**info, "basis": "typical"}
    return compared, {**info, "basis": "mismatch"}


def _market_stats_from_pool(pool: list, km: Optional[int], label: str = "",
                            year: Optional[int] = None) -> dict:
    """Live market stats for one car out of a filtered comparable pool
    ({"price", "km", "year"} dicts). `year_comparison` and `km_comparison` say
    what the car was compared with. `pool_stats` (the whole pool, whatever the
    car) is what gets written back to market_price_stats, which is shared by
    every car of that model and year."""
    adjusted, year_info = _adjust_pool_to_car(pool, year, km)
    km_info = None
    if adjusted is not None:
        prices = adjusted
    else:
        not_adjusted = year_info
        compared, km_info = _select_km_comparables(pool, km)
        year_info = None
        if (km_info or {}).get("basis") != "mismatch":
            compared, year_info = _select_year_comparables(compared, year)
            if year_info:
                year_info["not_adjusted"] = not_adjusted
        prices = [l["price"] for l in compared]

    stats = {**_price_stats(prices), "source": "live"}
    if km_info:
        stats["km_comparison"] = km_info
    if year_info:
        stats["year_comparison"] = year_info
    if adjusted is not None or len(prices) != len(pool):
        stats["pool_stats"] = _price_stats([l["price"] for l in pool])
    print(f"[MARKET] {label}: median={stats['median_price']} avg={stats['avg_price']} "
          f"n={stats['sample_count']}"
          + (f" km={km_info['basis']} {km_info['km_from']}-{km_info['km_to']}"
             f" ({km_info['in_band_count']}/{km_info['pool_count']} in band)" if km_info else "")
          + (f" year={year_info['basis']} (car {year_info['car_year']}, median {year_info['median_year']:g})"
             if year_info else "")
          + (f" {year_info['per_year_pct']:+}%/year {year_info['per_10k_km_pct']:+}%/10k km"
             f" ±{year_info['margin_pct']}%" if adjusted is not None else ""))
    return stats


def _not_comparable(market_stats: Optional[dict]) -> bool:
    stats = market_stats or {}
    return ((stats.get("km_comparison") or {}).get("basis") == "mismatch"
            or (stats.get("year_comparison") or {}).get("basis") == "mismatch")


def _withhold_if_not_comparable(market_stats: dict) -> dict:
    """Drop the price reference when the comparables' mileage or model year is
    not comparable with the car's. With no reference, the price verdict, the
    negotiation figures and the price anomaly are all withheld rather than
    computed against different cars. What was found stays in km_comparison /
    year_comparison."""
    if not _not_comparable(market_stats):
        return market_stats
    return {k: v for k, v in market_stats.items()
            if k not in _MARKET_PRICE_KEYS and k != "pool_stats"}


_MARKET_REF_KEYS = (*_MARKET_PRICE_KEYS, "km_comparison", "year_comparison", "power_comparison")


def _market_ref_for_cache(market_stats: Optional[dict]) -> Optional[dict]:
    """The price reference worked out for this one car, kept with its cached
    analysis: the DB stats used on a cache hit are the whole pool's, unaware of
    the car's year and km."""
    stats = market_stats or {}
    if not (stats.get("km_comparison") or stats.get("year_comparison") or stats.get("power_comparison")):
        return None
    return {k: stats[k] for k in _MARKET_REF_KEYS if k in stats}


def _cached_market_for(market_stats: Optional[dict], llm: Optional[dict]) -> dict:
    """Market stats for a cached analysis: the reference the car was judged
    against when the analysis ran (or its absence, when it was withheld), on
    top of the DB stats' freshness fields."""
    ref = (llm or {}).get("_market_ref")
    if ref:
        kept = {k: v for k, v in (market_stats or {}).items() if k not in _MARKET_PRICE_KEYS}
        return {**kept, **ref}
    # Analyses cached before the reference was kept: only a withheld mileage
    # comparison was recorded.
    km_info = (llm or {}).get("_market_km")
    if (km_info or {}).get("basis") != "mismatch":
        return market_stats or {}
    return _withhold_if_not_comparable({**(market_stats or {}), "km_comparison": km_info})


def _get_market_stats(db: Session, model_id: int, year: Optional[int] = None) -> dict:
    """
    Fetch market price statistics for a model/year combination.
    Includes freshness info: source and days since last update.
    Stale data (>14 days) is flagged so the live scraper knows to refresh.

    Only rows written by an earlier live comparison ("live_scraped") count,
    and only analyses cached before the car's own reference was kept with them
    still read this. Not the seeded placeholder rows (source "Standvirtual/OLX
    2025"), and not the snapshot's "aggregated" rows either: those are the
    price of a model and year across every fuel and engine — right for a
    recommendation card, not a like-for-like reference for one car.
    """
    if year:
        row = db.execute(text("""
            SELECT AVG(avg_price) as avg_price,
                   MIN(min_price) as min_price,
                   MAX(max_price) as max_price,
                   SUM(sample_count) as sample_count,
                   MAX(updated_at) as last_updated,
                   MAX(source) as source
            FROM market_price_stats
            WHERE model_id = :model_id
              AND ABS(year - :year) <= 1
              AND source = 'live_scraped'
        """), {"model_id": model_id, "year": year}).mappings().fetchone()
    else:
        row = db.execute(text("""
            SELECT AVG(avg_price) as avg_price,
                   MIN(min_price) as min_price,
                   MAX(max_price) as max_price,
                   SUM(sample_count) as sample_count,
                   MAX(updated_at) as last_updated,
                   MAX(source) as source
            FROM market_price_stats
            WHERE model_id = :model_id
              AND source = 'live_scraped'
        """), {"model_id": model_id}).mappings().fetchone()

    if row and row["avg_price"]:
        result = {
            "avg_price": float(row["avg_price"]),
            "min_price": row["min_price"],
            "max_price": row["max_price"],
            "sample_count": int(row["sample_count"]) if row["sample_count"] else 0,
            "source": row["source"] or "seed",
        }
        if row["last_updated"]:
            from datetime import datetime, timezone
            try:
                updated = row["last_updated"]
                if hasattr(updated, 'tzinfo') and updated.tzinfo is None:
                    updated = updated.replace(tzinfo=timezone.utc)
                age_days = (datetime.now(timezone.utc) - updated).days
                result["age_days"] = age_days
                result["stale"] = age_days > 14
            except Exception:
                result["stale"] = True
        return result
    return {}


_STORED_POOL_MAX_AGE_DAYS = 45


def _stored_market_data(
    db: Session,
    model_id: Optional[int],
    brand_name: str,
    model_name: str,
    year: Optional[int],
    fuel_type: Optional[str] = None,
    gen_year_start: Optional[int] = None,
    gen_year_end: Optional[int] = None,
    sv_model_slug: Optional[str] = None,
    km: Optional[int] = None,
    trim: Optional[str] = None,
    power_hp: Optional[int] = None,
) -> dict:
    """
    The like-for-like comparison of _fetch_live_market_data, run on the
    listings the last market snapshot stored (price_observations) instead of a
    live search. Used when the live search fails or times out, so the price
    verdict does not depend on the marketplace answering this minute.

    Same rules: the comparison year window, the car's fuel, its engine power
    band (strict), and the site's sub-model or body variant when the listing
    gave one. A series or a trim-priced model with neither power nor
    sub-model is not compared at all. The year and mileage step is the
    same function. Returns {} when fewer than 3 stored listings qualify or the
    snapshot is older than _STORED_POOL_MAX_AGE_DAYS.
    """
    if not model_id or not year:
        return {}
    from app.scrapers.standvirtual import _sv_fuel_values, is_series_model, search_needs_trim

    model_search = _strip_accents(model_name or "").strip()
    power_range = _power_range(power_hp)
    variants = [v for v in (sv_model_slug or "").strip().lower().split("--") if v]
    if not power_range:
        # A MINI hatch is compared within its trim, which stored listings do
        # not carry; a series only within a sub-model.
        if search_needs_trim(brand_name, model_search, sv_model_slug):
            return {}
        if not variants and is_series_model(brand_name, model_search):
            return {}

    year_from, year_to, _ = _comparison_year_window(year, gen_year_start, gen_year_end)
    where = ["model_id = :model_id", "extraction_method = 'search_snapshot'",
             "price > 1000", "observed_at > now() - make_interval(days => :max_age)"]
    params: dict = {"model_id": model_id, "max_age": _STORED_POOL_MAX_AGE_DAYS}
    if year_from is not None:
        where.append("vehicle_year >= :year_from")
        params["year_from"] = year_from
    if year_to is not None:
        where.append("vehicle_year <= :year_to")
        params["year_to"] = year_to
    powertrains = _sv_fuel_values(fuel_type)
    if powertrains:
        where.append("powertrain = ANY(:powertrains)")
        params["powertrains"] = powertrains
    if power_range:
        where.append("engine_power_hp BETWEEN :p_from AND :p_to")
        params["p_from"], params["p_to"] = power_range
    # The site's own model of the listing, as the live search uses it: an
    # Astra hatch is compared with hatches, not with the Sports Tourer the
    # snapshot also files under "Astra" (the estate asks about 6% more).
    if variants:
        where.append("variant = ANY(:variants)")
        params["variants"] = variants
    try:
        rows = db.execute(text(f"""
            SELECT price, km, vehicle_year,
                   EXTRACT(EPOCH FROM (now() - observed_at)) / 86400 AS age_days
            FROM price_observations
            WHERE {' AND '.join(where)}
        """), params).fetchall()
    except Exception as e:
        # The snapshot columns do not exist before the first load.
        db.rollback()
        print(f"[MARKET] Stored pool unavailable: {e}")
        return {}
    if len(rows) < 3:
        return {}
    pool = [{"price": int(r[0]), "km": r[1], "year": _int_or_none(r[2])} for r in rows]
    label = f"stored:{model_id}:{year_from or 'x'}-{year_to or 'now'}"
    stats = _market_stats_from_pool(pool, km, label, year)
    stats["source"] = "snapshot"
    stats["age_days"] = int(min(float(r[3]) for r in rows))
    stats["stale"] = False
    return _with_power_comparison(stats, power_hp, power_range, pool)


def _extract_engine_hint(text: str) -> Optional[str]:
    """
    Extract engine variant string from listing text, e.g. '1.6 TDI', '2.0 TSI'.
    Used to narrow market comparisons to the same mechanical variant.
    """
    if not text:
        return None
    m = re.search(
        r"\b([1-9]\.[0-9]{1,2})\s*"
        r"(TDI|TSI|TFSI|TFSi|HDi|HDI|BlueHDi|BlueHDI|CDI|EcoBoost|EcoTec|"
        r"eTSI|eTDI|HEV|PHEV|GTE|GTI|GTD|SCe|TCe|dCi|VTi|THP|PureTech|"
        r"T-GDi|CRDI|D4D|Turbo|T[0-9]|D[0-9])?",
        text, re.IGNORECASE,
    )
    if m:
        disp = m.group(1)
        code = (m.group(2) or "").upper()
        return f"{disp} {code}".strip() if code else disp
    return None


def _sv_variant_code(url: Optional[str]) -> Optional[str]:
    """First standalone 3-digit token in a listing slug — the variant (e.g. '320',
    '525'). For BMW its first digit is the series. Returns None when absent."""
    if not url:
        return None
    m = re.search(r"/anuncio/([a-z0-9-]+?)-ID", url)
    if not m:
        return None
    for tok in m.group(1).split("-"):
        if re.fullmatch(r"\d{3}", tok):
            return tok
    return None


def _market_model_slug(normalized: dict, brand_name: str, model_name: str,
                       listing_url: Optional[str]) -> Optional[str]:
    """Standvirtual model slug to search the car's market under: the listing's
    own when it is a Standvirtual listing, else — for a model the site files as
    a series (BMW "Serie 3", Mercedes "Classe A", Lexus "NX") — the sub-model
    its title, its model as the source wrote it, or its URL names
    ("BMW 320d Touring" -> "320"). None otherwise: the search then goes by the
    model name."""
    slug = normalized.get("sv_model_slug")
    if slug:
        return slug
    from app.scrapers.standvirtual import sv_model_slug_for
    return sv_model_slug_for(brand_name, model_name, normalized.get("source_title"),
                             normalized.get("source_model_name"), listing_url)


def _market_trim(normalized: dict, listing_url: Optional[str]) -> Optional[str]:
    """The trim the listing names (title, version, model as the source wrote
    it, URL), for the models whose comparables must share it — see
    sv_models.trim_label. The catalogue's model name is not asked: every MINI
    hatch is a "Cooper" there."""
    from app.scrapers.standvirtual import trim_label
    return trim_label(normalized.get("source_title"), normalized.get("version"),
                      normalized.get("source_model_name"), listing_url)


def _power_range(power_hp) -> Optional[tuple]:
    """(from, to) in cv the comparables' engine power must lie in, or None when
    the car's power is not known (or not a plausible one)."""
    try:
        power = int(power_hp) if power_hp else 0
    except (TypeError, ValueError):
        return None
    if not 30 <= power <= 1200:
        return None
    return math.floor(power * (1 - _POWER_BAND)), math.ceil(power * (1 + _POWER_BAND))


def _with_power_comparison(stats: dict, power_hp, power_range: Optional[tuple], pool: list) -> dict:
    """Say what engine power the car was compared within, for the caption."""
    if not power_range or not stats:
        return stats
    return {**stats, "power_comparison": {
        "car_power_hp": int(power_hp), "power_from": power_range[0], "power_to": power_range[1],
        "pool_count": len(pool),
    }}


async def _fetch_live_market_data(
    brand_name: str,
    model_name: str,
    year: Optional[int],
    fuel_type: Optional[str] = None,
    engine_hint: Optional[str] = None,
    gen_year_start: Optional[int] = None,
    gen_year_end: Optional[int] = None,
    sv_model_slug: Optional[str] = None,
    variant_code: Optional[str] = None,
    km: Optional[int] = None,
    trim: Optional[str] = None,
    power_hp: Optional[int] = None,
) -> dict:
    """
    Fetch real-time market pricing from Standvirtual + OLX.

    The search is scoped to the comparison year window and the fuel, and up to
    _MARKET_MAX_PAGES Standvirtual result pages are read (the whole market of
    the variant when it has at most 128 listings). sv_model_slug is the site's
    model to search (see _market_model_slug); a series without one returns {}.

    Filters comparables progressively to ensure like-for-like pricing:
      1. Generation window (year_start–year_end from generations table) when available,
         else ±3 year fallback — so a Golf Mk7 (2012–2019) only compares with Mk7 listings.
         A generation wider than 8 years is narrowed to the car's year ±2
         (see _comparison_year_window).
      2. Fuel type match (diesel / gasolina / híbrido / elétrico)
      3. Engine: listings within 15% of the car's engine power when power_hp is
         known (the search is scoped to it too, see _POWER_BAND); else the
         engine variant hint in the listing title (e.g. '1.6 TDI', '2.0 TSI')
      4. The car's own year and mileage: listing prices are adjusted to them
         when a fit of price on year and km is well supported (see
         _adjust_pool_to_car). Otherwise only listings inside the car's km band
         are compared, if at least 5 are (_select_km_comparables), then only
         those of its year ±1 (_select_year_comparables). The result's
         `year_comparison` / `km_comparison` say what was compared.

    Filters 1–3 are only applied if they leave ≥ 3 listings — otherwise the broader
    pool is kept, so we never return empty due to over-filtering. The power band
    and the trim are the exceptions: listings outside them are never kept.

    Returns empty dict on failure or insufficient data (< 3 results).
    The filtered pool is cached in-memory for 6 hours per variant key; step 4
    runs per car on top of it.
    """
    if not brand_name or not model_name:
        return {}

    # Use the FULL model name (accent-stripped) for both search and cache key.
    # Using only the first word collapsed "Serie 1"/"Serie 3"/"Serie 5" into one
    # bucket ("serie") — mixing all BMW series into one search and one cache entry.
    # The scrapers resolve full names against the site's own list for a
    # precise search.
    model_search = _strip_accents(model_name).strip()          # "Série 3" -> "Serie 3"
    model_key   = model_search.lower().replace(" ", "-")       # -> "serie-3"
    fuel_key    = (fuel_type or "").lower().replace(" ", "")[:8]
    engine_key  = (engine_hint or "").lower().replace(" ", "")[:8]
    # The effective comparison window (not the raw generation) keys the cache:
    # two cars of one wide generation are compared against different years.
    cmp_year_from, cmp_year_to, cmp_label = _comparison_year_window(
        year, gen_year_start, gen_year_end)
    gen_key     = f"{cmp_year_from or 'x'}-{cmp_year_to or 'now'}"
    # The sub-model searched is part of the key: an A 180 and an A 250 are both
    # "Classe A" and must not share a cached pool.
    if sv_model_slug:
        model_key = f"{model_key}~{sv_model_slug.strip().lower()}"

    # The engine-power band the comparables must lie in (see _POWER_BAND). It
    # does what the trim and the sub-model do, so neither is required with it.
    power_range = _power_range(power_hp)
    if power_range:
        model_key = f"{model_key}~{power_range[0]}-{power_range[1]}cv"

    # A model whose trims are priced as different cars (the MINI hatch: One,
    # Cooper, Cooper S, John Cooper Works) is compared within the car's trim
    # only, and not at all when the listing does not name it: against all
    # trims the reference is off by more than 20% for half the petrol cars.
    from app.scrapers.standvirtual import search_needs_trim, trim_label
    if power_range:
        trim = None
    elif search_needs_trim(brand_name, model_search, sv_model_slug):
        if not trim:
            print(f"[MARKET] {brand_name} {model_name}: trim unknown - no like-for-like pool")
            return {}
        model_key = f"{model_key}~{trim.replace(' ', '-')}"
    else:
        trim = None

    cache_key   = f"{brand_name.lower().replace(' ', '-')}_{model_key}_{gen_key}_{fuel_key}_{engine_key}"
    now = time.time()

    # A series ("Serie 3", "Classe A") whose sub-model is not known is not
    # searched: against the whole series the reference is off by more than 20%
    # for one car in four that is not the series' most common sub-model
    # (leave-one-out over six series, 2026-11-13), one in ten against its own.
    # With the car's power known, the series is searched within the band.
    if not sv_model_slug and not power_range:
        from app.scrapers.standvirtual import is_series_model
        if is_series_model(brand_name, model_search):
            print(f"[MARKET] {brand_name} {model_name}: a series, sub-model unknown - no like-for-like pool")
            return {}

    cached = _market_cache.get(cache_key)
    if cached and (now - cached["cached_at"]) < _MARKET_CACHE_TTL:
        print(f"[MARKET] Cache hit for {cache_key}")
        return _with_power_comparison(_market_stats_from_pool(cached["pool"], km, cache_key, year),
                                      power_hp, power_range, cached["pool"])

    gen_label = (f"gen {gen_year_start}-{gen_year_end or 'now'}"
                 if gen_year_start is not None else "no gen")
    print(f"[MARKET] Live scrape - {brand_name} {model_name}"
          f"{' ' + fuel_type if fuel_type else ''}{' ' + engine_hint if engine_hint else ''}"
          f" [{gen_label}]")
    try:
        from app.scrapers.dispatcher import fetch_listings_all_sources

        # Pass the comparison year bounds directly into the search URL so
        # Standvirtual/OLX return only listings from this generation (or, for a
        # wide generation / no generation record, from around the car's year).
        scrape_year_from: Optional[int] = cmp_year_from
        scrape_year_to:   Optional[int] = cmp_year_to   # None = open-ended (still-current gen)

        listings = await fetch_listings_all_sources(
            brand=brand_name,
            model=model_search,
            budget_max=None,
            max_per_source=_MARKET_MAX_LISTINGS,
            max_pages=_MARKET_MAX_PAGES,
            power_range=power_range,
            fuel_type=fuel_type,
            sv_model_slug=sv_model_slug,
            year_from=scrape_year_from,
            year_to=scrape_year_to,
        )

        if not listings:
            return {}

        # Start with all listings that have a valid price
        pool = [
            l for l in listings
            if l.get("price") and isinstance(l["price"], (int, float)) and l["price"] > 1000
        ]

        # ── Filter 1: year guard — safety net for any stragglers the URL filter missed ──
        # The search URL already scopes results by year, so listings whose year we
        # couldn't parse (common on OLX cards) are kept — only listings with a parsed
        # year clearly OUTSIDE the window are dropped. This preserves sample size.
        if year and cmp_year_from is not None and len(pool) >= 5:
            cmp_end = cmp_year_to if cmp_year_to else 9999
            year_pool = [
                l for l in pool
                if (not l.get("year")) or (cmp_year_from <= int(l["year"]) <= cmp_end)
            ]
            if len(year_pool) >= 3:
                pool = year_pool
                print(f"[MARKET] Year guard ({cmp_label}) -> {len(pool)} listings")

        # ── Filter 2: fuel type ───────────────────────────────────────────────
        if fuel_type and len(pool) >= 4:
            fuel_norm = fuel_type.lower()
            fuel_pool = [
                l for l in pool
                if (l.get("fuel_type") or "").lower() and fuel_norm in (l.get("fuel_type") or "").lower()
            ]
            if len(fuel_pool) >= 3:
                pool = fuel_pool
                print(f"[MARKET] Fuel filter '{fuel_type}' -> {len(pool)} listings")

        # ── Filter 2a: trim ───────────────────────────────────────────────────
        # Strict, unlike the other filters: the listings of other trims are
        # never kept as a fallback (see above).
        if trim:
            pool = [l for l in pool if trim_label(l.get("title")) == trim]
            print(f"[MARKET] Trim filter '{trim}' -> {len(pool)} listings")

        # ── Filter 2p: engine power ───────────────────────────────────────────
        # Strict as well. The Standvirtual search was scoped to the band, so a
        # result of it that states no power is kept; anything else must state
        # a power inside it.
        if power_range:
            p_from, p_to = power_range
            pool = [
                l for l in pool
                if (p_from <= l["engine_power_hp"] <= p_to if l.get("engine_power_hp")
                    else l.get("source") == "standvirtual")
            ]
            print(f"[MARKET] Power filter {p_from}-{p_to} cv -> {len(pool)} listings")

        # ── Filter 2b: BMW series scope ───────────────────────────────────────
        # A "/bmw/serie-3" search over-returns the whole BMW range (116, 220,
        # 420, 520...). For BMW the first digit of the 3-digit variant IS the
        # series, so scope to it. Listings whose variant we can't read are kept.
        # BMW-only: for Mercedes the 3-digit number is not the class.
        if variant_code and len(variant_code) == 3 and "bmw" in (brand_name or "").lower() and len(pool) >= 5:
            series = variant_code[0]
            scoped = [
                l for l in pool
                if (lambda vc: vc is None or vc[0] == series)(_sv_variant_code(l.get("source_url")))
            ]
            if len(scoped) >= 4:
                pool = scoped
                print(f"[MARKET] BMW series filter '{series}xx' -> {len(pool)} listings")

        # ── Filter 3: engine variant hint ─────────────────────────────────────
        # A hard cut from 3 matches up, kept as it was now that prices are
        # adjusted for year and km. Leave-one-out over ten models' live pools
        # (2026-11-13), pricing each listing from the others:
        #   - 8 or more share the engine: the reference is off by more than 20%
        #     for 8–9% of cars against same-engine listings, 12–15% against all.
        #   - only 3–4 share it: against all engines the verdict is off by more
        #     than 20% for one car in three. Cutting leaves fewer than
        #     _MIN_RELIABLE_MARKET_SAMPLE, so the price verdict is withheld.
        # Raising the threshold to 5 would trade that withheld verdict for the
        # wrong one.
        # Not applied on top of the power band: together they are no more
        # accurate than the band alone and withhold more.
        if engine_hint and not power_range and len(pool) >= 5:
            hint_lower = engine_hint.lower()
            engine_pool = [
                l for l in pool
                if hint_lower in (l.get("title") or "").lower()
            ]
            if len(engine_pool) >= 3:
                pool = engine_pool
                print(f"[MARKET] Engine filter '{engine_hint}' -> {len(pool)} listings")

        if len(pool) < 3:
            print(f"[MARKET] Insufficient data ({len(pool)} listings) for {cache_key}")
            return {}

        # The pool is the same for every car of this variant; only the year and
        # mileage steps below depend on the car, so the pool is what is cached.
        pool = [{"price": l["price"], "km": l.get("km"), "year": _int_or_none(l.get("year"))}
                for l in pool]
        _market_cache[cache_key] = {"pool": pool, "cached_at": now}
        # Evict oldest entries if cache grows too large
        if len(_market_cache) > _MAX_MARKET_CACHE_KEYS:
            oldest = sorted(_market_cache, key=lambda k: _market_cache[k].get("cached_at", 0))
            for k in oldest[:len(_market_cache) - _MAX_MARKET_CACHE_KEYS]:
                del _market_cache[k]

        # ── Filter 4: the car's own model year and mileage ────────────────────
        return _with_power_comparison(_market_stats_from_pool(pool, km, cache_key, year),
                                      power_hp, power_range, pool)

    except Exception as e:
        print(f"[MARKET] Live scrape error for {brand_name} {model_name}: {e}")
        return {}


def _classify_source_type(source: str, domain: str) -> str:
    """Classify a source into marketplace | dealer | private | unknown."""
    if source in ("standvirtual", "olx", "custojusto"):
        return "marketplace"
    if source and source.startswith("dealer:"):
        return "dealer"
    # Known marketplace domains
    _MARKETPLACES = {"custojusto.pt", "autoscout24.pt", "carsnow.pt"}
    if domain in _MARKETPLACES:
        return "marketplace"
    # Known dealer aggregators
    _DEALER_AGGS = {"autosapo.pt", "auto.sapo.pt", "carnext.pt", "flexicar.pt"}
    if domain in _DEALER_AGGS:
        return "dealer"
    if domain:
        return "dealer"  # any other website is likely a dealer
    return "unknown"


def _extract_domain(url: str) -> str:
    """Extract clean domain from URL: 'https://www.soauto.pt/...' → 'soauto.pt'"""
    try:
        from urllib.parse import urlparse
        host = urlparse(url).netloc.lower().lstrip("www.")
        return host
    except Exception:
        return ""


def _record_price_observation(
    db: Session,
    model_id: Optional[int],
    generation_id: Optional[int],
    year: Optional[int],
    km: Optional[int],
    price: Optional[int],
    fuel_type: Optional[str],
    seller_type: str,
    source_url: str,
    source: str,
    extraction_method: Optional[str],
    data_quality_score: Optional[float],
    observation_type: str = "user_analysis",
) -> None:
    """
    Record a price observation from any source into the market intelligence table.
    Every analysis — SV, OLX, dealer site, private — feeds the collective data.
    Silently skips if price is missing or out of range.
    """
    if not price or price < 500 or price > 500_000:
        return
    if not source_url:
        return

    domain = _extract_domain(source_url)
    source_type = _classify_source_type(source, domain)

    try:
        db.execute(text("""
            INSERT INTO price_observations
                (model_id, generation_id, vehicle_year, km, price, fuel_type,
                 seller_type, source_type, source_domain, source_url,
                 extraction_method, data_quality, observation_type, observed_at)
            VALUES
                (:model_id, :gen_id, :year, :km, :price, :fuel,
                 :seller, :src_type, :domain, :url,
                 :method, :quality, :obs_type, now())
            ON CONFLICT (source_url) DO UPDATE SET
                price           = EXCLUDED.price,
                km              = COALESCE(EXCLUDED.km, price_observations.km),
                data_quality    = EXCLUDED.data_quality,
                extraction_method = EXCLUDED.extraction_method,
                observed_at     = now()
        """), {
            "model_id": model_id,
            "gen_id":   generation_id,
            "year":     year,
            "km":       km,
            "price":    price,
            "fuel":     fuel_type,
            "seller":   seller_type or "desconhecido",
            "src_type": source_type,
            "domain":   domain,
            "url":      source_url,
            "method":   extraction_method,
            "quality":  data_quality_score,
            "obs_type": observation_type,
        })
        db.commit()
    except Exception as e:
        print(f"[PRICE_OBS] Insert error: {e}")
        db.rollback()


def _compute_identity_hash(
    brand_name: Optional[str],
    model_name: Optional[str],
    year: Optional[int],
    fuel_type: Optional[str],
    description: Optional[str],
) -> Optional[str]:
    """
    Fingerprint a physical car so it can be matched across relists at different URLs.
    Sellers who relist typically copy-paste their own description, so a normalized
    description hash combined with brand/model/year/fuel is a strong identity signal.
    Returns None when there isn't enough signal to fingerprint reliably.
    """
    desc = (description or "").strip()
    if not desc or len(desc) < 40:
        # Too little text to fingerprint reliably — skip rather than create false matches.
        return None
    # Normalize: strip accents, lowercase, collapse whitespace, cap length.
    norm = unicodedata.normalize("NFKD", desc)
    norm = "".join(c for c in norm if not unicodedata.combining(c))
    norm = re.sub(r"\s+", " ", norm.lower()).strip()[:600]
    signature = "|".join([
        (brand_name or "").lower().strip(),
        (model_name or "").lower().strip(),
        str(year or ""),
        (fuel_type or "").lower().strip(),
        norm,
    ])
    return hashlib.sha256(signature.encode("utf-8")).hexdigest()


def _record_listing_snapshot(
    db: Session,
    normalized_listing_id: Optional[int],
    model_id: Optional[int],
    brand_name: Optional[str],
    model_name: Optional[str],
    year: Optional[int],
    km: Optional[int],
    price: Optional[int],
    fuel_type: Optional[str],
    seller_type: Optional[str],
    photo_count: Optional[int],
    source_url: str,
    description: Optional[str],
) -> None:
    """
    Append an immutable snapshot of this listing observation. NEVER overwrites —
    every call is a new row. This is the moat data: price history per URL,
    days-on-market, relisting detection, and odometer-rollback detection all
    derive from accumulated snapshots. Fire-and-forget: never breaks an analysis.
    """
    if not source_url or not price or price < 500 or price > 500_000:
        return
    try:
        identity_hash = _compute_identity_hash(brand_name, model_name, year, fuel_type, description)
        db.execute(text("""
            INSERT INTO listing_snapshots
                (source_url, source_domain, normalized_listing_id, model_id,
                 brand_name, model_name, year, km, price, fuel_type,
                 seller_type, photo_count, identity_hash, observed_at)
            VALUES
                (:url, :domain, :norm_id, :model_id,
                 :brand, :model, :year, :km, :price, :fuel,
                 :seller, :photos, :ihash, now())
        """), {
            "url":     source_url,
            "domain":  _extract_domain(source_url),
            "norm_id": normalized_listing_id,
            "model_id": model_id,
            "brand":   brand_name,
            "model":   model_name,
            "year":    year,
            "km":      km,
            "price":   price,
            "fuel":    fuel_type,
            "seller":  seller_type or "desconhecido",
            "photos":  photo_count,
            "ihash":   identity_hash,
        })
        db.commit()
    except Exception as e:
        print(f"[SNAPSHOT] Insert error: {e}")
        db.rollback()


def _build_price_history(db: Session, listing: dict) -> Optional[dict]:
    """
    Surface price history + relisting from the accumulated listing_snapshots —
    things ChatGPT structurally cannot know. Returns None until there's a real
    signal (a price change, or the same car seen before at another URL).
    """
    url = listing.get("source_url")
    if not url:
        return None
    try:
        rows = db.execute(text("""
            SELECT price, km, observed_at
            FROM listing_snapshots
            WHERE source_url = :url AND price IS NOT NULL
            ORDER BY observed_at ASC
        """), {"url": url}).mappings().fetchall()
    except Exception:
        return None
    if not rows:
        return None

    def _days_ago(dt) -> Optional[int]:
        if not dt:
            return None
        if getattr(dt, "tzinfo", None) is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return (datetime.now(timezone.utc) - dt).days

    first, last = rows[0], rows[-1]
    prices = [r["price"] for r in rows]
    drop_total = first["price"] - last["price"]

    last_change = None
    for i in range(len(rows) - 1, 0, -1):
        if rows[i]["price"] != rows[i - 1]["price"]:
            last_change = {
                "from": rows[i - 1]["price"],
                "to": rows[i]["price"],
                "days_ago": _days_ago(rows[i]["observed_at"]),
            }
            break

    # Same physical car seen before at a different URL (relisting / rollback).
    relisted = False
    rollback = False
    ihash = _compute_identity_hash(
        listing.get("brand_name"), listing.get("model_name"),
        listing.get("year"), listing.get("fuel_type"), listing.get("description"),
    )
    if ihash:
        try:
            prev = db.execute(text("""
                SELECT km FROM listing_snapshots
                WHERE identity_hash = :h AND source_url != :url
                ORDER BY observed_at ASC LIMIT 1
            """), {"h": ihash, "url": url}).mappings().fetchone()
            if prev:
                relisted = True
                cur_km = listing.get("km")
                if prev["km"] and cur_km and cur_km < prev["km"] - 500:
                    rollback = True
        except Exception:
            pass

    if len(set(prices)) <= 1 and not relisted:
        return None  # nothing worth showing yet

    return {
        "observations":       len(rows),
        "tracked_days":       _days_ago(first["observed_at"]),
        "first_price":        first["price"],
        "current_price":      last["price"],
        "drop_total":         drop_total if drop_total > 0 else 0,
        "last_change":        last_change,
        "relisted_before":    relisted,
        "rollback_suspected": rollback,
    }


def _with_stored_engine(row: dict) -> dict:
    """A listing row read back from the DB, plus the engine facts its last
    analysis saved (power, version, displacement, gearbox).

    The listing table has no column for them; they live in the analysis blob
    (`_listing_engine`), which stays on the row after the analysis goes stale.
    Without them a re-analysed listing is compared across every engine of its
    model, and matched against no engine-specific known issue. A column the
    row does have (fuel) is never overridden; a listing analysed before the
    blob carried them, or never analysed, comes back as it is."""
    out = dict(row)
    blob = out.pop("llm_analysis", None)
    if isinstance(blob, str):
        try:
            blob = json.loads(blob)
        except ValueError:
            blob = None
    engine = blob.get("_listing_engine") if isinstance(blob, dict) else None
    if isinstance(engine, dict):
        for key in _LISTING_ENGINE_KEYS:
            if out.get(key) is None and engine.get(key) is not None:
                out[key] = engine[key]
    return out


def _resolve_model_from_url(db: Session, listing_url: str) -> Optional[dict]:
    """A listing already in the DB, as stored. It is fetched again before it
    is analysed (_refetch_stored_listing); this row is what the analysis falls
    back on when that fetch fails.

    The row's id comes with it: the analysis that follows is stored on that
    row (and gets its permalink) like the analysis of a fresh scrape. Without
    it the re-analysis of a listing whose stored analysis had gone stale was
    thrown away, and redone in full on every later request. The row read is
    the one the cache check reads (the latest for the URL)."""
    row = db.execute(text("""
        SELECT n.id, n.model_id, n.brand_name, n.model_name, n.year, n.km, n.price,
               n.km_per_year, n.price_delta, n.deal_tier, n.deal_score, n.seller_type,
               n.description, n.photo_count, n.fuel_type, n.llm_analysis, r.source_url
        FROM normalized_listings n
        JOIN raw_listings r ON r.id = n.raw_listing_id
        WHERE r.source_url = :url
        ORDER BY n.id DESC
        LIMIT 1
    """), {"url": listing_url}).mappings().fetchone()
    return _with_stored_engine(row) if row else None


# ── Variant → series mapping for brands that use numeric/letter variants ──

# BMW: "116", "116d", "120i" → "Série 1"; "320d" → "Série 3"; "X3" → "X3"
_BMW_SERIES_MAP = {
    "1": "Serie 1",  # 114, 116, 118, 120, 125, 128, 130, 135, 140
    "2": "Serie 2",  # 216, 218, 220, 225, 228, 230, 235, 240
    "3": "Serie 3",  # 316, 318, 320, 325, 328, 330, 335, 340
    "4": "Serie 4",  # 418, 420, 425, 428, 430, 435, 440
    "5": "Serie 5",  # 518, 520, 525, 528, 530, 535, 540, 545, 550
    "6": "Serie 6",  # 620, 630, 640, 650
    "7": "Serie 7",  # 725, 730, 740, 745, 750, 760
    "8": "Serie 8",  # 840, 850
}

# Mercedes: "A 180", "A180" → "Classe A"; "CLA" stays "CLA"
_MERC_CLASS_MAP = {
    "a": "Classe A", "b": "Classe B", "c": "Classe C",
    "e": "Classe E", "s": "Classe S", "v": "Classe V",
}


def _models_compatible(extracted: str, matched: str) -> bool:
    """
    Guard against a loose LIKE match resolving to a DIFFERENT model — e.g.
    'Range Rover Velar' matching 'Range Rover Evoque' on the shared word 'range'.
    A loose match is only trusted when the names are equal, one contains the
    other, or they share the DISTINGUISHING (last) token.
    """
    e = _strip_accents(extracted or "").lower().strip()
    m = _strip_accents(matched or "").lower().strip()
    if not e or not m:
        return True
    if e == m or e in m or m in e:
        return True
    et, mt = e.split(), m.split()
    # A shared last word only identifies the model when it is not a body style:
    # a BMW "640 Gran Coupé" is not a "Série 2 Gran Coupé".
    return bool(et and mt and et[-1] == mt[-1] and et[-1] not in _BODY_STYLE_WORDS)


# Body styles, raised-suspension lines and powertrain badges: the same model
# in the catalogue ("A3 Sportback" is an A3, "Niro EV" a Niro). Deliberately
# short. Words that can name a different car are NOT here: "Cross" (Corolla
# Cross), "Sport" (Range Rover Sport), "Grand" (Grand Vitara), "Plus" (Golf
# Plus), "Verso", "Picasso", "E-Tech" (the Mégane E-Tech is another car).
_BODY_STYLE_PHRASES = (
    "cross country", "sport tourer", "sports tourer", "touring sports",
    "station wagon", "sport turismo",
)
_BODY_STYLE_WORDS = frozenset({
    "sportback", "avant", "limousine", "cabrio", "cabriolet", "coupe", "roadster",
    "sw", "break", "st", "cw", "fastback", "tourer", "touring", "caravan", "variant",
    "combi", "sedan", "estate", "hatchback", "crossback",
    "allroad", "alltrack", "allstreet", "citycarver", "x-perience", "active",
    "ev", "electric", "hybrid", "phev", "n", "amg",
})

_BRAND_ALIASES = {"vw": "volkswagen", "mercedes": "mercedes-benz", "merc": "mercedes-benz"}

# Another name the market uses for a catalogue model, (brand, name as listed)
# -> catalogue name. Checked on 2026-11-13 against every model name on
# Standvirtual: the Hyundai Kona is sold in Portugal as the Kauai, the plug-in
# MG HS as the EHS, the 2017-2021 Opel Grandland as the Grandland X, the
# electric Renault Scénic as the Scenic E-Tech.
_MODEL_NAME_ALIASES = {
    ("hyundai", "kauai"): "kona",
    ("mg", "ehs"): "hs",
    ("opel", "grandland x"): "grandland",
    ("renault", "scenic e-tech"): "scenic",
}


def _electric_twin(name: str) -> Optional[str]:
    """The model an electric version is named after, when the name is nothing
    but that model with an "e": 'e-208' -> '208', 'mokka-e' -> 'mokka',
    '500e' -> '500'. None otherwise — and 'megane e-tech' is not one (it is a
    different car from the Mégane)."""
    m = re.fullmatch(r"e[- ](.+)", name) or re.fullmatch(r"(.+)-e", name) or re.fullmatch(r"(\d{3,4})e", name)
    return m.group(1).strip() if m and m.group(1).strip() else None


_MINI_HATCH_WORDS = frozenset({"one", "cooper", "john", "works", "jcw"})
_MINI_OTHER_MODELS = frozenset({"clubman", "countryman", "paceman", "aceman", "coupe", "roadster"})


def _norm_name(s: Optional[str]) -> str:
    """Accent-free, lower-case, single-spaced: 'Citroën' -> 'citroen', 'Série  3' -> 'serie 3'."""
    return re.sub(r"\s+", " ", _strip_accents(s or "").lower()).strip()


def _core_model_name(name: str) -> str:
    """A normalised model name without body-style words: 'a3 sportback' -> 'a3'."""
    for phrase in _BODY_STYLE_PHRASES:
        name = name.replace(phrase, " ")
    return " ".join(w for w in name.split() if w not in _BODY_STYLE_WORDS)


def match_catalogue_model(
    catalogue: list, brand_name: str, model_name: str, model_first_word: str
) -> Optional[dict]:
    """
    Pure matcher behind _resolve_vehicle_model. `catalogue` is every
    vehicle_models row as {id, brand_name, model_name, body_type}.

    Names are compared without accents on BOTH sides. The SQL this replaces
    stripped accents from the listing only, so nothing matched a catalogue
    name that has one: every Citroën, Renault Mégane and Scénic, and every BMW
    "Série" (so every 320, 118, 530 ...) missed and became a stub model.

    Strict on purpose — a wrong match corrupts the whole analysis, a miss only
    loses the catalogue extras. A listing matches a model when:
      1. BMW: its number names a series we have ("320" -> "Série 3"); checked
         first, so a stub named "530" cannot capture the 530s. Two models of
         one series (Série 2 Active Tourer / Gran Coupé) need the body words.
      2. its name is the catalogue name (this also finds stubs), or
      3. its name without body-style words is ("A3 Sportback" -> "A3"), or it
         is another name for the model: a market alias ("Kauai" -> "Kona") or
         the electric version under its own name ("e-208" -> "208").
      4. Mercedes: a class letter -> "Classe X"; MINI: a hatch trim -> "Cooper".
    The old substring and any-word matches are gone: they made a C4 Cactus a
    C4, a Range Rover a Range Rover Sport and a Kangoo E-Tech a Renault 5.
    """
    brand = _norm_name(brand_name)
    brand = _BRAND_ALIASES.get(brand, brand)
    model = _norm_name(model_name)
    first = _norm_name(model_first_word)
    if not brand or not first or not model:
        return None

    rows = []
    for r in catalogue:
        rb = _norm_name(r.get("brand_name"))
        if rb and (brand == rb or brand in rb.split("-") or rb in brand.split()):
            rows.append({**r, "_name": _norm_name(r.get("model_name")),
                         "_stub": not (r.get("body_type") or "").strip()})
    if not rows:
        return None
    real = [r for r in rows if not r["_stub"]]
    tokens = model.split()

    def out(row: dict) -> dict:
        return {"id": row["id"], "brand_name": row["brand_name"], "model_name": row["model_name"]}

    def named(name: str, pool: list = real) -> Optional[dict]:
        return next((r for r in pool if r["_name"] == name), None)

    # 0. a site model that belongs to a catalogue model of another name: a
    # body style or sub-model ("Insignia Sports Tourer", BMW "216 Gran
    # Tourer"), one car under several site names ("Crossland X").
    from app.scrapers.sv_models import catalogue_target
    target = catalogue_target(brand_name, model_name)
    if target:
        want = (_norm_name(target[0]), _norm_name(target[1]))
        hit = next((r for r in catalogue if (r.get("body_type") or "").strip()
                    and (_norm_name(r.get("brand_name")), _norm_name(r.get("model_name"))) == want), None)
        if hit:
            return out(hit)

    # 1. BMW number -> series
    if brand == "bmw":
        m = re.match(r"^(\d)[1-9]\d(?!\d)", first)
        if m:
            series = _norm_name(_BMW_SERIES_MAP.get(m.group(1)))
            cands = [r for r in real if r["_name"] == series or r["_name"].startswith(series + " ")]
            if len(cands) == 1:
                hit = cands[0]
            else:
                scored = sorted(((len(set(tokens) & set(r["_name"].split())), r) for r in cands),
                                key=lambda t: -t[0])
                hit = scored[0][1] if scored and scored[0][0] > 0 and (
                    len(scored) == 1 or scored[0][0] > scored[1][0]) else None
            if hit:
                print(f"[MODEL] BMW variant '{model_name}' -> '{hit['model_name']}'")
                return out(hit)
            return named(model, rows) and out(named(model, rows))   # a stub from an earlier analysis

    # 2. the catalogue name — with and without the brand repeated in front ("DS 7" -> "7")
    names = [model]
    for b in {brand, _norm_name(brand_name)}:
        if model.startswith(b + " "):
            names.append(model[len(b) + 1:])
    for name in names:
        hit = named(name) or named(name, rows)
        if hit:
            return out(hit)

    # 3. the name without body-style words
    for name in names:
        core = _core_model_name(name)
        hit = named(core) if core and core != name else None
        if hit:
            return out(hit)

    # 3b. another name for a catalogue model: a market alias ("Kauai" is the
    # Kona), or the electric version filed under its own name ("e-208" is a
    # 208, "Mokka-e" a Mokka). With and without body-style words.
    for name in names:
        for candidate in (name, _core_model_name(name)):
            other = _MODEL_NAME_ALIASES.get((brand, candidate)) or _electric_twin(candidate)
            hit = named(other) if other else None
            if hit:
                return out(hit)

    # 4. Mercedes: "A 180", "A180", "Classe A" -> "Classe A"; "Classe CLA" -> "CLA"
    if brand == "mercedes-benz":
        key = tokens[1] if tokens[0] == "classe" and len(tokens) > 1 else tokens[0]
        letters = re.match(r"^[a-z]+", key)
        key = letters.group(0) if letters else key
        classe = _norm_name(_MERC_CLASS_MAP.get(key))
        if classe:
            hit = (named(f"{key} coupe") if "coupe" in tokens else None) or named(classe)
            if hit:
                print(f"[MODEL] Mercedes variant '{model_name}' -> '{hit['model_name']}'")
                return out(hit)
        elif len(key) >= 2:
            hit = named(key)
            if hit:
                return out(hit)

    # MINI: the hatch is sold by trim ("One", "Cooper S", "John Cooper Works")
    if brand == "mini" and set(tokens) & _MINI_HATCH_WORDS and not set(tokens) & _MINI_OTHER_MODELS:
        hit = named("cooper")
        if hit:
            return out(hit)

    return None


def _resolve_vehicle_model(
    db: Session, brand_name: str, model_name: str, model_first_word: str
) -> Optional[dict]:
    """
    Resolve a scraped brand/model to a vehicle_models DB row.

    Strategy (precision over recall — a wrong match corrupts the whole analysis):
    0. Exact full model-name match (also finds previously auto-created models)
    1. BMW variant mapping: "116" → "Série 1", "320" → "Série 3"
    2. Mercedes variant mapping: "A" → "Classe A", "C" → "Classe C"
    3. Exact / loose match on first word — loose matches validated by
       _models_compatible so a generic word can't match a different model
    4. Fuzzy: each word, also compatibility-validated
    Returns None when there's no confident match (caller auto-creates the model).
    """
    if not brand_name or not model_first_word:
        return None

    catalogue = [dict(r) for r in db.execute(text("""
        SELECT vm.id, b.name AS brand_name, vm.name AS model_name, vm.body_type
        FROM vehicle_models vm
        JOIN brands b ON b.id = vm.brand_id
        ORDER BY vm.id
    """)).mappings()]
    row = match_catalogue_model(catalogue, brand_name, model_name, model_first_word)
    if row is None:
        print(f"[MODEL] No DB match for {brand_name} '{model_name}' (first_word='{model_first_word}')")
    return row


def _get_or_create_model(
    db: Session, brand_name: str, model_name: str, model_first_word: str
) -> Optional[dict]:
    """
    Resolve a scraped brand/model to a vehicle_models row, CREATING it if it's
    not in the DB (self-healing catalogue). A model we don't have is registered
    on first sight rather than mis-matched to a different one — the market
    comparison then uses the listing's own source slug, so it's correct from day
    one even before reliability/known-issues are enriched.
    """
    resolved = _resolve_vehicle_model(db, brand_name, model_name, model_first_word)
    if resolved:
        return resolved

    # Only auto-create when we have a clean, plausible brand + model.
    brand_clean = (brand_name or "").strip()
    model_clean = (model_name or "").strip()
    if not brand_clean or not model_clean or len(model_clean) > 40:
        return None
    # Guard against trim noise leaking into the model name.
    model_clean = re.sub(r"\s+", " ", model_clean)[:40].strip()

    try:
        # Compared without accents on both sides — "Citroën" must find the
        # existing brand, not create a second one.
        brand_norm = _norm_name(brand_clean)
        brand_norm = _BRAND_ALIASES.get(brand_norm, brand_norm)
        brand_row = next((b for b in db.execute(text(
            "SELECT id, name FROM brands ORDER BY id"
        )).mappings() if _norm_name(b["name"]) == brand_norm), None)
        if brand_row:
            brand_id = brand_row["id"]
        else:
            brand_id = db.execute(text(
                "INSERT INTO brands (name) VALUES (:n) RETURNING id"
            ), {"n": brand_clean}).scalar()
            print(f"[MODEL] Auto-created brand '{brand_clean}'")

        new_id = db.execute(text("""
            INSERT INTO vehicle_models (brand_id, name)
            VALUES (:bid, :name)
            RETURNING id
        """), {"bid": brand_id, "name": model_clean}).scalar()
        db.commit()
        print(f"[MODEL] Auto-registered '{brand_clean} {model_clean}' (id={new_id})")
        return {"id": new_id, "brand_name": brand_clean, "model_name": model_clean}
    except Exception as e:
        db.rollback()
        print(f"[MODEL] Auto-create failed for '{brand_clean} {model_clean}': {e}")
        return None


async def _scrape_and_store_listing(db: Session, listing_url: str, refetch: bool = False,
                                    pasted_text: Optional[str] = None) -> Optional[dict]:
    """
    Fetch the listing detail page via the appropriate scraper (SV or OLX),
    infer model from URL slugs or title, store in raw_listings + normalized_listings.
    Returns the normalized row dict.

    refetch: the listing is already stored and is being fetched again for its
    current state. A fetch that brings no usable price then writes nothing and
    returns None — see the guard below.
    """
    # Detect source and validate
    source = detect_source(listing_url) or "desconhecido"

    # Route to correct scraper via dispatcher — or read the text the buyer
    # pasted, when the page could not be fetched.
    if pasted_text:
        from app.scrapers.generic import extract_from_pasted_text
        detail = await extract_from_pasted_text(pasted_text, listing_url)
    else:
        detail = await fetch_detail_for_url(listing_url)

    # Listing sold/removed (HTTP 404/410) — surface it cleanly rather than a
    # broken empty analysis.
    if detail.get("_gone"):
        return {"_gone": True}

    # JS SPA flag — site had minimal page text, but may still have meta tags.
    # Continue with whatever data we have; the response will include a caveat.
    _js_limited = detail.pop("_js_only", False)
    _pw_debug = detail.pop("_pw_debug", None)

    # Extraction metadata — track scraper health and data quality
    _extraction_method = detail.pop("_extraction_method", None)
    _extraction_layers = detail.pop("_extraction_layers", None)
    _data_quality = detail.pop("_data_quality", None)
    # Title used internally by extraction layers. Kept aside: it names the
    # sub-model ("BMW 320d Touring") that the series-level model name loses.
    source_title = detail.pop("title", None)

    # Brand/model: prefer what the scraper extracted (generic scraper returns brand/model directly)
    # Fall back to URL slug extraction for native sources
    brand_name = detail.get("brand", "")
    model_name = detail.get("model", "")

    if not brand_name or not model_name:
        brand_slug, model_slug = extract_slugs_from_url(listing_url)
        if not brand_name:
            brand_name = brand_slug.replace("-", " ").title()
        if not model_name:
            model_name = model_slug.replace("-", " ").title()

    # Brand normalisation map (slugs → canonical brand names)
    slug_to_brand = {
        "bmw": "BMW", "mercedes-benz": "Mercedes-Benz", "mercedes": "Mercedes-Benz",
        "volkswagen": "Volkswagen", "vw": "Volkswagen",
        "toyota": "Toyota", "honda": "Honda", "mazda": "Mazda", "volvo": "Volvo",
        "peugeot": "Peugeot", "renault": "Renault", "ford": "Ford",
        "seat": "SEAT", "kia": "Kia", "hyundai": "Hyundai",
        "audi": "Audi", "opel": "Opel", "skoda": "Skoda",
        "fiat": "Fiat", "dacia": "Dacia", "citroen": "Citroen", "citroën": "Citroen",
        "nissan": "Nissan", "mini": "MINI", "alfa-romeo": "Alfa Romeo", "alfa romeo": "Alfa Romeo",
        "land-rover": "Land Rover", "land rover": "Land Rover",
        "porsche": "Porsche", "tesla": "Tesla",
    }
    brand_name = slug_to_brand.get(brand_name.lower(), brand_name)

    # If detail page returned richer data (OLX provides year/km/price in detail), use it
    year = detail.get("year")
    km = detail.get("km")
    price = detail.get("price")
    fuel_type = detail.get("fuel_type")

    # ── Data validation: catch suspicious/impossible values ──────────────
    _data_warnings: list[str] = []

    # Range checks — clamp or clear impossible values
    if price is not None:
        if price < 500 or price > 500_000:
            _data_warnings.append(f"price_out_of_range:{price}")
            price = None
    if km is not None:
        if km < 0 or km > 999_000:
            _data_warnings.append(f"km_out_of_range:{km}")
            km = None
    if year is not None:
        if year < 1990 or year > datetime.now(timezone.utc).year + 1:
            _data_warnings.append(f"year_out_of_range:{year}")
            year = None

    # Cross-field consistency checks
    if year and km:
        age = max(1, datetime.now(timezone.utc).year - year)
        km_per_year = km / age
        if km_per_year > 80_000:  # >80k km/year is almost certainly wrong
            _data_warnings.append(f"km_vs_year_mismatch:km={km},year={year},kpy={km_per_year:.0f}")
        elif year >= 2023 and km > 100_000:
            _data_warnings.append(f"new_car_high_km:{year},{km}")

    if year and price:
        age = max(1, datetime.now(timezone.utc).year - year)
        if age <= 3 and price < 2000:
            _data_warnings.append(f"new_car_too_cheap:{year},EUR{price}")
        if age >= 20 and price > 100_000 and "porsche" not in brand_name.lower():
            _data_warnings.append(f"old_car_too_expensive:{year},EUR{price}")

    # Suspicious price patterns (test/placeholder values)
    if price and str(price) in ("1234", "9999", "1111", "99999", "12345", "11111"):
        _data_warnings.append(f"suspicious_price_pattern:{price}")

    if _data_warnings:
        print(f"[VALIDATION] {listing_url}: {_data_warnings}")

    # A stored listing fetched again: when the page did not come back, or came
    # back without a usable price, nothing below may run. It would replace the
    # stored description with a blank and the stored model with a guess from
    # the URL. The caller keeps the stored row.
    if refetch and not price:
        print(f"[AD_ANALYSIS] Re-fetch of {listing_url} brought no price "
              f"({_extraction_method or 'no method'}) — stored listing kept")
        return None

    # Insert raw_listing (source-tagged correctly)
    raw_id = db.execute(text("""
        INSERT INTO raw_listings (source, source_url, description, seller_type, photo_count, scraped_at)
        VALUES (:source, :url, :desc, :seller_type, :photo_count, NOW())
        ON CONFLICT (source_url) DO UPDATE
            SET description = EXCLUDED.description,
                seller_type = EXCLUDED.seller_type,
                photo_count = EXCLUDED.photo_count,
                scraped_at = NOW()
        RETURNING id
    """), {
        "source": source,
        "url": listing_url,
        "desc": detail.get("description", ""),
        "seller_type": detail.get("seller_type", "desconhecido"),
        "photo_count": detail.get("photo_count", 0),
    }).scalar()
    db.commit()

    # Lookup model — resolve, or auto-register if unknown (self-healing catalogue).
    # Guard against empty brand/model (generic scraper may not resolve them).
    source_model_name = model_name
    model_first_word = (model_name.lower().split() or [""])[0]
    model_row = _get_or_create_model(db, brand_name, model_name, model_first_word)

    model_id = model_row["id"] if model_row else None
    resolved_brand = model_row["brand_name"] if model_row else brand_name
    resolved_model = model_row["model_name"] if model_row else model_name

    # Insert or update normalized_listing — include year/km/price when scraper provided them
    norm_id = db.execute(text("""
        INSERT INTO normalized_listings
            (raw_listing_id, model_id, brand_name, model_name,
             seller_type, description, photo_count,
             year, km, price, fuel_type)
        VALUES (:raw_id, :model_id, :brand, :model,
                :seller_type, :desc, :photos,
                :year, :km, :price, :fuel_type)
        ON CONFLICT (raw_listing_id) DO UPDATE
            SET model_id    = EXCLUDED.model_id,
                brand_name  = EXCLUDED.brand_name,
                model_name  = EXCLUDED.model_name,
                seller_type = EXCLUDED.seller_type,
                description = EXCLUDED.description,
                photo_count = EXCLUDED.photo_count,
                year        = COALESCE(EXCLUDED.year, normalized_listings.year),
                km          = COALESCE(EXCLUDED.km, normalized_listings.km),
                price       = COALESCE(EXCLUDED.price, normalized_listings.price),
                fuel_type   = COALESCE(EXCLUDED.fuel_type, normalized_listings.fuel_type)
        RETURNING id
    """), {
        "raw_id":      raw_id,
        "model_id":    model_id,
        "brand":       resolved_brand,
        "model":       resolved_model,
        "seller_type": detail.get("seller_type"),
        "desc":        detail.get("description", ""),
        "photos":      detail.get("photo_count", 0),
        "year":        year,
        "km":          km,
        "price":       price,
        "fuel_type":   fuel_type,
    }).scalar()
    db.commit()

    from app.scrapers.normalizer import _compute_km_per_year
    km_per_year = _compute_km_per_year(km, year)

    # ── Record price observation (market intelligence flywheel) ──
    # Every analysis from any source feeds the collective pricing data.
    _quality_score = (_data_quality or {}).get("score") if _data_quality else None
    _record_price_observation(
        db,
        model_id=model_id,
        generation_id=None,  # resolved later during aggregation
        year=year,
        km=km,
        price=price,
        fuel_type=fuel_type,
        seller_type=detail.get("seller_type", "desconhecido"),
        source_url=listing_url,
        source=source,
        extraction_method=_extraction_method,
        data_quality_score=_quality_score,
        observation_type="user_analysis",
    )

    # ── Append immutable snapshot (price-history + relisting/rollback moat) ──
    # Append-only: never overwrites. Starts accumulating the day this ships.
    _record_listing_snapshot(
        db,
        normalized_listing_id=norm_id,
        model_id=model_id,
        brand_name=resolved_brand,
        model_name=resolved_model,
        year=year,
        km=km,
        price=price,
        fuel_type=fuel_type,
        seller_type=detail.get("seller_type", "desconhecido"),
        photo_count=detail.get("photo_count", 0),
        source_url=listing_url,
        description=detail.get("description", ""),
    )

    return {
        "id":            norm_id,
        "raw_listing_id": raw_id,
        "model_id":      model_id,
        "brand_name":    resolved_brand,
        "model_name":    resolved_model,
        "year":          year,
        "km":            km,
        "price":         price,
        "fuel_type":     fuel_type,
        "km_per_year":   km_per_year,
        "price_delta":   0.0,
        "deal_tier":     "razoavel",
        "deal_score":    0.5,
        "seller_type":   detail.get("seller_type"),
        "description":   detail.get("description", ""),
        "photo_count":   detail.get("photo_count", 0),
        "listing_age_days": detail.get("listing_age_days"),
        "engine_power_hp":  detail.get("engine_power_hp"),
        "transmission":     detail.get("transmission"),
        "colour":           detail.get("colour"),
        "version":              detail.get("version"),
        "engine_displacement_cc": detail.get("engine_displacement_cc"),
        "sv_model_slug":        detail.get("sv_model_slug"),
        "source_title":         source_title,
        "source_model_name":    source_model_name,
        "source_url":    listing_url,
        "source":        source,
        "_js_limited":   _js_limited,
        "_pw_debug":     _pw_debug,
        "_extraction_method": _extraction_method,
        "_data_quality":      _data_quality,
        "_data_warnings":     _data_warnings,
    }


# A stored listing is fetched again within this long; past it the analysis goes
# ahead on the stored row instead of failing on the pipeline's overall limit.
_REFETCH_TIMEOUT_SECONDS = 30
# What the stored row lends a re-fetch that missed it: the same fields the row's
# own update keeps (COALESCE), and the engine facts of its last analysis.
_REFETCH_KEEP_KEYS = ("year", "km") + _LISTING_ENGINE_KEYS


async def _refetch_stored_listing(db: Session, listing_url: str, stored: dict) -> dict:
    """A listing already in the DB whose analysis is stale or missing: fetched
    again, so the analysis is of the listing as it is now — its price today, or
    the fact that it is gone — and the price history gains an observation.

    The stored row used to be analysed as it was, so a car reduced or sold
    since was judged on the price first seen. It is now only the fallback:
    when the fetch fails, times out or brings no price, the stored row is
    returned (and was not written to). A field the fetch missed that the row
    has (year, km, fuel, engine facts) is taken from the row."""
    fresh = None
    try:
        fresh = await asyncio.wait_for(
            _scrape_and_store_listing(db, listing_url, refetch=True),
            timeout=_REFETCH_TIMEOUT_SECONDS,
        )
    except Exception as e:  # incl. the timeout; never worse than the read-back
        print(f"[AD_ANALYSIS] Re-fetch of {listing_url} failed ({type(e).__name__}: {e}) — stored listing kept")
        try:
            db.rollback()
        except Exception:
            pass
    if not fresh:
        return stored
    if fresh.get("_gone"):
        return fresh
    for key in _REFETCH_KEEP_KEYS:
        if fresh.get(key) is None and stored.get(key) is not None:
            fresh[key] = stored[key]
    if stored.get("price") and fresh.get("price") != stored.get("price"):
        print(f"[AD_ANALYSIS] Stored listing re-fetched: price {stored.get('price')} -> {fresh.get('price')}")
    return fresh


def _store_analysis(db: Session, normalized_id: int, llm_result: dict, deal_tier: str, deal_score: float) -> None:
    """Persist LLM analysis and deal tier back to DB."""
    db.execute(text("""
        UPDATE normalized_listings
        SET llm_analysis = :analysis,
            analysis_cached_at = NOW(),
            deal_tier = :tier,
            deal_score = :score
        WHERE id = :id
    """), {
        "analysis": json.dumps(llm_result),
        "tier": llm_result.get("verdict", deal_tier),
        "score": deal_score,
        "id": normalized_id,
    })
    db.commit()


# ── Main public function ───────────────────────────────────────────────────

async def analyse_listing(
    db: Session,
    listing_url: str,
    user_profile: Optional[dict] = None,
    force_refresh: bool = False,
    pasted_text: Optional[str] = None,
) -> dict:
    """
    Full ad analysis pipeline for a listing URL:
    1. Check DB cache (return if fresh) — skipped when force_refresh=True
    2. Fetch detail page if not in DB
    3. Run deal scoring
    4. Call Gemini for analysis (falls back to rule engine)
    5. Call Gemini again for narrative enrichment (extras, negotiation, verdict narrative)
    6. Cache result in DB
    7. Return structured analysis

    Always returns a dict safe to send to the frontend.
    """
    try:
        return await asyncio.wait_for(
            _analyse_listing_inner(db, listing_url, user_profile, force_refresh, pasted_text),
            timeout=90,  # hard cap: entire pipeline must finish in 90s
        )
    except asyncio.TimeoutError:
        print(f"[AD_ANALYSIS] Global timeout (90s) for {listing_url}")
        return {
            "error": "A análise demorou demasiado. Tente novamente — pode ser uma questão temporária.",
        }
    except Exception as e:
        print(f"[AD_ANALYSIS] Unhandled error analysing {listing_url}: {e}")
        import traceback
        traceback.print_exc()
        return {
            "error": "Ocorreu um erro ao analisar este anúncio. Tente novamente em breve.",
            "_debug_error": str(e),
        }


async def _analyse_listing_inner(
    db: Session,
    listing_url: str,
    user_profile: Optional[dict] = None,
    force_refresh: bool = False,
    pasted_text: Optional[str] = None,
) -> dict:
    """Inner implementation — caller wraps in try/except."""
    if pasted_text:
        force_refresh = True       # the buyer's text is newer than anything stored
    # ── 0. Validate source URL ──
    if not is_supported_url(listing_url):
        return {
            "error": "URL inválido. Cole um link direto de um anúncio (Standvirtual, OLX, ou qualquer site de dealer)."
        }

    # ── 1. Check cache (skip on force_refresh) ──
    cached = None if force_refresh else _get_cached_analysis(db, listing_url)
    if force_refresh:
        print(f"[AD_ANALYSIS] force_refresh=True — skipping cache for {listing_url}")
    if cached and cached.get("llm_analysis"):
        llm = cached["llm_analysis"] if isinstance(cached["llm_analysis"], dict) else json.loads(cached["llm_analysis"])
        # Re-hydrate enrichment from cached llm blob (stored there since v4.4.1)
        cached_enrichment = {
            "extras_analysis":      llm.get("extras_analysis"),
            "negotiation_script":   llm.get("negotiation_script"),
            "verdict_narrative":    llm.get("verdict_narrative"),
            "seller_read":          llm.get("seller_read"),
            "inspection_checklist": llm.get("inspection_checklist", []),
            "negotiation_tips":     llm.get("negotiation_tips", []),
        }
        # Re-fetch model_info for reliability / maintenance (cheap DB query)
        cached_model_info: dict = {}
        brand_n = cached.get("brand_name", "")
        model_n = cached.get("model_name", "")
        if brand_n and model_n:
            cached_model_info = _get_model_info(db, brand_n, model_n, year=cached.get("year"),
                                                fuel=cached.get("fuel_type")) or {}
        # Pull market stats from DB (no live scrape on cache hit)
        cached_market: dict = {}
        cached_model_id = cached_model_info.get("id") if cached_model_info else None
        if cached_model_id and cached.get("year"):
            cached_market = _get_market_stats(db, cached_model_id, cached.get("year")) or {}
        cached_market = _cached_market_for(cached_market, llm)
        if not cached.get("source_url"):
            cached["source_url"] = listing_url
        cached_dealbreakers = known_issue_dealbreakers_for_cached(cached_model_info, cached, llm)
        return _build_response(
            cached, llm, from_cache=True,
            enrichment=cached_enrichment or None,
            model_info=cached_model_info or None,
            market_stats=cached_market or None,
            analysis_id=cached.get("id"),
            price_history=_build_price_history(db, cached),
            dealbreakers=cached_dealbreakers,
        )

    # ── 2. Resolve or scrape listing ──
    if force_refresh:
        # Always re-scrape on force_refresh (bypasses stale cached scrape data)
        normalized = await _scrape_and_store_listing(db, listing_url, pasted_text=pasted_text)
    else:
        # Reached only without a fresh cached analysis. A listing seen before
        # is fetched again rather than analysed on what was first scraped.
        stored = _resolve_model_from_url(db, listing_url)
        if stored:
            normalized = await _refetch_stored_listing(db, listing_url, stored)
        else:
            normalized = await _scrape_and_store_listing(db, listing_url)

    if normalized and normalized.get("_gone"):
        return {"error": "Este anúncio já não está disponível — foi vendido ou removido do site."}

    if not normalized:
        return {"error": "Não foi possível obter o anúncio. Verifique o URL e tente novamente.",
                "error_code": "fetch_failed"}

    # No price means the page was not read (blocked, behind a login, or built
    # by scripts we could not run): an analysis without it has no verdict to
    # give. The buyer is offered to paste the ad's text instead.
    if not normalized.get("price"):
        if pasted_text:
            return {"error": "Não encontrámos o preço no texto colado. Copia a página inteira do anúncio "
                             "(Ctrl+A, Ctrl+C) e cola outra vez.",
                    "error_code": "paste_incomplete"}
        return {"error": "Não conseguimos ler este anúncio no site.",
                "error_code": "fetch_failed"}

    # ── 3. Fetch market stats ──
    model_id   = normalized.get("model_id")
    brand_name = normalized.get("brand_name", "")
    model_name = normalized.get("model_name", "")
    year       = normalized.get("year")
    model_info = {}

    # Live-first: scrape real prices via Playwright; fall back to seeded DB stats
    fuel_type   = normalized.get("fuel_type")
    description = normalized.get("description", "")
    engine_hint = _extract_engine_hint(description)

    # Resolve generation boundaries for like-for-like comparison
    gen_year_start: Optional[int] = None
    gen_year_end:   Optional[int] = None
    generation_id:  Optional[int] = None
    if model_id and year:
        gen_window = _get_generation_window(db, model_id, year, fuel_type)
        if gen_window:
            gen_year_start, gen_year_end, generation_id = gen_window
            print(f"[ANALYSIS] Generation window: {gen_year_start}–{gen_year_end or 'now'} "
                  f"(gen_id={generation_id}) for {brand_name} {model_name} ({year})")
        else:
            print(f"[ANALYSIS] No generation record for {brand_name} {model_name} {year} — using ±3 fallback")

    market_stats = {}
    if brand_name and model_name and not DISABLE_LIVE_MARKET:
        try:
            market_stats = await asyncio.wait_for(
                _fetch_live_market_data(
                    brand_name, model_name, year,
                    fuel_type=fuel_type,
                    engine_hint=engine_hint,
                    gen_year_start=gen_year_start,
                    gen_year_end=gen_year_end,
                    sv_model_slug=_market_model_slug(normalized, brand_name, model_name, listing_url),
                    trim=_market_trim(normalized, listing_url),
                    power_hp=normalized.get("engine_power_hp"),
                    variant_code=_sv_variant_code(listing_url),
                    km=normalized.get("km"),
                ),
                timeout=45,  # 45s hard cap — Playwright can't hang the whole app
            )
        except asyncio.TimeoutError:
            print(f"[ANALYSIS] Live market fetch timed out after 45s — falling back to DB")
        except Exception as e:
            print(f"[ANALYSIS] Live market fetch failed: {e}")
    elif DISABLE_LIVE_MARKET and brand_name:
        print(f"[ANALYSIS] Live market scrape disabled (DISABLE_LIVE_MARKET=true) — using DB only")

    # No live comparison (the marketplace did not answer, or timed out): the
    # same comparison on the listings the last market snapshot stored. The old
    # fallback, a stored row of the model and year whatever the fuel or engine,
    # is gone: it was not like-for-like. Live results are no longer written
    # back to market_price_stats either — that row is shared by every car of
    # the model and year, and one car's pool (its fuel, its power band)
    # overwrote it.
    if not market_stats.get("avg_price") and model_id:
        stored = _stored_market_data(
            db, model_id, brand_name, model_name, year,
            fuel_type=fuel_type,
            gen_year_start=gen_year_start,
            gen_year_end=gen_year_end,
            sv_model_slug=_market_model_slug(normalized, brand_name, model_name, listing_url),
            km=normalized.get("km"),
            trim=_market_trim(normalized, listing_url),
            power_hp=normalized.get("engine_power_hp"),
        )
        if stored:
            print(f"[ANALYSIS] Live comparison unavailable — using the stored snapshot "
                  f"({stored.get('sample_count')} listings, {stored.get('age_days')} days old)")
            market_stats = stored

    # Listings that are not comparable with this car in mileage or model year:
    # no price reference at all, rather than a wrong one.
    market_stats = _withhold_if_not_comparable(market_stats)

    if model_id:
        model_info = _get_model_info(db, brand_name, model_name, year=year, fuel=fuel_type)

    # Curated known engine/gearbox failures for THIS car (year + engine).
    # Matched on the listing itself, so it works even when the model isn't
    # in the catalogue.
    dealbreakers, known_matched = _known_issue_dealbreakers(model_info, normalized)

    # ── 3a. Compute deal metrics ──
    # Use the MEDIAN as the market reference, not the average. The average is
    # skewed by expensive trims/outliers (e.g. M-Sport variants), which made the
    # verdict say "atrativo" while the negotiation panel (median-based) showed the
    # car was actually at market. Median keeps both consistent.
    price = normalized.get("price")
    ref_price = market_stats.get("median_price") or market_stats.get("avg_price")
    avg_price = ref_price
    km_per_year = normalized.get("km_per_year") or _compute_km_per_year(normalized.get("km"), normalized.get("year"))

    # Only let the market drive the price verdict when the comparable pool is big
    # enough to trust. Off a handful of listings the median is noisy — a 2021
    # 116d was flagged "cuidado, 40% above" against just 3 comparables. When the
    # sample is thin we go price-neutral and lean on km/engine/condition instead.
    market_sample = market_stats.get("sample_count") or 0
    # Without the fuel the pool mixes every engine of the model: a 2020 3008
    # GT diesel from a dealer site came out "30% above market, evitar" against
    # all 3008s. Unknown fuel → no price verdict, like a thin pool.
    fuel_known = bool(normalize_fuel(normalized.get("fuel_type")))
    market_reliable = (bool(ref_price) and price and market_sample >= _MIN_RELIABLE_MARKET_SAMPLE
                       and fuel_known)

    if market_reliable:
        price_delta = _compute_price_delta(price, ref_price)
        deal_tier = _classify_deal_tier(price_delta, km_per_year, price, ref_price, normalized.get("seller_type", "desconhecido"))
        normalized["price_delta_pct"] = round(abs((ref_price - price) / ref_price * 100), 1)
    else:
        # Market too thin to judge price — neutral on price, km-based tier only.
        price_delta = 0.0
        deal_tier = _classify_deal_tier(0.0, km_per_year, price, None, normalized.get("seller_type", "desconhecido"))
        normalized["price_delta_pct"] = None

    deal_score = _compute_deal_score(price_delta, km_per_year)

    # Enrich listing with computed metrics
    normalized["km_per_year"] = km_per_year
    normalized["price_delta"] = price_delta
    normalized["deal_tier"] = deal_tier
    normalized["deal_score"] = deal_score
    normalized["_market_reliable"] = market_reliable

    # ── 4. Analysis (Gemini or rule engine fallback) ──
    # Single unified LLM call returns both analysis + enrichment fields.
    # This halves Gemini API calls (critical on free tier: 20/day limit).
    prompt_model_info = model_info
    if known_matched:
        note = _known_issues_prompt_note(known_matched)
        prompt_model_info = {**(model_info or {}),
                             "known_issues": f"{note}. {(model_info or {}).get('known_issues') or ''}".strip()}
    llm_result = await _analyse(normalized, prompt_model_info, market_stats, user_profile)

    # ── 4a. Profile fit (when user_profile provided and model_info available) ──
    fit_result = None
    if user_profile and model_info:
        fit_result = _compute_profile_fit(user_profile, model_info)

    # ── 4b. Enrichment: extract from unified LLM result, fall back to rules ──
    rule_inspection = _build_inspection_checklist(model_info or {}, normalized)
    rule_negotiation = _build_negotiation_tips(normalized, market_stats or {})

    enrichment = {
        "extras_analysis":      llm_result.get("extras_analysis"),
        "negotiation_script":   llm_result.get("negotiation_script"),
        "verdict_narrative":    llm_result.get("verdict_narrative"),
        "seller_read":          llm_result.get("seller_read"),
        "inspection_checklist": llm_result.get("inspection_checklist") or rule_inspection,
        "negotiation_tips":     llm_result.get("negotiation_tips") or rule_negotiation,
    }

    # ── 5. Cache ──
    norm_id = normalized.get("id")
    if norm_id:
        try:
            # Include enrichment in the cached blob so cache hits return full responses
            llm_result_to_cache = {
                **llm_result, **enrichment,
                "_listing_engine": {k: normalized.get(k) for k in _LISTING_ENGINE_KEYS},
                # The curated faults this analysis matched: a permalink rebuilt
                # later (with less to match on, e.g. an ad read from pasted
                # text) must still show them.
                "_known_issue_ids": [i["id"] for i in known_matched],
                "_market_ref": _market_ref_for_cache(market_stats),
            }
            _store_analysis(db, norm_id, llm_result_to_cache, deal_tier, deal_score)
        except Exception as e:
            print(f"[AD_ANALYSIS] Cache store error: {e}")

    # ── 6. Depreciation data ──
    depreciation_data = None
    if generation_id:
        try:
            from app.services.depreciation import get_depreciation_for_generation, estimate_future_value
            depreciation_data = get_depreciation_for_generation(db, generation_id)
            if depreciation_data and price:
                depreciation_data["future_value"] = estimate_future_value(
                    price, depreciation_data["annual_pct"], years=3
                )
        except Exception as e:
            print(f"[AD_ANALYSIS] Depreciation lookup error: {e}")

    price_history = _build_price_history(db, normalized)

    return _build_response(
        normalized, llm_result, from_cache=False, market_stats=market_stats,
        gen_year_start=gen_year_start, gen_year_end=gen_year_end,
        fit=fit_result, model_info=model_info, enrichment=enrichment,
        js_limited=normalized.get("_js_limited", False),
        pw_debug=normalized.get("_pw_debug"),
        depreciation=depreciation_data,
        analysis_id=normalized.get("id"),
        price_history=price_history,
        dealbreakers=dealbreakers,
    )


def _build_inspection_checklist(model_info: dict, listing: dict) -> list[str]:
    """
    Build a practical inspection checklist from known engine_issues and general km checks.
    """
    checklist = []

    # Known issues → inspection prompts
    known = model_info.get("known_issues") or ""
    if known:
        for issue in known.split(";")[:3]:
            issue = issue.strip()
            if issue and len(issue) > 5:
                checklist.append(f"Perguntar sobre: {issue[:90]}")

    # General high-km checks
    km = listing.get("km") or 0
    if km > 100000:
        checklist.append("Correia/corrente de distribuição — perguntar data da última substituição")
    if km > 150000:
        checklist.append("Embraiagem — testar deslizamento em aceleração")
    if km > 80000:
        checklist.append("Travões — verificar espessura dos discos e pastilhas")

    # Always included
    checklist.append("Histórico de serviços — pedir caderneta ou registos de manutenção")
    checklist.append("Teste em estrada — verificar vibrações, ruídos e travagem")

    return checklist[:7]  # cap at 7 items


def _build_negotiation_tips(listing: dict, market_stats: dict) -> list[str]:
    """
    Generate negotiation leverage points from price position, listing age, seller type.
    """
    tips = []
    price = listing.get("price") or 0
    avg_price = market_stats.get("avg_price") or 0
    price_delta = listing.get("price_delta", 0.0) or 0.0
    listing_age = listing.get("listing_age_days") or 0
    seller_type = listing.get("seller_type", "desconhecido")
    km = listing.get("km") or 0

    # Price position leverage
    if avg_price and price:
        if price_delta < -0.05:  # car is above market
            pct_above = round(abs(price_delta) * 100)
            target = round(price * 0.93 / 500) * 500
            target_fmt = f"{target:,}".replace(",", ".")
            tips.append(
                f"Anda uns {pct_above}% acima de carros parecidos. Leva-lhe alguns anúncios semelhantes e atira um valor à volta dos {target_fmt}€ — com jeitinho costuma resultar."
            )
        elif price_delta > 0.05:  # car is below market — validate before paying
            tips.append(
                "Está abaixo da média do mercado, o que é bom sinal — mas confirma bem o estado antes de avançar, às vezes há um motivo."
            )

    # Listing age leverage
    if listing_age >= 30:
        tips.append(
            f"Já está à venda há {listing_age} dias. Quem espera há tanto tempo costuma estar mais aberto a baixar — usa isso a teu favor."
        )
    elif listing_age >= 14:
        tips.append(f"Está anunciado há {listing_age} dias, por isso há margem para pedir uns 3 a 5% de desconto sem ofender ninguém.")

    # Seller type
    if seller_type == "particular":
        tips.append(
            "É particular, por isso há mais espaço para negociar — mas lembra-te que não ficas com a garantia que terias num stand."
        )
    elif seller_type == "profissional":
        tips.append(
            "Sendo stand, a margem no preço é menor, mas tens garantia. Se não baixarem, tenta antes pedir extras: revisão feita, pneus, multimédia."
        )

    # High km leverage
    if km > 150000:
        tips.append(
            f"Com {km:,} km".replace(",", ".") + ", vale mesmo a pena uma inspeção independente antes de fechar. Se aparecer alguma coisa, é o teu argumento para baixar o preço."
        )
    elif km > 100000:
        tips.append(
            "Já passou dos 100 mil km — lembra-lhe com simpatia que vais ter manutenção pela frente, ajuda a justificar um valor mais baixo."
        )

    if not tips:
        tips.append("Antes de qualquer oferta, pede o histórico de revisões completo. Se faltar, é logo meio caminho andado para negociar.")

    return tips[:4]


def _build_negotiation_numbers(listing: dict, market_stats: dict) -> Optional[dict]:
    """
    Concrete negotiation figures the buyer can act on: opening offer, fair value,
    and walk-away ceiling — grounded in market data plus this listing's leverage
    (days on market, seller type, price position, mileage). The "weapon": three
    numbers instead of vague advice.

    Returns None when there isn't enough market data to give honest figures —
    we never invent a number we can't defend.
    """
    price = listing.get("price") or 0
    fair = market_stats.get("median_price") or market_stats.get("avg_price") or 0
    sample = market_stats.get("sample_count") or 0
    if not price or not fair or fair < 500:
        return None
    # Honesty gate: never put precise offer/walk-away numbers in front of the
    # buyer off a handful of comparables — a noisy median would mislead. Below
    # the threshold we show nothing rather than a wrong number.
    if sample and sample < _MIN_NEGOTIATION_SAMPLE:
        return None
    # Sanity gate: if the asking price is wildly off the market reference, we've
    # almost certainly matched the wrong comparison pool (a model not in our DB
    # mis-resolved to another) or the listing itself is anomalous (scam/typo).
    # Precise offer numbers ("fair €17k for a €39.5k car") would be absurd —
    # suppress them and let the verdict narrative explain.
    ratio = price / fair
    if ratio < 0.55 or ratio > 1.8:
        return None

    def _round50(x: float) -> int:
        return int(round(x / 50.0) * 50)

    listing_age = listing.get("listing_age_days") or 0
    seller_type = (listing.get("seller_type") or "").lower()
    km = listing.get("km") or 0
    year = listing.get("year")

    # Baseline ~3% off, scaled up by each leverage point we can defend out loud.
    margin = 0.03
    leverage: list[str] = []

    if listing_age >= 30:
        margin += 0.03
        leverage.append(f"Já está há {listing_age} dias à venda — quem espera tanto costuma estar mais aberto a baixar")
    elif listing_age >= 14:
        margin += 0.015
        leverage.append(f"Anunciado há {listing_age} dias, há espaço para negociar")

    if "particular" in seller_type:
        margin += 0.01
        leverage.append("É particular: mais margem para negociar (mas sem garantia)")
    elif "profiss" in seller_type or "stand" in seller_type:
        margin -= 0.005  # less wiggle, but legal warranty

    if price > fair * 1.05:
        pct = round((price - fair) / fair * 100)
        margin += 0.02
        leverage.append(f"Está uns {pct}% acima de carros parecidos — mostra-lhe os comparáveis")
    elif price < fair * 0.95:
        pct = round((fair - price) / fair * 100)
        leverage.append(f"Está uns {pct}% abaixo da média — já é bom preço, confirma o estado")

    if year:
        try:
            age_years = max(1, datetime.now().year - int(year))
            if km and km > age_years * 15000 * 1.2:
                margin += 0.015
                leverage.append("Tem mais km do que a média para o ano")
        except (ValueError, TypeError):
            pass

    margin = max(0.0, min(margin, 0.12))  # never claim more than 12% headroom

    fair_value = _round50(fair)
    anchor = min(price, fair)                       # don't anchor above market
    opening_offer = _round50(anchor * (1 - margin))
    walk_away = _round50(fair)                       # don't pay above market for a normal car
    if opening_offer >= walk_away:
        opening_offer = _round50(walk_away * 0.95)

    potential_saving = max(0, price - opening_offer)

    if sample >= 20:
        confidence = "alta"
    elif sample >= 8:
        confidence = "media"
    else:
        confidence = "baixa"

    return {
        "asking_price":     int(price),
        "opening_offer":    opening_offer,
        "fair_value":       fair_value,
        "walk_away":        walk_away,
        "potential_saving": potential_saving,
        "leverage":         leverage[:4],
        "confidence":       confidence,
        "sample_count":     int(sample),
    }


# ── Cost of ownership (custo de utilização) ──────────────────────────────────
# Portuguese fuel prices (€/L) and electricity (€/kWh) — update periodically.
_FUEL_PRICE_EUR = {"diesel": 1.60, "gasolina": 1.75, "gpl": 0.95}
_ELEC_PRICE_EUR_KWH = 0.22
_DEFAULT_KM_YEAR = 15000

# Typical consumption (l/100km, or kWh/100km for electric) by fuel + displacement band.
def _estimate_consumption(fuel: str, displacement_l: Optional[float], power_hp: Optional[int]) -> tuple[float, str]:
    """Return (consumption_per_100, unit) where unit is 'l' or 'kwh'."""
    f = (fuel or "").lower()
    disp = displacement_l or 0.0
    if "elétr" in f or "eletr" in f or "electric" in f:
        return (16.5, "kwh")  # ~16.5 kWh/100km typical EV
    if "híbr" in f or "hibr" in f or "hybrid" in f:
        return (5.0, "l")
    if "diesel" in f or "gasóleo" in f or "gasoleo" in f:
        base = 4.8 if disp <= 1.6 else (5.6 if disp <= 2.0 else 7.0)
        return (base, "l")
    # petrol / gpl / unknown → treat as petrol
    base = 6.0 if disp <= 1.4 else (7.2 if disp <= 2.0 else 9.5)
    if power_hp and power_hp > 200:
        base += 1.5
    return (base, "l")


def _estimate_iuc(displacement_cc: Optional[int], fuel: str, year: Optional[int]) -> Optional[int]:
    """
    Rough annual IUC (road tax) estimate for a Portuguese passenger car.
    Post-2007 vehicles (Cat. B): cilindrada component + a CO2 component we
    approximate from displacement + fuel. Diesel carries a surcharge.
    This is an ESTIMATE — exact IUC needs the registration CO2 value.
    """
    if not displacement_cc or displacement_cc < 600:
        return None
    cc = displacement_cc
    # Cilindrada component (approx. 2024 Cat. B brackets)
    if cc <= 1250:
        cilindrada = 30
    elif cc <= 1750:
        cilindrada = 60
    elif cc <= 2500:
        cilindrada = 118
    else:
        cilindrada = 400
    # CO2 component — estimate CO2 from displacement + fuel, map to bracket
    f = (fuel or "").lower()
    if "elétr" in f or "eletr" in f or "electric" in f:
        return 0  # EVs are IUC-exempt / nominal
    co2_est = (cc / 1000.0) * (62 if "diesel" in f or "gasóleo" in f or "gasoleo" in f else 75) + 40
    if co2_est <= 120:
        co2 = 60
    elif co2_est <= 140:
        co2 = 100
    elif co2_est <= 160:
        co2 = 150
    elif co2_est <= 180:
        co2 = 230
    else:
        co2 = 320
    total = cilindrada + co2
    # Diesel surcharge (adicional de gasóleo)
    if "diesel" in f or "gasóleo" in f or "gasoleo" in f:
        total = int(total * 1.20)
    return int(round(total / 5.0) * 5)


def _build_anomaly(listing: dict, market_stats: dict, data_warnings: Optional[list]) -> Optional[dict]:
    """
    Turn price/data anomalies into an explicit, user-facing warning — the kind of
    'too good to be true' / scam protection a buyer most wants. Returns the most
    severe signal found, or None.
    """
    price = listing.get("price") or 0
    fair = (market_stats or {}).get("median_price") or (market_stats or {}).get("avg_price") or 0
    warnings = data_warnings or []

    # Hard danger: placeholder/impossible prices flagged during validation.
    for w in warnings:
        if w.startswith("new_car_too_cheap") or w.startswith("suspicious_price_pattern"):
            return {
                "level": "danger",
                "title": "Preço improvável",
                "message": "O preço pedido é improvável para este carro. Desconfia — "
                           "pode ser um erro, um esquema, ou esconder um problema grave. "
                           "Vê o carro pessoalmente e nunca transfiras dinheiro nem sinal "
                           "antes de confirmar tudo.",
            }

    if price and fair and fair > 0:
        ratio = price / fair
        if ratio < 0.55:
            return {
                "level": "danger",
                "title": "Preço muito abaixo do normal",
                "message": f"Está bem abaixo do que carros semelhantes valem (~{int(fair):,}€). "
                           "Pode ser uma oportunidade real, mas é também o padrão típico de "
                           "fraudes e carros com problemas escondidos. Confirma o estado e a "
                           "documentação em pessoa — nunca pagues sinal antes disso.",
            }
        if ratio < 0.68:
            return {
                "level": "warning",
                "title": "Preço abaixo do mercado",
                "message": "Está abaixo da média do mercado. Pode ser bom negócio — confirma "
                           "o estado real, a documentação e o histórico de manutenção antes de avançar.",
            }

    for w in warnings:
        if w.startswith("km_vs_year_mismatch"):
            return {
                "level": "warning",
                "title": "Quilometragem invulgar",
                "message": "A quilometragem não encaixa bem com o ano do carro. Confirma com o "
                           "vendedor e verifica o histórico — pode ser erro no anúncio ou "
                           "manipulação do conta-quilómetros.",
            }

    return None


def _build_cost_of_ownership(
    listing: dict,
    model_info: Optional[dict],
    depreciation: Optional[dict],
    engine_hint: Optional[str],
) -> Optional[dict]:
    """
    Estimate the monthly cost of running this car: fuel + IUC + maintenance,
    plus depreciation as the bigger-picture "true" monthly cost when available.
    Insurance is deliberately excluded — it varies too much by driver to estimate
    honestly. Every figure is an estimate with stated assumptions.
    """
    fuel = (listing.get("fuel_type") or "").lower()
    price = listing.get("price") or 0
    year = listing.get("year")
    power_hp = listing.get("engine_power_hp")
    try:
        power_hp = int(power_hp) if power_hp else None
    except (ValueError, TypeError):
        power_hp = None

    # Displacement — prefer the exact value extracted from the listing
    # (SV's engine_capacity, e.g. 1999cc); else parse the engine hint "2.0 TDI".
    displacement_cc = listing.get("engine_displacement_cc")
    if not displacement_cc and engine_hint:
        m = re.match(r"([1-9]\.[0-9])", engine_hint.strip())
        if m:
            displacement_cc = int(float(m.group(1)) * 1000)
    displacement_l = (displacement_cc / 1000.0) if displacement_cc else None

    # ── Fuel cost / year ──
    cons, unit = _estimate_consumption(fuel, displacement_l, power_hp)
    if unit == "kwh":
        price_per_unit = _ELEC_PRICE_EUR_KWH
    else:
        if "diesel" in fuel or "gasóleo" in fuel or "gasoleo" in fuel:
            price_per_unit = _FUEL_PRICE_EUR["diesel"]
        elif "gpl" in fuel:
            price_per_unit = _FUEL_PRICE_EUR["gpl"]
        else:
            price_per_unit = _FUEL_PRICE_EUR["gasolina"]
    annual_fuel = int(round((cons / 100.0) * _DEFAULT_KM_YEAR * price_per_unit))

    # ── IUC / year ──
    annual_iuc = _estimate_iuc(displacement_cc, fuel, year)

    # ── Maintenance / year (from model data when available) ──
    annual_maint = None
    if model_info and model_info.get("maintenance_cost_year"):
        try:
            annual_maint = int(round(float(model_info["maintenance_cost_year"])))
        except (ValueError, TypeError):
            annual_maint = None

    running_components = [c for c in (annual_fuel, annual_iuc, annual_maint) if c]
    if not running_components:
        return None
    monthly_running = int(round(sum(running_components) / 12.0))

    # ── Depreciation / month (the biggest real cost) when we have a curve ──
    depreciation_monthly = None
    if depreciation and price and depreciation.get("annual_pct"):
        try:
            annual_dep = price * float(depreciation["annual_pct"])
            depreciation_monthly = int(round(annual_dep / 12.0))
        except (ValueError, TypeError):
            depreciation_monthly = None

    monthly_true = monthly_running + (depreciation_monthly or 0)

    return {
        "monthly_running":      monthly_running,
        "monthly_true":         monthly_true if depreciation_monthly else None,
        "annual_fuel":          annual_fuel,
        "annual_iuc":           annual_iuc,
        "annual_maintenance":   annual_maint,
        "depreciation_monthly": depreciation_monthly,
        "assumptions": {
            "km_year":          _DEFAULT_KM_YEAR,
            "consumption":      round(cons, 1),
            "consumption_unit": unit,
            "fuel_price":       price_per_unit,
        },
    }


def _price_position(listing: dict, market_stats: Optional[dict]) -> dict:
    """price_delta and price_delta_pct of a listing against a market
    reference, by the rule of a fresh analysis: the median (else the average),
    and only when the comparable sample is big enough to trust. {} when no
    position can be given."""
    stats = market_stats or {}
    price = listing.get("price")
    ref = stats.get("median_price") or stats.get("avg_price")
    if not (price and ref and (stats.get("sample_count") or 0) >= _MIN_RELIABLE_MARKET_SAMPLE):
        return {}
    return {"price_delta": _compute_price_delta(price, ref),
            "price_delta_pct": round(abs((ref - price) / ref * 100), 1)}


def _safe_plan(listing: dict, numbers, dealbreakers, price_history):
    """The negotiation plan; a failure here never breaks an analysis."""
    try:
        from app.services.negotiation import build_plan
        return build_plan(listing, numbers, dealbreakers, price_history)
    except Exception as e:
        print(f"[NEGOTIATION] plan failed: {e}")
        return None


def _build_response(
    listing: dict,
    llm: dict,
    from_cache: bool = False,
    market_stats: Optional[dict] = None,
    gen_year_start: Optional[int] = None,
    gen_year_end: Optional[int] = None,
    fit: Optional[dict] = None,
    model_info: Optional[dict] = None,
    enrichment: Optional[dict] = None,
    js_limited: bool = False,
    pw_debug: Optional[str] = None,
    depreciation: Optional[dict] = None,
    analysis_id: Optional[int] = None,
    price_history: Optional[dict] = None,
    dealbreakers: Optional[dict] = None,
) -> dict:
    """Build the final response dict sent to the frontend."""
    # A cached or shared analysis is read back from the listing row, which does
    # not keep the price position: it was computed only for a fresh analysis,
    # so every shared link lost its "vs mercado" figure.
    if listing.get("price_delta_pct") is None:
        listing = {**listing, **_price_position(listing, market_stats)}
    km_per_year = listing.get("km_per_year")
    price_delta = listing.get("price_delta", 0.0) or 0.0

    return {
        "analysis_id": analysis_id,
        "from_cache": from_cache,
        "source": listing.get("source") or detect_source(listing.get("source_url", "")) or "generic",
        "source_label": source_label(listing.get("source") or detect_source(listing.get("source_url", "")) or "generic"),
        "source_domain": listing.get("source_domain", ""),
        "source_url": listing.get("source_url", ""),
        "listing": {
            "brand_name": listing.get("brand_name"),
            "model_name": listing.get("model_name"),
            "year": listing.get("year"),
            "km": listing.get("km"),
            "price": listing.get("price"),
            "seller_type": listing.get("seller_type"),
            "photo_count": listing.get("photo_count"),
            "listing_age_days": listing.get("listing_age_days"),
        },
        "deal": {
            "tier": llm.get("verdict", listing.get("deal_tier", "razoavel")),
            "score": listing.get("deal_score", 0.5),
            "price_delta": price_delta,
            "price_delta_pct": listing.get("price_delta_pct"),
            "km_per_year": km_per_year,
            "market_avg_price": (market_stats or {}).get("avg_price"),
            "market_median_price": (market_stats or {}).get("median_price"),
            "market_sample_count": (market_stats or {}).get("sample_count"),
            "market_data_source": (market_stats or {}).get("source", "none"),
            "market_data_age_days": (market_stats or {}).get("age_days"),
            "market_data_stale": (market_stats or {}).get("stale", False),
            "market_fuel_type": listing.get("fuel_type"),
            # What the mileage step compared (see _select_km_comparables); None
            # when mileage was not taken into account, or was handled by the
            # year-and-km adjustment below.
            "market_km_comparison": (market_stats or {}).get("km_comparison"),
            # How the model-year mix was handled (see _adjust_pool_to_car and
            # _select_year_comparables); None when the year was not looked at.
            "market_year_comparison": (market_stats or {}).get("year_comparison"),
            # The engine-power band the comparables lie in (see _POWER_BAND);
            # None when the car's power is not known.
            "market_power_comparison": (market_stats or {}).get("power_comparison"),
            "generation_year_start": gen_year_start,
            "generation_year_end": gen_year_end,
        },
        "analysis": {
            "verdict": llm.get("verdict", "razoavel"),
            "verdict_reason": llm.get("verdict_reason", ""),
            "green_flags": llm.get("green_flags", []),
            "red_flags": llm.get("red_flags", []),
            "seller_analysis": llm.get("seller_analysis", ""),
            "profile_fit": llm.get("profile_fit", ""),
            "trim_level": llm.get("trim_level") or listing.get("version"),
            "spec_tier": llm.get("spec_tier", "base"),
            "trim_includes": llm.get("trim_includes", []),
            "optional_extras": llm.get("optional_extras", []),
            "equipment_note": llm.get("equipment_note"),
            "key_extras": llm.get("key_extras", []),
            "spec_value_assessment": llm.get("spec_value_assessment", "adequado"),
            "engine_code": llm.get("engine_code"),
            "engine_analysis": llm.get("engine_analysis"),
            # LLM narrative enrichment (None when Gemini unavailable)
            "extras_analysis":    (enrichment or {}).get("extras_analysis"),
            "negotiation_script": (enrichment or {}).get("negotiation_script"),
            "verdict_narrative":  (enrichment or {}).get("verdict_narrative"),
            "seller_read":        (enrichment or {}).get("seller_read"),
        },
        "inspection_checklist": (enrichment or {}).get("inspection_checklist", []),
        "negotiation_tips":     (enrichment or {}).get("negotiation_tips", []),
        "negotiation":          (_numbers := _build_negotiation_numbers(listing, market_stats or {})),
        "negotiation_plan":     _safe_plan(listing, _numbers, dealbreakers, price_history),
        "anomaly":              _build_anomaly(listing, market_stats or {}, listing.get("_data_warnings")),
        "price_history":        price_history,
        "cost_of_ownership":    _build_cost_of_ownership(
                                    listing, model_info, depreciation,
                                    _extract_engine_hint(listing.get("description") or ""),
                                ),
        "maintenance_estimate": (model_info or {}).get("maintenance_cost_year"),
        "caveat": (
            "Este site usa JavaScript — só conseguimos extrair dados parciais. "
            "Para uma análise completa, usa um link do Standvirtual, OLX ou CustoJusto."
            if js_limited else
            "Análise baseada na descrição do anúncio — o vendedor pode não ter listado todo o equipamento."
        ),
        "js_limited": js_limited,
        "_analysis_engine": llm.get("_analysis_engine"),
        "_llm_error": llm.get("_llm_error"),
        "_extraction_method": listing.get("_extraction_method"),
        "_data_quality": listing.get("_data_quality"),
        "_data_warnings": listing.get("_data_warnings") or [],
        "fit": fit,
        "reliability": {
            "score":        (model_info or {}).get("bayesian_reliability_score"),
            "ci_low":       (model_info or {}).get("bayesian_reliability_ci_low"),
            "ci_high":      (model_info or {}).get("bayesian_reliability_ci_high"),
            "data_quality": (model_info or {}).get("bayesian_reliability_quality"),
        } if model_info and model_info.get("bayesian_reliability_score") else None,
        "dealbreakers": dealbreakers if dealbreakers is not None else (model_info or {}).get("dealbreakers"),
        "depreciation": depreciation,
    }


# ── Market refresh ──────────────────────────────────────────────────────────

async def refresh_all_market_data(db: Session) -> dict:
    """
    Iterates all known vehicle models, scrapes live prices via Playwright,
    and upserts results into market_price_stats.
    Safe to call manually (admin endpoint) or from the background scheduler.
    """
    rows = db.execute(
        text("SELECT id, brand_name, model_name FROM vehicle_models ORDER BY brand_name, model_name")
    ).fetchall()

    updated, skipped = 0, 0
    for row in rows:
        model_id, brand_name, model_name = row.id, row.brand_name, row.model_name
        try:
            stats = await _fetch_live_market_data(brand_name, model_name, year=None)
            if stats.get("avg_price"):
                db.execute(
                    text("""
                        INSERT INTO market_price_stats
                            (model_id, year, avg_price, min_price, max_price, sample_count, source, updated_at)
                        VALUES
                            (:model_id, NULL, :avg, :mn, :mx, :cnt, 'live_scraped', NOW())
                        ON CONFLICT (model_id, year) DO UPDATE SET
                            avg_price    = EXCLUDED.avg_price,
                            min_price    = EXCLUDED.min_price,
                            max_price    = EXCLUDED.max_price,
                            sample_count = EXCLUDED.sample_count,
                            source       = 'live_scraped',
                            updated_at   = NOW()
                    """),
                    {
                        "model_id": model_id,
                        "avg": stats["avg_price"],
                        "mn":  stats.get("min_price"),
                        "mx":  stats.get("max_price"),
                        "cnt": stats.get("sample_count", 0),
                    },
                )
                db.commit()
                updated += 1
            else:
                skipped += 1
        except Exception as e:
            print(f"[REFRESH] Failed {brand_name} {model_name}: {e}")
            db.rollback()
            skipped += 1
        await asyncio.sleep(2)  # polite delay between models

    print(f"[REFRESH] Complete — updated: {updated}, skipped: {skipped}")
    return {"updated": updated, "skipped": skipped, "total": len(rows)}
