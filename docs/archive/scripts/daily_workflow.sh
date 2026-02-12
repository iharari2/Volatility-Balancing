# 1) Activate venv
source .venv/bin/activate

# 2) Run API (reloader)
python -m uvicorn --app-dir backend app.main:app --reload

# 3) In a second terminal (same venv): tests + lint + types
python -m pytest -q
python -m ruff check backend
python -m mypy backend
