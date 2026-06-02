"""Motor de coaching — Riot + IA, informe ESTRUCTURADO v2, con CACHÉ y plan global.

Informe por partida: payload enriquecido (extract_summary + timeline LoL) → LLM v2
con esquema estructurado y evidencia → validación + reintento → persistencia.
Cache-first (no re-llama si ya existe; `regenerate` fuerza y versiona). Plan global:
agrega los hallazgos de los informes YA cacheados en una sola llamada.
"""
import asyncio

from app.core.config import settings
from app.data import mock
from app.services import report_store, match_features, prompts


async def generate_report(game: str, match_id: str, riot_id: str = "", lang: str = "es", regenerate: bool = False):
    """Informe de coaching estructurado (cache-first + persistencia)."""
    if settings.use_mock:
        return mock.report(game, match_id)

    user_key = report_store.norm_key(riot_id or settings.default_riot_id)
    if not regenerate and user_key:
        cached = report_store.get_report(user_key, game, match_id)
        if cached:
            cached["stale"] = cached.get("prompt_version") != prompts.PROMPT_VERSION
            return cached

    from app.services.riot_client import riot_client, RiotApiError
    from app.services.ollama_client import ollama_client, OllamaError, current_model

    if not riot_id or "#" not in riot_id:
        raise RiotApiError(400, "Riot ID requerido (Nombre#TAG) para el coaching real")
    name, tag = riot_id.split("#", 1)
    puuid = await riot_client.get_puuid(name.strip(), tag.strip())
    match = await riot_client.get_match(match_id, game)
    timeline = None
    if game == "lol":
        try:
            timeline = await riot_client.get_match_timeline(match_id)
        except RiotApiError:
            timeline = None  # sin timeline degradamos a evidencia por stats

    summary = prompts.extract_summary(game, match, puuid)
    payload = match_features.enrich(game, match, summary, puuid, timeline)
    base = {"game": game, "match_id": match_id, "metrics": match_features.metrics_for(game, summary)}
    model = current_model()
    system = prompts.system_report(lang)
    prompt = prompts.build_report_prompt_v2(game, payload, lang)

    report, last_err = None, ""
    for attempt in range(2):
        p = prompt if attempt == 0 else (
            prompt + f"\n\nTu respuesta anterior NO validó ({last_err}). Devuelve SOLO el JSON con el esquema exacto.")
        raw = await ollama_client.generate(p, system=system, json_mode=True)
        try:
            report = prompts.validate_report(raw, base)
            break
        except Exception as e:  # noqa: BLE001 — reintento con el error como feedback
            last_err = str(e)[:300]
    if report is None:
        raise OllamaError("La IA no devolvió un informe válido tras 2 intentos. Inténtalo de nuevo.")

    if user_key:
        return report_store.save_report(user_key, game, match_id, report.model_dump(), prompts.PROMPT_VERSION, model)
    return report


def _aggregate(reports: list[dict]) -> dict:
    """Lista compacta de hallazgos por partida. NO los contamos por texto exacto (nunca
    casa: cada informe los redacta distinto) — se los pasamos al LLM para que AGRUPE los
    recurrentes por tema y calcule la frecuencia real."""
    partidas = []
    for r in reports:
        partidas.append({
            "decision": [e.get("what_happened") for e in r.get("decision_errors", []) if e.get("what_happened")][:3],
            "macro": [i.get("title") for i in r.get("macro_issues", []) if i.get("title")][:3],
            "mecanica": [i.get("title") for i in r.get("mechanical_issues", []) if i.get("title")][:3],
            "mental": [m.get("pattern") for m in r.get("mental_patterns", []) if m.get("pattern")][:2],
        })
    return {"n_matches": len(reports), "partidas": partidas}


