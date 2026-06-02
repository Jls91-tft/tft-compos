# Frontend — Synapse (HTML/CSS/JS vanilla)

App de producción. Reutiliza el diseño validado en la Etapa 1 y consume la API real.

> ⚠️ **No se abre con doble clic.** Hace `fetch` a `/api`, así que se sirve con **nginx** (servicio `web` del Docker Compose), que también hace de proxy a la API. El prototipo de doble clic está en `synapse-prototipo/`.

## Estructura
```
frontend/
├── index.html        # Home pública (landing/marketing) — sin login
├── app.html          # App (tras Cloudflare Access): Coaching · Estadísticas · Meta
├── informe.html      # Informe de coaching (?game=&id=) + chat del coach
├── guia-comp.html    # Guía de comp (con tablero de posicionamiento)
└── assets/
    ├── synapse.css   # Design system (tokens + componentes de todas las pantallas)
    ├── api.js        # Cliente de la API (base /api; guarda el Riot ID en localStorage)
    └── charts.js     # Gráficas en SVG puro (línea, barras, tablas)
```

## Cómo consume la API
- `api.js` expone `API.matches(game)`, `API.report(game,id)`, `API.stats(game)`, `API.meta(game)`, `API.chat(game,id,question)`.
- Todas las llamadas van a `/api/...`; nginx las redirige al backend.
- El **Riot ID** (campo de la cabecera) se guarda en `localStorage` y se adjunta a las peticiones (se ignora en modo mock del backend).
- Cada vista muestra **estado de carga** (spinner) y **de error** si la API falla.

## Cómo añadir una vista
1. Crea la página HTML enlazando `assets/synapse.css` y los scripts que necesites.
2. Reutiliza componentes del design system (clases en `synapse.css`).
3. Para datos, usa `API.*` de `api.js`; añade un método nuevo si hace falta un endpoint nuevo.

## Diseño
- Tema oscuro, acento violeta (IA). Tokens y componentes en `synapse.css`.
- Marca propia genérica; sin assets de Riot.
