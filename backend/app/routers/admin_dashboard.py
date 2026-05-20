"""
Caractr — Admin Dashboard API
Single endpoint returning all analytics metrics for the admin dashboard.
Protected by X-Admin-Token header.
"""

import os
import hmac
import json
from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.database import get_db

router = APIRouter(prefix="/api/admin", tags=["admin"])

_PERIOD_MAP = {"7d": 7, "30d": 30, "90d": 90}


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
