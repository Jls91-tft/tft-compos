# AGENTS.md

Guía para agentes de IA que trabajen en este repositorio (estándar abierto).
El contenido canónico y detallado está en **[`CLAUDE.md`](CLAUDE.md)** — léelo primero.

## Resumen rápido
- **Proyecto:** DivisionUp — coaching post-partida para **TFT** (beta cerrada 100 % TFT; LoL solo "en el roadmap"). Informes sobre **hechos verificados**, lenguaje de hipótesis, template-first (sin LLM en el pipeline de informes).
- **Stack:** FastAPI (backend) · frontend vanilla servido por nginx · Docker Compose en VM GCP.
- **Diseño:** paleta "Hielo"; referencia canónica en `design-reference/*.html`.
- **Idioma:** español (respuestas, comentarios, commits).

## Reglas imprescindibles
1. Sin logos/marcas de Riot en branding propio. Nombres reales de unidades/ítems solo desde datos del usuario (API oficial) o Data Dragon/CDragon — nunca inventados en copy o ejemplos.
2. Secretos solo en `.env` (gitignored); nunca en el código. `.env.example` con placeholders.
3. Commits en castellano y `git push` tras cada avance (repo `Jls91-tft/tft-compos`, rama `main`).
4. En el equipo de desarrollo **no se instala ni ejecuta** el stack; eso se hace en la VM. No ejecutes `pip`/`npm`/`docker` salvo petición.
5. Decisiones de producto cerradas y acciones prohibidas: ver CLAUDE.md (no reabrirlas).

## Convenciones
- Contrato API↔frontend = schemas Pydantic en `backend/app/schemas/models.py`.
- Datos de ejemplo en `backend/app/data/mock.py`; cada endpoint respeta `USE_MOCK`.
- Ejecutar: `cp .env.example .env` → `docker compose up -d --build` (frontend `:8080`, API `:8000/docs`).

Más detalle: [`CLAUDE.md`](CLAUDE.md) · [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).
