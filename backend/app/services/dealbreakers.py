"""
Deal-breakers and the "before you buy" checklist.

Two inputs, deliberately treated differently:

  1. Critical known failures — engine_issues with severity 'critico' (timing
     belts in oil, DSG mechatronics, chronic oil consumption...). These are the
     only thing that raises the loud deal-breaker (`has_dealbreaker`): a chronic,
     expensive weakness of a specific engine or gearbox is a reason to pick a
     different version.
  2. Official EU recalls (Safety Gate), high-severity only. A recall is the
     manufacturer fixing a defect for free, often for one production batch —
     a checklist item ("confirm it was done"), not a verdict on the model. They
     are returned for the listing-level checklist and never raise the alarm.
     Airbag-inflator recalls are flagged `priority`: on an older car that
     missed the campaign they are genuinely dangerous.

US (NHTSA) recalls are not returned at all: they cover US-spec cars and we
can't say whether they apply in Europe. They still feed the reliability score.

This never excludes a car. Recall matching upstream is deliberately
high-precision, so a shown recall is one we're confident belongs to this model.
"""
import json
import re
from datetime import date

from sqlalchemy import text
from sqlalchemy.orm import Session

# Recall severities that rise to a "loud warning". Lower-severity recalls still
# feed the reliability score; they just don't shout at the buyer.
_DEALBREAKER_RECALL_SEVERITIES = ("serious", "high")

_SOURCE_LABELS = {
    "eu_safety_gate": "UE Safety Gate",
    "nhtsa": "NHTSA (EUA)",
    "kba_de": "KBA (Alemanha)",
}

_EMPTY = {
    "has_dealbreaker": False,
    "recall_count": 0,
    "critical_issue_count": 0,
    "recalls": [],
    "critical_issues": [],
}

# Sources shown to buyers. NHTSA (US-spec cars) is left out on purpose — see
# the module docstring; it still feeds the reliability score.
_SHOWN_RECALL_SOURCES = ("eu_safety_gate", "kba_de")

# Airbag inflators that degrade with age (the Takata/ARC family of defects):
# the one recall type worth stressing on an older car.
_AIRBAG = re.compile(r"airbag", re.I)
_INFLATOR = re.compile(r"insufl|propuls|inflat|gerador de g[aá]s|deterior|degrad", re.I)


def _clip(s: str, n: int) -> str:
    """Cut at a word boundary with an ellipsis — never mid-word."""
    s = s.strip()
    if len(s) <= n:
        return s
    return s[:n].rsplit(" ", 1)[0].rstrip(",;:") + "…"


def _is_priority(title: str, desc: str) -> bool:
    text_ = f"{title} {desc}"
    return bool(_AIRBAG.search(text_) and _INFLATOR.search(text_))


def _risk_label(title: str) -> str | None:
    """Safety Gate titles read '<Model>: Risco de ferimentos, Risco de incêndio'.
    The model is redundant on the page; the risk part is a useful tag."""
    if ":" not in title:
        return None
    risk = title.split(":", 1)[1].strip()
    return risk or None


def merge_known_issues(payload: dict | None, matched: list[dict]) -> dict:
    """Fold curated, listing-matched engine issues (known_issues.match_listing)
    into a deal-breaker payload. Curated 'critico' entries lead the red list;
    'alto' entries become `watch_items` — amber "what to check", never red."""
    from app.services.known_issues import to_payload
    out = {**_EMPTY, **(payload or {})}
    crit = [to_payload(i) for i in matched if i["severity"] == "critico"]
    watch = [to_payload(i) for i in matched if i["severity"] != "critico"]
    out["critical_issues"] = crit + list(out.get("critical_issues") or [])
    out["critical_issue_count"] = len(out["critical_issues"])
    out["has_dealbreaker"] = out["critical_issue_count"] > 0
    out["watch_items"] = watch
    return out


def _source_label(source: str) -> str:
    return _SOURCE_LABELS.get((source or "").lower(), source or "Fonte oficial")


def _as_dict(payload) -> dict:
    """reliability_evidence.payload is JSONB (usually already a dict); be tolerant."""
    if isinstance(payload, dict):
        return payload
    if isinstance(payload, str):
        try:
            return json.loads(payload)
        except Exception:
            return {}
    return {}


def _component_title(component) -> str | None:
    """NHTSA component codes ('SERVICE BRAKES, HYDRAULIC:POWER ASSIST:...') →
    a readable title ('Recall: service brakes')."""
    if not component:
        return None
    first = str(component).split(":")[0].split(",")[0].strip().lower()
    return f"Recall: {first}" if first else None


def _recall_years(payload: dict, gen_start, gen_end) -> tuple[int | None, int | None]:
    """Production years a recall applies to. Safety Gate stores the real
    per-model production range ("years"); NHTSA rows are de-duplicated per
    campaign, so their single "year" is just the first one seen — for those,
    and anything else, fall back to the matched generation's range."""
    ys = payload.get("years")
    if isinstance(ys, list) and ys:
        ys = [int(y) for y in ys if str(y).isdigit()]
        if ys:
            return min(ys), max(ys)
    return gen_start, gen_end


def _parse_affected_years(s) -> tuple[int | None, int | None] | None:
    """'2010-2014' → (2010, 2014); '2020+' → (2020, None); unparseable → None."""
    ys = [int(y) for y in re.findall(r"\b(19[89]\d|20[0-3]\d)\b", s or "")]
    if not ys:
        return None
    if "+" in (s or "") and len(ys) == 1:
        return ys[0], None
    return min(ys), max(ys)


