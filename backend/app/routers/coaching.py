"""Coaching — lista de partidas e informe de coaching.

- /coaching/matches : mock (Fase 0) o Riot API real (Fase 1) según USE_MOCK.
- /coaching/report  : mock (Fase 0) o IA local sobre datos reales (Fase 2).
"""
from fastapi import APIRouter, HTTPException, Query

from app.schemas.models import MatchCard, CoachingReport, ImprovementPlan, Game
from app.services import coaching_engine, riot_parser, report_store, prompts
from app.services.riot_client import riot_client, RiotApiError
from app.services.ollama_client import OllamaError
from app.core.config import settings
from app.data import mock

router = APIRouter(prefix="/coaching", tags=["coaching"])


def _parse_riot_id(riot_id: str) -> tuple[str, str]:
    if "#" not in riot_id:
        raise HTTPException(status_code=400, detail="Riot ID inválido. Formato: Nombre#TAG")
    name, tag = riot_id.split("#", 1)
    return name.strip(), tag.strip()


def _riot_error(e: RiotApiError) -> HTTPException:
    return HTTPException(status_code=502 if e.status >= 500 else e.status, detail=e.message)


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
        ids = await riot_client.get_match_ids(puuid, game, count=20)
        cards: list[MatchCard] = []
        for mid in ids:
            raw = await riot_client.get_match(mid, game)
            parse = riot_parser.tft_match_to_card if game == "tft" else riot_parser.lol_match_to_card
            cards.append(parse(raw, puuid))
        return cards
    except RiotApiError as e:
        raise _riot_error(e)


@router.get("/analyzed/{game}")
async def analyzed(game: Game, riot_id: str = Query(default="", description="Nombre#TAG")):
    """Estado de análisis por partida: {match_id: {analyzed, stale, model, generated_at}}.
    Permite al frontend marcar qué partidas ya tienen informe (y cuáles están caducadas)."""
    if settings.use_mock:
        return {}
    rid = riot_id or settings.default_riot_id
    status = report_store.analyzed_status(report_store.norm_key(rid), game)
    return {
        mid: {
            "analyzed": True,
            "stale": meta.get("prompt_version") != prompts.PROMPT_VERSION,
            "model": meta.get("model", ""),
            "generated_at": meta.get("generated_at", ""),
        }
        for mid, meta in status.items()
    }


@router.get("/report/{game}/{match_id}", response_model=CoachingReport)
async def get_report(game: Game, match_id: str, riot_id: str = Query(default="", description="Nombre#TAG"),
                     lang: str = Query(default="es", description="Idioma del informe: es | en"),
                     regenerate: bool = Query(default=False, description="Fuerza nueva llamada al LLM (versiona, no sobrescribe)")):
    """Informe de coaching (cache-first; `regenerate` fuerza una nueva generación)."""
    try:
        report = await coaching_engine.generate_report(
            game, match_id, riot_id or settings.default_riot_id, lang, regenerate)
    except RiotApiError as e:
        raise _riot_error(e)
    except OllamaError as e:
        raise HTTPException(status_code=502, detail=str(e))
    if report is None:
        raise HTTPException(status_code=404, detail="Partida no encontrada")
    return report


@router.get("/plan/{game}", response_model=ImprovementPlan)
async def get_plan(game: Game, riot_id: str = Query(default="", description="Nombre#TAG"),
                   lang: str = Query(default="es", description="Idioma: es | en"),
                   regenerate: bool = Query(default=False, description="Regenera el plan agregado")):
    """Plan de mejora GLOBAL agregando los informes ya cacheados del jugador (1 llamada al LLM)."""
    try:
        return await coaching_engine.build_improvement_plan(
            game, riot_id or settings.default_riot_id, lang, regenerate)
    except RiotApiError as e:
        raise _riot_error(e)
    except OllamaError as e:
        raise HTTPException(status_code=502, detail=str(e))
