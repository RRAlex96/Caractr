"""
Funnel report — the Monday numbers.

    cd backend && python -m scripts.funnel_report            # last 7 and 30 days
    cd backend && python -m scripts.funnel_report --days 14

Read-only. Counts people (distinct anonymous browser ids), not events, for the
funnel steps; leaves out events flagged internal (a browser opened once with
?internal=1). AI cost comes from the usage stored with each fresh analysis.
"""
import argparse
import sys

from sqlalchemy import text

from app.db.database import SessionLocal   # loads backend/.env

_NOT_INTERNAL = "COALESCE((properties::jsonb)->>'internal', '') <> 'true'"


def funnel(db, days: int) -> dict:
    """Everything the report prints for one window, as plain numbers."""
    w = {"days": days}
    row = db.execute(text(f"""
        SELECT
          COUNT(DISTINCT anon_id) FILTER (WHERE event_name = 'page_view')              AS visitors,
          COUNT(DISTINCT anon_id) FILTER (WHERE event_name = 'selector_completed')     AS wizard_users,
          COUNT(DISTINCT anon_id) FILTER (WHERE event_name = 'analysis_completed')     AS analysing_users,
          COUNT(*) FILTER (WHERE event_name = 'analysis_completed')                    AS analyses,
          COUNT(*) FILTER (WHERE event_name = 'analysis_completed'
                           AND (properties::jsonb)->>'from_cache' = 'true')            AS analyses_cached,
          COUNT(*) FILTER (WHERE event_name = 'analysis_failed')                       AS failures,
          COUNT(*) FILTER (WHERE event_name = 'analysis_failed'
                           AND (properties::jsonb)->>'code' = 'fetch_failed')          AS fetch_blocked,
          COUNT(*) FILTER (WHERE event_name = 'analysis_started')                      AS attempts,
          COUNT(*) FILTER (WHERE event_name = 'analysis_shared')                       AS shares,
          COUNT(DISTINCT anon_id) FILTER (WHERE event_name = 'shared_analysis_viewed') AS share_visitors,
          COUNT(*) FILTER (WHERE event_name = 'shared_cta_clicked')                    AS share_cta_clicks,
          COUNT(DISTINCT anon_id) FILTER (WHERE event_name = 'pass_interest')          AS pass_interest,
          COUNT(DISTINCT anon_id) FILTER (WHERE event_name = 'sell_side_answer')       AS sell_answers,
          COUNT(DISTINCT anon_id) FILTER (WHERE event_name = 'sell_side_answer'
                           AND (properties::jsonb)->>'answer' <> 'no')                 AS has_car_to_sell,
          COUNT(DISTINCT anon_id) FILTER (WHERE event_name = 'seller_message_copied')  AS seller_messages
        FROM analytics_events
        WHERE created_at >= NOW() - make_interval(days => :days) AND {_NOT_INTERNAL}
    """), w).mappings().one()
    out = {"days": days, **row}

    out["sources"] = [dict(r) for r in db.execute(text(f"""
        SELECT COALESCE((properties::jsonb)->>'src', '(before tracking)') AS src,
               COUNT(DISTINCT anon_id) FILTER (WHERE event_name = 'page_view')          AS visitors,
               COUNT(DISTINCT anon_id) FILTER (WHERE event_name = 'analysis_completed') AS analysing_users
        FROM analytics_events
        WHERE created_at >= NOW() - make_interval(days => :days) AND {_NOT_INTERNAL}
        GROUP BY 1 HAVING COUNT(DISTINCT anon_id) FILTER (WHERE event_name = 'page_view') > 0
        ORDER BY 2 DESC, 3 DESC LIMIT 10
    """), w).mappings()]

    out["failure_reasons"] = [dict(r) for r in db.execute(text(f"""
        SELECT (properties::jsonb)->>'site' AS site, (properties::jsonb)->>'reason' AS reason, COUNT(*) AS n
        FROM analytics_events
        WHERE created_at >= NOW() - make_interval(days => :days) AND {_NOT_INTERNAL}
          AND event_name = 'analysis_failed'
        GROUP BY 1, 2 ORDER BY 3 DESC LIMIT 5
    """), w).mappings()]

    ai = db.execute(text("""
        SELECT COUNT(*) AS calls,
               COALESCE(SUM(((llm_analysis::jsonb)->'_llm_usage'->>'cost_usd')::numeric), 0)      AS cost_usd,
               COALESCE(AVG(((llm_analysis::jsonb)->'_llm_usage'->>'input_tokens')::numeric), 0)  AS avg_in,
               COALESCE(AVG(((llm_analysis::jsonb)->'_llm_usage'->>'output_tokens')::numeric
                          + ((llm_analysis::jsonb)->'_llm_usage'->>'thinking_tokens')::numeric), 0) AS avg_out
        FROM normalized_listings
        WHERE analysis_cached_at >= NOW() - make_interval(days => :days)
          AND (llm_analysis::jsonb) ? '_llm_usage'
    """), w).mappings().one()
    out["ai"] = {k: float(v) for k, v in ai.items()}
    return out


