# Despliegue de la beta (gratis o casi gratis)

Objetivo: Synapse funcionando para **usuarios controlados** (beta cerrada), barato y fiable.
El despliegue es **idéntico en cualquier VM Linux**: Docker Compose + Cloudflare Tunnel. Como la IA va por **Groq (API)**, basta con **~1 GB de RAM**.

## Arquitectura
```
Beta testers ──HTTPS──> Cloudflare (Access: lista blanca + Tunnel) ──> VM Linux
                                                                        └─ Docker Compose:
                                                                           nginx(web) → FastAPI(api) → Groq API (IA)
                                                                                                     → Riot API
```

## 1. Elige y crea la VM
| Opción | Coste | RAM | Región | Nota |
|---|---|---|---|---|
| **Google Cloud `e2-micro` (Always Free)** ⭐ | 0 € siempre | 1 GB | US | Recomendada: gratis de verdad y fiable. |
| Oracle `E2.1.Micro` (AMD, Always Free) | 0 € siempre | 1 GB | tu tenancy | Si tu cuenta Oracle es de región UE, mejor latencia. La AMD sí suele tener disponibilidad. |
| Hetzner `CAX11` (ARM) | ~3,79 €/mes | 4 GB | UE | Si aceptas coste mínimo: más holgura, baja latencia y permite Ollama local. |

> **Google Cloud**: Compute Engine → Crear instancia → serie **E2**, tipo **e2-micro**, región **us-west1 / us-central1 / us-east1** (las del *free tier*), disco estándar 30 GB, Ubuntu 22.04. No necesitas abrir puertos (el túnel sale hacia fuera).

## 2. Swap (solo en VMs de 1 GB, recomendado)
```bash
sudo fallocate -l 2G /swapfile && sudo chmod 600 /swapfile
sudo mkswap /swapfile && sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

## 3. Docker
```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER && newgrp docker
```

## 4. Clonar y configurar
```bash
git clone https://github.com/Jls91-tft/tft-compos.git
cd tft-compos
cp .env.example .env && nano .env
```
En `.env`:
```
USE_MOCK=false
RIOT_API_KEY=...            # Production API Key (paso 7)
RIOT_REGION=europe
RIOT_PLATFORM=euw1
LLM_PROVIDER=groq
GROQ_API_KEY=...            # gratis en https://console.groq.com
GROQ_MODEL=llama-3.1-8b-instant
TUNNEL_TOKEN=...            # del paso 5
```

## 5. Cloudflare Tunnel (HTTPS sin abrir puertos)
1. Añade tu **dominio a Cloudflare** (gratis; o uno barato).
2. **Zero Trust → Networks → Tunnels → Create tunnel** → copia el **token** → `TUNNEL_TOKEN`.
3. **Public Hostname**: `synapse.tudominio.com` → Service **HTTP** `web:80`.

## 6. Beta cerrada — Cloudflare Access (gratis ≤50 usuarios)
1. **Zero Trust → Access → Applications → Add → Self-hosted** → dominio `synapse.tudominio.com`.
2. **Policy** *Allow* → regla **Emails** con los correos de tus beta testers.
3. Login por One-time PIN (email) o Google. Solo esos correos entran.

## 7. Riot API Key
- Registra el producto en https://developer.riotgames.com y solicita la **Production API Key** (gratis; no caduca como la *dev key*).

## 8. Levantar
```bash
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml logs -f api
```
Abre **https://synapse.tudominio.com** → login de Access → la app.

> ¿Ollama local en vez de Groq? Solo en VM con RAM suficiente (Hetzner): `LLM_PROVIDER=ollama` y `--profile local-llm`.

## Límites a vigilar (gratis, con topes)
- **Groq free**: límite de peticiones/min — sobra para una beta pequeña.
- **Riot API**: rate limits por clave.
- **Google e2-micro**: 1 GB (de ahí el swap). 1 instancia free por proyecto, en regiones US.
- **Datos de meta** (`/lab/*`): mock hasta montar el worker de agregación (`docs/DATOS.md`).
