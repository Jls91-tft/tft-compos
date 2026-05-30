"""Cliente de la Riot API (TFT + LoL) — Fase 1.

Resuelve Riot ID → puuid, historial y detalle de partidas. Incluye:
  - routing regional (europe/americas/asia) para account-v1 y match
  - control de concurrencia (semáforo) y reintento ante 429 (Retry-After)
  - caché: detalle de partida 24 h (inmutable), historial 60 s

La clave (RIOT_API_KEY) se lee del entorno; nunca está en el código.
"""
import asyncio
import httpx

from app.core.config import settings
from app.services.cache import TTLCache

_match_cache = TTLCache()   # detalle de partida (inmutable)
_ids_cache = TTLCache()     # historial de IDs (cambia poco)


class RiotApiError(Exception):
    """Error de la Riot API con código HTTP y mensaje legible."""

    def __init__(self, status: int, message: str) -> None:
        self.status = status
        self.message = message
        super().__init__(f"[{status}] {message}")


class RiotClient:
    def __init__(self) -> None:
        self._sem = asyncio.Semaphore(settings.riot_max_concurrency)

    @property
    def _regional(self) -> str:
        return f"https://{settings.riot_region}.api.riotgames.com"

    async def _get(self, url: str) -> dict:
        if settings.riot_api_key.startswith("RGAPI-PON"):
            raise RiotApiError(401, "Falta configurar RIOT_API_KEY en el .env")
        headers = {"X-Riot-Token": settings.riot_api_key}
        async with self._sem:
            async with httpx.AsyncClient(timeout=settings.http_timeout) as client:
                for _ in range(3):
                    r = await client.get(url, headers=headers)
                    if r.status_code == 429:
                        await asyncio.sleep(float(r.headers.get("Retry-After", "1")))
                        continue
                    if r.status_code == 404:
                        raise RiotApiError(404, "Recurso no encontrado en Riot")
                    if r.status_code in (401, 403):
                        raise RiotApiError(r.status_code, "Clave de Riot inválida o sin permisos")
                    r.raise_for_status()
                    return r.json()
        raise RiotApiError(429, "Límite de peticiones de Riot alcanzado, inténtalo de nuevo")

    async def get_puuid(self, game_name: str, tag_line: str) -> str:
        """Riot ID (Nombre#TAG) → puuid (account-v1)."""
        url = f"{self._regional}/riot/account/v1/accounts/by-riot-id/{game_name}/{tag_line}"
        data = await self._get(url)
        return data["puuid"]

    async def get_match_ids(self, puuid: str, game: str, count: int = 8) -> list[str]:
        """IDs de las últimas partidas (match-v5 LoL · tft-match-v1 TFT)."""
        key = f"{game}:{puuid}:{count}"
        cached = _ids_cache.get(key)
        if cached is not None:
            return cached
        if game == "tft":
            url = f"{self._regional}/tft/match/v1/matches/by-puuid/{puuid}/ids?count={count}"
        else:
            url = f"{self._regional}/lol/match/v5/matches/by-puuid/{puuid}/ids?start=0&count={count}"
        ids = await self._get(url)
        _ids_cache.set(key, ids, ttl=60)
        return ids

    async def get_match(self, match_id: str, game: str) -> dict:
        """Detalle completo de una partida (cacheado, es inmutable)."""
        cached = _match_cache.get(match_id)
        if cached is not None:
            return cached
        if game == "tft":
            url = f"{self._regional}/tft/match/v1/matches/{match_id}"
        else:
            url = f"{self._regional}/lol/match/v5/matches/{match_id}"
        data = await self._get(url)
        _match_cache.set(match_id, data, ttl=86400)
        return data


riot_client = RiotClient()
