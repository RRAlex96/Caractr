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


def get_dealbreakers(db: Session, model_id: int | None) -> dict:
    """Return the structured deal-breaker payload for a model (recalls + critical
    known failures). Always returns the full shape, empty when nothing serious."""
    if not model_id:
        return dict(_EMPTY)

    # ── Official recalls (high-severity only) ────────────────────────────────
    recalls: list[dict] = []
    seen: set = set()
    # Severities are fixed internal constants (not user input) — inlined so the
    # IN-list is a plain SQL literal, no bind-expansion needed.
    sev_list = ", ".join(f"'{s}'" for s in _DEALBREAKER_RECALL_SEVERITIES)
    rows = db.execute(text(f"""
        SELECT re.source, re.source_url, re.severity, re.observed_month, re.payload
        FROM reliability_evidence re
        JOIN generations g ON g.id = re.generation_id
        WHERE g.model_id = :mid
          AND re.evidence_type IN ('recall', 'safety_gate')
          AND lower(coalesce(re.severity, '')) IN ({sev_list})
        ORDER BY (lower(re.severity) = 'serious') DESC, re.observed_month DESC NULLS LAST
        LIMIT 12
    """), {"mid": model_id}).mappings().fetchall()

    for r in rows:
        p = _as_dict(r["payload"])
        title = (p.get("title") or p.get("component") or p.get("model_raw")
                 or "Recall de segurança")
        desc = (p.get("description") or p.get("summary") or p.get("consequence")
                or p.get("issue") or p.get("risk") or "")
        date = (p.get("pub_date") or p.get("report_date")
                or (r["observed_month"].isoformat() if r["observed_month"] else None))
        key = (str(title)[:80], str(desc)[:80])
        if key in seen:
            continue
        seen.add(key)
        url = r["source_url"]
        recalls.append({
            "title": str(title)[:160],
            "description": str(desc)[:400],
            "severity": (r["severity"] or "").lower(),
            "source": _source_label(r["source"]),
            "source_url": url if isinstance(url, str) and url.startswith("http") else None,
            "date": date,
        })
        if len(recalls) >= 6:
            break

    # ── Critical known failures (curator deal-breaker tier) ──────────────────
    critical: list[dict] = []
    crows = db.execute(text("""
        SELECT DISTINCT ei.description, ei.affected_years,
               ei.fix_cost_estimate, ei.source
        FROM engine_issues ei
        JOIN engines e ON e.id = ei.engine_id
        WHERE e.model_id = :mid AND lower(ei.severity) = 'critico'
        LIMIT 6
    """), {"mid": model_id}).mappings().fetchall()

    for c in crows:
        if not c["description"]:
            continue
        critical.append({
            "description": str(c["description"])[:400],
            "affected_years": c["affected_years"],
            "fix_cost_estimate": c["fix_cost_estimate"],
            "source": c["source"] or "Investigação",
        })

    count = len(recalls) + len(critical)
    return {
        "has_dealbreaker": count > 0,
        "recall_count": len(recalls),
        "critical_issue_count": len(critical),
        "recalls": recalls,
        "critical_issues": critical,
    }
