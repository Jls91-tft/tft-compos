"""Worker: refresca los datos de meta REALES y los guarda en JSON.

Uso (en el PC con clave de PRODUCCIÓN de Riot y USE_MOCK=false):
    python -m app.worker.refresh_meta            # ambos juegos
    python -m app.worker.refresh_meta tft        # solo TFT

En la beta lo lanza el servicio 'meta-worker' (docker-compose.prod.yml,
perfil 'meta') en bucle cada META_REFRESH_SECONDS.
"""
import asyncio
import sys

from app.services import meta_pipeline, meta_store


async def main() -> None:
    games = [g for g in sys.argv[1:] if g in ("tft", "lol")] or ["tft", "lol"]
    for game in games:
        try:
            payload = await meta_pipeline.run(game)
            meta_store.save_explorer(game, payload)
            s = payload.get("sample", {})
            print(
                f"[meta] {game}: {s.get('players', 0)} jugadores, "
                f"{s.get('matches', 0)} partidas → {len(payload.get('units', []))} unidades"
            )
        except Exception as e:  # noqa: BLE001 — el worker no debe caer por un juego
            print(f"[meta] {game} ERROR: {e}")


if __name__ == "__main__":
    asyncio.run(main())
