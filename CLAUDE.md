# CLAUDE.md — Guía para agentes de IA

> Léelo antes de tocar nada. Resume el proyecto, las reglas y dónde está cada cosa.
> Documentación complementaria: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md), [`backend/README.md`](backend/README.md), [`frontend/README.md`](frontend/README.md), [`docs/RIOT_APPLICATION.md`](docs/RIOT_APPLICATION.md).

## Qué es DivisionUp
Producto de **coaching post-partida para Teamfight Tactics (TFT)**, en **beta cerrada 100 % TFT**.
League of Legends NO forma parte de la beta: solo aparece en el copy como "en el roadmap".
El diferencial es el **informe por partida construido sobre hechos verificados** del match (API oficial de Riot), no un panel de estadísticas.

## Decisiones de producto CERRADAS (no reabrir)
1. **Beta 100 % TFT.** LoL solo como roadmap en el copy.
2. **Lenguaje de hipótesis:** el informe dice "Hipótesis principal" (NUNCA "veredicto") y "Señal de decisión" (NUNCA "error"). Las señales pueden llevar una pregunta de coach en cursiva.
3. **Objetivo semanal protagonista:** banner arriba con regla concreta y progreso (ej. 6/10); cada partida lleva ✓/✗; cada informe abre con el chip "OBJETIVO DE LA SEMANA: ✓/✗".
4. **Comparación "VS · PODIO DE TU LOBBY"** (media del top 4), NUNCA contra el Top 1 individual.
5. **Transparencia radical:** desplegable "HECHOS VERIFICADOS · N REGISTROS" con líneas crudas en monoespaciada, incluidos los patrones DESCARTADOS por contraevidencia; pie con versión del catálogo.
6. **Feedback por señal:** botones "✓ Acierta / ✗ Falla" que persisten el voto (telemetría por patrón).
7. **Honestidad de alcance:** el análisis NO ve posicionamiento ni tiendas/rolls, y el copy lo declara (FAQ).
8. **Captación:** UN solo CTA en la landing → formulario de waitlist (`POST /api/waitlist`).
9. **Discord solo como canal de aviso** (fase futura; no implementado).
10. **PROHIBIDO inventar métricas, testimonios o nombres de unidades/rasgos del set en copy o datos de ejemplo.** Arquetipos genéricos ("Reroll de 1 coste", "Fast 8") y datos de Data Dragon/CDragon cuando sean reales.

## Acciones PROHIBIDAS
- **NUNCA llamar a un LLM en el pipeline de informes**: la v1 es template-first (plantillas deterministas en castellano sobre hechos). El motor LLM antiguo (`coaching_engine`/`prompts`/`ollama_client`) está en retirada — no ampliarlo.
- **NUNCA implementar MMR/ELO propio** ni nada presentable como ranking alternativo (políticas de Riot). La "posición esperada" solo por partida individual.
- **NUNCA hardcodear claves**: `RIOT_API_KEY` y demás secretos solo en `.env` (gitignored). Si se expone una clave, revócala.
- **NO añadir features no pedidas** (auth social, temas, i18n, modo LoL, pagos…).
- **Parar y preguntar** antes de: borrar archivos, añadir dependencias, modificar esquemas de BD existentes, tocar despliegue/CI.

## Reglas de trabajo
1. **Idioma:** español en respuestas, comentarios, docstrings y commits.
2. **Marca propia:** sin logos/marcas de Riot en branding propio. Nombres reales de campeones/ítems/rasgos SÍ cuando provengan de los datos del usuario (API oficial) o de Data Dragon/CommunityDragon.
3. **Versionado:** commits en castellano y `git push` tras cada avance. Repo `github.com/Jls91-tft/tft-compos`, rama `main`.
4. **En este equipo (Windows) no se ejecuta el stack**: la ejecución real (Docker, pytest) vive en la VM de GCP (`docs/DEPLOY.md`). Los tests se lanzan en la VM vía Docker.

## Diseño (paleta "Hielo")
La referencia canónica de UI es **`design-reference/divisionup-landing-v3.html`** y **`design-reference/divisionup-app-v3.html`** — léelas antes de tocar frontend y replica tokens/copys/comportamientos.
- Fondos `#070B12 / #0A0F17`, paneles `#101724 / #16202F`, líneas `#1F2C3E / #2B3B52`.
- Acentos: azul `#5BA8FF` (primario), menta `#53E0C4` (positivo), frambuesa `#F0668F` (señales), oro `#FFC95C` (**reservado** a Top 1 y logros).
- Texto `#EAF1FA / #9FB2CB / #62758F`. Degradado de marca `linear-gradient(92deg,#53E0C4,#5BA8FF)`.
- Tipos: Rajdhani (display/uppercase), Instrument Sans (cuerpo), JetBrains Mono (datos).
- Logo: tres chevrones ascendentes (plata → oro → degradado), símbolo SVG en las referencias y `frontend/assets/logo.svg`.

## Arquitectura objetivo del análisis (en construcción por fases)
```
CAPA 1  Motor de hechos       determinista, sin IA — end-state de los 8 jugadores
CAPA 2  Catálogo de patrones  versionado; disparador + contraevidencia + confianza + severidad + plantilla + telemetría
CAPA 3  Generador             template-first determinista (misma partida + misma versión = mismo informe)
```
Infra prevista (FASE 2, aprobada con reserva): FastAPI + PostgreSQL + RQ/Redis en la VM e2-micro; si la RAM no aguanta, fallback a SQLite + APScheduler.

## Estructura del repo
```
backend/            API FastAPI (routers, services, schemas, data, worker)
frontend/           index.html (landing) · app.html (app) · privacy.html · tos.html · assets/
design-reference/   Referencia canónica de UI v3 (NO servir; solo consulta)
nginx/              Sirve frontend + proxy /api
docs/               Documentación (DEPLOY, DATOS, RIOT_APPLICATION…)
synapse-prototipo/  Prototipo Etapa 1 (cerrado, no tocar)
```

## Estado actual (junio 2026)
- **FASE 1 (interfaz v3 "Hielo")**: landing + app nuevas, waitlist real (`POST /api/waitlist`, SQLite). La vista Coaching usa datos de ejemplo hasta FASE 4.
- **Pipelines de meta reales** (reutilizados): `meta_pipeline`/`comps_pipeline`/`cdragon_client` + worker (`--profile meta`) alimentan `/meta` y `/lab/explorer` con ladder Challenger.
- **Pendiente**: FASE 2 (modelos+migraciones, rate limiter central, motor de hechos, polling), FASE 3 (catálogo 10 patrones + generador + objetivo semanal), FASE 4 (endpoints reales, /debug, golden tests, desconexión del motor LLM antiguo).

## Convenciones clave
- Contrato API↔frontend = schemas Pydantic en `backend/app/schemas/models.py`.
- Patrón mock: `if settings.use_mock: return mock...` (datos de ejemplo en `backend/app/data/`).
- Frontend vanilla sin framework; se sirve con nginx (no funciona con doble clic, hace fetch a `/api`).
- Frontend en la VM va **bind-mounted**: desplegar = `git pull` en la VM. Backend requiere `docker compose -f docker-compose.prod.yml up -d --build api`.
