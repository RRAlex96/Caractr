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
import json
import asyncio
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
from app.scrapers.normalizer import (
    _compute_price_delta,
    _compute_km_per_year,
    _classify_deal_tier,
    _compute_deal_score,
)

import time

# In-memory market data cache: key → {stats, cached_at}
# Keyed by "{brand}_{model_first_word}" — refreshed every 6h
_market_cache: dict = {}
_MARKET_CACHE_TTL = 6 * 3600  # 6 hours
_MAX_MARKET_CACHE_KEYS = 500  # evict oldest entries if cache grows beyond this

USE_RULE_ANALYSIS = os.getenv("USE_RULE_ANALYSIS", "false").lower() == "true"
DISABLE_LIVE_MARKET = os.getenv("DISABLE_LIVE_MARKET", "true").lower() == "true"  # Playwright OOMs on Railway
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
    km_note = f"{km_per_year:.0f} km/ano" if km_per_year else "desconhecido"

    known_issues = model_info.get("known_issues", "Sem problemas conhecidos registados.")

    fuel_type = listing.get('fuel_type', '')
    engine_hp = listing.get('engine_power_hp', '')
    colour = listing.get('colour', '')
    transmission = listing.get('transmission', '')

    listing_age = listing.get("listing_age_days")
    listing_age_str = f"{listing_age} dias" if listing_age else "desconhecido"
    maintenance = model_info.get("maintenance_cost_year")
    maintenance_str = f"~€{int(maintenance):,}/ano" if maintenance else "N/D"
    avg_price = market_stats.get('avg_price', 0) or 0
    price = listing.get('price', 0) or 0
    price_delta_pct = listing.get('price_delta_pct', '?')
    price_pos = 'abaixo' if (listing.get('price_delta', 0) or 0) > 0 else 'acima'

    return f"""És um consultor especialista em carros usados em Portugal com 20 anos de experiência. Conheces TODOS os modelos, gerações, motores, versões e problemas típicos. Fala em PT-PT. Tom direto e honesto como um amigo que percebe muito de carros. Responde APENAS com JSON válido, sem texto extra.

O teu trabalho: analisar este anúncio como se o comprador te estivesse a pagar para o aconselhar. Sê ESPECÍFICO — nunca genérico.

ANÚNCIO:
Modelo: {listing.get('brand_name', '')} {listing.get('model_name', '')}
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
Preço médio de mercado: €{int(avg_price):,} | Este carro está {price_delta_pct}% {price_pos} do mercado
Custo manutenção estimado: {maintenance_str}
Problemas conhecidos do modelo: {known_issues}
{profile_note}

INSTRUÇÕES IMPORTANTES:
1. IDENTIFICA O MOTOR EXATO: com base na cilindrada, potência e combustível, identifica o código do motor (ex: "Motor N47D20 no BMW", "Motor K9K no Renault", "OM651 no Mercedes"). Isto é crítico para os problemas conhecidos.
2. IDENTIFICA A VERSÃO/TRIM: Avantgarde, Comfort, Sport, R-Line, GT-Line, etc. Cada versão tem equipamento diferente — não os mistures.
3. ANALISA OS EXTRAS DA DESCRIÇÃO: Lê cuidadosamente a descrição e extrai TODOS os extras mencionados. Cada extra tem impacto no valor.
4. AVALIA O PREÇO COM BASE NOS EXTRAS: Um carro "base" e um "full extras" do mesmo modelo podem ter €3-5k de diferença. Reflecte isso no veredicto.

Responde APENAS com este JSON (sem texto extra, sem markdown):
{{
  "verdict": "forte|razoavel|cuidado|evitar",
  "verdict_reason": "Uma frase em português, máximo 20 palavras. Sê ESPECÍFICO — referencia o motor, extras ou km.",
  "green_flags": ["MÁXIMO 4. Cada flag deve ser específica a ESTE carro. Ex: 'Motor 2.0 TDI CR (150cv) — um dos mais fiáveis do grupo VAG'. NUNCA ponhas flags genéricas como 'Bom preço'."],
  "red_flags": ["MÁXIMO 4. Cada flag deve ser específica. Ex: 'Motor N47 com >150k km — corrente de distribuição traseira, verificar urgentemente'. NUNCA flags genéricas."],
  "seller_analysis": "2-3 frases: o que a descrição REVELA sobre o vendedor. Profissional ou particular? O que omite? O tom é confiante ou vago? Há sinais de urgência na venda?",
  "profile_fit": "Como este anúncio específico se adequa ao perfil do comprador (1-2 frases)",
  "trim_level": "Nome exato da versão/trim detectado (ex: 'Avantgarde', 'R-Line', 'GT-Line') ou null se não identificável",
  "spec_tier": "base|medio|alto — baseado nos extras reais detectados na descrição",
  "key_extras": ["Lista TODOS os extras mencionados na descrição. Ex: 'Bancos em pele', 'Teto panorâmico', 'Navegação', 'Câmara traseira', 'Jantes 19', 'Sensores estacionamento', 'LED'. Máximo 12."],
  "spec_value_assessment": "acima_do_esperado|adequado|abaixo_do_esperado — considerando os extras para esta versão e preço",
  "engine_code": "Código do motor se identificável (ex: 'EA888', 'N47D20', 'K9K 636', 'OM651') ou null",
  "engine_analysis": "1-2 frases sobre ESTE motor específico: fiabilidade conhecida, pontos fracos, o que verificar. Ex: 'O EA888 Gen3 é sólido mas consome óleo — verificar nível entre revisões. Correia aos 210k km.'",
  "extras_analysis": "2-3 frases: que extras tem, o que valem no mercado, e o que FALTA em relação ao esperado para esta versão.",
  "negotiation_script": "Script CONCRETO de negociação: valor de primeira oferta, argumentos específicos baseados nos dados (km, tempo no mercado, extras em falta, problemas do motor).",
  "verdict_narrative": "3-4 frases: síntese final como amigo especialista. Honesto e direto. Contextualiza preço, km, motor, extras — vale ou não? Para quem é ideal?",
  "seller_read": "2-3 frases: psicologia do vendedor baseada na descrição. Descrição detalhada = transparência, vaga = possível ocultação. Palavras como 'urgente', 'impecável' — o que significam.",
  "inspection_checklist": ["5-7 pontos de inspeção ESPECÍFICOS para ESTE motor e modelo. Ex: 'Verificar corrente de distribuição — problema conhecido acima de 120k km'. Não ponhas coisas genéricas como 'verificar pneus'."],
  "negotiation_tips": ["3-5 dicas de negociação específicas para ESTA situação, baseadas no preço, km, tempo no mercado e tipo de vendedor."]
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
        result = await asyncio.wait_for(
            asyncio.to_thread(generate_json, prompt, 8192),
            timeout=90,
        )
        if not isinstance(result, dict) or not result.get("verdict"):
            print(f"[AD_ANALYSIS] Gemini returned unexpected structure: {str(result)[:200]}")
            return {}
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
    - Gemini 2.5 Flash: when GEMINI_API_KEY is set and USE_RULE_ANALYSIS != true
    - Rule engine: fallback when no API key, flag set, or Gemini fails
    """
    from app.services.llm_client import llm_available

    if USE_RULE_ANALYSIS or not llm_available():
        reason = f"USE_RULE={USE_RULE_ANALYSIS}|llm_avail={llm_available()}"
        print(f"[AD_ANALYSIS] Using rule engine ({reason})")
        result = _run_rule_engine(listing, model_info, market_stats, user_profile)
        result["_analysis_engine"] = f"rule:{reason}"
        return result

    print("[AD_ANALYSIS] Using Gemini 2.5 Flash for analysis")
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
               n.llm_analysis, n.analysis_cached_at, n.photo_count, n.listing_age_days
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


