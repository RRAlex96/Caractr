"""
Caractr — Listings API v4.2
Endpoints:
    POST /api/listings/analyse       — analyse a specific listing URL (any Portuguese car dealer)
    GET  /api/listings/{model_id}    — get cached listings for a model
    GET  /api/listings/sources       — list supported ad sources
"""

import asyncio
import hmac
import os
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from typing import Optional
from app.db.database import get_db
from app.services.ad_analysis_service import analyse_listing
from app.scrapers.dispatcher import get_supported_sources, is_supported_url

router = APIRouter(prefix="/api/listings", tags=["listings"])


class AnalyseRequest(BaseModel):
    listing_url: str
    model_id: Optional[int] = None        # hint to skip DB model lookup
    user_profile: Optional[dict] = None  # {economy, comfort, driving, practical, status, reliability}
    force_refresh: bool = False           # bust cache and re-scrape/re-analyse


@router.get("/sources")
def supported_sources():
    """Return list of natively supported ad source domains (any valid URL also accepted via generic scraper)."""
    return {
        "sources": [
            {"id": "standvirtual", "name": "Standvirtual",    "domain": "standvirtual.com", "url": "https://www.standvirtual.com",                       "native": True},
            {"id": "olx",          "name": "OLX Auto",        "domain": "olx.pt",           "url": "https://www.olx.pt/carros-motos-e-barcos/carros/",   "native": True},
            {"id": "generic",      "name": "Qualquer dealer", "domain": "*",                "url": None,                                                  "native": False},
        ],
        "note": "Qualquer URL de anúncio válido (http/https) é aceite via extractor genérico.",
    }


@router.post("/analyse")
async def analyse_ad(req: AnalyseRequest, db: Session = Depends(get_db)):
    """
    Analyse a specific listing URL from any Portuguese car dealer website.
    Native scrapers: Standvirtual, OLX. Generic extractor: any valid http/https URL.
    Returns deal scoring + analysis with spec detection.
    ~200ms on cache miss (rule engine), ~5ms on cache hit.
    """
    # Quick pre-validation before hitting the full pipeline
    if not is_supported_url(req.listing_url):
        return {
            "error": "URL inválido. Cole um link direto de um anúncio (deve começar com http:// ou https://)."
        }

    result = await analyse_listing(
        db=db,
        listing_url=req.listing_url,
        user_profile=req.user_profile,
        force_refresh=req.force_refresh,
    )
    return result


