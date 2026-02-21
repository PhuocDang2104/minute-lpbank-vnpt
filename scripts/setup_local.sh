#!/usr/bin/env bash

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
INFRA_DIR="$PROJECT_ROOT/infra"

echo "Minute local development setup"
echo "================================"

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is not installed."
  exit 1
fi

if ! docker info >/dev/null 2>&1; then
  echo "Docker is not running."
  exit 1
fi

pushd "$INFRA_DIR" >/dev/null
if command -v docker-compose >/dev/null 2>&1; then
  docker-compose up -d postgres
else
  docker compose up -d postgres
fi
popd >/dev/null

echo "Waiting for PostgreSQL (minute_db)..."
for _ in $(seq 1 30); do
  if docker exec minute_db pg_isready -U minute >/dev/null 2>&1; then
    break
  fi
  sleep 2
done

if ! docker exec minute_db pg_isready -U minute >/dev/null 2>&1; then
  echo "PostgreSQL did not become ready in time."
  exit 1
fi

if [ ! -d "$BACKEND_DIR/.venv" ]; then
  python3 -m venv "$BACKEND_DIR/.venv"
fi

# shellcheck disable=SC1091
source "$BACKEND_DIR/.venv/bin/activate"
pip install --upgrade pip >/dev/null
pip install -r "$BACKEND_DIR/requirements.txt"

ENV_FILE="$BACKEND_DIR/.env.local"
if [ ! -f "$ENV_FILE" ]; then
  cat > "$ENV_FILE" <<'ENVVARS'
ENV=development
DATABASE_URL=postgresql+psycopg2://minute:minute@localhost:5433/minute
SECRET_KEY=dev-secret-key-change-in-production
CORS_ORIGINS=*

# LLM settings
GEMINI_API_KEY=
GROQ_API_KEY=
GEMINI_MODEL=gemini-2.5-flash-lite
LLM_OUTPUT_LANGUAGE=vi

# ASR settings
ASR_URL=http://localhost:9000
ASR_LANGUAGE=vi
ENVVARS
fi

echo
echo "Setup complete."
echo "1) Start full stack: cd infra && docker compose up -d --build"
echo "2) Run backend local: cd backend && source .venv/bin/activate && uvicorn app.main:app --reload --port 8000"
echo "3) Frontend: cd frontend && npm install && npm run dev"
