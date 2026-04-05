"""
Caractr Recommendation API v4.0
Endpoints: /recommend, /dream-cars, /feedback, /profile-dimensions
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from app.db.database import get_db
from app.services.recommend_service import get_recommendations, get_dream_cars, log_feedback

router = APIRouter(prefix="/api", tags=["recommend"])


# ── Request models ──

class WizardAnswers(BaseModel):
    # V4 fields
    p1_context:       str   = "misto"    # cidade | misto | estrada | familia
    p2_relationship:  float = 0.5        # 0.0 = só uso ↔ 1.0 = adoro conduzir
    p3_driving_style: float = 0.5        # 0.0 = conforto ↔ 1.0 = sentir o carro
    p4_risk:          float = 0.5        # 0.0 = segurança ↔ 1.0 = carácter
    p5_presence:      float = 0.5        # 0.0 = discreto ↔ 1.0 = presença
    p6_aversion:      str   = "nenhuma"  # conforto | fiabilidade | espaco | potencia | nenhuma
    p7_dream_car:     Optional[str] = None
    p8_budget_min:    int   = 8000
    p8_budget_max:    int   = 25000


class DreamCarRequest(BaseModel):
    p1_context:       str   = "misto"
    p2_relationship:  float = 0.5
    p3_driving_style: float = 0.5
    p4_risk:          float = 0.5
    p5_presence:      float = 0.5
    p6_aversion:      str   = "nenhuma"
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
