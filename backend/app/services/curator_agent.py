"""
Curator agent — keeps the model catalogue's reliability data filled.

WHY THIS IS AN AGENT (and not just a script):
  - It has a GOAL: no model left without reliability data.
  - It runs a LOOP, and each step it DECIDES what to do from what it observed.
  - It uses TOOLS: read the catalogue, research a model, validate, write.
  - It ROUTES its own output by confidence: auto-save when sure, otherwise leave
    the model in the pending list for a human to review (human-in-the-loop).

The LLM is only the *reasoning engine* inside one tool (`research_model`). The
"agent" is everything around it — the loop, the tools, the validation, and the
decisions. That orchestration is the engineering.

Run it on demand (cheap, no always-on infra):
    cd backend && DATABASE_URL=… python -m scripts.curate
"""
from typing import Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.services.llm_client import generate_json, llm_available, QuotaExhaustedError

# How sure the agent must be to write without a human looking. Below this, the
# model is left in the pending list for one-click review in the admin.
AUTOSAVE_CONFIDENCE = 0.75


# ── TOOL 1 · perceive: which models still need reliability data ──────────────
def find_gaps(db: Session, limit: int = 10) -> list[dict]:
    """Return models with no reliability score yet, most-analysed first — so the
    agent spends its effort where real users actually land."""
    rows = db.execute(text("""
        SELECT vm.id, b.name AS brand, vm.name AS model
        FROM vehicle_models vm
        JOIN brands b ON b.id = vm.brand_id
        WHERE NOT EXISTS (
            SELECT 1 FROM generations g
            WHERE g.model_id = vm.id AND g.reliability_score IS NOT NULL
        )
        ORDER BY (SELECT COUNT(*) FROM normalized_listings n WHERE n.model_id = vm.id) DESC,
                 vm.id DESC
        LIMIT :limit
    """), {"limit": limit}).mappings().fetchall()
    return [dict(r) for r in rows]


# ── TOOL 2 · act/reason: research one model into a structured draft ──────────
def research_model(brand: str, model: str) -> dict:
    """
    Ask the LLM to produce structured reliability data for a model, PLUS a
    self-assessed confidence (0–1) — that confidence is what lets the agent
    decide whether a human needs to look.

    This is "closed-book": the model answers from training knowledge. The next
    upgrade is to give it a web-search tool so it researches live sources
    ("grounding") — same function signature, better sourcing. The agent loop
    around it doesn't change, which is the whole point of a clean tool boundary.
    """
    prompt = f"""És um especialista em fiabilidade de automóveis usados no mercado português.
Avalia o modelo: {brand} {model}.

Responde APENAS com JSON válido:
{{
  "reliability_score": número 0-10 (10 = extremamente fiável),
  "reliability_summary": "1-2 frases honestas sobre a fiabilidade geral",
  "maintenance_cost_year": custo médio anual de manutenção em euros (inteiro),
  "year_start": ano de início de produção (inteiro),
  "year_end": ano de fim ou null se ainda em produção,
  "engine_code": "código do motor mais comum ou null",
  "fuel_type": "diesel|gasolina|híbrido|elétrico",
  "displacement_cc": cilindrada típica em cm3 (inteiro) ou null,
  "power_hp": potência típica em cv (inteiro) ou null,
  "known_issues": [
    {{"severity": "alto|medio|baixo", "description": "problema concreto", "affected_years": "ex: '2015-2018'", "fix_cost_estimate": "ex: '€800-1500'"}}
  ],
  "confidence": número 0-1 — quão SEGURO estás desta informação para ESTE modelo
                específico (alto só para modelos que conheces bem; baixo se é raro
                ou estás a adivinhar)
}}
known_issues: máximo 5, só problemas REAIS e conhecidos. Sê específico e honesto."""
    draft = generate_json(prompt, max_tokens=1400)
    return draft


# ── TOOL 3 · guard: deterministic sanity check (never trust raw LLM output) ──
def validate_draft(draft: dict) -> tuple[bool, list[str]]:
    """Catch obviously-bad drafts before they ever reach the DB. Deterministic,
    not another LLM call — the guard must be trustworthy."""
    issues: list[str] = []
    score = draft.get("reliability_score")
    if not isinstance(score, (int, float)) or not (0 <= score <= 10):
        issues.append(f"reliability_score out of range: {score}")
    maint = draft.get("maintenance_cost_year")
    if maint is not None and (not isinstance(maint, (int, float)) or not (50 <= maint <= 8000)):
        issues.append(f"maintenance_cost_year implausible: {maint}")
    ys = draft.get("year_start")
    if ys is not None and (not isinstance(ys, int) or not (1950 <= ys <= 2030)):
        issues.append(f"year_start implausible: {ys}")
    conf = draft.get("confidence")
    if not isinstance(conf, (int, float)) or not (0 <= conf <= 1):
        issues.append(f"confidence out of range: {conf}")
    if not isinstance(draft.get("known_issues", []), list):
        issues.append("known_issues is not a list")
    return (len(issues) == 0, issues)


