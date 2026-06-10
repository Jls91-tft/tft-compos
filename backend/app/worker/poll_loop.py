"""Scheduler de polling por puuid (FASE 2).

Riot no tiene webhooks: cada POLL_INTERVAL_SECONDS consulta los últimos IDs de
partida de cada usuario activo de la beta, deduplica contra la tabla
``partidas`` y encola el análisis de las nuevas.

Cola: RQ sobre Redis (REDIS_URL). Sin Redis (opción B / desarrollo), los jobs
se ejecutan inline en este mismo proceso — misma lógica, cero servicios extra.

Lo lanza el servicio 'poller' del docker-compose.prod.yml:
    python -m app.worker.poll_loop          # bucle infinito
    python -m app.worker.poll_loop --once   # una sola pasada (pruebas)
"""
import asyncio
import sys
import time
from datetime import datetime, timezone

from sqlalchemy import select

from app.core.config import settings
from app.db import sesion
from app.models import Partida, UsuarioBeta
from app.services.riot_client import riot_client
from app.worker import jobs


def _cola():
    """Cola RQ si hay Redis; None → ejecución inline."""
    if not settings.redis_url:
        return None
    try:
        from redis import Redis
        from rq import Queue
        return Queue(settings.rq_queue, connection=Redis.from_url(settings.redis_url))
    except Exception as e:  # noqa: BLE001 — sin cola seguimos inline, no paramos la beta
        print(f"[poller] sin cola RQ ({e}); ejecutando inline")
        return None


def _encolar(cola, match_id: str, puuid: str) -> None:
    if cola is not None:
        cola.enqueue(jobs.analizar_partida, match_id, puuid, job_timeout=120)
    else:
        try:
            print("[poller][inline]", jobs.analizar_partida(match_id, puuid))
        except Exception as e:  # noqa: BLE001
            print(f"[poller][inline] {match_id} ERROR: {e}")


def una_pasada() -> int:
    """Sondea a todos los usuarios activos. Devuelve el nº de partidas encoladas."""
    cola = _cola()
    encoladas = 0
    with sesion() as s:
        usuarios = list(s.scalars(select(UsuarioBeta).where(UsuarioBeta.activo == True)))  # noqa: E712
        for u in usuarios:
            try:
                ids = asyncio.run(riot_client.get_match_ids(u.puuid, "tft", count=settings.poll_count))
            except Exception as e:  # noqa: BLE001 — un usuario con error no debe parar el resto
                print(f"[poller] {u.riot_id}: ERROR pidiendo IDs: {e}")
                continue
            existentes = set(s.scalars(
                select(Partida.match_id).where(Partida.puuid == u.puuid, Partida.match_id.in_(ids))
            ))
            nuevas = [m for m in ids if m not in existentes]
            for mid in nuevas:
                _encolar(cola, mid, u.puuid)
                encoladas += 1
            u.last_polled_at = datetime.now(timezone.utc)
            if nuevas:
                print(f"[poller] {u.riot_id}: {len(nuevas)} partida(s) nueva(s) encolada(s)")
        s.commit()
    return encoladas


def main() -> None:
    if "--once" in sys.argv:
        n = una_pasada()
        print(f"[poller] pasada única: {n} encoladas")
        return
    print(f"[poller] arrancado · intervalo {settings.poll_interval_seconds}s · cola "
          f"{'RQ' if settings.redis_url else 'inline'}")
    while True:
        try:
            una_pasada()
        except Exception as e:  # noqa: BLE001 — el poller no debe morir
            print(f"[poller] ERROR en la pasada: {e}")
        time.sleep(settings.poll_interval_seconds)


if __name__ == "__main__":
    main()
