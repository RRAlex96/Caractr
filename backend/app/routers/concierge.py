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
    model_interest:  Optional[str]       = Field(None, max_length=200)
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

    background_tasks.add_task(_notify_operator, req, request_id, session_context)
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
