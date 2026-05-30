"""Motor de coaching — orquesta datos de partida (Riot) + IA (Ollama).

En modo mock devuelve los datos de ejemplo. En modo real:
  Riot (detalle de partida) → resumen → prompt → IA local → informe validado.
"""
from app.core.config import settings
from app.data import mock


async def generate_report(game: str, match_id: str, riot_id: str = ""):
    """Informe de coaching de una partida."""
    if settings.use_mock:
        return mock.report(game, match_id)

    # Imports perezosos: en modo mock no se cargan httpx/Riot/Ollama.
    from app.services.riot_client import riot_client, RiotApiError
    from app.services.ollama_client import ollama_client
    from app.services import prompts

    if not riot_id or "#" not in riot_id:
        raise RiotApiError(400, "Riot ID requerido (Nombre#TAG) para el coaching real")

    name, tag = riot_id.split("#", 1)
    puuid = await riot_client.get_puuid(name.strip(), tag.strip())
    match = await riot_client.get_match(match_id, game)
    summary = prompts.extract_summary(game, match, puuid)
    raw = await ollama_client.generate(
        prompts.build_report_prompt(game, summary), system=prompts.COACH_SYSTEM, json_mode=True
    )
    return prompts.parse_report(raw, game, match_id)


async def answer_question(game: str, match_id: str, question: str, riot_id: str = "") -> str:
    """Respuesta del chat del coach sobre una partida."""
    if settings.use_mock:
        return mock.chat_answer(game, question)

    from app.services.riot_client import riot_client
    from app.services.ollama_client import ollama_client
    from app.services import prompts

    # Sin Riot ID respondemos de forma general (sin contexto de partida).
    if not riot_id or "#" not in riot_id:
        return await ollama_client.generate(f"El jugador pregunta: {question}", system=prompts.COACH_SYSTEM)

    name, tag = riot_id.split("#", 1)
    puuid = await riot_client.get_puuid(name.strip(), tag.strip())
    match = await riot_client.get_match(match_id, game)
    summary = prompts.extract_summary(game, match, puuid)
    return await ollama_client.generate(
        prompts.build_chat_prompt(game, summary, question), system=prompts.COACH_SYSTEM
    )
