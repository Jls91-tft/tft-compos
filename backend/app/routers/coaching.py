"""Coaching — lista de partidas e informe de coaching."""
from fastapi import APIRouter, HTTPException
from app.schemas.models import MatchCard, CoachingReport, Game
from app.services import coaching_engine
from app.data import mock

router = APIRouter(prefix="/coaching", tags=["coaching"])


@router.get("/matches", response_model=list[MatchCard])
def list_matches(game: Game = "tft"):
    """Partidas recientes del jugador (mock en Fase 0; Riot API en Fase 1)."""
    return mock.matches(game)


@router.get("/report/{game}/{match_id}", response_model=CoachingReport)
def get_report(game: Game, match_id: str):
    """Informe de coaching de una partida (mock en Fase 0; IA en Fase 2)."""
    report = coaching_engine.generate_report(game, match_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Partida no encontrada")
    return report
