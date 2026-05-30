"""Riot — utilidades de cuenta (resolución de Riot ID).

Útil para el onboarding del frontend: comprobar que un Riot ID existe y
obtener su puuid antes de pedir partidas.
"""
from fastapi import APIRouter, HTTPException, Query

from app.services.riot_client import riot_client, RiotApiError
from app.core.config import settings

router = APIRouter(prefix="/riot", tags=["riot"])


@router.get("/account")
async def account(riot_id: str = Query(..., description="Formato Nombre#TAG")):
    """Resuelve un Riot ID a su puuid."""
    if settings.use_mock:
        return {"riot_id": riot_id, "puuid": "MOCK-PUUID", "mock": True}
    if "#" not in riot_id:
        raise HTTPException(status_code=400, detail="Riot ID inválido. Formato: Nombre#TAG")
    name, tag = riot_id.split("#", 1)
    try:
        puuid = await riot_client.get_puuid(name.strip(), tag.strip())
        return {"riot_id": riot_id, "puuid": puuid}
    except RiotApiError as e:
        raise HTTPException(status_code=502 if e.status >= 500 else e.status, detail=e.message)
