"""
Caractr Recommendation API v4.0
Endpoints: /recommend, /dream-cars, /feedback, /profile-dimensions
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel, model_validator
from typing import Optional, Union
from app.db.database import get_db
from app.services.recommend_service import get_recommendations, get_dream_cars, log_feedback

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


class FeedbackRequest(BaseModel):
    session_id:          str
    satisfaction:        Optional[str] = None   # "sim" | "mais_ou_menos" | "nao"
    preferred_model_id:  Optional[int] = None
    email:               Optional[str] = None


# ── Endpoints ──

@router.post("/recommend")
def recommend(answers: WizardAnswers, db: Session = Depends(get_db)):
    """Main recommendation endpoint. Returns session_id + profile + 5 models."""
    return get_recommendations(db, answers.model_dump())


@router.post("/dream-cars")
def dream_cars(answers: DreamCarRequest):
    """Get sorted dream cars for P7 based on partial profile."""
    return {"dream_cars": get_dream_cars(answers.model_dump())}


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