# ── TOOL 4 · act: write a validated draft into the catalogue ─────────────────
def save_reliability(db: Session, model_id: int, draft: dict) -> None:
    """Persist the reviewed/validated draft: a generation score + an engine row +
    known issues. Tagged as AI-estimated for honesty, exactly like the admin
    'enrich' flow — the agent just does it at scale."""
    score = draft.get("reliability_score")
    ci_low = max(0.0, round((score or 0) - 1.0, 1)) if score is not None else None
    ci_high = min(10.0, round((score or 0) + 1.0, 1)) if score is not None else None

    gen_id = db.execute(
        text("SELECT id FROM generations WHERE model_id = :m ORDER BY id LIMIT 1"),
        {"m": model_id},
    ).scalar()
    params = {"m": model_id, "ys": draft.get("year_start"), "ye": draft.get("year_end"),
              "sc": score, "lo": ci_low, "hi": ci_high}
    if gen_id is None:
        db.execute(text("""
            INSERT INTO generations
                (model_id, name, year_start, year_end,
                 reliability_score, reliability_ci_low, reliability_ci_high, reliability_data_quality)
            VALUES (:m, 'Geração principal', :ys, :ye, :sc, :lo, :hi, 'limited')
        """), params)
    else:
        params["g"] = gen_id
        db.execute(text("""
            UPDATE generations SET reliability_score = :sc, reliability_ci_low = :lo,
                reliability_ci_high = :hi, reliability_data_quality = 'limited',
                year_start = COALESCE(year_start, :ys), year_end = COALESCE(year_end, :ye)
            WHERE id = :g
        """), params)

    eng_id = db.execute(text("""
        INSERT INTO engines (model_id, code, fuel_type, displacement_cc, power_hp,
                             reliability_score, maintenance_cost_year)
        VALUES (:m, :code, :fuel, :disp, :pow, :sc, :maint) RETURNING id
    """), {
        "m": model_id, "code": (draft.get("engine_code") or "")[:80] or None,
        "fuel": (draft.get("fuel_type") or "")[:20] or None,
        "disp": draft.get("displacement_cc"), "pow": draft.get("power_hp"),
        "sc": score, "maint": draft.get("maintenance_cost_year"),
    }).scalar()

    for iss in (draft.get("known_issues") or [])[:6]:
        if not isinstance(iss, dict) or not iss.get("description"):
            continue
        db.execute(text("""
            INSERT INTO engine_issues (engine_id, severity, description, affected_years, fix_cost_estimate, source)
            VALUES (:e, :sev, :desc, :ay, :fc, 'IA (curator)')
        """), {
            "e": eng_id, "sev": (iss.get("severity") or "medio")[:20],
            "desc": str(iss["description"])[:500],
            "ay": (iss.get("affected_years") or "")[:50] or None,
            "fc": (iss.get("fix_cost_estimate") or "")[:50] or None,
        })
    db.commit()


# ── THE AGENT LOOP ───────────────────────────────────────────────────────────
def run_curator(db: Session, limit: int = 10,
                autosave_confidence: float = AUTOSAVE_CONFIDENCE) -> dict:
    """
    Work toward the goal (fill reliability gaps), one model at a time, deciding
    what to do with each result. Returns a report of what it did.
    """
    if not llm_available():
        return {"error": "LLM unavailable — set GEMINI_API_KEY"}

    gaps = find_gaps(db, limit)
    report = {"gaps": len(gaps), "researched": 0, "saved": 0, "queued": 0, "errors": 0, "log": []}

    for m in gaps:
        label = f"{m['brand']} {m['model']}"
        try:
            draft = research_model(m["brand"], m["model"])          # TOOL: reason
            report["researched"] += 1
            ok, issues = validate_draft(draft)                      # GUARD
            if not ok:
                report["queued"] += 1
                report["log"].append(f"review  {label}: failed validation ({'; '.join(issues)})")
                continue
            conf = float(draft.get("confidence", 0))
            if conf >= autosave_confidence:                         # DECISION: autonomy dial
                save_reliability(db, m["id"], draft)                # TOOL: write
                report["saved"] += 1
                report["log"].append(f"saved   {label}: score {draft.get('reliability_score')} (conf {conf:.2f})")
            else:
                report["queued"] += 1                               # human-in-the-loop
                report["log"].append(f"review  {label}: low confidence {conf:.2f} — left for human")
        except QuotaExhaustedError:
            report["log"].append("STOP: LLM quota exhausted — run again later")
            break                                                   # resource-aware termination
        except Exception as e:
            report["errors"] += 1
            report["log"].append(f"error   {label}: {type(e).__name__}: {e}")

    return report
