"""Synapse API — punto de entrada FastAPI (ETAPA 2).

En la Fase 0 la API responde con datos de EJEMPLO (mock) que replican el
prototipo, para poder conectar el frontend cuanto antes. En las siguientes
fases, los servicios de Riot y de IA (Ollama) sustituyen esos mocks.

# AQUÍ se conectan los datos reales: Riot API + IA local (Ollama) en Fases 1-3.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import health, riot, coaching, stats, meta, chat, lab

app = FastAPI(
    title="Synapse API",
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
app.include_router(coaching.router)
app.include_router(stats.router)
app.include_router(meta.router)
app.include_router(chat.router)
app.include_router(lab.router)


@app.get("/", tags=["meta"])
def root():
    """Raíz informativa."""
    return {
        "app": "Synapse API",
        "version": app.version,
        "modo": "mock" if settings.use_mock else "real",
        "docs": "/docs",
    }
