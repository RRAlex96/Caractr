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
