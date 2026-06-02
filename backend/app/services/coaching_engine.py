"""Motor de coaching — Riot + IA, con CACHÉ en BD y plan de mejora global.

Informe por partida: cache-first (no re-llama al LLM si ya existe; `regenerate`
fuerza una nueva generación y VERSIONA, no sobrescribe). Plan global: agrega los
informes YA cacheados en una sola llamada. Reutiliza el pipeline de prompts
existente (rúbrica/rigor) sin cambiar su schema.
"""
from collections import Counter

from app.core.config import settings
from app.data import mock
from app.services import report_store, prompts


async def generate_report(game: str, match_id: str, riot_id: str = "", lang: str = "es", regenerate: bool = False):
    """Informe de coaching de una partida (cache-first + persistencia)."""
    if settings.use_mock:
        return mock.report(game, match_id)

    user_key = report_store.norm_key(riot_id or settings.default_riot_id)
    if not regenerate and user_key:
        cached = report_store.get_report(user_key, game, match_id)
        if cached:
            cached["stale"] = cached.get("prompt_version") != prompts.PROMPT_VERSION
            return cached

    from app.services.riot_client import riot_client, RiotApiError
    from app.services.ollama_client import ollama_client

    if not riot_id or "#" not in riot_id:
        raise RiotApiError(400, "Riot ID requerido (Nombre#TAG) para el coaching real")
    name, tag = riot_id.split("#", 1)
    puuid = await riot_client.get_puuid(name.strip(), tag.strip())
    match = await riot_client.get_match(match_id, game)
    summary = prompts.extract_summary(game, match, puuid)
    raw = await ollama_client.generate(
        prompts.build_report_prompt(game, summary, lang), system=prompts.system_for(lang), json_mode=True
    )
    report = prompts.parse_report(raw, game, match_id)

    model = settings.groq_model if settings.llm_provider == "groq" else settings.ollama_model
    if user_key:
        return report_store.save_report(user_key, game, match_id, report.model_dump(), prompts.PROMPT_VERSION, model)
    return report


def _aggregate(reports: list[dict]) -> dict:
    """Resume errores y focos recurrentes de los informes cacheados (schema actual)."""
    n = len(reports)
    errs, foci = Counter(), Counter()
    sev: dict[str, list] = {}
    for r in reports:
        for e in r.get("errors", []):
            t = (e.get("title") or "")[:90]
            if t:
                errs[t] += 1
                sev.setdefault(t, []).append(2 if e.get("severity") == "major" else 1)
        f = (r.get("focus") or "")[:120]
        if f:
            foci[f] += 1

    def top(c):
        return [{"item": k, "count": v, "pct": round(100 * v / n) if n else 0} for k, v in c.most_common(10)]
    return {"n_matches": n, "errores_frecuentes": top(errs), "focos_repetidos": top(foci),
            "severidad_media": {k: round(sum(v) / len(v), 1) for k, v in sev.items()}}


async def build_improvement_plan(game: str, riot_id: str = "", lang: str = "es", regenerate: bool = False):
    """Plan de mejora GLOBAL sobre los informes YA cacheados (1 sola llamada al LLM)."""
    user_key = report_store.norm_key(riot_id or settings.default_riot_id)
    reports = report_store.latest_reports(user_key, game, settings.plan_match_window)
    analyzed_ids = [r.get("match_id") for r in reports if r.get("match_id")]

    if not regenerate:
        cached = report_store.get_plan(user_key, game)
        if cached:
            based = set(cached.get("based_on_match_ids") or [])
            cached["new_matches"] = len([m for m in analyzed_ids if m not in based])
            return cached

    from app.services.riot_client import RiotApiError
    if not reports:
        raise RiotApiError(400, "Aún no hay informes analizados. Genera coaching de algunas partidas primero.")

    from app.services.ollama_client import ollama_client, OllamaError
    aggregate = _aggregate(reports)
    model = settings.groq_model if settings.llm_provider == "groq" else settings.ollama_model
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
        except Exception as e:  # noqa: BLE001 — reintento con el error como feedback
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
