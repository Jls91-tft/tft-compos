"""Enriquecimiento LLM de las comps agregadas (paso opcional sobre la opción A).

A partir del cluster bruto (rasgos + carry + unidades + ítems + métricas) le
pedimos al LLM:
- ``name``      — nombre evocador en español (3-5 palabras) que use el nombre del juego
- ``lema``      — frase de una línea con la idea de juego
- ``guia``      — 2-3 líneas accionables (economía/tempo, prioridad de ítems, posicionamiento)
- ``difficulty``— "Fácil" | "Media" | "Difícil"

Si la llamada falla (cuota, modelo caído, etc.) el cluster se devuelve sin
cambios para que la tier list nunca se quede en blanco.

Lo invoca el worker (``app/worker/refresh_meta.py``) cuando ``META_ENRICH_LLM=true``.
NO se llama desde la API.
"""
import asyncio
import json
import re

from app.core.config import settings
from app.services.ollama_client import OllamaClient, OllamaError


_SYSTEM = (
    "Eres un analista experto de Teamfight Tactics. Hablas en español natural, "
    "directo, con jerga del juego (carry, tempo, fast 8, reroll, slow roll, "
    "frontline, lose streak). NUNCA inventes datos: solo describes lo que ves "
    "en la composición agregada que se te pasa. Devuelves JSON estricto y NADA más."
)


def _build_prompt(comp: dict) -> str:
    return (
        "A continuación tienes una composición agregada del ladder Challenger del "
        "parche en vivo: rasgos dominantes, carry detectado por ítems, unidades "
        "más recurrentes con su coste, mejores ítems del carry, mejores aumentos "
        "y métricas reales.\n\n"
        f"Composición: {json.dumps(_compact(comp), ensure_ascii=False)}\n\n"
        "Devuelve EXACTAMENTE este JSON (sin texto fuera del objeto):\n"
        "{\n"
        '  "name": "nombre evocador en español, 3-5 palabras",\n'
        '  "lema": "una línea con la idea de juego",\n'
        '  "guia": "2-3 frases accionables: economía/tempo, prioridad de ítems al carry, posicionamiento clave",\n'
        '  "difficulty": "Fácil" | "Media" | "Difícil"\n'
        "}\n"
        "Reglas: no menciones ningún champion fuera del listado; no inventes ítems; "
        "si no hay carry claro, el nombre se centra en los rasgos."
    )


def _compact(comp: dict) -> dict:
    """Manda al LLM solo lo útil (ahorra tokens)."""
    return {
        "traits": [t for t in comp.get("name", "").split(" — ")[0].split(" · ") if t],
        "style": comp.get("style"),
        "carry": comp.get("carry"),
        "carry_items": comp.get("carry_items", []),
        "units": comp.get("units", []),
        "augments": comp.get("augments", []),
        "metrics": comp.get("metrics", {}),
        "sample_games": comp.get("_games", 0),
    }


_JSON_RE = re.compile(r"\{[\s\S]*\}")


def _parse(raw: str) -> dict | None:
    """Extrae el primer objeto JSON del texto del LLM; tolerante a envoltorios."""
    if not raw:
        return None
    m = _JSON_RE.search(raw)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except ValueError:
        return None


async def _enrich_one(client: OllamaClient, comp: dict) -> dict:
    try:
        raw = await client.generate(_build_prompt(comp), system=_SYSTEM, json_mode=True)
    except (OllamaError, Exception):  # noqa: BLE001 — fallback silencioso
        return comp
    data = _parse(raw)
    if not data:
        return comp
    name = (data.get("name") or "").strip()
    lema = (data.get("lema") or "").strip()
    guia = (data.get("guia") or "").strip()
    diff = (data.get("difficulty") or "").strip()
    out = dict(comp)
    if name:
        out["name"] = name
    if lema:
        out["lema"] = lema
    if guia:
        out["guia"] = guia
    if diff in ("Fácil", "Media", "Difícil"):
        out["difficulty"] = diff
    return out


async def enrich(payload: dict) -> dict:
    """Enriquece in-place los mejores N comps; el resto queda tal cual."""
    comps = payload.get("comps", []) or []
    if not comps:
        return payload
    n = max(0, int(settings.meta_enrich_top))
    if n <= 0:
        return payload
    client = OllamaClient()
    # Secuencial: el modelo 'free' de OpenRouter limita concurrencia. Son 10-12 llamadas.
    head = comps[:n]
    enriched = []
    for c in head:
        enriched.append(await _enrich_one(client, c))
        await asyncio.sleep(0.2)   # respiro mínimo entre llamadas
    payload["comps"] = enriched + comps[n:]
    payload["enriched"] = True
    return payload
