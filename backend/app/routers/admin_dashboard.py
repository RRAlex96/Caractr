"""
Caractr — Admin Dashboard API
Analytics metrics + concierge pipeline management for the admin dashboard.
All endpoints protected by X-Admin-Token header.
"""

import os
import hmac
import json
from fastapi import APIRouter, Depends, Header, HTTPException, Query, Body
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from typing import Optional
from app.db.database import get_db

router = APIRouter(prefix="/api/admin", tags=["admin"])

_PERIOD_MAP = {"7d": 7, "30d": 30, "90d": 90}
_VALID_STATUSES = {"new", "contacted", "searching", "delivered", "closed"}
FREE_CONCIERGE_LIMIT = 50


def _auth(x_admin_token: str = Header(...)):
    admin_token = os.getenv("ADMIN_TOKEN", "")
    if not admin_token or not hmac.compare_digest(x_admin_token, admin_token):
        raise HTTPException(status_code=403, detail="Forbidden")


@router.get("/health/extraction", dependencies=[Depends(_auth)])
async def health_extraction():
    """
    Daily canary: one Standvirtual search and one listing read from this
    server, no AI call and no database write. 200 when a listing reads with
    every critical field, 503 otherwise — so a scheduled `curl --fail` alerts.
    Admin-only: it makes outbound requests, so it must not be open to abuse.
    """
    from fastapi.responses import JSONResponse
    from app.services.extraction_check import check_extraction

    result = await check_extraction()
    return JSONResponse(result, status_code=200 if result["ok"] else 503)


