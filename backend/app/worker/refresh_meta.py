"""Worker: refresca los datos de meta REALES y los guarda en JSON.

Reutiliza UNA SOLA descarga del ladder para alimentar dos agregaciones:
- ``explorer_{game}.json`` → /lab/explorer (unidades, ítems, aumentos)
- ``comps_tft.json``       → /meta (tier list de comps, solo TFT)

Uso (en el PC con clave de PRODUCCIÓN de Riot y USE_MOCK=false):
    python -m app.worker.refresh_meta            # ambos juegos
    python -m app.worker.refresh_meta tft        # solo TFT

En la beta lo lanza el servicio 'meta-worker' (docker-compose.prod.yml,
perfil 'meta') en bucle cada META_REFRESH_SECONDS.
"""
import asyncio
import sys

from app.services import comps_pipeline, meta_pipeline, meta_store


async def _refresh(game: str) -> None:
    matches = await meta_pipeline.fetch_sample(game)

    # 1) Explorer (unidades/ítems/aumentos) — ambos juegos.
    explorer = meta_pipeline.aggregate_explorer(game, matches)
    meta_store.save_explorer(game, explorer)

    # 2) Comps (tier list) — solo TFT (LoL no tiene 'comp' análoga).
    n_comps = 0
    if game == "tft":
        comps = comps_pipeline.run_sync(matches)
        meta_store.save_comps("tft", comps)
        n_comps = len(comps.get("comps", []))

    n_units = len(explorer.get("units", []))
    print(
        f"[meta] {game}: {len(matches)} partidas → "
        f"{n_units} unidades, {n_comps} comps"
    )


async def main() -> None:
    games = [g for g in sys.argv[1:] if g in ("tft", "lol")] or ["tft", "lol"]
    for game in games:
        try:
            await _refresh(game)
        except Exception as e:  # noqa: BLE001 — el worker no debe caer por un juego
            print(f"[meta] {game} ERROR: {e}")


if __name__ == "__main__":
    asyncio.run(main())
