# Despliegue gratuito de la beta (Oracle Cloud Free Tier + Cloudflare)

Objetivo: tener Synapse funcionando **gratis** para pruebas con **usuarios controlados** (beta cerrada).
Coste total: **0 €** (Oracle Always Free + Cloudflare Free + Groq Free + Riot Free).

## Arquitectura
```
Beta testers ──HTTPS──> Cloudflare (Access: lista blanca + Tunnel) ──> VM Oracle ARM
                                                                         └─ Docker Compose:
                                                                            nginx(web) → FastAPI(api) → Groq API (IA)
                                                                                                      → Riot API
```

## 1. Crear la VM (Oracle Cloud — Always Free)
1. Cuenta en Oracle Cloud (Always Free).
2. Compute → Create Instance:
   - **Shape: VM.Standard.A1.Flex (Ampere ARM)** → **4 OCPU / 24 GB RAM** (todo gratis "Always Free").
   - Imagen: Ubuntu 22.04/24.04. Disco: hasta 200 GB (gratis).
   - Guarda la clave SSH.
   - ⚠️ Si da *"out of capacity"*, reintenta o cambia de Availability Domain/región.
3. No hace falta abrir puertos 80/443 (el túnel sale hacia fuera).

## 2. Instalar Docker en la VM
```bash
ssh ubuntu@<IP>
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER && newgrp docker
```

## 3. Clonar y configurar
```bash
git clone https://github.com/Jls91-tft/tft-compos.git
cd tft-compos
cp .env.example .env
nano .env
```
En `.env`:
```
USE_MOCK=false
RIOT_API_KEY=...           # Production API Key (ver paso 6)
RIOT_REGION=europe
RIOT_PLATFORM=euw1
LLM_PROVIDER=groq
GROQ_API_KEY=...           # gratis en https://console.groq.com
GROQ_MODEL=llama-3.1-8b-instant
TUNNEL_TOKEN=...           # del paso 4
```

## 4. Cloudflare Tunnel (HTTPS sin abrir puertos)
1. Necesitas un **dominio en Cloudflare** (gratis añadir un dominio; o uno barato).
2. **Zero Trust → Networks → Tunnels → Create a tunnel** (Cloudflared).
3. Copia el **token** del túnel → ponlo en `TUNNEL_TOKEN` del `.env`.
4. En el túnel, **Public Hostname**: `synapse.tudominio.com` → Service **HTTP** `web:80`.

## 5. Beta cerrada (Cloudflare Access — gratis ≤50 usuarios)
1. **Zero Trust → Access → Applications → Add → Self-hosted**.
2. Dominio de la app: `synapse.tudominio.com`.
3. **Policy**: Action *Allow*, regla *Emails* → añade los correos de tus beta testers (lista blanca).
4. Método de login: One-time PIN (email) o Google. Solo esos correos entrarán.

## 6. Riot API Key
- Para una beta estable, registra el producto en https://developer.riotgames.com y solicita la **Production API Key** (gratis). La *dev key* caduca cada 24 h.

## 7. Levantar
```bash
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs -f api
```
Abre **https://synapse.tudominio.com** → login de Access → la app.

> Para usar **Ollama local** en vez de Groq: pon `LLM_PROVIDER=ollama` y arranca con `--profile local-llm` (descarga el modelo: `docker compose -f docker-compose.prod.yml exec ollama ollama pull llama3.1:8b`). Más privado, pero lento en CPU ARM.

## Límites a vigilar (gratis, pero con topes)
- **Groq / Gemini free**: límite de peticiones por minuto/día — sobra para una beta pequeña.
- **Riot API**: rate limits por clave.
- **Oracle ARM**: puede reclamar instancias *idle*; con la beta activa no hay problema.
- **Datos de meta** (`/lab/*`): siguen siendo mock hasta montar el worker de agregación (ver `docs/DATOS.md`).