@router.get("/dashboard", dependencies=[Depends(_auth)])
def get_dashboard(
    period: str = Query("30d", pattern="^(7d|30d|90d)$"),
    db: Session = Depends(get_db),
):
    days = _PERIOD_MAP[period]

    # ── 1. Overview cards ─────────────────────────────────────────────────
    overview = db.execute(text(f"""
        SELECT
            COUNT(DISTINCT anon_id) FILTER (WHERE anon_id IS NOT NULL) AS unique_users,
            COUNT(*) FILTER (WHERE event_name = 'selector_started') AS sessions_started,
            COUNT(*) FILTER (WHERE event_name = 'selector_completed') AS sessions_completed,
            COUNT(*) FILTER (WHERE event_name = 'ad_analysis_requested') AS analyses_requested,
            COUNT(*) FILTER (WHERE event_name = 'analysis_completed') AS analyses_completed,
            COUNT(*) AS total_events
        FROM analytics_events
        WHERE created_at >= NOW() - INTERVAL '{days} days'
    """)).mappings().fetchone()

    concierge_count = db.execute(text(f"""
        SELECT COUNT(*) AS cnt
        FROM concierge_requests
        WHERE created_at >= NOW() - INTERVAL '{days} days'
    """)).mappings().fetchone()["cnt"]

    # ── 2. Funnel ─────────────────────────────────────────────────────────
    funnel_raw = db.execute(text(f"""
        SELECT event_name, COUNT(DISTINCT anon_id) AS unique_users
        FROM analytics_events
        WHERE created_at >= NOW() - INTERVAL '{days} days'
          AND event_name IN (
            'selector_started', 'selector_completed', 'results_viewed',
            'model_clicked', 'ad_analysis_requested', 'concierge_interest'
          )
        GROUP BY event_name
    """)).mappings().fetchall()

    funnel_map = {r["event_name"]: r["unique_users"] for r in funnel_raw}
    funnel_steps = [
        ("selector_started", "Início do wizard"),
        ("selector_completed", "Wizard completo"),
        ("results_viewed", "Resultados vistos"),
        ("model_clicked", "Modelo clicado"),
        ("ad_analysis_requested", "Análise pedida"),
        ("concierge_interest", "Interesse concierge"),
    ]
    first_count = funnel_map.get("selector_started", 0)
    funnel = []
    prev_count = first_count
    for event_name, label in funnel_steps:
        count = funnel_map.get(event_name, 0)
        pct_of_start = round(count / first_count * 100, 1) if first_count else 0
        pct_of_prev = round(count / prev_count * 100, 1) if prev_count else 0
        funnel.append({
            "event": event_name,
            "label": label,
            "count": count,
            "pct_of_start": pct_of_start,
            "pct_of_prev": pct_of_prev,
        })
        prev_count = count if count > 0 else prev_count

    # Add concierge submissions from the actual table (not always tracked as event)
    funnel.append({
        "event": "concierge_submitted",
        "label": "Concierge submetido",
        "count": concierge_count,
        "pct_of_start": round(concierge_count / first_count * 100, 1) if first_count else 0,
        "pct_of_prev": round(concierge_count / funnel_map.get("concierge_interest", 1) * 100, 1) if funnel_map.get("concierge_interest") else 0,
    })

    # ── 3. Daily trend ────────────────────────────────────────────────────
    daily_rows = db.execute(text(f"""
        SELECT DATE(created_at) AS day, COUNT(*) AS events,
               COUNT(DISTINCT anon_id) AS users
        FROM analytics_events
        WHERE created_at >= NOW() - INTERVAL '{days} days'
        GROUP BY DATE(created_at)
        ORDER BY day
    """)).mappings().fetchall()

    daily_trend = [
        {"day": str(r["day"]), "events": r["events"], "users": r["users"]}
        for r in daily_rows
    ]

    # ── 4. Top models — recommended ───────────────────────────────────────
    model_rows = db.execute(text(f"""
        SELECT (elem->>'model_id')::int AS model_id,
               COUNT(*) AS times_shown
        FROM recommendation_sessions,
             jsonb_array_elements(models_shown) AS elem
        WHERE created_at >= NOW() - INTERVAL '{days} days'
        GROUP BY (elem->>'model_id')::int
        ORDER BY times_shown DESC
        LIMIT 10
    """)).mappings().fetchall()

    # Resolve model names
    model_ids = [r["model_id"] for r in model_rows if r["model_id"]]
    model_names = {}
    if model_ids:
        name_rows = db.execute(text("""
            SELECT vm.id, b.name AS brand, vm.name AS model
            FROM vehicle_models vm
            JOIN brands b ON b.id = vm.brand_id
            WHERE vm.id = ANY(:ids)
        """), {"ids": model_ids}).mappings().fetchall()
        model_names = {r["id"]: f"{r['brand']} {r['model']}" for r in name_rows}

    top_recommended = [
        {"model_id": r["model_id"], "name": model_names.get(r["model_id"], f"ID {r['model_id']}"), "count": r["times_shown"]}
        for r in model_rows
    ]

    # ── 5. Top models — analysed ──────────────────────────────────────────
    analysed_rows = db.execute(text(f"""
        SELECT brand_name, model_name, COUNT(*) AS cnt
        FROM normalized_listings
        WHERE analysis_cached_at >= NOW() - INTERVAL '{days} days'
          AND brand_name IS NOT NULL AND brand_name != ''
        GROUP BY brand_name, model_name
        ORDER BY cnt DESC
        LIMIT 10
    """)).mappings().fetchall()

    top_analysed = [
        {"name": f"{r['brand_name']} {r['model_name']}", "count": r["cnt"]}
        for r in analysed_rows
    ]

    # ── 6. Analysis stats ─────────────────────────────────────────────────
    analysis_stats = db.execute(text(f"""
        SELECT
            COUNT(*) AS total_analysed,
            ROUND(AVG(deal_score)::numeric, 2) AS avg_deal_score,
            COUNT(*) FILTER (WHERE deal_tier = 'forte') AS tier_forte,
            COUNT(*) FILTER (WHERE deal_tier = 'razoavel') AS tier_razoavel,
            COUNT(*) FILTER (WHERE deal_tier = 'cuidado') AS tier_cuidado,
            COUNT(*) FILTER (WHERE deal_tier = 'evitar') AS tier_evitar
        FROM normalized_listings
        WHERE analysis_cached_at >= NOW() - INTERVAL '{days} days'
    """)).mappings().fetchone()

    # ── 7. Budget distribution ────────────────────────────────────────────
    budget_rows = db.execute(text(f"""
        SELECT budget_range
        FROM recommendation_sessions
        WHERE created_at >= NOW() - INTERVAL '{days} days'
          AND budget_range IS NOT NULL
    """)).mappings().fetchall()

    buckets = {"<10k": 0, "10-20k": 0, "20-30k": 0, "30-50k": 0, "50k+": 0}
    for row in budget_rows:
        br = row["budget_range"]
        if isinstance(br, str):
            try:
                br = json.loads(br)
            except Exception:
                continue
        if not isinstance(br, dict):
            continue
        mx = br.get("max") or br.get("budget_max") or 0
        if mx < 10000:
            buckets["<10k"] += 1
        elif mx < 20000:
            buckets["10-20k"] += 1
        elif mx < 30000:
            buckets["20-30k"] += 1
        elif mx < 50000:
            buckets["30-50k"] += 1
        else:
            buckets["50k+"] += 1

    budget_distribution = [{"bucket": k, "count": v} for k, v in buckets.items()]

    # ── 8. Feedback & analysis helpfulness ────────────────────────────────
    feedback_rows = db.execute(text(f"""
        SELECT satisfaction, COUNT(*) AS cnt
        FROM user_feedback
        WHERE created_at >= NOW() - INTERVAL '{days} days'
        GROUP BY satisfaction
    """)).mappings().fetchall()
    feedback_dist = {r["satisfaction"]: r["cnt"] for r in feedback_rows}

    helpfulness = db.execute(text(f"""
        SELECT
            COUNT(*) FILTER (WHERE properties->>'helpful' = 'true') AS helpful,
            COUNT(*) FILTER (WHERE properties->>'helpful' = 'false') AS not_helpful,
            COUNT(*) AS total
        FROM analytics_events
        WHERE event_name = 'analysis_feedback'
          AND created_at >= NOW() - INTERVAL '{days} days'
    """)).mappings().fetchone()

    # ── 9. Popular wizard answers ─────────────────────────────────────────
    step_rows = db.execute(text(f"""
        SELECT properties->>'field' AS field,
               properties->>'value' AS val,
               COUNT(*) AS cnt
        FROM analytics_events
        WHERE event_name = 'selector_step_completed'
          AND created_at >= NOW() - INTERVAL '{days} days'
          AND properties->>'field' IS NOT NULL
        GROUP BY properties->>'field', properties->>'value'
        ORDER BY field, cnt DESC
    """)).mappings().fetchall()

    # Group by field, take top 5 values per field
    wizard_answers: dict = {}
    for row in step_rows:
        field = row["field"]
        if field not in wizard_answers:
            wizard_answers[field] = []
        if len(wizard_answers[field]) < 5:
            wizard_answers[field].append({"value": row["val"], "count": row["cnt"]})

    # ── Build response ────────────────────────────────────────────────────
    return {
        "period": period,
        "period_days": days,
        "overview": {
            "unique_users": overview["unique_users"],
            "sessions_started": overview["sessions_started"],
            "sessions_completed": overview["sessions_completed"],
            "analyses_requested": overview["analyses_requested"],
            "concierge_submissions": concierge_count,
            "total_events": overview["total_events"],
        },
        "funnel": funnel,
        "daily_trend": daily_trend,
        "top_recommended": top_recommended,
        "top_analysed": top_analysed,
        "analysis_stats": {
            "total": analysis_stats["total_analysed"],
            "avg_deal_score": float(analysis_stats["avg_deal_score"] or 0),
            "tiers": {
                "forte": analysis_stats["tier_forte"],
                "razoavel": analysis_stats["tier_razoavel"],
                "cuidado": analysis_stats["tier_cuidado"],
                "evitar": analysis_stats["tier_evitar"],
            },
        },
        "budget_distribution": budget_distribution,
        "feedback": {
            "satisfaction": feedback_dist,
            "analysis_helpful": helpfulness["helpful"],
            "analysis_not_helpful": helpfulness["not_helpful"],
            "analysis_feedback_total": helpfulness["total"],
        },
        "wizard_answers": wizard_answers,
    }


