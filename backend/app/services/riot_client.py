"""Cliente de la Riot API (TFT + LoL).

ESTADO: stub (Fase 1). La estructura está lista; la implementación real de las
llamadas se hará en el OTRO PC, con la RIOT_API_KEY en el entorno.

Endpoints que usaremos:
  - account-v1     : Riot ID (gameName#tagLine) -> puuid
  - match-v5       : historial y detalle de partidas de LoL
  - tft-match-v1   : historial y detalle de partidas de TFT
Consideraciones: rate limiting, caché (las partidas terminadas son inmutables).
"""
import httpx
from app.core.config import settings


class RiotClient:
    def __init__(self) -> None:
        self.key = settings.riot_api_key
        self.region = settings.riot_region      # americas | asia | europe
        self.platform = settings.riot_platform  # euw1 | na1 | kr ...
        self._headers = {"X-Riot-Token": self.key}

    async def get_puuid(self, game_name: str, tag_line: str) -> str:
        """Riot ID -> puuid (account-v1)."""
        # AQUÍ (Fase 1): GET https://{region}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{name}/{tag}
        raise NotImplementedError("Integración Riot pendiente (Fase 1)")

    async def get_match_ids(self, puuid: str, game: str, count: int = 10) -> list[str]:
        """Últimas partidas (match-v5 para LoL, tft-match-v1 para TFT)."""
        raise NotImplementedError("Integración Riot pendiente (Fase 1)")

    async def get_match(self, match_id: str, game: str) -> dict:
        """Detalle completo de una partida."""
        raise NotImplementedError("Integración Riot pendiente (Fase 1)")


riot_client = RiotClient()
