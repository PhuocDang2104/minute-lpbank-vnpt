# Huong Dan Chay Local (Minute)

## Yeu cau
- Docker Desktop
- Node.js 18+
- Python 3.11+ (neu chay backend ngoai Docker)

## Cach nhanh (Docker full stack)

```bash
cd infra
docker compose up -d --build
```

Service:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- Swagger: http://localhost:8000/docs
- ASR: http://localhost:9000
- Postgres: localhost:5433

## Env local de nghi

Tao `backend/.env.local`:

```env
ENV=development
DATABASE_URL=postgresql+psycopg2://minute:minute@localhost:5433/minute
SECRET_KEY=dev-secret-key-change-in-production
CORS_ORIGINS=*

# LLM
GEMINI_API_KEY=
GROQ_API_KEY=
GEMINI_MODEL=gemini-2.5-flash-lite
LLM_OUTPUT_LANGUAGE=vi
AI_TEMPERATURE=0.2
AI_MAX_TOKENS=4096

# ASR
ASR_URL=http://localhost:9000
ASR_LANGUAGE=vi
```

## Chay frontend

```bash
cd frontend
npm install
VITE_API_URL=http://localhost:8000 npm run dev
```

## Kiem tra nhanh

```bash
curl http://localhost:8000/api/v1/health
curl http://localhost:8000/api/v1/chat/status
curl http://localhost:9000/health
```

## Dung service

```bash
cd infra
docker compose down
```

## Neu gap loi
- Postgres khoi dong loi: `docker compose down -v && docker compose up -d postgres`
- Backend khong thay env: kiem tra file `backend/.env.local` hoac `infra/env/.env.local`
- ASR loi model: kiem tra `WHISPER_MODEL` va build lai image `asr`