# ── Concierge Management ─────────────────────────────────────────────────────


class ConciergeUpdate(BaseModel):
    status: Optional[str] = None
    admin_notes: Optional[str] = None


@router.get("/concierge/stats", dependencies=[Depends(_auth)])
def concierge_stats(db: Session = Depends(get_db)):
    """Quick concierge stats for the admin header."""
    row = db.execute(text("""
        SELECT
            COUNT(*)                                          AS total,
            COUNT(*) FILTER (WHERE status = 'new')            AS status_new,
            COUNT(*) FILTER (WHERE status = 'contacted')      AS status_contacted,
            COUNT(*) FILTER (WHERE status = 'searching')      AS status_searching,
            COUNT(*) FILTER (WHERE status = 'delivered')      AS status_delivered,
            COUNT(*) FILTER (WHERE status = 'closed')         AS status_closed,
            ROUND(AVG(EXTRACT(EPOCH FROM (delivered_at - created_at)) / 3600)
                  FILTER (WHERE delivered_at IS NOT NULL)::numeric, 1)
                                                              AS avg_hours_to_delivery
        FROM concierge_requests
    """)).mappings().fetchone()

    delivered = row["status_delivered"] or 0
    return {
        "total":               row["total"],
        "by_status": {
            "new":       row["status_new"],
            "contacted": row["status_contacted"],
            "searching": row["status_searching"],
            "delivered": row["status_delivered"],
            "closed":    row["status_closed"],
        },
        "free_limit":          FREE_CONCIERGE_LIMIT,
        "free_remaining":      max(0, FREE_CONCIERGE_LIMIT - delivered),
        "avg_hours_to_delivery": float(row["avg_hours_to_delivery"]) if row["avg_hours_to_delivery"] else None,
    }


