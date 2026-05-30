"""Meta del parche — tier list de comps / builds."""
from fastapi import APIRouter
from app.schemas.models import Game
from app.data import mock

router = APIRouter(tags=["meta"])


@router.get("/meta")
def get_meta(game: Game = "tft"):
    """Tier list con filtros y métricas (mock en Fase 0; agregaciones en Fase 3)."""
    return mock.meta(game)
