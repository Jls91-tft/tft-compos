"""Cliente de la IA local (Ollama) — Fase 2.

Se conecta al servicio 'ollama' del docker-compose. La descarga del modelo se
hace una vez en el otro PC:
    docker compose exec ollama ollama pull llama3.1:8b
"""
import httpx
from app.core.config import settings


class OllamaError(Exception):
    """La IA local no está disponible o devolvió un error."""


class OllamaClient:
    def __init__(self) -> None:
        self.host = settings.ollama_host
        self.model = settings.ollama_model

    async def generate(self, prompt: str, system: str | None = None, json_mode: bool = False) -> str:
        """Genera texto con el modelo local (endpoint /api/chat de Ollama).

        json_mode=True fuerza salida JSON (para el informe estructurado).
        """
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload = {"model": self.model, "messages": messages, "stream": False}
        if json_mode:
            payload["format"] = "json"

        try:
            async with httpx.AsyncClient(timeout=180.0) as client:
                r = await client.post(f"{self.host}/api/chat", json=payload)
                r.raise_for_status()
                return r.json()["message"]["content"]
        except httpx.HTTPError as e:
            raise OllamaError(
                f"No se pudo contactar con la IA local (Ollama) en {self.host}. "
                f"¿Está levantado el servicio y descargado el modelo '{self.model}'? Detalle: {e}"
            )


ollama_client = OllamaClient()