@router.get("/concierge", dependencies=[Depends(_auth)])
def list_concierge(
    status: Optional[str] = Query(None),
    period: str = Query("all", pattern="^(7d|30d|90d|all)$"),
    db: Session = Depends(get_db),
):
    """List all concierge requests with optional status/period filter."""
    conditions = []
    params: dict = {}

    if status and status in _VALID_STATUSES:
        conditions.append("c.status = :status")
        params["status"] = status

    if period != "all" and period in _PERIOD_MAP:
        days = _PERIOD_MAP[period]
        conditions.append(f"c.created_at >= NOW() - INTERVAL '{days} days'")

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    rows = db.execute(text(f"""
        SELECT
            c.id, c.session_id, c.name, c.email, c.model_interest,
            c.budget_max, c.feedback_tags, c.consent_dealer,
            c.status, c.admin_notes, c.created_at, c.delivered_at,
            rs.profile_computed, rs.models_shown
        FROM concierge_requests c
        LEFT JOIN recommendation_sessions rs ON rs.id = c.session_id
        {where}
        ORDER BY c.created_at DESC
        LIMIT 200
    """), params).mappings().fetchall()

    requests = []
    for r in rows:
        # Parse session context for profile summary
        profile_summary = None
        models_shown = None
        if r["profile_computed"]:
            try:
                pc = json.loads(r["profile_computed"]) if isinstance(r["profile_computed"], str) else r["profile_computed"]
                profile_summary = pc
            except Exception:
                pass
        if r["models_shown"]:
            try:
                ms = json.loads(r["models_shown"]) if isinstance(r["models_shown"], str) else r["models_shown"]
                models_shown = [
                    {"model_id": m.get("model_id"), "full_name": m.get("full_name", "?")}
                    for m in (ms or [])[:5]
                ]
            except Exception:
                pass

        feedback_tags = r["feedback_tags"]
        if isinstance(feedback_tags, str):
            try:
                feedback_tags = json.loads(feedback_tags)
            except Exception:
                feedback_tags = []

        requests.append({
            "id":              r["id"],
            "session_id":      str(r["session_id"]) if r["session_id"] else None,
            "name":            r["name"],
            "email":           r["email"],
            "model_interest":  r["model_interest"],
            "budget_max":      r["budget_max"],
            "feedback_tags":   feedback_tags or [],
            "consent_dealer":  r["consent_dealer"],
            "status":          r["status"],
            "admin_notes":     r["admin_notes"],
            "created_at":      r["created_at"].isoformat() if r["created_at"] else None,
            "delivered_at":    r["delivered_at"].isoformat() if r["delivered_at"] else None,
            "profile_summary": profile_summary,
            "models_shown":    models_shown,
        })

    return {"count": len(requests), "requests": requests}


