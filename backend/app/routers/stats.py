"""Estadísticas personales (dashboard + insights).

Mock (Fase 0) o agregación real del historial de Riot (Fase 3) según USE_MOCK.
"""
from fastapi import APIRouter, HTTPException, Query

from app.schemas.models import Game
from app.services import stats_engine
from app.services.riot_client import RiotApiError
from app.core.config import settings
from app.data import mock

router = APIRouter(tags=["stats"])


@router.get("/stats")
async def get_stats(game: Game = "tft", riot_id: str = Query(default="", description="Nombre#TAG")):
    """KPIs, evolución, distribución, tablas e insights del jugador."""
    if settings.use_mock:
        return mock.stats(game)

    rid = riot_id or settings.default_riot_id
    if not rid:
        raise HTTPException(
            status_code=400,
            detail="Indica tu Riot ID (?riot_id=Nombre%23TAG) o configura DEFAULT_RIOT_ID en el .env",
        )
    try:
        return await stats_engine.compute_stats(game, rid)
    except RiotApiError as e:
        raise HTTPException(status_code=502 if e.status >= 500 else e.status, detail=e.message)
