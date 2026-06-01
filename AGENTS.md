# AGENTS.md

Guía para agentes de IA que trabajen en este repositorio (estándar abierto).
El contenido canónico y detallado está en **[`CLAUDE.md`](CLAUDE.md)** — léelo primero.

## Resumen rápido
- **Proyecto:** Synapse — coaching IA + estadísticas para TFT y LoL. El coaching es el diferencial.
- **Stack:** FastAPI (backend) · frontend vanilla servido por nginx · Ollama (IA local) · Docker Compose.
- **Idioma:** español (respuestas, comentarios, commits).

## Reglas imprescindibles
1. Marca propia genérica: **sin** logos/marcas/personajes de Riot en branding ni datos de ejemplo.
2. Secretos solo en `.env` (gitignored); nunca en el código. `.env.example` con placeholders.
3. Commits en castellano y `git push` tras cada avance (repo `Jls91-tft/tft-compos`, rama `main`).
4. En el equipo de desarrollo **no se instala ni ejecuta** el stack; eso se hace en otro PC. No ejecutes `pip`/`npm`/`docker`/`ollama` salvo petición.

## Convenciones
- Contrato API↔frontend = schemas Pydantic en `backend/app/schemas/models.py`.
- Datos de ejemplo en `backend/app/data/mock.py`; cada endpoint respeta `USE_MOCK`.
- Ejecutar: `cp .env.example .env` → `docker compose up -d --build` (frontend `:8080`, API `:8000/docs`).

Más detalle: [`CLAUDE.md`](CLAUDE.md) · [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).
