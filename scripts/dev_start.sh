#!/usr/bin/env bash
set -euo pipefail

# Quick helper to boot infra + backend in dev
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/.." && pwd)"

pushd "$repo_root/infra" >/dev/null
if command -v docker-compose >/dev/null; then
  docker-compose up -d
else
  docker compose up -d
fi
popd >/dev/null

if [ -d "$repo_root/backend/.venv" ]; then
  source "$repo_root/backend/.venv/bin/activate"
fi

cd "$repo_root/backend"
uvicorn app.main:app --reload --port 8000