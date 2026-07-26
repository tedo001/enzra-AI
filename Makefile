# ---------------------------------------------------------------------------
# RailVision AI — developer task runner
# ---------------------------------------------------------------------------
.DEFAULT_GOAL := help
.PHONY: help install backend frontend dev test lint format typecheck \
        docker-up docker-down export-onnx benchmark clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

install: ## Install backend + frontend dependencies
	cd backend && pip install -e ".[dev]"
	cd frontend && npm install

backend: ## Run FastAPI backend (reload)
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

frontend: ## Run Next.js dev server
	cd frontend && npm run dev

desktop: ## Run the PyQt6 desktop app (backend + UI in one process)
	pip install -r desktop/requirements.txt
	python -m desktop.main

dev: ## Run full stack via docker-compose
	docker compose up --build

test: ## Run backend unit tests
	cd backend && pytest -q

lint: ## Lint backend (ruff)
	cd backend && ruff check .

format: ## Auto-format backend (ruff + black-compatible)
	cd backend && ruff format . && ruff check --fix .

typecheck: ## Static type check (mypy)
	cd backend && mypy app

docker-up: ## Start infra (db, redis, minio) + services
	docker compose up -d

docker-down: ## Stop all services
	docker compose down

export-onnx: ## Export YOLO26 weights to ONNX
	cd backend && python -m app.mlops.export --format onnx

benchmark: ## Benchmark inference throughput
	cd backend && python -m app.mlops.benchmark

clean: ## Remove caches and build artifacts
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	rm -rf backend/.pytest_cache backend/.ruff_cache backend/.mypy_cache
	rm -rf frontend/.next frontend/out
