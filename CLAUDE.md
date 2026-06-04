# CLAUDE.md — Guía para agentes de IA

> Léelo antes de tocar nada. Resume el proyecto, las reglas y dónde está cada cosa.
> Documentación complementaria: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md), [`backend/README.md`](backend/README.md), [`frontend/README.md`](frontend/README.md).

## Qué es DivisionUp
Plataforma de **coaching IA + estadísticas** para **TFT** (auto-battler) y **LoL** (MOBA).
El **coaching tras cada partida es el diferencial** (errores, correcciones, plan accionable y chat con el coach). Estadísticas y meta son complementos.

## Reglas no negociables
1. **Idioma:** responde y documenta en **español**.
2. **Marca propia genérica:** NUNCA uses logos, marcas registradas o el nombre "Riot" en branding propio (logo, nombre del producto, materiales de marketing). Sí está permitido usar nombres reales de campeones/rasgos/ítems/aumentos cuando provengan de:
   - **Datos de la partida del usuario** vía la Riot Games API oficial.
   - **Asset estático oficial** vía Data Dragon o CommunityDragon (idéntico camino que usan MetaTFT, Lolchess, Tactics.tools…).
   Tanto el mock dinámico (`data/mock_cdragon.py`) como las agregaciones reales (`services/comps_pipeline._cdragon_enrich`) usan CDragon. El mock estático invented (`data/mock.py`, arquetipos Místico/Vanguardia) sigue existiendo como último fallback cuando CDragon no responde.
3. **Secretos:** la clave de Riot va en `.env` (en `.gitignore`). Nunca en el código ni en commits. En `.env.example` solo placeholders. Si se expone una clave, **revócala**.
4. **Versionado:** commits en **castellano**, claros, y **`git push`** tras cada avance. Repo: `github.com/Jls91-tft/tft-compos` (rama `main`).
5. **Entorno de desarrollo actual:** se escribe el código pero **NO se instala ni ejecuta** el stack en este equipo (Windows). La ejecución real (Docker, instalaciones, Ollama) se hace en **otro PC**. No lances `pip` / `npm` / `docker` / `ollama` aquí salvo petición explícita.

## Estado
- **Etapa 1** (prototipo HTML autónomo): cerrada → `synapse-prototipo/` (tag `prototipo-etapa-1`).
- **Etapa 2** (producto): fases 0-5 completas (andamiaje, Riot API, coaching Ollama, stats, frontend, despliegue).

## Arquitectura (resumen)
```
navegador → nginx (web, :8080) ──/──> frontend estático
                                └─/api─> FastAPI (api, :8000) ──> Riot API
                                                              └─> Ollama (IA local, :11434)
```
Detalle y flujo de datos en [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## Estructura del repo
```
backend/        API FastAPI            → backend/README.md
frontend/       App de producción      → frontend/README.md
nginx/          Sirve frontend + proxy /api
synapse-prototipo/   Prototipo Etapa 1 (referencia visual, se abre con doble clic)
docs/           Documentación
docker-compose.yml · .env.example · README.md
```

## Cómo ejecutar (en el PC con Docker)
```bash
cp .env.example .env      # editar: RIOT_API_KEY, USE_MOCK
docker compose up -d --build
```
Frontend en `:8080`, API en `:8000/docs`. `USE_MOCK=true` → datos de ejemplo (sin clave ni IA); `false` → Riot + Ollama reales.

## Convenciones clave
- **El contrato API↔frontend** son los **schemas Pydantic** en `backend/app/schemas/models.py`. Si cambias una respuesta, cambia el schema.
- **Datos de ejemplo** centralizados en `backend/app/data/mock.py`. Patrón en cada router/servicio: `if settings.use_mock: return mock...` ; si no, lógica real. Así el frontend se integra antes de tener Riot/IA.
- **Servicios** (`backend/app/services/`): `riot_client` (Riot API), `ollama_client` (IA), `coaching_engine` (orquesta), `stats_engine` (agrega historial), `prompts` (voz del coach + extracción + parseo).
- **Frontend vanilla** (sin framework): `frontend/assets/` (`api.js`, `charts.js`, `synapse.css`) + páginas HTML. Se sirve con nginx; **no** funciona abriendo el HTML con doble clic (hace `fetch` a `/api`).

## Tareas típicas
- **Añadir endpoint:** crea el router en `backend/app/routers/`, inclúyelo en `backend/app/main.py`, define el schema en `schemas/models.py` y el mock en `data/mock.py`.
- **Mejorar la calidad/voz del coaching:** `backend/app/services/prompts.py` (`COACH_SYSTEM` y los `build_*_prompt`).
- **Tocar el diseño:** `frontend/assets/synapse.css` (design system con tokens).
- **Añadir una pantalla:** nueva página en `frontend/`, enlázala desde la navegación; usa `synapse.css` y `api.js`.

## Nota sobre la Meta global
La tier list del parche **no** se puede derivar del historial de un solo jugador. Hay dos pipelines reales sobre la Riot API oficial (muestreo Challenger):
- `services/meta_pipeline.py` → unidades/ítems/aumentos para `/lab/explorer`.
- `services/comps_pipeline.py` → clusteriza tableros por rasgos+carry para `/meta` (TFT).
Ambos los alimenta el worker (`app/worker/refresh_meta.py`, perfil `meta` del Compose) cada `META_REFRESH_SECONDS`. Si el JSON no existe (clave Dev caducada, worker apagado), los routers caen al mock genérico.
