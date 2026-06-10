"""Limitador de rate CENTRALIZADO para la Riot API (FASE 2).

Dos ventanas (por segundo y por 2 minutos) con margen bajo los límites reales
de la clave (20 req/s · 100 req/2 min). Configurable por entorno
(RIOT_RATE_RPS, RIOT_RATE_PER_2MIN).

Dos modos, transparentes para el caller:
- **Redis** (REDIS_URL definido): contadores compartidos entre TODOS los
  procesos (api, poller, rq-worker) → el límite se respeta globalmente.
  Ventana fija con INCR + EXPIRE; sencillo y suficiente con margen.
- **Local** (sin Redis, opción B/tests): ventana deslizante en memoria del
  proceso. Correcto mientras solo un proceso hable con Riot.

Uso: ``await limitador.adquirir()`` justo antes de cada petición a Riot.
"""
import asyncio
import time
from collections import deque

from app.core.config import settings

_PREFIJO = "divisionup:riot_rl"


class LimitadorRiot:
    def __init__(self) -> None:
        self._redis = None
        self._redis_intentado = False
        self._lock = asyncio.Lock()
        self._ultimo_s: deque[float] = deque()      # timestamps última ventana de 1 s
        self._ultimo_2m: deque[float] = deque()     # timestamps última ventana de 120 s

    # ------------------------------ Redis ------------------------------
    def _conexion_redis(self):
        """Conexión asyncio a Redis (lazy). None si no hay REDIS_URL o falla."""
        if self._redis_intentado:
            return self._redis
        self._redis_intentado = True
        if not settings.redis_url:
            return None
        try:
            import redis.asyncio as aioredis
            self._redis = aioredis.from_url(settings.redis_url, decode_responses=True)
        except Exception:
            self._redis = None
        return self._redis

    async def _adquirir_redis(self, r) -> None:
        while True:
            ahora = time.time()
            clave_s = f"{_PREFIJO}:s:{int(ahora)}"
            clave_2m = f"{_PREFIJO}:m:{int(ahora // 120)}"
            pipe = r.pipeline()
            pipe.incr(clave_s)
            pipe.expire(clave_s, 2)
            pipe.incr(clave_2m)
            pipe.expire(clave_2m, 130)
            n_s, _, n_2m, _ = await pipe.execute()
            if n_s <= settings.riot_rate_rps and n_2m <= settings.riot_rate_per_2min:
                return
            # Pasados de cupo: deshacemos nuestra cuenta y esperamos.
            pipe = r.pipeline()
            pipe.decr(clave_s)
            pipe.decr(clave_2m)
            await pipe.execute()
            # Si lo que está lleno es la ventana de 2 min, la espera útil es mayor.
            espera = 1.0 if n_s > settings.riot_rate_rps else 5.0
            await asyncio.sleep(espera)

    # ------------------------------ Local ------------------------------
    async def _adquirir_local(self) -> None:
        while True:
            async with self._lock:
                ahora = time.time()
                while self._ultimo_s and ahora - self._ultimo_s[0] >= 1.0:
                    self._ultimo_s.popleft()
                while self._ultimo_2m and ahora - self._ultimo_2m[0] >= 120.0:
                    self._ultimo_2m.popleft()
                if (len(self._ultimo_s) < settings.riot_rate_rps
                        and len(self._ultimo_2m) < settings.riot_rate_per_2min):
                    self._ultimo_s.append(ahora)
                    self._ultimo_2m.append(ahora)
                    return
                lleno_2m = len(self._ultimo_2m) >= settings.riot_rate_per_2min
            await asyncio.sleep(5.0 if lleno_2m else 0.2)

    # ------------------------------ API ------------------------------
    async def adquirir(self) -> None:
        """Bloquea hasta que haya hueco en ambas ventanas."""
        r = self._conexion_redis()
        if r is not None:
            try:
                await self._adquirir_redis(r)
                return
            except Exception:
                # Redis caído: degradar a local antes que parar el producto.
                pass
        await self._adquirir_local()


limitador = LimitadorRiot()