def _applies(year: int | None, lo: int | None, hi: int | None) -> bool:
    """Does a car from `year` fall in [lo, hi]? Unknown bounds never exclude."""
    if year is None or lo is None:
        return True
    return lo <= year <= (hi or date.today().year)


def _years_label(lo, hi) -> str | None:
    if lo is None:
        return None
    if hi is None or hi >= date.today().year:
        return f"{lo}+"
    return f"{lo}-{hi}" if hi != lo else str(lo)


def get_dealbreakers(db: Session, model_id: int | None, year: int | None = None,
                     include_recalls: bool = True) -> dict:
    """Return the deal-breaker payload for a model: critical known failures
    (the only thing that sets `has_dealbreaker`) and, for the checklist, EU
    recalls. Always returns the full shape, empty when nothing applies.

    `year` (the listing's model year, when known) filters out recalls and
    failures for other production periods — a 2020 car must not be told about
    a recall that only affects 2024-2026 builds. `include_recalls=False` skips
    them (recommendation cards: the year is unknown, so a model-wide recall
    list would be noise)."""
    if not model_id:
        return dict(_EMPTY)

    recalls: list[dict] = []
    seen: set = set()
    # Severities/sources are fixed internal constants (not user input) — inlined
    # so the IN-lists are plain SQL literals, no bind-expansion needed.
    sev_list = ", ".join(f"'{s}'" for s in _DEALBREAKER_RECALL_SEVERITIES)
    src_list = ", ".join(f"'{s}'" for s in _SHOWN_RECALL_SOURCES)
    rows = db.execute(text(f"""
        SELECT re.source, re.source_url, re.severity, re.observed_month, re.payload,
               g.year_start, g.year_end
        FROM reliability_evidence re
        JOIN generations g ON g.id = re.generation_id
        WHERE g.model_id = :mid
          AND re.evidence_type IN ('recall', 'safety_gate')
          AND lower(coalesce(re.source, '')) IN ({src_list})
          AND lower(coalesce(re.severity, '')) IN ({sev_list})
        ORDER BY (lower(re.severity) = 'serious') DESC, re.observed_month DESC NULLS LAST
        LIMIT 80
    """), {"mid": model_id}).mappings().fetchall() if include_recalls else []

    for r in rows:
        p = _as_dict(r["payload"])
        lo, hi = _recall_years(p, r["year_start"], r["year_end"])
        if not _applies(year, lo, hi):
            continue
        # Portuguese first (Safety Gate publishes official translations), then
        # the English original, then whatever the source provides.
        title = (p.get("title_pt") or p.get("title") or _component_title(p.get("component"))
                 or p.get("model_raw") or "Recall de segurança")
        desc = (p.get("description_pt") or p.get("description") or p.get("summary")
                or p.get("consequence") or p.get("issue") or p.get("risk") or "")
        date_ = (p.get("pub_date") or p.get("report_date")
                 or (r["observed_month"].isoformat() if r["observed_month"] else None))
        key = (str(title)[:80], str(desc)[:80])
        if key in seen:
            continue
        seen.add(key)
        url = r["source_url"]
        title, desc = str(title), str(desc)
        recalls.append({
            "title": _clip(title, 160),
            "description": _clip(desc, 420),
            "risk": _risk_label(title),
            "priority": _is_priority(title, desc),
            "severity": (r["severity"] or "").lower(),
            "source": _source_label(r["source"]),
            "source_url": url if isinstance(url, str) and url.startswith("http") else None,
            "date": date_,
            "affected_years": _years_label(lo, hi),
        })
    # Airbag-inflator campaigns first (the ones that matter on an older car),
    # then cap — sorting before the cap so one is never cut by newer rows.
    recalls.sort(key=lambda x: not x["priority"])
    recalls = recalls[:6]

    # ── Critical known failures (the deal-breaker tier) ──────────────────────
    critical: list[dict] = []
    crows = db.execute(text("""
        SELECT DISTINCT e.code AS engine, ei.description, ei.affected_years,
               ei.fix_cost_estimate, ei.source
        FROM engine_issues ei
        JOIN engines e ON e.id = ei.engine_id
        WHERE e.model_id = :mid AND lower(ei.severity) = 'critico'
          -- rows the AI curator wrote with no source to check are never
          -- passed on as known faults (see curator_agent._issue_source_label)
          AND COALESCE(ei.source, '') NOT LIKE 'IA (%sem fontes%'
        LIMIT 30
    """), {"mid": model_id}).mappings().fetchall()

    for c in crows:
        if not c["description"]:
            continue
        span = _parse_affected_years(c["affected_years"])
        if span and not _applies(year, *span):
            continue
        critical.append({
            "engine": c["engine"],
            "description": _clip(str(c["description"]), 420),
            "affected_years": c["affected_years"],
            "fix_cost_estimate": c["fix_cost_estimate"],
            "source": c["source"] or "Investigação",
        })
        if len(critical) >= 6:
            break

    return {
        # Only a chronic, expensive known failure is a deal-breaker. Recalls
        # are free fixes — they go on the checklist, never the alarm.
        "has_dealbreaker": len(critical) > 0,
        "recall_count": len(recalls),
        "critical_issue_count": len(critical),
        "recalls": recalls,
        "critical_issues": critical,
    }
