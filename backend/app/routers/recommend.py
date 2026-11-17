"""
Caractr Recommendation API v4.0
Endpoints: /recommend, /dream-cars, /feedback, /profile-dimensions
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel, model_validator
from typing import Optional, Union
from app.db.database import get_db
from app.services.recommend_service import (
    apply_refinement, get_alternative_recommendations, get_dream_cars, get_recommendations, log_feedback,
)
from sqlalchemy import text
import json

router = APIRouter(prefix="/api", tags=["recommend"])


# ── Request models ──

class WizardAnswers(BaseModel):
    """V5: Accepts both string card choices (V5) and float slider values (V4 backward compat)."""
    p1_context:       str   = "misto"
    p2_relationship:  Union[str, float] = "gosto_conduzir"
    p3_driving_style: Union[str, float] = "confortavel_com_alma"
    p4_risk:          Optional[Union[str, float]] = None   # V5 derives from P3; V4 sends explicit
    p5_presence:      Union[str, float] = "bom_aspeto"
    p6_aversion:      str   = "nenhuma"
    p7_dream_brand:   Optional[str] = None
    p7_dream_car:     Optional[str] = None   # V4 backward compat
    p8_budget_range:  Optional[str] = None   # V5: "8_15" | "15_25" | "25_40" | "40_plus"
    p8_budget_min:    int   = 8000
    p8_budget_max:    int   = 25000
    powertrain:       Optional[str] = None   # "indiferente" | "eletrico" | "hibrido" | "combustao"
    condition:        Optional[str] = None   # "usado" | "novo" | "indiferente"

    @model_validator(mode="after")
    def _compat(self):
        # V4 backward compat: p7_dream_car → p7_dream_brand
        if self.p7_dream_car and not self.p7_dream_brand:
            self.p7_dream_brand = self.p7_dream_car
        return self


class DreamCarRequest(BaseModel):
    """V5: Partial profile for fetching dynamic dream brands."""
    p1_context:       str   = "misto"
    p2_relationship:  Union[str, float] = "gosto_conduzir"
    p3_driving_style: Union[str, float] = "confortavel_com_alma"
    p4_risk:          Optional[Union[str, float]] = None
    p5_presence:      Union[str, float] = "bom_aspeto"
    p6_aversion:      str   = "nenhuma"
    p8_budget_range:  Optional[str] = None
    p8_budget_min:    int   = 8000
    p8_budget_max:    int   = 25000


class RefineRequest(BaseModel):
    """ "None of these convinces me": what was missing, then a new shortlist."""
    session_id:      Optional[str] = None
    answers:         Optional[dict] = None   # fallback when the session is not stored
    shown_model_ids: list[int] = []
    wants:           list[str] = []          # up to 2 of REFINE_WANTS
    powertrain:      Optional[str] = None
    condition:       Optional[str] = None


class FeedbackRequest(BaseModel):
    session_id:          str
    satisfaction:        Optional[str] = None   # "sim" | "mais_ou_menos" | "nao"
    preferred_model_id:  Optional[int] = None
    email:               Optional[str] = None


class RefreshRequest(BaseModel):
    session_id:           str
    dismissed_model_ids:  list[int] = []
    dismiss_reasons:      list[str] = []   # free-text reasons from frontend
    count:                int        = 3   # how many alternatives to return (max 3)


# ── Endpoints ──

@router.post("/recommend")
def recommend(answers: WizardAnswers, db: Session = Depends(get_db)):
    """Main recommendation endpoint. Returns session_id + profile + 5 models."""
    return get_recommendations(db, answers.model_dump())


@router.post("/dream-cars")
def dream_cars(answers: DreamCarRequest):
    """Get sorted dream cars for P7 based on partial profile."""
    return {"dream_cars": get_dream_cars(answers.model_dump())}


@router.post("/recommend/refresh")
def refresh_recommendations(req: RefreshRequest, db: Session = Depends(get_db)):
    """
    Get alternative recommendations after dismissing models.
    Adjusts profile based on dismiss reasons, excludes dismissed model IDs.
    """
    count = max(1, min(req.count, 3))
    return get_alternative_recommendations(
        db,
        session_id=req.session_id,
        dismissed_model_ids=req.dismissed_model_ids,
        dismiss_reasons=req.dismiss_reasons,
        count=count,
    )


@router.post("/recommend/refine")
def refine_recommendations(req: RefineRequest, db: Session = Depends(get_db)):
    """A new shortlist of 5 after the buyer said none convinced them: answers
    adjusted by what was missing, the models already shown left out."""
    answers = None
    if req.session_id:
        row = db.execute(text("SELECT answers_raw FROM recommendation_sessions WHERE id = :sid LIMIT 1"),
                         {"sid": req.session_id}).mappings().fetchone()
        if row and row["answers_raw"]:
            raw = row["answers_raw"]
            answers = json.loads(raw) if isinstance(raw, str) else dict(raw)
    if answers is None:
        answers = WizardAnswers(**(req.answers or {})).model_dump()
    answers, nudges = apply_refinement(answers, req.wants[:2], req.powertrain, req.condition)
    return get_recommendations(db, answers, exclude_ids=req.shown_model_ids[:30], nudges=nudges,
                               refined_from=req.session_id)


@router.post("/feedback")
def feedback(req: FeedbackRequest, db: Session = Depends(get_db)):
    """Log user feedback for a recommendation session."""
    log_feedback(db, req.session_id, req.satisfaction, req.preferred_model_id, req.email)
    return {"status": "ok", "session_id": req.session_id}


@router.get("/profile-dimensions")
def profile_dimensions():
    """Return the 6 profile dimensions with descriptions."""
    return {
        "dimensions": [
            {"key": "economy",     "label": "Economia",     "description": "Custo total de posse: combustivel, manutencao, seguro, desvalorizacao"},
            {"key": "comfort",     "label": "Conforto",     "description": "Refinamento, silencio, qualidade de viagem, materiais"},
            {"key": "driving",     "label": "Conducao",     "description": "Prazer ao volante, chassis, resposta dinamica"},
            {"key": "practical",   "label": "Praticidade",  "description": "Espaco, versatilidade, logistica familiar"},
            {"key": "status",      "label": "Imagem",       "description": "Presenca, marca, aspiracao, o que o carro comunica"},
            {"key": "reliability", "label": "Fiabilidade",  "description": "Paz de espirito, historico de avarias, previsibilidade"},
        ]
    }
