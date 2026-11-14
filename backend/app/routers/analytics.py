"""
Caractr Analytics API v4.1
Endpoint: POST /api/events — fire-and-forget client-side event ingestion.
"""

import uuid as _uuid
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Any
from app.db.database import get_db
import json

router = APIRouter(prefix="/api", tags=["analytics"])

# Whitelist of known event names — prevents arbitrary strings from being stored
_KNOWN_EVENTS = frozenset({
    # Wizard / selector flow (current names)
    "selector_started", "selector_step_completed", "selector_completed",
    # Legacy wizard names (backwards compat for cached browser sessions)
    "wizard_started", "wizard_completed", "wizard_step",
    # Results
    "results_viewed", "recommend_loaded",
    "model_clicked", "model_expanded", "model_analysis_started",
    # Analysis
    "ad_analysis_requested",
    "analysis_started", "analysis_completed", "analysis_failed", "analysis_shared",
    # Share loop: a visit to a shared analysis, and its click through to /analisar
    "shared_analysis_viewed", "shared_cta_clicked",
    # Buyer Pass: interest recorded before checkout exists
    "pass_interest",
    # The message to the seller, generated from the analysis
    "seller_message_copied",
    "analysis_feedback", "analysis_feedback_reason",
    # Trust panel
    "trust_panel_viewed", "trust_panel_feedback",
    # Shortlist / concierge
    "shortlist_added", "watchlist_opt_in",
    "concierge_interest", "concierge_opened", "concierge_submitted",
    # Feedback
    "feedback_submitted",
    # Profile
    "profile_shown", "quick_profile_completed",
    # Session
    "return_visit", "dual_verdict_shown",
    # Navigation
    "page_view",
})


class EventPayload(BaseModel):
    event_name: str  = Field(..., max_length=100)
    session_id: Optional[str] = None
    anon_id:    Optional[str] = Field(None, max_length=100)
    properties: Optional[dict[str, Any]] = None

    @field_validator("event_name")
    @classmethod
    def validate_event_name(cls, v: str) -> str:
        # Allow known events; for unknown ones, normalise to "unknown_event"
        # so we never silently store arbitrary client-sent strings as event types.
        return v if v in _KNOWN_EVENTS else "unknown_event"

    @field_validator("session_id", "anon_id")
    @classmethod
    def validate_uuid_field(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v == "":
            return None
        try:
            _uuid.UUID(v)
            return v
        except ValueError:
            return None  # silently drop malformed IDs

    @field_validator("properties")
    @classmethod
    def strip_pii(cls, v: Optional[dict]) -> Optional[dict]:
        """
        Remove any keys that look like PII from event properties.
        Analytics events should never contain name, email, or phone.
        """
        if not v:
            return v
        pii_keys = {"email", "name", "phone", "full_name", "user_email"}
        return {k: val for k, val in v.items() if k.lower() not in pii_keys}


@router.post("/events", status_code=204)
def track_event(payload: EventPayload, db: Session = Depends(get_db)):
    """
    Ingest a single analytics event.
    Returns 204 No Content — clients fire-and-forget, never await this.
    """
    try:
        db.execute(text("""
            INSERT INTO analytics_events (session_id, anon_id, event_name, properties)
            VALUES (:session_id, :anon_id, :event_name, :properties)
        """), {
            "session_id": payload.session_id or None,
            "anon_id":    payload.anon_id or None,
            "event_name": payload.event_name,
            "properties": json.dumps(payload.properties or {}),
        })
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"[ANALYTICS] Event failed: {e}")
    return None
