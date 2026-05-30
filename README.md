# Synapse — Coaching IA + estadísticas para TFT y LoL

Plataforma con dos funciones:
- **Coaching IA (principal):** tras cada partida, genera un informe con errores, correcciones y consejos accionables; incluye chat con el coach. Para **TFT** y **LoL**.
- **Estadísticas y Meta (complemento):** dashboard personal con insights y tier list de comps con guías.

> Marca propia genérica. No está afiliada, asociada ni respaldada por los titulares de los juegos.

---

## Estado del proyecto

- **Etapa 1 — Prototipo (cerrado):** maquetas HTML autónomas en [`synapse-prototipo/`](synapse-prototipo/) (tag `prototipo-etapa-1`).
- **Etapa 2 — Producto (en curso):** backend FastAPI + Riot API + IA local (Ollama) + frontend conectado, todo orquestado con Docker Compose.

### Fases de la Etapa 2
- [x] **Fase 0** — Andamiaje: estructura, Docker, API con datos de ejemplo (mock).
- [x] **Fase 1** — Integración Riot API (partidas reales).
- [x] **Fase 2** — Motor de coaching con Ollama + chat.
- [x] **Fase 3** — Estadísticas personales agregadas (meta global = dataset curado).
- [ ] **Fase 4** — Conectar el frontend (reemplazar mocks por `fetch`).
- [ ] **Fase 5** — Despliegue final.

---

## Puesta en marcha (en el PC de desarrollo)

> Requisitos: **Docker Desktop** (o Docker + Compose) y **Git**. Nada más: no hace falta instalar Python, Node ni Ollama a mano.

```bash
# 1) Clonar
git clone https://github.com/Jls91-tft/tft-compos.git
cd tft-compos

# 2) Configurar variables de entorno
cp .env.example .env
#    Edita .env y pon tu clave de Riot (https://developer.riotgames.com).
#    Puedes empezar con USE_MOCK=true para probar sin clave todavía.

# 3) Levantar todo
docker compose up -d --build

# 4) Descargar el modelo de IA (solo la primera vez)
docker compose exec ollama ollama pull llama3.1:8b
```

Luego abre:
- **Frontend:** http://localhost:8080
- **API (docs interactivas):** http://localhost:8000/docs

Para parar: `docker compose down`.

### Modo mock vs. real
- `USE_MOCK=true` → la API responde con datos de ejemplo (útil para probar el frontend sin clave de Riot).
- `USE_MOCK=false` → usa Riot API + Ollama reales (a partir de las Fases 1-2).

---

## Estructura

```
tft-compos/
├── synapse-prototipo/     # Prototipo de la Etapa 1 (referencia visual)
├── backend/               # API FastAPI
│   └── app/
│       ├── main.py        # arranque + routers
│       ├── core/          # configuración (lee .env)
│       ├── routers/       # coaching · stats · meta · chat · health
│       ├── services/      # riot_client · ollama_client · coaching_engine
│       ├── schemas/       # contratos de datos (Pydantic)
│       └── data/          # datos de ejemplo (mock)
├── frontend/              # Frontend de producción (se conecta a la API en la Fase 4)
├── nginx/                 # Config de nginx (sirve frontend + proxy /api)
├── docker-compose.yml     # api + web + ollama
└── .env.example           # plantilla de variables de entorno
```

---

## Seguridad
- Las credenciales (clave de Riot) van en `.env`, **nunca** en el código. `.env` está en `.gitignore`.
- No subas claves reales al repositorio.
