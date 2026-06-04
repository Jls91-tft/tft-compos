"""Meta del parche — tier list de comps / builds.

Para TFT, sirve los datos REALES agregados por el worker (clusterización por
rasgos del ladder Challenger) cuando existen; si no, cae al mock genérico.
Para LoL aún no hay pipeline de comps → siempre mock por ahora.
"""
from fastapi import APIRouter

from app.core.config import settings
from app.schemas.models import Game
from app.data import mock, mock_cdragon
from app.services import meta_store

router = APIRouter(tags=["meta"])


@router.get("/meta")
def get_meta(game: Game = "tft"):
    # 1) Datos REALES del ladder (worker activo + clave Riot OK).
    if game == "tft" and not settings.use_mock:
        real = meta_store.load_comps("tft")
        if real and real.get("comps"):
            return real

    # 2) Mock construido desde CDragon — nombres y rasgos REALES del set en vivo,
    #    métricas todavía ficticias (banner amarillo "datos de ejemplo").
    if game == "tft":
        cd = mock_cdragon.build()
        if cd and cd.get("comps"):
            return cd

    # 3) Último recurso: mock invented (CDragon caído / LoL).
    payload = dict(mock.meta(game))
    payload["source"] = "mock"
    return payload