@router.patch("/concierge/{request_id}", dependencies=[Depends(_auth)])
def update_concierge(
    request_id: int,
    update: ConciergeUpdate,
    db: Session = Depends(get_db),
):
    """Update a concierge request's status and/or admin notes."""
    # Verify request exists
    existing = db.execute(
        text("SELECT id, status FROM concierge_requests WHERE id = :id"),
        {"id": request_id},
    ).mappings().fetchone()

    if not existing:
        raise HTTPException(status_code=404, detail="Concierge request not found")

    updates = []
    params: dict = {"id": request_id}

    if update.status is not None:
        if update.status not in _VALID_STATUSES:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid status. Must be one of: {', '.join(sorted(_VALID_STATUSES))}",
            )
        updates.append("status = :status")
        params["status"] = update.status

        # Auto-set delivered_at when transitioning to 'delivered'
        if update.status == "delivered" and existing["status"] != "delivered":
            updates.append("delivered_at = NOW()")

    if update.admin_notes is not None:
        updates.append("admin_notes = :notes")
        params["notes"] = update.admin_notes

    if not updates:
        raise HTTPException(status_code=422, detail="No fields to update")

    set_clause = ", ".join(updates)
    row = db.execute(text(f"""
        UPDATE concierge_requests
        SET {set_clause}
        WHERE id = :id
        RETURNING id, status, admin_notes, delivered_at
    """), params).mappings().fetchone()
    db.commit()

    return {
        "id":           row["id"],
        "status":       row["status"],
        "admin_notes":  row["admin_notes"],
        "delivered_at": row["delivered_at"].isoformat() if row["delivered_at"] else None,
    }


@router.get("/models/pending", dependencies=[Depends(_auth)])
def models_pending_enrichment(db: Session = Depends(get_db)):
    """
    Models lacking reliability data — primarily those auto-registered on first
    analysis. Lets the operator do a weekly pass to fill in reliability/known
    issues. Ordered by how often each is actually analysed, so the most-used
    gaps surface first.
    """
    try:
        rows = db.execute(text("""
            SELECT vm.id,
                   b.name  AS brand_name,
                   vm.name AS model_name,
                   vm.created_at,
                   (SELECT COUNT(*) FROM normalized_listings n WHERE n.model_id = vm.id)  AS analyses,
                   (SELECT COUNT(*) FROM generations g WHERE g.model_id = vm.id)           AS generations,
                   EXISTS(SELECT 1 FROM engines e WHERE e.model_id = vm.id)                AS has_engines
            FROM vehicle_models vm
            JOIN brands b ON b.id = vm.brand_id
            WHERE NOT EXISTS (
                SELECT 1 FROM generations g
                WHERE g.model_id = vm.id AND g.reliability_score IS NOT NULL
            )
            ORDER BY analyses DESC, vm.created_at DESC NULLS LAST
            LIMIT 300
        """)).mappings().fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {e}")

    items = []
    for r in rows:
        created = r["created_at"]
        items.append({
            "id":            r["id"],
            "brand_name":    r["brand_name"],
            "model_name":    r["model_name"],
            "created_at":    created.isoformat() if created else None,
            "analyses":      int(r["analyses"] or 0),
            "generations":   int(r["generations"] or 0),
            "has_engines":   bool(r["has_engines"]),
        })

    # Surface the ones people actually hit but we can't yet score.
    analysed_gap = sum(1 for i in items if i["analyses"] > 0)
    return {
        "count": len(items),
        "analysed_gap": analysed_gap,
        "models": items,
    }


