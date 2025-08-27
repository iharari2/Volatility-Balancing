# Volatility Balancing — API Scaffold

A thin FastAPI service exposing a REST API over a simple domain (Positions, Orders, Events) with **idempotent** order submission. It’s structured by layers (app/domain/application/infrastructure) and ships with unit + integration tests.

---

## TL;DR (Dev Loop)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
python -m uvicorn --app-dir backend app.main:app --reload
# in another terminal (same venv):
python -m pytest -q
python -m ruff check backend
python -m mypy backend
If you prefer Make:

bash
Copy
Edit
make venv install dev     # run server with reload
make test lint type fmt   # tests, lint, types, autofix
Project Structure
bash
Copy
Edit
backend/
  app/               # FastAPI wiring (routes, DI container)
  domain/            # Entities (dataclasses), ports (protocols), errors, value objects
  application/       # Use cases (Flows A–E), DTOs (Pydantic)
  infrastructure/    # Adapters (memory, sql, redis, market)
  tests/             # unit + integration tests
pyproject.toml       # deps + pytest/mypy/ruff config
Makefile             # handy targets (run, dev, test, fmt, type)
Domain → Python dataclasses (no runtime validation): fast, minimal, library-agnostic.

DTOs / API models → Pydantic v2 models (validation + serialization).

Adapters → In-memory by default; SQL/Redis/Market stubs provided.

API Reference
Base URL: http://localhost:8000

Health
GET /healthz → {"status":"ok"}

GET /v1/healthz → {"status":"ok","version":"v1"}

Positions
POST /v1/positions

Body: {"ticker": "ZIM", "qty": 0.0, "cash": 10000.0}

201 → {"id","ticker","qty","cash"}

GET /v1/positions/{position_id}

200 → position details, or 404 position_not_found

GET /v1/positions/{position_id}/events

200 → {"position_id","events":[...]}

POST /v1/positions/{position_id}/evaluate

Placeholder: returns {"position_id","proposals":[]}

Orders (Flow A: Idempotent submit)
POST /v1/positions/{position_id}/orders

Headers: Idempotency-Key: <key> (required)

Body: {"side":"BUY"|"SELL","qty": float>0}

First request for a given (key + body): 201 Created
{ "order_id": "...", "accepted": true, "position_id": "..." }

Replay (same key + same body): 200 OK, same order_id

Mismatched body for same key: 409 Conflict (idempotency_signature_mismatch)

Unknown position: 404 position_not_found

POST /v1/orders/{order_id}/fill (Flow C: simplistic fill)

Body: {"price": >0, "filled_qty": >0, "commission": >=0}

200 → {"order_id","status":"filled","position_qty","position_cash"}

404 → order_not_found (or position_not_found behind it)

Curl Smoke (copy/paste)
bash
Copy
Edit
# Create a position
POS=$(curl -s -X POST localhost:8000/v1/positions \
  -H 'Content-Type: application/json' \
  -d '{"ticker":"ZIM","qty":0,"cash":10000}' \
  | python3 -c 'import sys,json; print(json.load(sys.stdin)["id"])')
echo "$POS"

# First submit -> 201 Created
curl -i -X POST "http://localhost:8000/v1/positions/$POS/orders" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: k1" \
  -d '{"side":"BUY","qty":1.5}'

# Replay same key+body -> 200 OK, same order_id
curl -i -X POST "http://localhost:8000/v1/positions/$POS/orders" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: k1" \
  -d '{"side":"BUY","qty":1.5}'

# Mismatch (same key, different body) -> 409 Conflict
curl -i -X POST "http://localhost:8000/v1/positions/$POS/orders" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: k1" \
  -d '{"side":"SELL","qty":2.0}'

# See audit events
curl -s "http://localhost:8000/v1/positions/$POS/events" | sed 's/},{/},\n{/g'
Architecture & Flows
app/: FastAPI routers (positions.py, orders.py), DI container (di.py), and main.py.

application/: Use cases

SubmitOrderUC (Flow A): idempotent order submission.

EvaluatePositionUC (Flow B): placeholder for proposal generation.

ExecuteOrderUC (Flow C): simplistic fills updating position balances.

ProcessDividendUC (Flow D): cash credit with tax (placeholder).

domain/:

Entities: Order, Position, Event (dataclasses).

Ports: repository protocols (interfaces).

Errors & value objects (guardrails, triggers).

infrastructure/:

In-memory repos (default), plus stubs for SQL (SQLAlchemy) and Redis idempotency.

infrastructure/time/clock.py for testable time.

Why dataclasses vs Pydantic?

Dataclasses for domain (no validation overhead, library-agnostic).

Pydantic for API DTOs (validation + JSON schema/OpenAPI).

Conversion is trivial (dataclasses.asdict() and model.model_dump()).

Switching Persistence (optional)
Default: in-memory repos via app/di.py.

Redis idempotency:

pip install '.[redis]'

In app/di.py, swap InMemoryIdempotencyRepo for RedisIdempotencyRepo and pass a Redis client.

SQL (SQLite/Postgres):

pip install '.[sql]'

Configure engine in infrastructure/persistence/sql/models.py

Use SQLPositionsRepo / SQLOrdersRepo in app/di.py.

The SQL and Redis adapters are basic and intended as starting points.

Testing & Quality
bash
Copy
Edit
python -m pytest -q          # run tests
python -m ruff check backend # lint
python -m mypy backend       # types
pyproject.toml configures pytest to use backend as PYTHONPATH. If you run into path issues, use:

bash
Copy
Edit
PYTHONPATH=backend python -m pytest -q
Troubleshooting
“No module named app” (pytest)
Run tests with python -m pytest or ensure pyproject.toml has:

toml
Copy
Edit
[tool.pytest.ini_options]
pythonpath = ["backend"]
addopts = "-q"
Idempotency 400 (“missing idempotency key”)
The route expects idempotency_key: Optional[str] = Header(None) → send Idempotency-Key: <value> (hyphen, not underscore).

404 with //orders
Your $POS variable is empty. Echo it before use: echo "$POS".

Port already in use
pkill -f uvicorn or use another port: -–port 8001.

```
