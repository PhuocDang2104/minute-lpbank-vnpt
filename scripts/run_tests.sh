#!/usr/bin/env bash
set -euo pipefail

# Simple CI runner: executes backend unit + integration tests three times for stability.
# Requirements: python3, pip install -r requirements.txt (run from repo root).

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PYTHONPATH="${ROOT_DIR}/backend:${PYTHONPATH:-}"

cd "${ROOT_DIR}"

for run in 1 2 3; do
  echo "=== Test run ${run}/3 ==="
  pytest -q backend/tests/unit backend/tests/integration
done

echo "All test runs completed."