def _get_model_info(db: Session, brand_name: str, model_name: str) -> dict:
    """Fetch model reliability info, known issues, maintenance cost, and Bayesian trust data."""
    # Strip accents so 'Citroën' matches 'Citroen' in DB, 'Série 3' matches 'Serie 3'
    brand_norm = _strip_accents(brand_name).lower()
    model_norm = _strip_accents(model_name).lower()
    row = db.execute(text("""
        SELECT vm.id,
               AVG(e.reliability_score)::float           AS avg_reliability,
               AVG(e.maintenance_cost_year)::float       AS maintenance_cost_year,
               MAX(dc.comfort_score)                     AS comfort_score,
               MAX(dc.driving_fun_score)                 AS driving_fun_score,
               MAX(dc.family_score)                      AS family_score,
               (SELECT ROUND(AVG(g.reliability_score)::numeric, 2)
                FROM generations g WHERE g.model_id = vm.id
                AND g.reliability_score IS NOT NULL)     AS reliability_score,
               STRING_AGG(DISTINCT ei.description, '; ') AS known_issues,
               STRING_AGG(DISTINCT ei.fix_cost_estimate::text, '; ') AS fix_cost_estimates
        FROM vehicle_models vm
        JOIN brands b ON b.id = vm.brand_id
        LEFT JOIN engines e ON e.model_id = vm.id
        LEFT JOIN driving_character dc ON dc.model_id = vm.id
        LEFT JOIN engine_issues ei ON ei.engine_id = e.id AND ei.severity IN ('alto', 'critico', 'medio')
        WHERE LOWER(b.name) = LOWER(:brand) AND LOWER(vm.name) = LOWER(:model)
        GROUP BY vm.id
        LIMIT 1
    """), {"brand": brand_norm, "model": model_norm}).mappings().fetchone()

    if not row:
        return {"reliability_score": None, "known_issues": None}

    info = dict(row)
    model_id = info.get("id")

    # Enrich with Bayesian reliability data from generations
    if model_id:
        trust_row = db.execute(text("""
            SELECT
                ROUND(AVG(reliability_score)::numeric, 2)  AS score,
                ROUND(MIN(reliability_ci_low)::numeric, 2)  AS ci_low,
                ROUND(MAX(reliability_ci_high)::numeric, 2) AS ci_high,
                (SELECT reliability_data_quality FROM generations
                 WHERE model_id = :mid AND reliability_data_quality IS NOT NULL
                 ORDER BY year_start DESC LIMIT 1) AS data_quality
            FROM generations
            WHERE model_id = :mid AND reliability_score IS NOT NULL
        """), {"mid": model_id}).mappings().fetchone()

        if trust_row and trust_row["score"] is not None:
            info["bayesian_reliability_score"]   = float(trust_row["score"])
            info["bayesian_reliability_ci_low"]  = float(trust_row["ci_low"]) if trust_row["ci_low"] else None
            info["bayesian_reliability_ci_high"] = float(trust_row["ci_high"]) if trust_row["ci_high"] else None
            info["bayesian_reliability_quality"] = trust_row["data_quality"] or "prior_only"

    return info


