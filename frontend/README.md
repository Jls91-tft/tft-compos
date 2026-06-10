# Frontend — DivisionUp (HTML/CSS/JS vanilla)

App de producción de la beta cerrada (100 % TFT). Diseño v3 "Hielo"; la referencia
canónica de UI vive en `design-reference/` (raíz del repo).

> ⚠️ **No se abre con doble clic.** Hace `fetch` a `/api`, así que se sirve con **nginx**
> (servicio `web` del Docker Compose), que también hace de proxy a la API.

## Estructura
```
frontend/
├── index.html        # Landing pública: un solo CTA → formulario de waitlist (POST /api/waitlist)
├── app.html          # App: Resumen · Coaching IA · Plan semanal · Estadísticas · Meta del parche · Ajustes
├── privacy.html      # Política de privacidad (RGPD)
├── tos.html          # Términos de servicio
└── assets/
    ├── api.js        # Cliente de la API (base /api; Riot ID en localStorage: divisionup_riot_id)
    └── logo.svg      # Marca: tres chevrones ascendentes (plata → oro → degradado menta-azul)
```

## Cómo consume la API
- `api.js` expone `API.matches()`, `API.rank()`, `API.stats()`, `API.meta()`, `API.waitlist(datos)` y `API.feedback(datos)` (FASE 4).
- Todas las llamadas van a `/api/...`; nginx las redirige al backend.
- El **Riot ID** se configura en la vista Ajustes (localStorage) y se adjunta a las peticiones.
- La vista **Coaching IA** usa datos de ejemplo (arquetipos genéricos) hasta que el motor de
  hechos + catálogo de patrones esté conectado (FASES 2-4).

## Diseño
- Paleta "Hielo": tokens definidos inline en cada página (copiados de la referencia canónica).
- Oro `#FFC95C` RESERVADO a Top 1 y logros. Tipos: Rajdhani · Instrument Sans · JetBrains Mono.
- Lenguaje del informe: "Hipótesis principal" y "Señal de decisión" (nunca "veredicto"/"error").
- Marca propia; sin logos de Riot. Disclaimer de no afiliación en el footer de la landing.
