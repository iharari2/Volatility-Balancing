# =========================
# Makefile
# =========================
# (Place at repo root)
# Usage examples:
#   make venv install dev   # first-time setup + run dev server
#   make test lint type      # run tests, ruff, mypy
#   make run                 # run without reloader
#   make fmt                 # auto-fix lint issues

.PHONY: venv install run dev test lint type fmt cov clean help

PY := python
APP := app.main:app
APP_DIR := backend
SRC := backend

venv:
	python3 -m venv .venv

install:
	. .venv/bin/activate && pip install -e ".[dev]"

run:
	. .venv/bin/activate && PYTHONPATH=$(SRC) $(PY) -m uvicorn --app-dir $(APP_DIR) $(APP)

dev:
	. .venv/bin/activate && PYTHONPATH=$(SRC) $(PY) -m uvicorn --app-dir $(APP_DIR) $(APP) --reload

test:
	. .venv/bin/activate && PYTHONPATH=$(SRC) $(PY) -m pytest -q

lint:
	. .venv/bin/activate && $(PY) -m ruff check $(SRC)

fmt:
	. .venv/bin/activate && $(PY) -m ruff check $(SRC) --fix

type:
	. .venv/bin/activate && $(PY) -m mypy $(SRC)

cov:
	. .venv/bin/activate && $(PY) -m pytest --cov=$(SRC) -q || true

clean:
	find $(SRC) -name "__pycache__" -type d -exec rm -rf {} + ; find . -name "*.pyc" -delete

help:
	@echo "Targets: venv install run dev test lint fmt type cov clean"

