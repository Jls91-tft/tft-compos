"""Cliente de la IA local (Ollama).

ESTADO: stub (Fase 2). Se conecta al servicio 'ollama' del docker-compose.
La descarga del modelo se hace una vez en el otro PC:
    docker compose exec ollama ollama pull llama3.1:8b
"""
import httpx
from app.core.config import settings


class OllamaClient:
    def __init__(self) -> None:
        self.host = settings.ollama_host
        self.model = settings.ollama_model

    async def generate(self, prompt: str, system: str | None = None) -> str:
        """Genera texto con el modelo local (Ollama /api/generate)."""
        # AQUÍ (Fase 2):
        # async with httpx.AsyncClient(timeout=120) as c:
        #     r = await c.post(f"{self.host}/api/generate",
        #         json={"model": self.model, "prompt": prompt, "system": system, "stream": False})
        #     return r.json()["response"]
        raise NotImplementedError("Integración Ollama pendiente (Fase 2)")


ollama_client = OllamaClient()