@router.get("/extraction-health", dependencies=[Depends(_auth)])
def extraction_health(db: Session = Depends(get_db)):
    """
    Extraction health over time: % of scraped listings with a price and a
    resolved model, daily + per source. A sustained drop signals the sites are
    serving bot-walls / degraded pages — so it's seen, not hit silently by users.
    """
    try:
        daily = db.execute(text("""
            SELECT date_trunc('day', r.scraped_at)::date AS day,
                   COUNT(*)                              AS total,
                   COUNT(n.price)                        AS with_price,
                   COUNT(n.model_id)                     AS with_model
            FROM normalized_listings n
            JOIN raw_listings r ON r.id = n.raw_listing_id
            WHERE r.scraped_at >= NOW() - INTERVAL '21 days'
            GROUP BY day
            ORDER BY day
        """)).mappings().fetchall()

        by_source = db.execute(text("""
            SELECT r.source                              AS source,
                   COUNT(*)                              AS total,
                   COUNT(n.price)                        AS with_price
            FROM normalized_listings n
            JOIN raw_listings r ON r.id = n.raw_listing_id
            WHERE r.scraped_at >= NOW() - INTERVAL '7 days'
            GROUP BY r.source
            ORDER BY total DESC
        """)).mappings().fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {e}")

    def pct(part, whole):
        return round(100 * part / whole) if whole else None

    days = [{
        "day": d["day"].isoformat() if d["day"] else None,
        "total": int(d["total"]),
        "price_pct": pct(d["with_price"], d["total"]),
        "model_pct": pct(d["with_model"], d["total"]),
    } for d in daily]

    sources = [{
        "source": s["source"] or "desconhecido",
        "total": int(s["total"]),
        "price_pct": pct(s["with_price"], s["total"]),
    } for s in by_source]

    # Recent health = price completeness over the last 7 days.
    recent = [d for d in days[-7:]]
    recent_total = sum(d["total"] for d in recent)
    recent_priced = sum(round((d["price_pct"] or 0) / 100 * d["total"]) for d in recent)
    recent_pct = pct(recent_priced, recent_total)
    status = (
        "ok" if (recent_pct or 0) >= 80 else
        "degraded" if (recent_pct or 0) >= 55 else
        "critical"
    ) if recent_total else "no_data"

    return {"status": status, "recent_price_pct": recent_pct, "daily": days, "by_source": sources}


@router.post("/models/{model_id}/enrich/draft", dependencies=[Depends(_auth)])
def enrich_model_draft(model_id: int, db: Session = Depends(get_db)):
    """Ask the LLM to draft reliability data for a model. Returns a draft for the
    operator to review — does NOT write to the DB."""
    from app.services.llm_client import generate_json, llm_available

    row = db.execute(text("""
        SELECT vm.id, b.name AS brand, vm.name AS model
        FROM vehicle_models vm JOIN brands b ON b.id = vm.brand_id
        WHERE vm.id = :id
    """), {"id": model_id}).mappings().fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Modelo não encontrado")
    if not llm_available():
        raise HTTPException(status_code=503, detail="LLM indisponível")

    prompt = f"""És um especialista em fiabilidade de automóveis usados no mercado português.
Avalia o modelo: {row['brand']} {row['model']}.

Responde APENAS com JSON válido (sem markdown):
{{
  "reliability_score": número 0-10 (10 = extremamente fiável),
  "reliability_summary": "1-2 frases honestas sobre a fiabilidade geral deste modelo",
  "maintenance_cost_year": custo médio anual de manutenção em euros (inteiro),
  "year_start": ano de início de produção (inteiro),
  "year_end": ano de fim ou null se ainda em produção,
  "engine_code": "código do motor mais comum (ex: 'B47D20', 'EA288') ou null",
  "fuel_type": "diesel|gasolina|híbrido|elétrico",
  "displacement_cc": cilindrada típica em cm3 (inteiro) ou null,
  "power_hp": potência típica em cv (inteiro) ou null,
  "known_issues": [
    {{"severity": "alto|medio|baixo", "description": "problema concreto e específico", "affected_years": "ex: '2015-2018'", "fix_cost_estimate": "ex: '€800-1500'"}}
  ]
}}
known_issues: máximo 5, só problemas REAIS e conhecidos deste modelo. Sê específico e honesto."""

    try:
        draft = generate_json(prompt, max_tokens=1400)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Erro do LLM: {e}")

    draft["model_id"] = model_id
    draft["brand_name"] = row["brand"]
    draft["model_name"] = row["model"]
    return draft


