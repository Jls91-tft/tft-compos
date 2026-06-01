"""Lab (centro de entrenamiento): exploradores, recetas, GPI y build de campeón.

Los exploradores sirven datos REALES agregados por el worker de meta cuando
existen (USE_MOCK=false y JSON generado); si no, caen al mock genérico.
Recetas/GPI/champion siguen en mock (GPI = pipeline personal; champion = Data Dragon).
"""
from fastapi import APIRouter, HTTPException, Query

from app.core.config import settings
from app.schemas.models import Game
from app.data import mock_lab
from app.services import meta_store

router = APIRouter(prefix="/lab", tags=["lab"])


@router.get("/explorer")
def explorer(game: Game = "tft", kind: str = Query("units", description="units | items | augments")):
    if kind not in ("units", "items", "augments"):
        raise HTTPException(status_code=400, detail="kind debe ser 'units', 'items' o 'augments'")
    # Datos reales del worker si están disponibles; si no, mock genérico.
    if not settings.use_mock:
        data = meta_store.load_explorer(game)
        if data and data.get(kind):
            return {
                "items": data[kind],
                "styles": data.get("styles") or mock_lab.STYLES.get(game, []),
                "source": "real",
                "generated_at": data.get("generated_at"),
                "sample": data.get("sample"),
            }
    return {"items": mock_lab.explorer(game, kind), "styles": mock_lab.STYLES.get(game, []), "source": "mock"}


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