def _pct(part: int, whole: int) -> str:
    return f"{100 * part / whole:.0f}%" if whole else "-"


def render(f: dict) -> str:
    v, a = f["visitors"], f["analysing_users"]
    ai = f["ai"]
    lines = [
        f"=== Last {f['days']} days ===",
        f"Visitors                 {v}",
        f"Finished the wizard      {f['wizard_users']}  ({_pct(f['wizard_users'], v)} of visitors)",
        f"Analysed an ad           {a}  ({_pct(a, v)} of visitors)",
        f"  analyses run           {f['analyses']}  ({f['analyses_cached']} from cache)",
        f"  analyses failed        {f['failures']}  "
        f"({_pct(f['failures'], f['failures'] + f['analyses'])} of attempts)",
        f"  listing page not read  {f['fetch_blocked']}  "
        f"({_pct(f['fetch_blocked'], f['attempts'])} of attempts; the buyer is offered to paste the ad)",
        f"Shares                   {f['shares']}  ({_pct(f['shares'], f['analyses'])} of analyses)",
        f"  visitors from a share  {f['share_visitors']}  ({f['share_cta_clicks']} clicked through)",
        f"Buyer Pass interest      {f['pass_interest']}  ({_pct(f['pass_interest'], a)} of analysing users)",
        f"Message to seller used   {f['seller_messages']}  ({_pct(f['seller_messages'], a)} of analysing users)",
        f"Has a car to sell        {f['has_car_to_sell']} of {f['sell_answers']} who answered  "
        f"({_pct(f['has_car_to_sell'], f['sell_answers'])}; a quarter or more makes sell-side a phase-3 candidate)",
    ]
    if ai["calls"]:
        per_user = ai["cost_usd"] / a if a else 0
        lines += [
            f"AI analyses with cost    {ai['calls']:.0f}  total ${ai['cost_usd']:.2f}  "
            f"(${ai['cost_usd'] / ai['calls']:.4f} each; "
            f"avg {ai['avg_in']:.0f} tokens in, {ai['avg_out']:.0f} out)",
            f"  AI cost per analysing user  ${per_user:.3f}",
        ]
    else:
        lines.append("AI analyses with cost    none recorded yet")
    if f["sources"]:
        lines.append("Where visitors came from (visitors / analysed an ad):")
        lines += [f"  {s['src'][:44]:<44} {s['visitors']:>5} / {s['analysing_users']}" for s in f["sources"]]
    if f["failure_reasons"]:
        lines.append("Why analyses failed:")
        lines += [f"  {r['n']:>3}x  {r['site']}: {r['reason']}" for r in f["failure_reasons"]]
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--days", type=int, action="append", help="window in days (repeatable)")
    args = ap.parse_args()
    db = SessionLocal()
    try:
        db.execute(text("SET TRANSACTION READ ONLY"))
        for days in args.days or [7, 30]:
            print(render(funnel(db, days)).encode("ascii", "replace").decode())
            print()
    finally:
        db.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
