"""Jobs de análisis — los ejecuta el worker de RQ (o inline sin Redis).

``analizar_partida(match_id, puuid)``:
  1. descarga el match si aún no está en BD (con limitador de rate)
  2. extrae los hechos con el motor determinista (CAPA 1)
  3. persiste el snapshot en ``hechos`` (idempotente por versión del motor)
  4. evalúa el catálogo (CAPA 2) y genera el informe template-first (CAPA 3),
     cacheado por (partida, versión de catálogo) — NUNCA se regenera
"""
import asyncio
import json
from datetime import datetime, timezone

from sqlalchemy import select

from app.catalog import CATALOG_VERSION
from app.db import sesion
from app.models import CatalogoVersion, Feedback, Hechos, Informe, Partida
from app.services import facts_engine, pattern_evaluator, report_builder
from app.services.riot_client import riot_client


def _telemetria(s) -> dict:
    """Votos acumulados por patrón ({patron_id: {acierta, falla}}) para la
    retirada automática de patrones que fallan demasiado."""
    filas = s.execute(select(Feedback.patron_id, Feedback.voto)).all()
    out: dict[str, dict] = {}
    for patron_id, voto in filas:
        out.setdefault(patron_id, {"acierta": 0, "falla": 0})
        if voto in ("acierta", "falla"):
            out[patron_id][voto] += 1
    return out


def _game_datetime(match: dict) -> datetime | None:
    ms = (match.get("info", {}) or {}).get("game_datetime")
    if not ms:
        return None
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc)


def analizar_partida(match_id: str, puuid: str) -> str:
    """Descarga (si falta), extrae hechos y persiste. Devuelve un estado legible."""
    with sesion() as s:
        partida = s.scalar(select(Partida).where(Partida.match_id == match_id, Partida.puuid == puuid))

        if partida is None:
            match = asyncio.run(riot_client.get_match(match_id, "tft"))
            partida = Partida(
                match_id=match_id,
                puuid=puuid,
                game_datetime=_game_datetime(match),
                queue_id=(match.get("info", {}) or {}).get("queue_id"),
                payload_json=json.dumps(match, ensure_ascii=False),
            )
            s.add(partida)
            s.flush()          # asigna partida.id
        else:
            match = json.loads(partida.payload_json)

        fila_hechos = s.scalar(select(Hechos).where(
            Hechos.partida_id == partida.id,
            Hechos.engine_version == facts_engine.ENGINE_VERSION,
        ))
        if fila_hechos is None:
            hechos = facts_engine.extraer(match, puuid)
            fila_hechos = Hechos(
                partida_id=partida.id,
                puuid=puuid,
                engine_version=facts_engine.ENGINE_VERSION,
                hechos_json=json.dumps(hechos, ensure_ascii=False),
            )
            s.add(fila_hechos)
            s.flush()
            estado_hechos = "hechos extraídos"
        else:
            hechos = json.loads(fila_hechos.hechos_json)
            estado_hechos = "hechos ya existentes"

        # CAPA 2 + CAPA 3 — informe cacheado por versión de catálogo (nunca se regenera).
        informe = s.scalar(select(Informe).where(
            Informe.partida_id == partida.id,
            Informe.catalogo_version == CATALOG_VERSION,
        ))
        if informe is None:
            evaluacion = pattern_evaluator.evaluar(hechos, telemetria=_telemetria(s))
            cuerpo = report_builder.construir(hechos, evaluacion)
            s.add(Informe(
                partida_id=partida.id,
                puuid=puuid,
                hechos_id=fila_hechos.id,
                catalogo_version=CATALOG_VERSION,
                informe_json=json.dumps(cuerpo, ensure_ascii=False),
            ))
            if s.get(CatalogoVersion, CATALOG_VERSION) is None:
                s.add(CatalogoVersion(version=CATALOG_VERSION, descripcion="Catálogo inicial (10 patrones end-state)"))
            estado_informe = f"informe generado (catálogo {CATALOG_VERSION})"
        else:
            estado_informe = "informe ya existente"

        s.commit()
        return f"{match_id}: {estado_hechos} · {estado_informe}"
