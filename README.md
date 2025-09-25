# Volatility Balancing — Trading System

A complete semi-passive trading platform for volatility balancing with blue-chip equities. Features a React frontend, FastAPI backend with Clean Architecture, and comprehensive trading capabilities including position management, order execution, dividend processing, and **advanced parameter optimization**.

## 🎉 **NEW: Parameter Optimization System**

**✅ Phase 1 Complete** - We've successfully implemented a comprehensive Parameter Optimization System that enables:

- **Single & Multi-parameter optimization** with realistic simulation processing
- **Configurable metric weights** for fine-tuned optimization control
- **React frontend** with intuitive form-based configuration
- **Heatmap visualization** for parameter space analysis
- **8 REST API endpoints** for complete optimization management
- **Real-time progress tracking** and status monitoring
- **10+ optimization metrics** including Sharpe ratio, drawdown, volatility
- **Constraint validation** and parameter type support

**Demo Results**: Successfully processed 20 parameter combinations with Sharpe ratios up to 1.616!

## 🏗️ Architecture Overview

- **Frontend**: React 18 + TypeScript + Vite + Tailwind CSS
- **Backend**: Python FastAPI with Clean Architecture (Hexagonal)
- **Database**: SQLite (dev) / PostgreSQL (prod) + Redis cache
- **Market Data**: YFinance integration
- **Architecture**: Domain-Driven Design with dependency injection

---

## 🚀 Quick Start

### Backend Setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Parameter Optimization Demo

```bash
cd backend
# Run the comprehensive demo
python demo_optimization_system.py

# Or run simple tests
python test_optimization_simple.py
python test_optimization_api.py
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

### Full Stack Demo

```bash
# Terminal 1: Backend
cd backend && python -m uvicorn app.main:app --reload

# Terminal 2: Frontend
cd frontend && npm run dev

# Open http://localhost:3000
```

## 🎯 **Parameter Optimization System**

### **API Endpoints**

The system provides 8 REST endpoints for complete optimization management:

| Method | Endpoint                                 | Description                       |
| ------ | ---------------------------------------- | --------------------------------- |
| POST   | `/v1/optimization/configs`               | Create optimization configuration |
| GET    | `/v1/optimization/configs/{id}`          | Get configuration details         |
| POST   | `/v1/optimization/configs/{id}/start`    | Start optimization run            |
| GET    | `/v1/optimization/configs/{id}/progress` | Track optimization progress       |
| GET    | `/v1/optimization/configs/{id}/results`  | Get optimization results          |
| GET    | `/v1/optimization/configs/{id}/heatmap`  | Generate heatmap data             |
| GET    | `/v1/optimization/metrics`               | Available optimization metrics    |
| GET    | `/v1/optimization/parameter-types`       | Supported parameter types         |

### **Key Features**

- **Single & Multi-Goal Optimization**: Optimize for one or multiple metrics simultaneously
- **Configurable Weights**: Fine-tune metric influence with custom weight settings
- **React Frontend**: Intuitive form-based configuration with real-time validation
- **Real-time Processing**: Background job processing with progress tracking
- **Heatmap Visualization**: Interactive parameter space analysis
- **10+ Metrics**: Sharpe ratio, drawdown, volatility, win rate, and more
- **Constraint Support**: Min/max values, ranges, and custom validation
- **Export Capabilities**: Complete data export and heatmap generation

### **Interactive Documentation**

Visit `http://localhost:8000/docs` for interactive API documentation with Swagger UI.

## 📁 Project Structure

```
├── frontend/                 # React SPA
│   ├── src/
│   │   ├── components/      # Reusable UI components
│   │   ├── pages/          # Page components
│   │   ├── hooks/          # Custom React hooks
│   │   └── types/          # TypeScript definitions
│   └── package.json
├── backend/                 # FastAPI Backend
│   ├── app/                # FastAPI routes & DI
│   ├── domain/             # Core business logic
│   │   ├── entities/       # Domain entities
│   │   ├── value_objects/  # Value objects
│   │   └── ports/          # Repository interfaces
│   ├── application/        # Use cases & DTOs
│   ├── infrastructure/     # External adapters
│   └── tests/              # Test suite
└── docs/                   # Documentation
    ├── architecture/       # System architecture
    └── api/               # API documentation
```

## 🏛️ Clean Architecture

The system follows Clean Architecture principles with clear separation of concerns:

- **Domain Layer**: Core business entities and rules
- **Application Layer**: Use cases and application services
- **Infrastructure Layer**: External concerns (database, APIs)
- **Presentation Layer**: FastAPI routes and React components

## 📚 Documentation

- **[System Architecture](docs/architecture/system_architecture_v1.md)** - Complete system overview with UML diagrams
- **[Component Architecture](docs/architecture/component_architecture.md)** - Detailed component relationships
- **[Deployment Architecture](docs/architecture/deployment_architecture.md)** - Infrastructure and deployment diagrams
- **[Sequence Diagrams](docs/architecture/SEQUENCE_EXAMPLE.md)** - API flow documentation
- **[API Documentation](docs/api/openapi.yaml)** - Complete OpenAPI 3.0 specification

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
python -m pytest -q # run tests
python -m ruff check backend # lint
python -m mypy backend # types
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

```
