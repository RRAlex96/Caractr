"""
Deal-breakers — the loud "would this car put a buyer off?" signal.

Two authoritative inputs, surfaced together but always honest about where each
came from (every item carries its source, recalls carry a citation URL):

  1. Official recalls  — reliability_evidence rows from EU Safety Gate / NHTSA /
     KBA, high-severity only. The defect text is persisted by the scrapers
     (Phase A) so we can show *why*, not just that something exists.
  2. Critical known failures — engine_issues with severity 'critico', the
     deal-breaker tier the curator agent researches (timing chains, DSG
     mechatronics, oil consumption, DPF/EGR, structural/safety).

This never excludes a car — the product shows it as a prominent warning and
lets the buyer decide. Recall matching upstream is deliberately high-precision,
so a shown recall is one we're confident belongs to this model.
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
    "us_recall_count": 0,
    "us_recalls": [],
}

# US recalls (NHTSA) cover US-spec cars — engines, emissions kit and suppliers
# often differ from the European version — so they never drive the loud
# deal-breaker on their own. They're listed separately, with that caveat, and
# still feed the reliability score.
_US_SOURCES = {"nhtsa"}


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


def get_dealbreakers(db: Session, model_id: int | None, year: int | None = None) -> dict:
    """Return the structured deal-breaker payload for a model (recalls + critical
    known failures). Always returns the full shape, empty when nothing serious.

    `year` (the listing's model year, when known) filters out recalls and
    failures for other production periods — a 2020 car must not be warned
    about a recall that only affects 2024-2026 builds."""
    if not model_id:
        return dict(_EMPTY)

    # ── Official recalls (high-severity only) ────────────────────────────────
    recalls: list[dict] = []      # EU-official (Safety Gate / KBA): the loud tier
    us_recalls: list[dict] = []   # NHTSA: shown separately, never loud on its own
    seen: set = set()
    # Severities are fixed internal constants (not user input) — inlined so the
    # IN-list is a plain SQL literal, no bind-expansion needed.
    sev_list = ", ".join(f"'{s}'" for s in _DEALBREAKER_RECALL_SEVERITIES)
    rows = db.execute(text(f"""
        SELECT re.source, re.source_url, re.severity, re.observed_month, re.payload,
               g.year_start, g.year_end
        FROM reliability_evidence re
        JOIN generations g ON g.id = re.generation_id
        WHERE g.model_id = :mid
          AND re.evidence_type IN ('recall', 'safety_gate')
          AND lower(coalesce(re.severity, '')) IN ({sev_list})
        ORDER BY (lower(re.severity) = 'serious') DESC, re.observed_month DESC NULLS LAST
        LIMIT 80
    """), {"mid": model_id}).mappings().fetchall()

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
        is_us = (r["source"] or "").lower() in _US_SOURCES
        target, cap = (us_recalls, 4) if is_us else (recalls, 6)
        if len(target) >= cap:
            continue
        url = r["source_url"]
        target.append({
            "title": str(title)[:160],
            "description": str(desc)[:400],
            "severity": (r["severity"] or "").lower(),
            "source": _source_label(r["source"]),
            "source_url": url if isinstance(url, str) and url.startswith("http") else None,
            "date": date_,
            "affected_years": _years_label(lo, hi),
        })
        if len(recalls) >= 6 and len(us_recalls) >= 4:
            break

    # ── Critical known failures (curator deal-breaker tier) ──────────────────
    critical: list[dict] = []
    crows = db.execute(text("""
        SELECT DISTINCT ei.description, ei.affected_years,
               ei.fix_cost_estimate, ei.source
        FROM engine_issues ei
        JOIN engines e ON e.id = ei.engine_id
        WHERE e.model_id = :mid AND lower(ei.severity) = 'critico'
        LIMIT 30
    """), {"mid": model_id}).mappings().fetchall()

    for c in crows:
        if not c["description"]:
            continue
        span = _parse_affected_years(c["affected_years"])
        if span and not _applies(year, *span):
            continue
        critical.append({
            "description": str(c["description"])[:400],
            "affected_years": c["affected_years"],
            "fix_cost_estimate": c["fix_cost_estimate"],
            "source": c["source"] or "Investigação",
        })
        if len(critical) >= 6:
            break

    count = len(recalls) + len(critical)
    return {
        "has_dealbreaker": count > 0,
        "recall_count": len(recalls),
        "critical_issue_count": len(critical),
        "recalls": recalls,
        "critical_issues": critical,
        "us_recall_count": len(us_recalls),
        "us_recalls": us_recalls,
    }
