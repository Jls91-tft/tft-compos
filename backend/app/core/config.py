"""Configuración central de DivisionUp. Lee variables de entorno / fichero .env.

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

    # --- IA: proveedor configurable (ollama local | groq | openrouter) ---
    # Todos hablan API estilo OpenAI salvo Ollama. Cambia LLM_PROVIDER en el .env.
    llm_provider: str = "ollama"      # "ollama" | "groq" | "openrouter"
    ollama_host: str = "http://ollama:11434"
    ollama_model: str = "llama3.1:8b"
    # Groq (https://console.groq.com): 8b-instant = rápido; 70b-versatile = mucha más calidad (free).
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    # OpenRouter (https://openrouter.ai): acceso free a DeepSeek V4 Flash, Nemotron, etc.
    # Copia el slug EXACTO del modelo desde https://openrouter.ai/models (varía con el tiempo).
    openrouter_api_key: str = ""
    # Modelo gratis para coaching. OJO al límite de 100s de Cloudflare: el 120B de Nemotron
    # (razonamiento) iba demasiado lento → 524. Kimi K2.6 da buena calidad y es más rápido.
    # Alternativa aún más rápida si hiciera falta: google/gemma-4-31b-it:free.
    openrouter_model: str = "moonshotai/kimi-k2.6:free"
    # Cadena de respaldo (OpenRouter prueba en ORDEN si el primario falla: 429, caído, retirado…).
    # Mitiga la volatilidad del 'free' y reparte el cupo diario. Slugs separados por coma; verifica
    # los exactos en https://openrouter.ai/models (cambian). 'openrouter/free' al final = comodín.
    openrouter_fallback_models: str = "deepseek/deepseek-chat-v3.1:free,qwen/qwen3-235b-a22b:free,openrouter/free"
    llm_temperature: float = 0.4

    # --- Aplicación ---
    cors_origins: list[str] = [
        "http://localhost",
        "http://localhost:8080",
        "http://localhost:5173",
    ]
    # Fase 0: True (la API devuelve mocks). Se pondrá a False al cablear Riot/Ollama.
    use_mock: bool = True

    # --- Worker de meta (agregación real; docs/DATOS.md, opción B) ---
    meta_data_dir: str = "app/data/generated"   # JSON generados por el worker
    meta_sample_players: int = 40                # jugadores del ladder a muestrear
    meta_matches_per_player: int = 8             # partidas por jugador
    meta_top_n: int = 24                         # entradas por explorador
    meta_min_games: int = 5                      # mínimo de apariciones para listar
    meta_enrich_llm: bool = False                # si true, el worker pide al LLM nombre/lema/guía por comp
    meta_enrich_top: int = 12                    # nº de comps a enriquecer (las mejores)

    # --- Coaching IA: persistencia (SQLite stdlib) + plan global ---
    reports_db: str = "app/data/generated/synapse.db"   # informes y planes cacheados
    waitlist_db: str = "app/data/generated/waitlist.db"  # solicitudes de acceso a la beta
    plan_match_window: int = 20                          # nº de partidas que mira el plan global
    plan_autoanalyze: int = 2                            # informes que el endpoint /plan genera por sí mismo (respaldo;
    #                                                      el frontend ya los genera de uno en uno para no agotar el proxy)

    # --- FASE 2: núcleo de análisis (BD relacional + cola + polling) ---
    # En prod (compose): Postgres. Sin DATABASE_URL: SQLite en el volumen (fallback/tests).
    database_url: str = "sqlite:///app/data/generated/divisionup.db"
    # Sin REDIS_URL la cola se ejecuta inline (modo degradado/opción B) y el
    # limitador de rate pasa a ser local al proceso.
    redis_url: str = ""
    rq_queue: str = "analisis"                  # nombre de la cola de análisis
    poll_interval_seconds: int = 300            # cada cuánto sondea partidas nuevas por usuario
    poll_count: int = 10                        # nº de IDs recientes que pide por usuario
    # Límite real de la Dev/Personal key: 20 req/s y 100 req/2min. Margen de seguridad.
    riot_rate_rps: int = 15
    riot_rate_per_2min: int = 90

    # --- FASE 3: catálogo de patrones + objetivo semanal ---
    # Una señal se publica solo si confianza × severidad > este umbral.
    senal_umbral: float = 0.9
    # Objetivo semanal: patrón más recurrente en las últimas N partidas,
    # con un mínimo de apariciones para no entrenar ruido.
    objetivo_ventana: int = 10
    objetivo_min_apariciones: int = 3

    # --- FASE 4: visor /debug y retirada de patrones por telemetría ---
    debug_token: str = ""                # vacío = visor /debug desactivado (404)
    telemetria_min_votos: int = 10       # votos mínimos antes de poder retirar un patrón
    telemetria_falla_pct: int = 60       # % de '✗ Falla' a partir del cual se retira


settings = Settings()
