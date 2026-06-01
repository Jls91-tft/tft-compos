"""Lab (centro de entrenamiento): exploradores, recetas, GPI y build de campeón.

Mock (Fase actual). En producción saldrá de agregaciones de meta + Riot API.
"""
from fastapi import APIRouter, HTTPException, Query

from app.schemas.models import Game
from app.data import mock_lab

router = APIRouter(prefix="/lab", tags=["lab"])


@router.get("/explorer")
def explorer(game: Game = "tft", kind: str = Query("units", description="units | items | augments")):
    if kind not in ("units", "items", "augments"):
        raise HTTPException(status_code=400, detail="kind debe ser 'units', 'items' o 'augments'")
    return {"items": mock_lab.explorer(game, kind), "styles": mock_lab.STYLES.get(game, [])}


@router.get("/recipes")
def recipes():
    """Cheat sheet de componentes → ítem (TFT)."""
    return mock_lab.recipes()


@router.get("/gpi")
def gpi(game: Game = "tft"):
    """Perfil de habilidades (radar) del jugador."""
    return mock_lab.gpi(game)


@router.get("/champion")
def champion(id: str = Query("mago-control")):
    """Build de campeón (LoL): objetos, runas, habilidades, counters, power spikes."""
    return mock_lab.champion(id)
