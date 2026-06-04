# Solicitud de Production API Key (Riot Games)

Guion completo para registrar DivisionUp como **Personal API Key** primero y, en cuanto haya pago, migrar a **Production API Key**. La diferencia clave: Personal está pensada para **uso no comercial** (gratis siempre); Production requiere declarar el modelo de negocio y permite **monetizar** (suscripciones, créditos, IA premium…).

Estrategia recomendada: pedir Personal en cuanto la web pase el checklist (rápido, valida tu integración) y, cuando ya tengas un plan de pago real y un dominio fijo, migrar pidiendo Production con el plan declarado. Mobalytics, U.GG, Blitz, MetaTFT y Lolchess pasaron exactamente por ahí.

---

## ✅ Checklist técnico — todo lo que la revisión va a mirar

Antes de pulsar "Submit":

- [ ] Dominio fijo con HTTPS (`divisionup.gg` o el que elijas). Hoy: el túnel `trycloudflare.com` cambia → **compra el dominio antes de enviar**.
- [ ] `index.html` (landing) accesible públicamente y describe claramente qué hace el producto.
- [ ] `privacy.html` accesible y enlazado desde el footer.
- [ ] `tos.html` accesible y enlazado desde el footer.
- [ ] Email de contacto operativo (`contacto@divisionup.gg`) — el formulario y los documentos lo nombran. Si vas a usar otro, **haz búsqueda y reemplazo** en `privacy.html`, `tos.html`, `index.html`, `app.html` y este documento.
- [ ] Disclaimer visible: "no afiliada, asociada ni respaldada por Riot Games" en el footer de cada página. Hecho.
- [ ] Cero uso de logos, iconos o marcas de Riot en branding propio (regla 2 de CLAUDE.md). Hecho.
- [ ] La app, accesible para el revisor: o bien sin Cloudflare Access, o con **cuenta demo** cuyas credenciales adjuntas en el formulario. Si activas Access, **desactívalo durante la revisión** o crea una excepción por IP/email para el revisor.
- [ ] Endpoints que vas a usar declarados (lista más abajo).
- [ ] Rate limit del worker bajo el límite Personal (20 req/s, 100 req/2 min) — ya lo cumple sobradamente.
- [ ] Sin scraping de páginas web de Riot. Sí — solo API oficial.

---

## 📝 Texto para el formulario (copia y pega)

### Product Name
DivisionUp

### Product URL
https://divisionup.gg  *(sustituye por la URL real cuando esté lista)*

### Product Description (Personal Key, fase actual)
> DivisionUp is a personal post-match coaching tool for Teamfight Tactics and League of Legends. After each ranked match, it generates an AI-driven report identifying mistakes, suggesting concrete corrections and providing an actionable improvement plan; users can chat with the coach to dig deeper. It also offers personal statistics (rank, LP, performance over time) and a meta explorer aggregated from public Challenger ladder data.
>
> Built for individual ranked players who want structured, post-game feedback without hiring a human coach. Free during beta, no advertising, no third-party data sharing.

### Product Description (Production Key, cuando migremos a pago)
> DivisionUp is a freemium post-match coaching product for Teamfight Tactics and League of Legends. The core analysis (one AI report per day, basic stats) is free; paid tiers unlock more reports per day, premium LLMs, extended history, global improvement plans and side-by-side comparisons. Conceptually similar to Mobalytics' AI Coach or Blitz's post-game insights, focused on coaching quality rather than draft assistance.
>
> Revenue is generated exclusively from our own added value (LLM analysis, UI, aggregations). Riot API data is never sold, never resold and never used outside the product. No advertising adjacent to Riot IP. Full disclaimer on every page that DivisionUp is not affiliated with Riot Games.

### Endpoints planned
- `match-v5` · `lol-match-v5` (LoL match detail + timeline)
- `tft-match-v1` (TFT match detail)
- `summoner-v4` · `tft-summoner-v1` (PUUID lookup)
- `league-v4` · `tft-league-v1` (rank, LP, Challenger ladder)
- `account-v1` (Riot ID → PUUID)
- `lol-challenges-v1` (skill metrics, complementa el coaching)

### Estimated traffic
- Concurrent users in beta: 10–50.
- Per user: ~10 API calls per analyzed match, ~3 matches/day average.
- Background meta worker: aggregates Challenger sample every 12 h (40 players × 8 matches per game).
- Well below Personal Key limits (20 req/s, 100 req/2 min).

### Data Storage & Usage
> We cache match IDs, match payloads and generated AI reports keyed by PUUID in a local SQLite database for up to 90 days. No data is shared with third parties beyond the LLM provider that generates the report (OpenRouter / Moonshot Kimi K2.6); only the structured match JSON is sent, never the Riot ID or any personal identifier. Users can request full deletion via email; we honor the request within 30 days. Full details in our privacy policy at https://divisionup.gg/privacy.html.

### Monetization Plan (sólo Production)
> Freemium model:
> - **Free tier**: 1 AI report per day, basic stats, meta explorer.
> - **Plus** (€4.99/month): up to 10 reports/day, extended history (last 60 days), comparisons vs higher-elo players, global improvement plan.
> - **Pro** (€9.99/month): unlimited reports, premium LLM (larger model), priority queue, early access to new features.
>
> No data resale. No advertising. No paid promotions. No premium currency. Cancellation is one click; EU consumers retain their 14-day withdrawal right per applicable law.

---

## 🗂️ Lo que ya está preparado en el repo

- `frontend/privacy.html` — política de privacidad RGPD-compliant.
- `frontend/tos.html` — términos de servicio.
- Footer con enlaces a Privacy/Términos/Contacto y disclaimer en `index.html` y `app.html`.
- `mock.py` y la UI **no usan nombres reales de Riot** en ejemplos (cumple la regla 2 de CLAUDE.md).
- El pipeline `meta_pipeline.py` consume **solo** la API oficial.

## ⚠️ Pendiente antes de enviar

1. **Comprar el dominio** (`divisionup.gg` u otro). Sin esto, el revisor va a un `trycloudflare.com` que cambia y suele rechazarse.
2. **Email de contacto** real (`contacto@divisionup.gg`). Si vas a usar otro, sustituir en los 4 archivos arriba mencionados.
3. **Cloudflare Access desactivado durante la revisión**, o cuenta demo con credenciales en el formulario.
4. (Opcional pero recomendado) Página `/about` o sección "¿Quién está detrás?" en la home, con tu nombre o el nombre del proyecto. Da seriedad.

## ⏱️ Tiempos esperados

- Personal Key: **3–10 días** de revisión.
- Production Key: **3–6 semanas**. A veces piden aclaraciones por email — responde rápido y específico.

## 🔁 Mientras esperas (Dev Key)

La Development Key (24 h) sigue funcionando para validar el flujo. El worker de meta no aguanta con ella (se renueva todos los días), pero el flujo de coaching personal sí. Si quieres mantener Dev hasta la aprobación, regenera la clave cada mañana en el portal y sustituye en `.env` con `set-model.sh`-style script.