@router.get("/{model_id}")
def get_model_listings(
    model_id: int,
    limit: int = 10,
    deal_tier: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    Get cached analysed listings for a given model_id.
    Ordered by deal_score DESC.
    Optionally filter by deal_tier: forte | razoavel | cuidado | evitar
    """
    base_query = """
        SELECT n.id, n.brand_name, n.model_name, n.year, n.km, n.price,
               n.km_per_year, n.price_delta, n.deal_tier, n.deal_score,
               n.seller_type, n.photo_count, n.llm_analysis, n.analysis_cached_at,
               r.source_url
        FROM normalized_listings n
        JOIN raw_listings r ON r.id = n.raw_listing_id
        WHERE n.model_id = :model_id
          AND n.price IS NOT NULL
    """
    params: dict = {"model_id": model_id, "limit": limit}

    if deal_tier:
        base_query += " AND n.deal_tier = :tier"
        params["tier"] = deal_tier

    base_query += " ORDER BY n.deal_score DESC NULLS LAST LIMIT :limit"

    rows = db.execute(text(base_query), params).mappings().fetchall()

    import json
    listings = []
    for row in rows:
        llm = row["llm_analysis"]
        if isinstance(llm, str):
            try:
                llm = json.loads(llm)
            except Exception:
                llm = {}
        if not isinstance(llm, dict):
            llm = {}

        listings.append({
            "id": row["id"],
            "full_name": f"{row['brand_name']} {row['model_name']}",
            "year": row["year"],
            "km": row["km"],
            "price": row["price"],
            "km_per_year": row["km_per_year"],
            "price_delta": row["price_delta"],
            "deal_tier": row["deal_tier"],
            "deal_score": row["deal_score"],
            "seller_type": row["seller_type"],
            "photo_count": row["photo_count"],
            "url": row["source_url"],
            "verdict_reason": (llm or {}).get("verdict_reason"),
            "spec_tier": (llm or {}).get("spec_tier"),
            "analysed": row["analysis_cached_at"] is not None,
        })

    return {"model_id": model_id, "count": len(listings), "listings": listings}


@router.post("/admin/refresh-market")
async def trigger_market_refresh(
    x_admin_token: str = Header(...),
    db: Session = Depends(get_db),
):
    """
    Manually trigger a full market data refresh (scrape + aggregate).
    Requires X-Admin-Token header.
    """
    admin_token = os.getenv("ADMIN_TOKEN", "")
    if not admin_token or not hmac.compare_digest(x_admin_token, admin_token):
        raise HTTPException(status_code=403, detail="Forbidden")

    import asyncio
    from app.services.market_scraper_runner import run_market_scraper
    from app.services.market_aggregator import run_aggregation

    scrape_result = await asyncio.get_event_loop().run_in_executor(
        None, run_market_scraper, db
    )
    agg_result = run_aggregation(db)
    return {"scrape": scrape_result, "aggregation": agg_result}


@router.post("/admin/refresh-reliability")
def trigger_reliability_refresh(
    x_admin_token: str = Header(...),
    db: Session = Depends(get_db),
):
    """
    Manually trigger the reliability update pipeline (Safety Gate + NHTSA + Bayesian scorer).
    Requires X-Admin-Token header.
    """
    admin_token = os.getenv("ADMIN_TOKEN", "")
    if not admin_token or not hmac.compare_digest(x_admin_token, admin_token):
        raise HTTPException(status_code=403, detail="Forbidden")

    from app.scrapers.safety_gate import ingest_safety_gate
    from app.scrapers.nhtsa import ingest_nhtsa_all
    from app.scrapers.kba_recalls import ingest_kba_incremental
    from app.services.reliability_runner import run_reliability_scorer

    sg_stats     = ingest_safety_gate(db, max_pages=20, sleep_seconds=1.5)
    nhtsa_stats  = ingest_nhtsa_all(db, sleep_seconds=0.4)
    kba_stats    = ingest_kba_incremental(db, sleep_seconds=2.0)
    scorer_stats = run_reliability_scorer(db)
    return {
        "safety_gate": sg_stats, "nhtsa": nhtsa_stats,
        "kba": kba_stats, "scorer": scorer_stats,
    }


@router.get("/admin/scraper-health")
def scraper_health(
    x_admin_token: str = Header(...),
    db: Session = Depends(get_db),
):
    """
    Scraper health dashboard — extraction method distribution, quality grades,
    and market data freshness. Use to detect when __NEXT_DATA__ degrades.
    """
    admin_token = os.getenv("ADMIN_TOKEN", "")
    if not admin_token or not hmac.compare_digest(x_admin_token, admin_token):
        raise HTTPException(status_code=403, detail="Forbidden")

    # Market data freshness
    market_freshness = db.execute(text("""
        SELECT
            source,
            COUNT(*) as count,
            MAX(updated_at) as last_updated,
            EXTRACT(EPOCH FROM (NOW() - MAX(updated_at))) / 86400 AS days_ago
        FROM market_price_stats
        WHERE updated_at IS NOT NULL
        GROUP BY source
        ORDER BY last_updated DESC
    """)).mappings().fetchall()

    # Market coverage: how many models have price data
    coverage = db.execute(text("""
        SELECT
            (SELECT COUNT(DISTINCT model_id) FROM market_price_stats
             WHERE avg_price IS NOT NULL) AS models_with_prices,
            (SELECT COUNT(*) FROM vehicle_models) AS total_models,
            (SELECT COUNT(*) FROM market_price_stats
             WHERE source = 'live_scraped'
               AND updated_at > NOW() - INTERVAL '7 days') AS live_updated_7d,
            (SELECT COUNT(*) FROM market_price_stats
             WHERE source = 'live_scraped'
               AND updated_at > NOW() - INTERVAL '14 days') AS live_updated_14d
    """)).mappings().fetchone()

    # Generation price data coverage
    gen_coverage = db.execute(text("""
        SELECT
            (SELECT COUNT(*) FROM generations) AS total_generations,
            (SELECT COUNT(*) FROM generations
             WHERE market_value_p50 IS NOT NULL) AS generations_with_p50,
            (SELECT COUNT(*) FROM generations
             WHERE market_value_as_of IS NOT NULL
               AND market_value_as_of >= (CURRENT_DATE - INTERVAL '30 days')) AS generations_fresh
    """)).mappings().fetchone()

    # Normalized listings stats (recent analyses)
    analysis_stats = db.execute(text("""
        SELECT
            COUNT(*) AS total_analyses_7d,
            COUNT(*) FILTER (WHERE price IS NOT NULL) AS with_price,
            COUNT(*) FILTER (WHERE km IS NOT NULL) AS with_km,
            COUNT(*) FILTER (WHERE year IS NOT NULL) AS with_year,
            COUNT(*) FILTER (WHERE model_id IS NOT NULL) AS with_model_id
        FROM normalized_listings
        WHERE created_at > NOW() - INTERVAL '7 days'
    """)).mappings().fetchone()

    return {
        "market_freshness": [
            {
                "source": r["source"],
                "count": r["count"],
                "last_updated": str(r["last_updated"]) if r["last_updated"] else None,
                "days_ago": round(r["days_ago"], 1) if r["days_ago"] else None,
            }
            for r in market_freshness
        ],
        "coverage": {
            "models_with_prices": coverage["models_with_prices"],
            "total_models": coverage["total_models"],
            "pct": round(coverage["models_with_prices"] / max(1, coverage["total_models"]) * 100, 1),
            "live_updated_7d": coverage["live_updated_7d"],
            "live_updated_14d": coverage["live_updated_14d"],
        },
        "generations": {
            "total": gen_coverage["total_generations"],
            "with_p50": gen_coverage["generations_with_p50"],
            "fresh_30d": gen_coverage["generations_fresh"],
        },
        "recent_analyses_7d": {
            "total": analysis_stats["total_analyses_7d"],
            "with_price": analysis_stats["with_price"],
            "with_km": analysis_stats["with_km"],
            "with_year": analysis_stats["with_year"],
            "with_model_id": analysis_stats["with_model_id"],
        },
    }
