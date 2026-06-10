"""Objetivo semanal (FASE 3) — derivado de los patrones recurrentes del jugador.

Mecánica (determinista, sin LLM):
  1. Mira los últimos OBJETIVO_VENTANA informes del jugador (misma versión de
     catálogo) y cuenta cuántas veces disparó cada patrón.
  2. El patrón más recurrente con >= OBJETIVO_MIN_APARICIONES define el
     objetivo: su regla entrenable (``objetivo_es`` del catálogo).
  3. El progreso es el nº de partidas de la ventana donde ese patrón NO
     disparó ("partidas cumpliendo el objetivo", ej. 6/10). El cumplimiento
     por partida (✓/✗) sale del mismo criterio.

Si no hay patrón recurrente (pocos datos o juego limpio), no se inventa un
objetivo: se devuelve None y la UI muestra el estado "sin objetivo aún".
"""
import json
from collections import Counter

from sqlalchemy import select

from app.catalog import CATALOG_VERSION, POR_ID
from app.core.config import settings
from app.db import sesion
from app.models import Informe


def _informes_recientes(puuid: str, limite: int) -> list[dict]:
    with sesion() as s:
        filas = list(s.scalars(
            select(Informe)
            .where(Informe.puuid == puuid, Informe.catalogo_version == CATALOG_VERSION)
            .order_by(Informe.id.desc())
            .limit(limite)
        ))
    return [json.loads(f.informe_json) | {"_informe_id": f.id, "_partida_id": f.partida_id} for f in filas]


def calcular(puuid: str) -> dict | None:
    """Objetivo activo del jugador, o None si aún no hay patrón recurrente."""
    informes = _informes_recientes(puuid, settings.objetivo_ventana)
    if not informes:
        return None

    contador: Counter[str] = Counter()
    for inf in informes:
        for s in inf.get("senales", []):
            contador[s["patron_id"]] += 1

    if not contador:
        return None
    patron_id, apariciones = contador.most_common(1)[0]
    if apariciones < settings.objetivo_min_apariciones:
        return None

    patron = POR_ID.get(patron_id)
    if patron is None:
        return None

    total = len(informes)
    cumplidas = sum(
        1 for inf in informes
        if not any(s["patron_id"] == patron_id for s in inf.get("senales", []))
    )
    return {
        "patron_id": patron_id,
        "nombre": patron.nombre,
        "regla": patron.objetivo_es,
        "apariciones": apariciones,
        "ventana": total,
        "cumplidas": cumplidas,
        "catalogo_version": CATALOG_VERSION,
    }


def cumplimiento_por_partida(puuid: str) -> dict[str, bool]:
    """Mapa {match_id: cumplió} según el objetivo activo (para los ✓/✗ de la lista).
    Vacío si no hay objetivo."""
    objetivo = calcular(puuid)
    if objetivo is None:
        return {}
    informes = _informes_recientes(puuid, settings.objetivo_ventana)
    return {
        inf.get("match_id", ""): not any(
            s["patron_id"] == objetivo["patron_id"] for s in inf.get("senales", [])
        )
        for inf in informes if inf.get("match_id")
    }
