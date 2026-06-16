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
