#!/usr/bin/env bash
set -euo pipefail
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/.." && pwd)"
cd "$repo_root/backend"

# Placeholder migration runner
if [ -f "alembic.ini" ]; then
  alembic upgrade head
else
  echo "alembic.ini missing; add Alembic config before running migrations." >&2
  exit 1
fi