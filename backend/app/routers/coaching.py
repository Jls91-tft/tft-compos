"""Coaching — lista de partidas e informe de coaching.

- /coaching/matches : mock (Fase 0) o Riot API real (Fase 1) según USE_MOCK.
- /coaching/report  : mock por ahora; pasará a IA (Ollama) en la Fase 2.
"""
from fastapi import APIRouter, HTTPException, Query

from app.schemas.models import MatchCard, CoachingReport, Game
from app.services import coaching_engine, riot_parser
from app.services.riot_client import riot_client, RiotApiError
from app.core.config import settings
from app.data import mock

router = APIRouter(prefix="/coaching", tags=["coaching"])


def _parse_riot_id(riot_id: str) -> tuple[str, str]:
    if "#" not in riot_id:
        raise HTTPException(status_code=400, detail="Riot ID inválido. Formato: Nombre#TAG")
    name, tag = riot_id.split("#", 1)
    return name.strip(), tag.strip()


def _riot_error(e: RiotApiError) -> HTTPException:
    status = 502 if e.status >= 500 else e.status
    return HTTPException(status_code=status, detail=e.message)


@router.get("/matches", response_model=list[MatchCard])
async def list_matches(game: Game = "tft", riot_id: str = Query(default="", description="Nombre#TAG")):
    """Partidas recientes del jugador."""
    if settings.use_mock:
        return mock.matches(game)

    rid = riot_id or settings.default_riot_id
    if not rid:
        raise HTTPException(
            status_code=400,
            detail="Indica tu Riot ID (?riot_id=Nombre%23TAG) o configura DEFAULT_RIOT_ID en el .env",
        )
    name, tag = _parse_riot_id(rid)
    try:
        puuid = await riot_client.get_puuid(name, tag)
        ids = await riot_client.get_match_ids(puuid, game, count=8)
        cards: list[MatchCard] = []
        for mid in ids:
            raw = await riot_client.get_match(mid, game)
            parse = riot_parser.tft_match_to_card if game == "tft" else riot_parser.lol_match_to_card
            cards.append(parse(raw, puuid))
        return cards
    except RiotApiError as e:
        raise _riot_error(e)


@router.get("/report/{game}/{match_id}", response_model=CoachingReport)
async def get_report(game: Game, match_id: str):
    """Informe de coaching de una partida (mock; IA en la Fase 2)."""
    report = coaching_engine.generate_report(game, match_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Partida no encontrada")
    return report