def _get_generation_window(db: Session, model_id: int, year: int) -> Optional[tuple]:
    """
    Return (year_start, year_end) for the generation that contains `year`.
    year_end may be NULL (current gen) — treated as present year.
    Returns None if no generation record found.
    """
    row = db.execute(text("""
        SELECT year_start, year_end
        FROM generations
        WHERE model_id = :model_id
          AND year_start <= :year
          AND (year_end IS NULL OR year_end >= :year)
        ORDER BY year_start DESC
        LIMIT 1
    """), {"model_id": model_id, "year": year}).mappings().fetchone()

    if row:
        return (row["year_start"], row["year_end"])
    return None


def _get_market_stats(db: Session, model_id: int, year: Optional[int] = None) -> dict:
    """
    Fetch market price statistics for a model/year combination.
    Includes freshness info: source and days since last update.
    Stale data (>14 days) is flagged so the live scraper knows to refresh.
    """
    if year:
        row = db.execute(text("""
            SELECT AVG(avg_price) as avg_price,
                   MIN(min_price) as min_price,
                   MAX(max_price) as max_price,
                   MAX(updated_at) as last_updated,
                   MAX(source) as source
            FROM market_price_stats
            WHERE model_id = :model_id
              AND ABS(year - :year) <= 2
        """), {"model_id": model_id, "year": year}).mappings().fetchone()
    else:
        row = db.execute(text("""
            SELECT AVG(avg_price) as avg_price,
                   MIN(min_price) as min_price,
                   MAX(max_price) as max_price,
                   MAX(updated_at) as last_updated,
                   MAX(source) as source
            FROM market_price_stats
            WHERE model_id = :model_id
        """), {"model_id": model_id}).mappings().fetchone()

    if row and row["avg_price"]:
        result = {
            "avg_price": float(row["avg_price"]),
            "min_price": row["min_price"],
            "max_price": row["max_price"],
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


async def _fetch_live_market_data(
    brand_name: str,
    model_name: str,
    year: Optional[int],
    fuel_type: Optional[str] = None,
    engine_hint: Optional[str] = None,
    gen_year_start: Optional[int] = None,
    gen_year_end: Optional[int] = None,
) -> dict:
    """
    Fetch real-time market pricing from Standvirtual + OLX.

    Filters comparables progressively to ensure like-for-like pricing:
      1. Generation window (year_start–year_end from generations table) when available,
         else ±3 year fallback — so a Golf Mk7 (2012–2019) only compares with Mk7 listings.
      2. Fuel type match (diesel / gasolina / híbrido / elétrico)
      3. Engine variant hint match in listing title (e.g. '1.6 TDI', '2.0 TSI')

    Each filter is only applied if it leaves ≥ 3 listings — otherwise the broader
    pool is kept, so we never return empty due to over-filtering.

    Returns empty dict on failure or insufficient data (< 3 results).
    Results cached in-memory for 6 hours per variant key.
    """
    if not brand_name or not model_name:
        return {}

    # Cache key includes generation + variant so Golf Mk7 diesel and Golf Mk8 diesel
    # are cached independently and never share market data.
    model_first = model_name.split()[0].lower()
    fuel_key    = (fuel_type or "").lower().replace(" ", "")[:8]
    engine_key  = (engine_hint or "").lower().replace(" ", "")[:8]
    gen_key     = f"{gen_year_start or 'x'}-{gen_year_end or 'now'}"
    cache_key   = f"{brand_name.lower().replace(' ', '-')}_{model_first}_{gen_key}_{fuel_key}_{engine_key}"
    now = time.time()

    cached = _market_cache.get(cache_key)
    if cached and (now - cached["cached_at"]) < _MARKET_CACHE_TTL:
        print(f"[MARKET] Cache hit for {cache_key}")
        return cached["stats"]

    gen_label = (f"gen {gen_year_start}–{gen_year_end or 'now'}"
                 if gen_year_start is not None else "no gen")
    print(f"[MARKET] Live scrape — {brand_name} {model_name}"
          f"{' ' + fuel_type if fuel_type else ''}{' ' + engine_hint if engine_hint else ''}"
          f" [{gen_label}]")
    try:
        from app.scrapers.dispatcher import fetch_listings_all_sources

        # Pass generation year bounds directly into the search URL so
        # Standvirtual/OLX return only listings from this generation.
        # Fall back to ±3 window if no generation record exists.
        scrape_year_from: Optional[int] = None
        scrape_year_to:   Optional[int] = None
        if gen_year_start is not None:
            scrape_year_from = gen_year_start
            scrape_year_to   = gen_year_end   # None = open-ended (still-current gen)
        elif year:
            scrape_year_from = year - 3
            scrape_year_to   = year + 3

        listings = await fetch_listings_all_sources(
            brand=brand_name,
            model=model_first,
            budget_max=None,
            max_per_source=20,
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
        if year and len(pool) >= 5:
            if gen_year_start is not None:
                gen_end = gen_year_end if gen_year_end else 9999
                year_pool = [
                    l for l in pool
                    if l.get("year") and gen_year_start <= int(l["year"]) <= gen_end
                ]
                label = f"gen {gen_year_start}–{gen_year_end or 'now'}"
            else:
                year_pool = [
                    l for l in pool
                    if l.get("year") and abs(int(l["year"]) - int(year)) <= 3
                ]
                label = "±3 years"

            if len(year_pool) >= 3:
                pool = year_pool
                print(f"[MARKET] Year guard ({label}) → {len(pool)} listings")

        # ── Filter 2: fuel type ───────────────────────────────────────────────
        if fuel_type and len(pool) >= 4:
            fuel_norm = fuel_type.lower()
            fuel_pool = [
                l for l in pool
                if (l.get("fuel_type") or "").lower() and fuel_norm in (l.get("fuel_type") or "").lower()
            ]
            if len(fuel_pool) >= 3:
                pool = fuel_pool
                print(f"[MARKET] Fuel filter '{fuel_type}' → {len(pool)} listings")

        # ── Filter 3: engine variant hint ─────────────────────────────────────
        if engine_hint and len(pool) >= 5:
            hint_lower = engine_hint.lower()
            engine_pool = [
                l for l in pool
                if hint_lower in (l.get("title") or "").lower()
            ]
            if len(engine_pool) >= 3:
                pool = engine_pool
                print(f"[MARKET] Engine filter '{engine_hint}' → {len(pool)} listings")

        if len(pool) < 3:
            print(f"[MARKET] Insufficient data ({len(pool)} listings) for {cache_key}")
            return {}

        all_prices = sorted(l["price"] for l in pool)
        n = len(all_prices)
        median = all_prices[n // 2] if n % 2 == 1 else (all_prices[n // 2 - 1] + all_prices[n // 2]) / 2

        # Trim outliers: drop top and bottom 10% for avg
        trim_n = max(1, n // 10)
        trimmed = all_prices[trim_n:-trim_n] if n > 4 else all_prices
        trimmed_avg = sum(trimmed) / len(trimmed)

        stats = {
            "avg_price":    round(trimmed_avg),
            "median_price": round(median),
            "min_price":    min(all_prices),
            "max_price":    max(all_prices),
            "sample_count": n,
            "source":       "live",
        }

        _market_cache[cache_key] = {"stats": stats, "cached_at": now}
        # Evict oldest entries if cache grows too large
        if len(_market_cache) > _MAX_MARKET_CACHE_KEYS:
            oldest = sorted(_market_cache, key=lambda k: _market_cache[k].get("cached_at", 0))
            for k in oldest[:len(_market_cache) - _MAX_MARKET_CACHE_KEYS]:
                del _market_cache[k]
        print(f"[MARKET] {cache_key}: median={median:.0f} avg={trimmed_avg:.0f} n={n}")
        return stats

    except Exception as e:
        print(f"[MARKET] Live scrape error for {brand_name} {model_name}: {e}")
        return {}


def _classify_source_type(source: str, domain: str) -> str:
    """Classify a source into marketplace | dealer | private | unknown."""
    if source in ("standvirtual", "olx"):
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


def _resolve_model_from_url(db: Session, listing_url: str) -> Optional[dict]:
    """Try to resolve model_id from a listing URL already in the DB."""
    row = db.execute(text("""
        SELECT n.model_id, n.brand_name, n.model_name, n.year, n.km, n.price,
               n.km_per_year, n.price_delta, n.deal_tier, n.deal_score, n.seller_type,
               n.description, n.photo_count, r.source_url
        FROM normalized_listings n
        JOIN raw_listings r ON r.id = n.raw_listing_id
        WHERE r.source_url = :url
        LIMIT 1
    """), {"url": listing_url}).mappings().fetchone()
    return dict(row) if row else None


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


def _resolve_vehicle_model(
    db: Session, brand_name: str, model_name: str, model_first_word: str
) -> Optional[dict]:
    """
    Resolve a scraped brand/model to a vehicle_models DB row.

    Strategy:
    1. Direct LIKE match on first word of model name
    2. BMW variant mapping: "116" → "Série 1", "320" → "Série 3"
    3. Mercedes variant mapping: "A" → "Classe A", "C" → "Classe C"
    4. Fuzzy: try each word of the model name individually
    """
    if not brand_name or not model_first_word:
        return None

    # Strip accents so 'Citroën' matches 'Citroen', 'Série' matches 'Serie'
    brand_norm = _strip_accents(brand_name).lower()

    def _query_model(model_pattern: str, exact: bool = False):
        pattern_norm = _strip_accents(model_pattern).lower()
        if exact:
            return db.execute(text("""
                SELECT vm.id, b.name as brand_name, vm.name as model_name
                FROM vehicle_models vm
                JOIN brands b ON b.id = vm.brand_id
                WHERE LOWER(b.name) LIKE :brand AND LOWER(vm.name) = :model
                LIMIT 1
            """), {
                "brand": f"%{brand_norm}%",
                "model": pattern_norm
            }).mappings().fetchone()
        return db.execute(text("""
            SELECT vm.id, b.name as brand_name, vm.name as model_name
            FROM vehicle_models vm
            JOIN brands b ON b.id = vm.brand_id
            WHERE LOWER(b.name) LIKE :brand AND LOWER(vm.name) LIKE :model
            LIMIT 1
        """), {
            "brand": f"%{brand_norm}%",
            "model": f"%{pattern_norm}%"
        }).mappings().fetchone()

    # ── Strategy 1: direct match ──
    # Skip for single-letter tokens (too ambiguous for LIKE) and Mercedes
    # (Mercedes needs specialized class mapping in Strategy 3)
    if len(model_first_word) > 1 and "mercedes" not in brand_norm:
        row = _query_model(model_first_word)
        if row:
            return row

    # ── Strategy 2: BMW variant number → series ──
    if "bmw" in brand_norm:
        # Extract the first digit from a 3-digit number: "116" → "1", "320" → "3"
        variant_match = re.match(r"^(\d)\d{2}", model_first_word)
        if variant_match:
            series = _BMW_SERIES_MAP.get(variant_match.group(1))
            if series:
                row = _query_model(series)
                if row:
                    print(f"[MODEL] BMW variant '{model_name}' → '{series}'")
                    return row
        # X-series: "X1", "X3", etc. — first word already works
        # iX, i3, i4, i7 — try as-is
        if model_first_word.startswith("i") and len(model_first_word) <= 3:
            row = _query_model(model_first_word)
            if row:
                return row

    # ── Strategy 3: Mercedes letter → Classe ──
    if "mercedes" in brand_norm:
        letter = model_first_word.lower()
        classe = _MERC_CLASS_MAP.get(letter)
        if classe:
            row = _query_model(classe)
            if row:
                print(f"[MODEL] Mercedes variant '{model_name}' → '{classe}'")
                return row
        # CLA, GLA, GLC, GLE, GLS — exact match to avoid 'CLA' matching 'Classe A'
        if len(letter) >= 2:
            row = _query_model(letter, exact=True)
            if row:
                return row

    # ── Strategy 4: try each word of model_name ──
    words = model_name.lower().split()
    for word in words[1:]:  # skip first word (already tried)
        if len(word) >= 2:
            row = _query_model(word)
            if row:
                print(f"[MODEL] Fuzzy match: '{model_name}' → word '{word}'")
                return row

    print(f"[MODEL] No DB match for {brand_name} '{model_name}' (first_word='{model_first_word}')")
    return None


async def _scrape_and_store_listing(db: Session, listing_url: str) -> Optional[dict]:
    """
    Fetch the listing detail page via the appropriate scraper (SV or OLX),
    infer model from URL slugs or title, store in raw_listings + normalized_listings.
    Returns the normalized row dict.
    """
    # Detect source and validate
    source = detect_source(listing_url) or "desconhecido"

    # Route to correct scraper via dispatcher
    detail = await fetch_detail_for_url(listing_url)

    # JS SPA flag — site had minimal page text, but may still have meta tags.
    # Continue with whatever data we have; the response will include a caveat.
    _js_limited = detail.pop("_js_only", False)
    _pw_debug = detail.pop("_pw_debug", None)

    # Extraction metadata — track scraper health and data quality
    _extraction_method = detail.pop("_extraction_method", None)
    _extraction_layers = detail.pop("_extraction_layers", None)
    _data_quality = detail.pop("_data_quality", None)
    # Pop title used internally by extraction layers
    detail.pop("title", None)

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

    # Lookup model — guard against empty brand/model (generic scraper may not resolve them)
    model_first_word = (model_name.lower().split() or [""])[0]
    model_row = _resolve_vehicle_model(db, brand_name, model_name, model_first_word)

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
        "source_url":    listing_url,
        "source":        source,
        "_js_limited":   _js_limited,
        "_pw_debug":     _pw_debug,
        "_extraction_method": _extraction_method,
        "_data_quality":      _data_quality,
        "_data_warnings":     _data_warnings,
    }


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
            _analyse_listing_inner(db, listing_url, user_profile, force_refresh),
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
) -> dict:
    """Inner implementation — caller wraps in try/except."""
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
            cached_model_info = _get_model_info(db, brand_n, model_n) or {}
        # Pull market stats from DB (no live scrape on cache hit)
        cached_market: dict = {}
        cached_model_id = cached_model_info.get("id") if cached_model_info else None
        if cached_model_id and cached.get("year"):
            cached_market = _get_market_stats(db, cached_model_id, cached.get("year")) or {}
        return _build_response(
            cached, llm, from_cache=True,
            enrichment=cached_enrichment or None,
            model_info=cached_model_info or None,
            market_stats=cached_market or None,
        )

    # ── 2. Resolve or scrape listing ──
    if force_refresh:
        # Always re-scrape on force_refresh (bypasses stale cached scrape data)
        normalized = await _scrape_and_store_listing(db, listing_url)
    else:
        normalized = _resolve_model_from_url(db, listing_url)
        if not normalized:
            normalized = await _scrape_and_store_listing(db, listing_url)

    if not normalized:
        return {"error": "Não foi possível obter o anúncio. Verifique o URL e tente novamente."}

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
    if model_id and year:
        gen_window = _get_generation_window(db, model_id, year)
        if gen_window:
            gen_year_start, gen_year_end = gen_window
            print(f"[ANALYSIS] Generation window: {gen_year_start}–{gen_year_end or 'now'} "
                  f"for {brand_name} {model_name} ({year})")
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
                ),
                timeout=45,  # 45s hard cap — Playwright can't hang the whole app
            )
        except asyncio.TimeoutError:
            print(f"[ANALYSIS] Live market fetch timed out after 45s — falling back to DB")
        except Exception as e:
            print(f"[ANALYSIS] Live market fetch failed: {e}")
    elif DISABLE_LIVE_MARKET and brand_name:
        print(f"[ANALYSIS] Live market scrape disabled (DISABLE_LIVE_MARKET=true) — using DB only")

    # Write live result back to DB so future requests skip scraping
    if market_stats.get("source") == "live" and model_id and market_stats.get("avg_price"):
        try:
            db.execute(
                text("""
                    INSERT INTO market_price_stats
                        (model_id, year, avg_price, min_price, max_price, sample_count, source, updated_at)
                    VALUES
                        (:model_id, :year, :avg_price, :min_price, :max_price, :sample_count, 'live_scraped', NOW())
                    ON CONFLICT (model_id, year) DO UPDATE SET
                        avg_price    = EXCLUDED.avg_price,
                        min_price    = EXCLUDED.min_price,
                        max_price    = EXCLUDED.max_price,
                        sample_count = EXCLUDED.sample_count,
                        source       = 'live_scraped',
                        updated_at   = NOW()
                """),
                {
                    "model_id":     model_id,
                    "year":         year,
                    "avg_price":    market_stats["avg_price"],
                    "min_price":    market_stats.get("min_price"),
                    "max_price":    market_stats.get("max_price"),
                    "sample_count": market_stats.get("sample_count", 0),
                },
            )
            db.commit()
        except Exception:
            db.rollback()  # non-critical — analysis continues regardless

    if not market_stats and model_id:
        market_stats = _get_market_stats(db, model_id, year)
        if market_stats:
            market_stats["source"] = "db"

    if model_id:
        model_info = _get_model_info(db, brand_name, model_name)

    # ── 3a. Compute deal metrics ──
    price = normalized.get("price")
    avg_price = market_stats.get("avg_price")
    km_per_year = normalized.get("km_per_year") or _compute_km_per_year(normalized.get("km"), normalized.get("year"))
    price_delta = _compute_price_delta(price or 0, avg_price or 0) if price and avg_price else 0.0
    deal_tier = _classify_deal_tier(price_delta, km_per_year, price, avg_price, normalized.get("seller_type", "desconhecido"))
    deal_score = _compute_deal_score(price_delta, km_per_year)

    # Enrich listing with computed metrics
    normalized["km_per_year"] = km_per_year
    normalized["price_delta"] = price_delta
    normalized["deal_tier"] = deal_tier
    normalized["deal_score"] = deal_score
    if avg_price and price:
        normalized["price_delta_pct"] = round(abs((avg_price - price) / avg_price * 100), 1)
    else:
        normalized["price_delta_pct"] = None

    # ── 4. Analysis (Gemini or rule engine fallback) ──
    # Single unified LLM call returns both analysis + enrichment fields.
    # This halves Gemini API calls (critical on free tier: 20/day limit).
    llm_result = await _analyse(normalized, model_info, market_stats, user_profile)

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
            llm_result_to_cache = {**llm_result, **enrichment}
            _store_analysis(db, norm_id, llm_result_to_cache, deal_tier, deal_score)
        except Exception as e:
            print(f"[AD_ANALYSIS] Cache store error: {e}")

    return _build_response(
        normalized, llm_result, from_cache=False, market_stats=market_stats,
        gen_year_start=gen_year_start, gen_year_end=gen_year_end,
        fit=fit_result, model_info=model_info, enrichment=enrichment,
        js_limited=normalized.get("_js_limited", False),
        pw_debug=normalized.get("_pw_debug"),
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
            tips.append(
                f"Está {pct_above}% acima do mercado — propõe {target:,}€ mencionando anúncios comparáveis"
            )
        elif price_delta > 0.05:  # car is below market — validate before paying
            tips.append(
                "Preço abaixo do mercado — confirma o estado real antes de fechar negócio"
            )

    # Listing age leverage
    if listing_age >= 30:
        tips.append(
            f"Anúncio há {listing_age} dias — vendedor está provavelmente motivado, podes negociar"
        )
    elif listing_age >= 14:
        tips.append(f"Anúncio há {listing_age} dias — há espaço para tentar 3-5% de desconto")

    # Seller type
    if seller_type == "particular":
        tips.append(
            "Vendedor particular — mais flexível em preço, mas sem garantia legal"
        )
    elif seller_type == "profissional":
        tips.append(
            "Stand profissional — menos margem de negociação, mas com garantia de 1 ano"
        )

    # High km leverage
    if km > 150000:
        tips.append(
            f"Com {km:,} km, pede uma inspeção independente antes — usa o resultado para negociar"
        )
    elif km > 100000:
        tips.append(
            "Acima de 100.000 km — menciona os custos de manutenção previsíveis para justificar desconto"
        )

    if not tips:
        tips.append("Pede sempre a história de serviços completa antes de fazer oferta")

    return tips[:4]


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
) -> dict:
    """Build the final response dict sent to the frontend."""
    km_per_year = listing.get("km_per_year")
    price_delta = listing.get("price_delta", 0.0) or 0.0

    return {
        "from_cache": from_cache,
        "source": listing.get("source") or detect_source(listing.get("source_url", "")) or "generic",
        "source_label": source_label(listing.get("source") or detect_source(listing.get("source_url", "")) or "generic"),
        "source_domain": listing.get("source_domain", ""),
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
            "trim_level": llm.get("trim_level"),
            "spec_tier": llm.get("spec_tier", "base"),
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