class KnownIssueIn(BaseModel):
    severity: str = "medio"
    description: str = ""
    affected_years: Optional[str] = None
    fix_cost_estimate: Optional[str] = None


class EnrichSave(BaseModel):
    reliability_score: Optional[float] = None
    reliability_summary: Optional[str] = None
    maintenance_cost_year: Optional[int] = None
    year_start: Optional[int] = None
    year_end: Optional[int] = None
    engine_code: Optional[str] = None
    fuel_type: Optional[str] = None
    displacement_cc: Optional[int] = None
    power_hp: Optional[int] = None
    known_issues: list[KnownIssueIn] = []


@router.post("/models/{model_id}/enrich/save", dependencies=[Depends(_auth)])
def enrich_model_save(model_id: int, payload: EnrichSave, db: Session = Depends(get_db)):
    """Persist the (reviewed) reliability data: generation score + engine + issues."""
    exists = db.execute(
        text("SELECT id FROM vehicle_models WHERE id = :id"), {"id": model_id}
    ).scalar()
    if not exists:
        raise HTTPException(status_code=404, detail="Modelo não encontrado")

    score = payload.reliability_score
    ci_low = max(0.0, round((score or 0) - 1.0, 1)) if score is not None else None
    ci_high = min(10.0, round((score or 0) + 1.0, 1)) if score is not None else None

    try:
        # Generation: create one if none, marked llm_estimated (honestly "limited").
        gen_id = db.execute(
            text("SELECT id FROM generations WHERE model_id = :m ORDER BY id LIMIT 1"),
            {"m": model_id},
        ).scalar()
        gen_params = {
            "m": model_id, "ys": payload.year_start, "ye": payload.year_end,
            "sc": score, "lo": ci_low, "hi": ci_high,
        }
        if gen_id is None:
            db.execute(text("""
                INSERT INTO generations
                    (model_id, name, year_start, year_end,
                     reliability_score, reliability_ci_low, reliability_ci_high,
                     reliability_data_quality)
                VALUES (:m, 'Geração principal', :ys, :ye, :sc, :lo, :hi, 'limited')
            """), gen_params)
        else:
            gen_params["g"] = gen_id
            db.execute(text("""
                UPDATE generations SET
                    reliability_score = :sc,
                    reliability_ci_low = :lo,
                    reliability_ci_high = :hi,
                    reliability_data_quality = 'limited',
                    year_start = COALESCE(year_start, :ys),
                    year_end = COALESCE(year_end, :ye)
                WHERE id = :g
            """), gen_params)

        # Engine row carrying reliability + maintenance for _get_model_info.
        eng_id = db.execute(text("""
            INSERT INTO engines
                (model_id, code, fuel_type, displacement_cc, power_hp,
                 reliability_score, maintenance_cost_year)
            VALUES (:m, :code, :fuel, :disp, :pow, :sc, :maint)
            RETURNING id
        """), {
            "m": model_id,
            "code": (payload.engine_code or "")[:80] or None,
            "fuel": (payload.fuel_type or "")[:20] or None,
            "disp": payload.displacement_cc,
            "pow": payload.power_hp,
            "sc": score,
            "maint": payload.maintenance_cost_year,
        }).scalar()

        for iss in (payload.known_issues or [])[:6]:
            if not iss.description:
                continue
            db.execute(text("""
                INSERT INTO engine_issues
                    (engine_id, severity, description, affected_years, fix_cost_estimate, source)
                VALUES (:e, :sev, :desc, :ay, :fc, 'IA (estimativa)')
            """), {
                "e": eng_id,
                "sev": (iss.severity or "medio")[:20],
                "desc": iss.description[:500],
                "ay": (iss.affected_years or "")[:50] or None,
                "fc": (iss.fix_cost_estimate or "")[:50] or None,
            })

        db.commit()
        return {"status": "saved", "model_id": model_id, "engine_id": eng_id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Falha ao guardar: {e}")
