"""Motor de coaching — orquesta datos de partida + IA para producir el informe.

En Fase 0 devuelve mocks (mismos datos que el prototipo). En Fase 2 sustituye
los mocks por: datos reales (riot_client) -> prompt -> IA local (ollama_client).
"""
from app.core.config import settings
from app.data import mock


def generate_report(game: str, match_id: str):
    """Informe de coaching de una partida."""
    if settings.use_mock:
        return mock.report(game, match_id)

    # AQUÍ (Fase 2) — pipeline real:
    #   from app.services.riot_client import riot_client
    #   from app.services.ollama_client import ollama_client
    #   datos = await riot_client.get_match(match_id, game)
    #   prompt = build_coaching_prompt(datos)
    #   texto = await ollama_client.generate(prompt, system=COACH_SYSTEM_PROMPT)
    #   return parse_report(texto)
    raise NotImplementedError("Coaching real pendiente (Fase 2)")


def answer_question(game: str, match_id: str, question: str) -> str:
    """Respuesta del chat del coach sobre una partida."""
    if settings.use_mock:
        return mock.chat_answer(game, question)

    # AQUÍ (Fase 2): contexto de la partida + pregunta -> ollama_client.generate(...)
    raise NotImplementedError("Chat real pendiente (Fase 2)")
