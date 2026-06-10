"""DivisionUp API — punto de entrada FastAPI (ETAPA 2).

En la Fase 0 la API responde con datos de EJEMPLO (mock) que replican el
prototipo, para poder conectar el frontend cuanto antes. En las siguientes
fases, los servicios de Riot y de IA (Ollama) sustituyen esos mocks.

# AQUÍ se conectan los datos reales: Riot API + IA local (Ollama) en Fases 1-3.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
# FASE 4: el motor LLM antiguo (coaching, chat) queda DESCONECTADO del producto.
# Los módulos siguen en el repo hasta el OK de borrado físico, pero no se sirven.
from app.routers import analisis, debug, health, lab, meta, riot, stats, waitlist

app = FastAPI(
    title="DivisionUp API",
    description="Coaching IA y estadísticas para auto-battler (TFT) y MOBA (LoL).",
    version="0.2.0-etapa2",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers de la API
app.include_router(health.router)
app.include_router(riot.router)
app.include_router(analisis.router)   # núcleo: matches, report, feedback, objective, rank, account
app.include_router(debug.router)      # visor interno protegido por DEBUG_TOKEN
app.include_router(stats.router)
app.include_router(meta.router)
app.include_router(lab.router)
app.include_router(waitlist.router)


@app.get("/", tags=["meta"])
def root():
    """Raíz informativa."""
    return {
        "app": "DivisionUp API",
        "version": app.version,
        "modo": "mock" if settings.use_mock else "real",
        "docs": "/docs",
    }
