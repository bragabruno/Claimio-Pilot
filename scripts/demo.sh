#!/usr/bin/env bash
# One-command demo: brings up the datastore, migrates, seeds, and runs the API + web UI.
# Ctrl-C stops both servers.
#
# Requirements: Docker, uv, node/npm, and a reachable embedding model (see .env).
# For a local Ollama that lacks the default llama3.1, export a model you have, e.g.:
#   LLM_MODEL=llama3.2:3b make demo
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "==> Starting Postgres + pgvector"
docker compose up -d db
until [ "$(docker inspect -f '{{.State.Health.Status}}' claimpilot-db 2>/dev/null)" = "healthy" ]; do
  sleep 1
done

echo "==> Applying migrations"
(cd backend && uv run alembic upgrade head)

echo "==> Seeding synthetic data + embedding state rules"
(cd backend && uv run python -m app.seed.load)

echo "==> Launching API (http://localhost:8000) and web UI (http://localhost:3000)"
echo "    Press Ctrl-C to stop both."
pids=()
(cd backend && uv run uvicorn app.main:app --port 8000) &
pids+=($!)
(cd frontend && npm run dev) &
pids+=($!)

trap 'echo; echo "Stopping..."; kill "${pids[@]}" 2>/dev/null || true; exit 0' INT TERM
wait
