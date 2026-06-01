"""Health check — útil para Docker y para comprobar que la API vive."""
from fastapi import APIRouter
from app.core.config import settings

router = APIRouter(tags=["meta"])


@router.get("/health")
def health():
    return {"status": "ok", "mock": settings.use_mock, "model": settings.ollama_model}


@router.get("/healthz")
def healthz():
    """Alias corto para sondas de salud."""
    return {"status": "ok"}
