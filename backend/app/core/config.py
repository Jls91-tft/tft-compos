"""Configuración central de Synapse. Lee variables de entorno / fichero .env.

Las credenciales NUNCA van en el código: se inyectan por entorno. Aquí solo
hay valores por defecto seguros y placeholders.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # --- Riot API ---
    # AQUÍ va tu clave de https://developer.riotgames.com (en el .env del otro PC).
    riot_api_key: str = "RGAPI-PON-TU-CLAVE-AQUI"
    riot_region: str = "europe"          # routing regional: americas | asia | europe
    riot_platform: str = "euw1"          # plataforma: euw1 | na1 | kr | ...
    default_riot_id: str = ""            # opcional: "Nombre#TAG" para pruebas rápidas
    http_timeout: float = 15.0
    riot_max_concurrency: int = 5

    # --- IA local (Ollama) ---
    ollama_host: str = "http://ollama:11434"
    ollama_model: str = "llama3.1:8b"

    # --- Aplicación ---
    cors_origins: list[str] = [
        "http://localhost",
        "http://localhost:8080",
        "http://localhost:5173",
    ]
    # Fase 0: True (la API devuelve mocks). Se pondrá a False al cablear Riot/Ollama.
    use_mock: bool = True


settings = Settings()
