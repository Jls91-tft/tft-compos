# Synapse — Coaching IA + estadísticas para TFT y LoL

Plataforma con dos funciones:
- **Coaching IA (principal):** tras cada partida, genera un informe con errores, correcciones y consejos accionables; incluye chat con el coach. Para **TFT** y **LoL**.
- **Estadísticas y Meta (complemento):** dashboard personal con insights y tier list de comps con guías.

> Marca propia genérica. No está afiliada, asociada ni respaldada por los titulares de los juegos.

> 🤖 **¿Eres un agente de IA?** Lee primero [`CLAUDE.md`](CLAUDE.md) — contiene el contexto, las reglas y la estructura del repo.

---

## Estado del proyecto

- **Etapa 1 — Prototipo (cerrado):** maquetas HTML autónomas en [`synapse-prototipo/`](synapse-prototipo/) (tag `prototipo-etapa-1`).
- **Etapa 2 — Producto:** backend FastAPI + Riot API + IA local (Ollama) + frontend conectado, orquestado con Docker Compose.

### Fases de la Etapa 2
- [x] **Fase 0** — Andamiaje: estructura, Docker, API con datos de ejemplo (mock).
- [x] **Fase 1** — Integración Riot API (partidas reales).
- [x] **Fase 2** — Motor de coaching con Ollama + chat.
- [x] **Fase 3** — Estadísticas personales agregadas (meta global = dataset curado).
- [x] **Fase 4** — Conectar el frontend (reemplazar mocks por `fetch`).
- [x] **Fase 5** — Despliegue final (Compose con healthchecks y auto-pull del modelo).

---

## Puesta en marcha (en el PC de desarrollo)

> Requisitos: **Docker Desktop** (o Docker + Compose) y **Git**. No hace falta instalar Python, Node ni Ollama a mano.

```bash
# 1) Clonar
git clone https://github.com/Jls91-tft/tft-compos.git
cd tft-compos

# 2) Configurar variables de entorno
cp .env.example .env
#    Edita .env: pon tu clave de Riot (https://developer.riotgames.com).
#    Puedes empezar con USE_MOCK=true para probar sin clave todavía.

# 3) Levantar todo (la primera vez descarga el modelo de IA automáticamente)
docker compose up -d --build
```

Cuando los servicios estén "healthy":
- **Frontend:** http://localhost:8080
- **API (docs interactivas):** http://localhost:8000/docs

Parar: `docker compose down`  ·  Ver estado: `docker compose ps`  ·  Logs: `docker compose logs -f api`.

### Modo mock vs. real
- `USE_MOCK=true` → la API responde con datos de ejemplo (prueba el frontend sin clave de Riot ni modelo).
- `USE_MOCK=false` → usa Riot API + Ollama reales. Necesitas `RIOT_API_KEY` y haber descargado el modelo (lo hace `ollama-pull`).

---

## Servicios y salud
- `api` expone `/health` y tiene healthcheck; `web` no arranca hasta que la API está *healthy*.
- `ollama` se comprueba con `ollama list`; `ollama-pull` espera a que esté sano, descarga `OLLAMA_MODEL` y termina.
- El modelo se guarda en el volumen `ollama_models` (persistente entre reinicios).

## Estructura

```
tft-compos/
├── CLAUDE.md / AGENTS.md  # Guía para agentes de IA (contexto y reglas)
├── docs/ARCHITECTURE.md   # Arquitectura y flujo de datos
├── synapse-prototipo/     # Prototipo de la Etapa 1 (referencia visual, doble clic)
├── backend/               # API FastAPI (ver backend/README.md)
├── frontend/              # Frontend de producción (ver frontend/README.md)
├── nginx/                 # nginx: sirve frontend + proxy /api
├── docker-compose.yml     # api + web + ollama (+ ollama-pull)
└── .env.example           # plantilla de variables de entorno
```

## Seguridad
- Las credenciales (clave de Riot) van en `.env`, **nunca** en el código. `.env` está en `.gitignore`.
- No subas claves reales al repositorio. Si una clave se expone, **revócala y genera otra**.
- CORS configurable en `backend/app/core/config.py` (`cors_origins`).
