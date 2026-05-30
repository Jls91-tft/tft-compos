"""Estadísticas personales (dashboard + insights)."""
from fastapi import APIRouter
from app.schemas.models import Game
from app.data import mock

router = APIRouter(tags=["stats"])


@router.get("/stats")
def get_stats(game: Game = "tft"):
    """KPIs, evolución, distribución, tablas e insights (mock en Fase 0)."""
    return mock.stats(game)
