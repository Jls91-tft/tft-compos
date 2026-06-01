"""Cliente de IA configurable — Ollama (local) o Groq (API gratuita y rápida).

Se elige con LLM_PROVIDER (ollama | groq). Se mantiene el nombre del módulo y de
`OllamaError` por compatibilidad con el resto del backend.
- Ollama  → privado/local (la VM lo aguanta; lento en CPU).
- Groq    → gratis y muy rápido (ideal para la beta). API estilo OpenAI.
"""
import httpx
from app.core.config import settings


class OllamaError(Exception):
    """La IA (Ollama o Groq) no está disponible o devolvió un error."""


class OllamaClient:
    async def generate(self, prompt: str, system: str | None = None, json_mode: bool = False) -> str:
        if settings.llm_provider == "groq":
            return await self._groq(prompt, system, json_mode)
        return await self._ollama(prompt, system, json_mode)

    # --- Ollama local (/api/chat) ---
    async def _ollama(self, prompt, system, json_mode):
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        payload = {"model": settings.ollama_model, "messages": messages, "stream": False}
        if json_mode:
            payload["format"] = "json"
        try:
            async with httpx.AsyncClient(timeout=180.0) as client:
                r = await client.post(f"{settings.ollama_host}/api/chat", json=payload)
                r.raise_for_status()
                return r.json()["message"]["content"]
        except httpx.HTTPError as e:
            raise OllamaError(
                f"No se pudo contactar con Ollama en {settings.ollama_host}. "
                f"¿Está levantado y el modelo '{settings.ollama_model}' descargado? Detalle: {e}"
            )

    # --- Groq (API compatible OpenAI) ---
    async def _groq(self, prompt, system, json_mode):
        if not settings.groq_api_key:
            raise OllamaError("Falta GROQ_API_KEY en el .env (consíguela gratis en console.groq.com).")
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        payload = {"model": settings.groq_model, "messages": messages, "temperature": 0.4}
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        headers = {"Authorization": f"Bearer {settings.groq_api_key}"}
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                r = await client.post("https://api.groq.com/openai/v1/chat/completions", json=payload, headers=headers)
                r.raise_for_status()
                return r.json()["choices"][0]["message"]["content"]
        except httpx.HTTPError as e:
            raise OllamaError(f"No se pudo contactar con Groq. Revisa GROQ_API_KEY / el modelo. Detalle: {e}")


ollama_client = OllamaClient()
