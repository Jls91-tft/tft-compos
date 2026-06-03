# Fuentes de datos de DivisionUp

Aclaración clave: hay **dos tipos de datos** con orígenes muy distintos.

## 1. Datos personales (tu perfil) y coaching → Riot API directa
- **Tu perfil / estadísticas**: salen de **tu historial** de partidas (Riot API: `match-v5` / `tft-match-v1`). Las agrega el backend (`backend/app/services/stats_engine.py`).
- **Coaching post-partida**: la partida concreta (Riot API) + la **IA local** (Ollama).
- ✅ Ya implementado. Funciona con la clave de Riot del usuario.

## 2. Meta global (winrate de ítems, mejores comps, augments, tier list) → pipeline de agregación
La Riot API **no** devuelve "el ítem X tiene 60% de winrate". Devuelve **partidas individuales**.
Las estadísticas de meta se **calculan agregando muchísimas partidas de alto elo**, igual que hacen MetaTFT, tactics.tools o Mobalytics.

### Pipeline necesario (worker en segundo plano)
1. **Leaderboards** por región (`league-v4` / `tft-league-v1`): los mejores jugadores (Challenger, GM, Master).
2. Por cada jugador: su **historial** y el **detalle de cada partida** (unidades, ítems, augments, colocación, rasgos…).
3. **ETL / agregación**: por cada ítem/unidad/augment/comp → colocación media, winrate, pick rate, etc.
4. Guardar agregados en **BD** y servirlos desde la API; refrescar por parche / cada X minutos.

### Consideraciones
- **Rate limits de Riot**: recolectar a gran escala requiere una **production API key** (aprobación de Riot, límites más altos) y gestionar el *rate limiting*.
- **Volumen y coste**: almacenar y procesar tantas partidas tiene coste (BD + cómputo). Es infraestructura aparte de la app.
- **Frescura**: la meta cambia con cada parche → el pipeline debe re-procesar.

### Opciones (de menor a mayor esfuerzo)
- **A. Mock** (estado actual): datos de ejemplo en `backend/app/data/mock_lab.py` y `mock.py`. Para diseñar/demostrar.
- **B. Pipeline ligero** ✅ **IMPLEMENTADO**: una sola región + solo Challenger + muestreo. Meta orientativa, coste bajo. Es el worker `backend/app/services/meta_pipeline.py` + `app/worker/refresh_meta.py`.
- **C. Pipeline completo**: todas las regiones, gran volumen (como MetaTFT). Requiere production key + infra.
- **D. Curaduría**: comps/guías definidas por expertos (estilo TFT Academy); los números (ítems/augments) salen igual del pipeline.

## Estado actual en el código
- `/stats` (perfil) → **datos reales** del historial del jugador (cuando `USE_MOCK=false`).
- `/lab/explorer` → **datos reales** (winrate y uso de unidades, ítems y augments) agregados por el **worker de meta** (opción B) cuando `USE_MOCK=false` y el worker ha generado los JSON; si no, mock.
- `/lab/recipes`, `/lab/gpi`, `/lab/champion` y `/meta` → **mock/curado** (recetas = conocimiento estático; GPI = pipeline personal; build de campeón y la tier list de comps quedan pendientes/curados).
- El cambio a datos reales no altera la forma de las respuestas (mismo contrato): solo se sustituye el origen.

### Cómo ejecutar el worker de meta (en el PC con clave de producción)
```bash
# una pasada (con USE_MOCK=false y RIOT_API_KEY de producción en el .env):
python -m app.worker.refresh_meta          # TFT y LoL
python -m app.worker.refresh_meta tft      # solo TFT
# en la beta, en bucle automático cada META_REFRESH_SECONDS:
docker compose -f docker-compose.prod.yml --profile meta up -d
```
Escribe `backend/app/data/generated/explorer_<juego>.json`, que sirve `/lab/explorer`.
Nota: TFT agrega unidades, ítems y augments completos; LoL agrega **campeones** (winrate/uso/rol) — sus ítems y runas requieren mapear ids con **Data Dragon** (trabajo futuro).
