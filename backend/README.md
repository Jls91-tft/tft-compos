# Backend — Aevyn API (FastAPI)

API de coaching IA + estadísticas para TFT y LoL.

## Estructura
```
app/
├── main.py            # arranque FastAPI, CORS, registro de routers
├── core/config.py     # Settings (lee .env): Riot, Ollama, USE_MOCK, CORS
├── routers/           # endpoints HTTP
│   ├── health.py      #   /health, /healthz
│   ├── riot.py        #   /riot/account (Riot ID → puuid)
│   ├── coaching.py    #   /coaching/matches, /coaching/report/...
│   ├── stats.py       #   /stats
│   ├── meta.py        #   /meta
│   └── chat.py        #   /chat
├── services/          # lógica
│   ├── riot_client.py     # Riot API (routing regional, caché, rate limit)
│   ├── ollama_client.py   # IA local (/api/chat, modo JSON)
│   ├── coaching_engine.py # orquesta Riot + IA → informe
│   ├── stats_engine.py    # agrega historial → estadísticas
│   ├── prompts.py         # voz del coach + extracción + parseo del informe
│   └── cache.py           # caché TTL en memoria
├── schemas/models.py  # contratos Pydantic (API ↔ frontend)
└── data/mock.py       # datos de ejemplo (modo USE_MOCK)
```

## Modo mock vs. real
`USE_MOCK` (en `.env`) decide el comportamiento de cada endpoint:
- `true` → responde desde `data/mock.py` (sin clave de Riot ni Ollama). Ideal para desarrollar el frontend.
- `false` → usa `riot_client` + `ollama_client` reales.

Patrón en routers/servicios:
```python
if settings.use_mock:
    return mock.algo(...)
# ... lógica real con Riot/Ollama ...
```

## Ejecutar
Lo normal es vía Docker Compose (raíz del repo). En local, para desarrollo:
```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000   # docs en http://localhost:8000/docs
```
> Recuerda: en el equipo de desarrollo actual NO se ejecuta nada; esto es para el otro PC.

## Cómo añadir un endpoint
1. Crea/edita un router en `routers/`.
2. Regístralo en `main.py` (`app.include_router(...)`).
3. Define el modelo de respuesta en `schemas/models.py`.
4. Añade su versión de ejemplo en `data/mock.py` y respeta `USE_MOCK`.

## Riot API (notas)
- `account-v1`, `match-v5` (LoL) y `tft-match-v1` (TFT) usan host **regional** (`RIOT_REGION`).
- El detalle de partida se cachea 24 h (inmutable). Reintento ante `429` respetando `Retry-After`.

## IA: Ollama (local) o Groq (API)
`LLM_PROVIDER` elige el backend de IA (`ollama` | `groq`), en `services/ollama_client.py`.
- **Ollama** (`/api/chat`, `format: json`): privado/local. Modelo en `OLLAMA_MODEL`.
- **Groq** (API estilo OpenAI, gratis/rápido): clave en `GROQ_API_KEY`, modelo en `GROQ_MODEL`. Recomendado para la beta.

## Worker de meta (datos reales del Lab)
`/lab/explorer` puede servir estadísticas **reales** (winrate y uso de unidades, ítems y augments) en vez del mock. Las genera un worker que agrega partidas del ladder Challenger vía Riot API (ver `docs/DATOS.md`).
- `services/meta_pipeline.py` — muestrea el ladder, descarga partidas y agrega.
- `services/meta_store.py` — lee/escribe los JSON en `data/generated/` (ignorado por git).
- `worker/refresh_meta.py` — entrypoint del worker.
```bash
python -m app.worker.refresh_meta            # requiere USE_MOCK=false + clave de producción
```
En la beta se lanza con `docker compose -f docker-compose.prod.yml --profile meta up -d`.
Sin datos generados, `/lab/explorer` cae al mock (`data/mock_lab.py`).
