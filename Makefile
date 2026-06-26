.PHONY: install dev down migrate seed api test lint typecheck eval

# Bring up the pgvector datastore (detached) and wait for health.
dev:
	docker compose up -d db
	@echo "Waiting for Postgres to be healthy..."
	@until [ "$$(docker inspect -f '{{.State.Health.Status}}' claimpilot-db)" = "healthy" ]; do sleep 1; done
	@echo "db is healthy."

down:
	docker compose down

# Install backend deps (uv).
install:
	cd backend && uv sync

# Apply migrations.
migrate:
	cd backend && uv run alembic upgrade head

# Load synthetic claimants/properties + ingest & embed state rules.
seed:
	cd backend && uv run python -m app.seed.load

# Run the API (FastAPI / uvicorn).
api:
	cd backend && uv run uvicorn app.main:app --reload --port 8000

test:
	cd backend && uv run pytest -q

lint:
	cd backend && uv run ruff check .

typecheck:
	cd backend && uv run mypy app

# Eval harness — implemented in Phase 6.
eval:
	@echo "Eval harness lands in Phase 6 (see docs/adr/0003, 0004)."
