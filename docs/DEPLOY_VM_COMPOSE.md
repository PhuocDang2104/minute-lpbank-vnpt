# Deploy to 1 VM with Docker Compose + Caddy

This guide is for production-style deploy on a single Linux VM (AWS EC2, GCP VM, Azure VM, etc.).
It uses:
- `infra/docker-compose.prod.yml` for app stack
- `infra/.env.prod` for secrets/env
- `infra/caddy-compose.yml` for HTTPS reverse proxy

## 1) VM prerequisites
- Docker Engine + Docker Compose plugin installed
- Inbound ports open: `22`, `80`, `443`
- Domain DNS A record points to VM public IP (example: `api.yourdomain.com`)

Do not open database port `5432/5433` to public internet.

## 2) Prepare production env file
From repository root:

```bash
cd infra
cp env.prod.example .env.prod
```

Edit `infra/.env.prod` and set real values:
- `POSTGRES_PASSWORD` (strong password)
- `SECRET_KEY` (random 32+ chars)
- `GEMINI_API_KEY` (if used)
- `CORS_ORIGINS` (must include Vercel frontend origin)

Example:

```env
POSTGRES_PASSWORD=your-strong-password
SECRET_KEY=your-random-secret-key
GEMINI_API_KEY=...
ASR_LANGUAGE=vi
LLM_OUTPUT_LANGUAGE=vi
CORS_ORIGINS=https://your-project.vercel.app,https://your-frontend-domain.com
```

## 3) Start app stack (postgres + asr + backend)

```bash
cd infra
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build
docker compose -f docker-compose.prod.yml --env-file .env.prod ps
docker compose -f docker-compose.prod.yml --env-file .env.prod logs -f --tail=200 backend
```

Quick check on VM:

```bash
curl -I http://localhost:8000/docs
```

Expected: `200`, `301`, or `302`.

## 4) Enable HTTPS with Caddy
Create runtime Caddyfile from template:

```bash
cd infra
cp Caddyfile.example Caddyfile
```

Edit `infra/Caddyfile` and set your API domain:

```caddy
api.yourdomain.com {
  encode zstd gzip
  reverse_proxy minute_backend:8000
}
```

Start Caddy:

```bash
cd infra
docker compose -f caddy-compose.yml up -d
docker compose -f caddy-compose.yml logs -f --tail=200
```

`caddy-compose.yml` joins Docker external network `minute_internal` created by `docker-compose.prod.yml`.
So start app stack (step 3) before starting Caddy.

After cert is issued, API should be reachable via:
- `https://api.yourdomain.com/docs`
- `https://api.yourdomain.com/api/v1/health`

## 5) Daily operations

Status:

```bash
cd /opt/minute/minute-lpbank-vnpt/infra
docker compose -f docker-compose.prod.yml --env-file .env.prod ps
```

Deploy latest code:

```bash
cd /opt/minute/minute-lpbank-vnpt
git pull
cd infra
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build
```

Backend logs:

```bash
cd /opt/minute/minute-lpbank-vnpt/infra
docker compose -f docker-compose.prod.yml --env-file .env.prod logs -f --tail=200 backend
```

## 6) Production defaults in this repo
- Postgres port is not published to host
- Backend has no bind mount and no `--reload`
- ASR uses internal `expose` only
- Caddy reverse proxy reaches backend via Docker network (`minute_backend:8000`)
- Backend is still bound to `127.0.0.1:8000` on host for local debug and health checks

If you need direct external API on port 8000 (not recommended), change:
- `backend.ports` in `infra/docker-compose.prod.yml` from `127.0.0.1:8000:8000` to `8000:8000`.
