"""Jobs de análisis (FASE 2) — los ejecuta el worker de RQ (o inline sin Redis).

``analizar_partida(match_id, puuid)``:
  1. descarga el match si aún no está en BD (con limitador de rate)
  2. extrae los hechos con el motor determinista (CAPA 1)
  3. persiste el snapshot en ``hechos`` (idempotente por versión del motor)

FASE 3 añadirá aquí la evaluación del catálogo y la generación del informe.
"""
import asyncio
import json
from datetime import datetime, timezone

from sqlalchemy import select

from app.db import sesion
from app.models import Hechos, Partida
from app.services import facts_engine
from app.services.riot_client import riot_client


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

        ya = s.scalar(select(Hechos).where(
            Hechos.partida_id == partida.id,
            Hechos.engine_version == facts_engine.ENGINE_VERSION,
        ))
        if ya is not None:
            s.commit()
            return f"{match_id}: hechos ya existentes (motor {facts_engine.ENGINE_VERSION})"

        hechos = facts_engine.extraer(match, puuid)
        s.add(Hechos(
            partida_id=partida.id,
            puuid=puuid,
            engine_version=facts_engine.ENGINE_VERSION,
            hechos_json=json.dumps(hechos, ensure_ascii=False),
        ))
        s.commit()
        return f"{match_id}: hechos extraídos y persistidos (motor {facts_engine.ENGINE_VERSION})"