async def _ensure_recent_analyzed(game: str, riot_id: str, lang: str) -> list[dict]:
    """Genera (en lote, reutilizando caché) los informes de las últimas partidas que aún
    no estén analizados, hasta `plan_autoanalyze` por llamada. Devuelve los cacheados."""
    user_key = report_store.norm_key(riot_id or settings.default_riot_id)
    if settings.use_mock:
        return report_store.latest_reports(user_key, game, settings.plan_match_window)
    rid = riot_id or settings.default_riot_id
    if not rid or "#" not in rid:
        return report_store.latest_reports(user_key, game, settings.plan_match_window)
    from app.services.riot_client import riot_client
    name, tag = rid.split("#", 1)
    puuid = await riot_client.get_puuid(name.strip(), tag.strip())
    ids = await riot_client.get_match_ids(puuid, game, count=settings.plan_match_window)
    from app.services.ollama_client import OllamaError
    generated = 0
    for mid in ids:
        if generated >= settings.plan_autoanalyze:
            break
        existing = report_store.get_report(user_key, game, mid)
        # Al día (versión de prompt/motor actual) → no lo tocamos. Sin informe o
        # con un análisis ANTIGUO (otra versión) → lo (re)generamos con el motor nuevo.
        if existing and existing.get("prompt_version") == prompts.PROMPT_VERSION:
            continue
        try:
            await generate_report(game, mid, rid, lang, regenerate=bool(existing))
            generated += 1
            await asyncio.sleep(0.8)   # suaviza la ráfaga para el rate limit de Groq
        except OllamaError:
            break   # IA saturada (429) tras reintentos: paramos el lote y seguimos con lo cacheado
        except Exception:  # noqa: BLE001 — una partida concreta que falle no para el plan
            continue
    return report_store.latest_reports(user_key, game, settings.plan_match_window)


async def build_improvement_plan(game: str, riot_id: str = "", lang: str = "es", regenerate: bool = False):
    """Plan de mejora GLOBAL. Genera primero los informes que falten (en lote) y luego
    agrega sus hallazgos en 1 sola llamada al LLM."""
    user_key = report_store.norm_key(riot_id or settings.default_riot_id)
    reports = await _ensure_recent_analyzed(game, riot_id, lang)
    analyzed_ids = [r.get("match_id") for r in reports if r.get("match_id")]

    if not regenerate:
        cached = report_store.get_plan(user_key, game)
        if cached:
            based = set(cached.get("based_on_match_ids") or [])
            cached["new_matches"] = len([m for m in analyzed_ids if m not in based])
            return cached

    from app.services.riot_client import RiotApiError
    if not reports:
        raise RiotApiError(400, "No hay partidas que analizar. Configura tu Riot ID (Nombre#TAG).")

    from app.services.ollama_client import ollama_client, OllamaError, current_model
    aggregate = _aggregate(reports)
    model = current_model()
    base = {"game": game, "based_on_match_ids": analyzed_ids, "new_matches": 0}

    plan, last_err = None, ""
    for attempt in range(2):
        p = prompts.build_plan_prompt(game, aggregate, lang)
        if attempt:
            p += f"\n\nTu respuesta anterior NO validó ({last_err}). Devuelve SOLO el JSON con el esquema exacto."
        raw = await ollama_client.generate(p, system=prompts.system_plan(lang), json_mode=True)
        try:
            plan = prompts.validate_plan(raw, base)
            break
        except Exception as e:  # noqa: BLE001
            last_err = str(e)[:300]
    if plan is None:
        raise OllamaError("La IA no devolvió un plan válido tras 2 intentos. Inténtalo de nuevo.")

    return report_store.save_plan(user_key, game, plan.model_dump(), analyzed_ids, prompts.PLAN_PROMPT_VERSION, model)


async def answer_question(game: str, match_id: str, question: str, riot_id: str = "", lang: str = "es") -> str:
    """Respuesta del chat del coach sobre una partida."""
    if settings.use_mock:
        return mock.chat_answer(game, question)

    from app.services.riot_client import riot_client
    from app.services.ollama_client import ollama_client

    if not riot_id or "#" not in riot_id:
        prompt = f"The player asks: {question}" if lang == "en" else f"El jugador pregunta: {question}"
        return await ollama_client.generate(prompt, system=prompts.system_for(lang))

    name, tag = riot_id.split("#", 1)
    puuid = await riot_client.get_puuid(name.strip(), tag.strip())
    match = await riot_client.get_match(match_id, game)
    summary = prompts.extract_summary(game, match, puuid)
    return await ollama_client.generate(
        prompts.build_chat_prompt(game, summary, question, lang), system=prompts.system_for(lang)
    )
