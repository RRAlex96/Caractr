"""
Caractr — Concierge / Lead Capture API v2
MVP: simple interest capture form. No tiers, no Stripe, no SLAs.

POST /api/concierge                     — submit interest + RGPD consent
DELETE /api/user/session/{session_id}   — GDPR Article 17: right to erasure
"""

import os
import uuid as _uuid
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List
from app.db.database import get_db

router = APIRouter(prefix="/api", tags=["concierge"])

OPERATOR_EMAIL = os.getenv("OPERATOR_EMAIL", "")
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")

# Allowed values — keep in sync with frontend FEEDBACK_TAGS and verdict tiers
_ALLOWED_FEEDBACK_TAGS = frozenset({
    "wrong_brand", "want_sportier", "want_comfort", "want_practical",
    "budget_off", "want_premium", "want_discreet", "want_bigger",
})
_ALLOWED_VERDICT_TIERS = frozenset({"forte", "razoavel", "cuidado", "evitar"})


class ConciergeRequest(BaseModel):
    session_id:      Optional[str]       = None
    name:            str                 = Field(..., min_length=1, max_length=200)
    email:           EmailStr
    model_interest:  Optional[str]       = Field(None, max_length=500)
    model_ids:       Optional[List[int]] = Field(default_factory=list)
    budget_max:      Optional[int]       = Field(None, ge=0, le=2_000_000)
    feedback_tags:   Optional[List[str]] = Field(default_factory=list)
    consent_caractr: bool                = False
    consent_dealer:  bool                = False
    listing_url:     Optional[str]       = Field(None, max_length=2000)
    listing_verdict: Optional[str]       = None

    @field_validator("session_id")
    @classmethod
    def validate_session_id(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        try:
            _uuid.UUID(v)
            return v
        except ValueError:
            return None  # silently drop malformed IDs

    @field_validator("feedback_tags")
    @classmethod
    def validate_tags(cls, v: Optional[List[str]]) -> List[str]:
        if not v:
            return []
        unknown = set(v) - _ALLOWED_FEEDBACK_TAGS
        if unknown:
            raise ValueError(f"Unknown feedback tags: {unknown}")
        return list(set(v))[:8]  # dedupe, cap

    @field_validator("listing_verdict")
    @classmethod
    def validate_verdict(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        if v not in _ALLOWED_VERDICT_TIERS:
            raise ValueError(f"Invalid verdict tier: {v!r}")
        return v


def _find_relevant_listings(db: Session, model_interest: str, budget_max: Optional[int]) -> list:
    """
    Quick DB lookup for cached listings matching the model of interest.
    Used to give the operator a head-start — no live scrape, just existing data.
    Returns up to 5 listings sorted by deal score.
    """
    if not model_interest:
        return []
    parts = model_interest.strip().split(None, 1)
    brand = parts[0] if parts else ""
    model = parts[1] if len(parts) > 1 else ""
    try:
        query = """
            SELECT nl.brand_name, nl.model_name, nl.year, nl.km, nl.price,
                   nl.deal_tier, nl.deal_score, nl.seller_type, rl.source_url
            FROM normalized_listings nl
            JOIN raw_listings rl ON rl.id = nl.raw_listing_id
            WHERE LOWER(nl.brand_name) LIKE LOWER(:brand_pat)
        """
        params: dict = {"brand_pat": f"%{brand}%"}
        if model:
            query += " AND LOWER(nl.model_name) LIKE LOWER(:model_pat)"
            params["model_pat"] = f"%{model}%"
        if budget_max:
            query += " AND (nl.price IS NULL OR nl.price <= :budget)"
            params["budget"] = budget_max
        query += " ORDER BY COALESCE(nl.deal_score, 0) DESC LIMIT 5"
        rows = db.execute(text(query), params).mappings().fetchall()
        return [dict(r) for r in rows]
    except Exception as e:
        print(f"[CONCIERGE] Listing lookup error: {e}")
        return []


def _build_profile_section(session_context: dict) -> str:
    lines = []
    try:
        from app.services.recommend_service import generate_profile_narrative
        profile   = session_context.get("profile") or {}
        answers   = session_context.get("answers") or {}
        narrative = generate_profile_narrative(profile, {}, answers)
        for key in ("priorities", "aversion", "identity", "context"):
            val = narrative.get(key)
            if val:
                label = {"priorities": "Prioridades", "aversion": "Aversão",
                         "identity": "Perfil", "context": "Contexto"}[key]
                lines.append(f"{label}: {val}")
    except Exception:
        pass
    return "\n".join(lines) if lines else "—"


def _build_models_section(session_context: dict) -> str:
    models = session_context.get("models") or []
    if not models:
        return "—"
    lines = []
    for i, m in enumerate(models[:5], 1):
        name = m.get("full_name") or m.get("model_name") or "?"
        markers = []
        if m.get("is_stretch"):  markers.append("stretch")
        if m.get("is_wildcard"): markers.append("wildcard")
        suffix = f" ({', '.join(markers)})" if markers else ""
        lines.append(f"{i}. {name}{suffix}")
    return "\n".join(lines)


async def _notify_operator(
    req: ConciergeRequest,
    request_id: int,
    session_context: Optional[dict] = None,
    relevant_listings: Optional[list] = None,
) -> None:
    """Plain text operator notification. Non-blocking, best-effort."""
    if not RESEND_API_KEY or not OPERATOR_EMAIL:
        return

    try:
        import httpx
        tags_str = ", ".join(req.feedback_tags) if req.feedback_tags else "—"

        dossier = ""
        if session_context:
            profile_section = _build_profile_section(session_context)
            models_section  = _build_models_section(session_context)
            dossier = f"PERFIL DO COMPRADOR:\n{profile_section}\n\nRECOMENDAÇÕES MOSTRADAS:\n{models_section}"

        listing_section = ""
        if req.listing_url:
            verdict_str = req.listing_verdict.upper() if req.listing_verdict else "?"
            listing_section = f"\nANÚNCIO ANALISADO: {req.listing_url}\nVeredicto: {verdict_str}"

        # Auto-found listings section
        listings_section = ""
        if relevant_listings:
            tier_label = {"forte": "✓ Forte", "razoavel": "~ Razoável", "cuidado": "⚠ Cuidado", "evitar": "✗ Evitar"}
            lines = ["ANÚNCIOS ENCONTRADOS NO MERCADO:"]
            for i, l in enumerate(relevant_listings, 1):
                tier = tier_label.get(l.get("deal_tier", ""), "")
                price = f"{int(l['price']):,} €" if l.get("price") else "?"
                km = f"{int(l['km']):,} km" if l.get("km") else "?"
                year = l.get("year") or "?"
                lines.append(
                    f"{i}. {l.get('brand_name','')} {l.get('model_name','')} {year} — {km} — {price} {tier}"
                )
                if l.get("source_url"):
                    lines.append(f"   {l['source_url']}")
            listings_section = "\n".join(lines)
        else:
            listings_section = "ANÚNCIOS: Nenhum encontrado em cache — pesquisa manual necessária."

        # NOTE: the operator email intentionally includes all fields disclosed in
        # the privacy policy under "Resend" (name, email, model, budget, tags,
        # session ID, profile summary, listing context).
        body_parts = [
            f"Nova solicitação concierge #{request_id}", "",
            f"Nome:      {req.name}",
            f"Email:     {req.email}",
            f"Modelo:    {req.model_interest or '—'}",
            f"Orçamento: {req.budget_max or '—'} EUR",
            f"Feedback:  {tags_str}",
            f"Dealer:    {'Sim' if req.consent_dealer else 'Não'}",
            f"Session:   {req.session_id or '—'}",
        ]
        if dossier:
            body_parts += ["", "─" * 40, dossier]
        if listing_section:
            body_parts += ["", listing_section.strip()]
        body_parts += ["", "─" * 40, listings_section]
        body_parts += ["", "Responde diretamente a este email para entrar em contacto."]

        async with httpx.AsyncClient() as client:
            await client.post(
                "https://api.resend.com/emails",
                headers={"Authorization": f"Bearer {RESEND_API_KEY}", "Content-Type": "application/json"},
                json={
                    "from":    "Caractr <noreply@caractr.pt>",
                    "to":      [OPERATOR_EMAIL],
                    "subject": f"[Caractr] Novo pedido #{request_id} — {req.name}",
                    "text":    "\n".join(body_parts),
                },
                timeout=10.0,
            )
    except Exception as e:
        print(f"[CONCIERGE] Operator email error: {e}")


async def _confirm_user(req: ConciergeRequest, session_context: Optional[dict] = None) -> None:
    """Personalised acknowledgement to the user. Non-blocking, best-effort."""
    if not RESEND_API_KEY:
        return
    try:
        import httpx
        first = req.name.split()[0] if req.name else ""
        priorities_line = ""
        if session_context:
            try:
                from app.services.recommend_service import generate_profile_narrative
                narrative = generate_profile_narrative(
                    session_context.get("profile") or {}, {},
                    session_context.get("answers") or {},
                )
                summary = narrative.get("summary")
                if summary:
                    priorities_line = f"\nSabemos que procuras um carro com {summary.lower()}"
            except Exception:
                pass

        body = f"""Olá {first},

Recebemos o teu pedido.{priorities_line} Já estamos a trabalhar nisso e entraremos em contacto em breve.

Podes pedir a eliminação dos teus dados a qualquer momento em privacidade@caractr.pt.

— Equipa Caractr""".strip()

        async with httpx.AsyncClient() as client:
            await client.post(
                "https://api.resend.com/emails",
                headers={"Authorization": f"Bearer {RESEND_API_KEY}", "Content-Type": "application/json"},
                json={
                    "from":    "Caractr <noreply@caractr.pt>",
                    "to":      [req.email],
                    "subject": "Recebemos o teu pedido — Caractr",
                    "text":    body,
                },
                timeout=10.0,
            )
    except Exception as e:
        print(f"[CONCIERGE] User confirmation error: {e}")


@router.post("/concierge")
async def submit_concierge(
    req: ConciergeRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Submit concierge interest.
    Requires consent_caractr=true (RGPD lawful basis: consent).
    """
    if not req.consent_caractr:
        raise HTTPException(
            status_code=422,
            detail="É necessário aceitar o contacto pela Caractr para continuar.",
        )

    # Session lookup — build buyer dossier for enriched emails
    session_context = None
    if req.session_id:
        try:
            import json
            row = db.execute(text("""
                SELECT profile_computed, models_shown, answers_raw
                FROM recommendation_sessions
                WHERE id = :sid
            """), {"sid": req.session_id}).mappings().fetchone()
            if row:
                session_context = {
                    "profile": json.loads(row["profile_computed"]) if row["profile_computed"] else None,
                    "models":  json.loads(row["models_shown"])     if row["models_shown"]     else None,
                    "answers": json.loads(row["answers_raw"])      if row["answers_raw"]      else None,
                }
        except Exception as e:
            print(f"[CONCIERGE] Session lookup error: {e}")

    import json as _json
    row = db.execute(text("""
        INSERT INTO concierge_requests
            (session_id, name, email, model_interest, budget_max,
             feedback_tags, consent_caractr, consent_dealer)
        VALUES
            (:session_id, :name, :email, :model_interest, :budget_max,
             :feedback_tags, :consent_caractr, :consent_dealer)
        RETURNING id
    """), {
        "session_id":      req.session_id,
        "name":            req.name,
        "email":           str(req.email),
        "model_interest":  req.model_interest,
        "budget_max":      req.budget_max,
        "feedback_tags":   _json.dumps(req.feedback_tags or []),
        "consent_caractr": req.consent_caractr,
        "consent_dealer":  req.consent_dealer,
    })
    db.commit()
    request_id = row.scalar()

    # Auto-search: find matching listings from DB cache to give operator a head start
    relevant_listings = _find_relevant_listings(db, req.model_interest or "", req.budget_max)

    background_tasks.add_task(_notify_operator, req, request_id, session_context, relevant_listings)
    background_tasks.add_task(_confirm_user, req, session_context)

    return {"status": "ok", "request_id": request_id}


# ── GDPR: Right to Erasure (Article 17) ───────────────────────────────────────

@router.delete("/user/session/{session_id}")
def delete_session_data(session_id: str, db: Session = Depends(get_db)):
    """
    GDPR Article 17 — right to erasure.
    Deletes all personal data tied to the given session ID:
      - recommendation_sessions (profile + answers)
      - concierge_requests (name, email, model, budget)

    Analytics events are keyed only by session UUID (no PII) and are
    retained per the privacy policy retention schedule (24 months).

    The session_id comes from the user's own localStorage — they control it.
    """
    try:
        _uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato de session_id inválido.")

    sessions_deleted = db.execute(text("""
        WITH del AS (
            DELETE FROM recommendation_sessions WHERE id = :sid RETURNING id
        ) SELECT COUNT(*) FROM del
    """), {"sid": session_id}).scalar()

    concierge_deleted = db.execute(text("""
        WITH del AS (
            DELETE FROM concierge_requests WHERE session_id = :sid RETURNING id
        ) SELECT COUNT(*) FROM del
    """), {"sid": session_id}).scalar()

    db.commit()

    return {
        "status": "deleted",
        "session_id": session_id,
        "sessions_deleted": sessions_deleted,
        "concierge_requests_deleted": concierge_deleted,
    }
