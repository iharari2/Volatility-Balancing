SHELL := /bin/bash
VENV ?= .venv
PY   ?= $(VENV)/bin/python
PIP  ?= $(VENV)/bin/pip
BACKEND_DIR ?= backend
FRONTEND_DIR ?= frontend
API_BASE ?= http://localhost:8000
API_TOKEN ?=
DATABASE_URL ?= postgresql://postgres:postgres@localhost:5432/app
REDIS_URL ?= redis://localhost:6379/0

venv:
	test -d $(VENV) || python3 -m venv $(VENV)

.PHONY: help setup lint fmt unit integration test run-api run-web up down migrate revision smoke local-smoke dbshell logs coverage clean

help:
	@echo "Targets: setup, lint, fmt, unit, integration, test, run-api, run-web, up, down, migrate, revision, smoke, local-smoke, dbshell, logs, coverage, clean"

setup:	venv
	$(PIP) install -U pip
	$(PIP) install -r $(BACKEND_DIR)/requirements.txt
	@if [ -f frontend/package-lock.json ]; then \
		cd frontend && npm ci ; \
	else \
		cd frontend && npm install ; \
	fi
	
lint:
	ruff check $(BACKEND_DIR) || true
	cd $(FRONTEND_DIR) && npm run lint || true

fmt:
	ruff format $(BACKEND_DIR) || true

unit:
	pytest -q $(BACKEND_DIR)/tests/unit --cov=$(BACKEND_DIR) --cov-report=term-missing || true

integration:
	pytest -q $(BACKEND_DIR)/tests/integration || true

test: unit integration

run-api: venv
	cd $(BACKEND_DIR) && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

run-web:
	cd $(FRONTEND_DIR) && npm run dev -- --port 3000

up:
	docker compose up -d || true
	echo "Waiting for DB..." && sleep 3 || true

down:
	docker compose down -v || true

revision:
	cd $(BACKEND_DIR) && alembic revision -m "$(m)" || true

migrate:
	cd $(BACKEND_DIR) && alembic upgrade head || true

smoke:
	curl -f $(API_BASE)/health || exit 1
	API_BASE=$(API_BASE) API_TOKEN=$(API_TOKEN) $(PY) scripts/smoke_place_cancel.py || true

local-smoke: API_BASE=http://localhost:8000
local-smoke:
	$(MAKE) smoke

dbshell:
	psql $(DATABASE_URL) || true

logs:
	docker compose logs -f --tail=200 || true

coverage:
	pytest -q $(BACKEND_DIR)/tests/unit --cov=$(BACKEND_DIR) --cov-report=html || true

clean:
	rm -rf .pytest_cache .mypy_cache htmlcov dist build **/__pycache__
