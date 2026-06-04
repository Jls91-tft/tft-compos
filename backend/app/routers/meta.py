"""Meta del parche — tier list de comps / builds.

Para TFT, sirve los datos REALES agregados por el worker (clusterización por
rasgos del ladder Challenger) cuando existen; si no, cae al mock genérico.
Para LoL aún no hay pipeline de comps → siempre mock por ahora.
"""
from fastapi import APIRouter

from app.core.config import settings
from app.schemas.models import Game
from app.data import mock
from app.services import meta_store

router = APIRouter(tags=["meta"])


@router.get("/meta")
def get_meta(game: Game = "tft"):
    if game == "tft" and not settings.use_mock:
        real = meta_store.load_comps("tft")
        if real and real.get("comps"):
            return real
    return mock.meta(game)
