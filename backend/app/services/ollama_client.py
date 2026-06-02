"""Cliente de IA configurable — Ollama (local), Groq u OpenRouter (APIs gratuitas).

Se elige con LLM_PROVIDER (ollama | groq | openrouter). Se mantiene el nombre del
módulo y de `OllamaError` por compatibilidad con el resto del backend.
- Ollama      → privado/local (la VM lo aguanta; lento en CPU).
- Groq        → gratis y muy rápido. 8b-instant (volumen) o 70b-versatile (calidad).
- OpenRouter  → gratis, acceso a modelos grandes (DeepSeek V4 Flash, Nemotron…).
Groq y OpenRouter comparten API estilo OpenAI: un único helper `_openai_chat`.
"""
import asyncio

import httpx
from app.core.config import settings


class OllamaError(Exception):
    """La IA (Ollama / Groq / OpenRouter) no está disponible o devolvió un error."""


def current_model() -> str:
    """Modelo activo según el proveedor configurado (para guardar en los informes)."""
    if settings.llm_provider == "groq":
        return settings.groq_model
    if settings.llm_provider == "openrouter":
        return settings.openrouter_model
    return settings.ollama_model


class OllamaClient:
    async def generate(self, prompt: str, system: str | None = None, json_mode: bool = False) -> str:
        if settings.llm_provider == "groq":
            return await self._openai_chat(
                "https://api.groq.com/openai/v1/chat/completions",
                settings.groq_api_key, settings.groq_model, "Groq", prompt, system, json_mode,
            )
        if settings.llm_provider == "openrouter":
            return await self._openai_chat(
                "https://openrouter.ai/api/v1/chat/completions",
                settings.openrouter_api_key, settings.openrouter_model, "OpenRouter",
                prompt, system, json_mode,
                extra_headers={"HTTP-Referer": "https://synapse.gg", "X-Title": "Synapse"},
            )
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

    # --- Groq / OpenRouter (API compatible OpenAI), con reintento ante 429 ---
    async def _openai_chat(self, url, api_key, model, label, prompt, system, json_mode, extra_headers=None):
        if not api_key:
            raise OllamaError(f"Falta la API key de {label} en el .env.")
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        payload = {"model": model, "messages": messages, "temperature": settings.llm_temperature}
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        headers = {"Authorization": f"Bearer {api_key}"}
        if extra_headers:
            headers.update(extra_headers)
        # 70B/DeepSeek razonan más despacio: timeout amplio.
        async with httpx.AsyncClient(timeout=120.0) as client:
            for attempt in range(4):
                try:
                    r = await client.post(url, json=payload, headers=headers)
                except httpx.HTTPError as e:
                    raise OllamaError(f"No se pudo contactar con {label}. Revisa la API key / el modelo. Detalle: {e}")
                if r.status_code == 429:  # rate limit del free tier → espera (Retry-After) y reintenta
                    if attempt < 3:
                        wait = min(float(r.headers.get("retry-after", 2 ** attempt)), 20)
                        await asyncio.sleep(wait)
                        continue
                    raise OllamaError(
                        f"Límite de {label} (free tier) alcanzado (429). Espera ~1 min y reintenta, "
                        "o analiza menos partidas de golpe."
                    )
                if r.status_code >= 400:
                    raise OllamaError(f"{label} devolvió {r.status_code}. Revisa la API key / el modelo. Detalle: {r.text[:200]}")
                data = r.json()
                try:
                    return data["choices"][0]["message"]["content"]
                except (KeyError, IndexError):
                    raise OllamaError(f"{label} devolvió una respuesta inesperada: {str(data)[:200]}")


ollama_client = OllamaClient()
