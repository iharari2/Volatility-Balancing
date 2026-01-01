# Volatility Balancing — Trading System

A semi-passive trading platform for volatility balancing with blue-chip equities. Features a React frontend, FastAPI backend with Clean Architecture, and comprehensive trading capabilities including position management, order execution, dividend processing, and parameter optimization.

> **📚 New to the project?** Start with the [Onboarding Guide](docs/ONBOARDING.md)  
> **🔍 Looking for documentation?** See the [Documentation Index](docs/DOCUMENTATION_INDEX.md)

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

## 📊 **Current Status**

**✅ Core System Implemented** - Production-ready trading system with portfolio management

### ✅ Implemented Features

- **Portfolio Management**: Multi-tenant, portfolio-scoped architecture
- **Position Management**: Create, manage, and track positions
- **Order Execution**: Idempotent order submission with guardrails
- **Trading Logic**: Volatility-triggered buy/sell with configurable thresholds
- **Simulation**: Backtesting with production logic
- **Parameter Optimization**: 8 REST endpoints for optimization management
- **Excel Export**: Data export capabilities
- **Audit Trails**: Complete event logging

### ⚠️ In Progress / Known Issues

- **UI Wiring**: Some UI components need better data connectivity (per UX feedback)
- **Trade Event Logging**: Enhanced verbose logging for traders (planned)
- **UX Improvements**: Error handling, empty states, confirmation dialogs (see [UX Feedback](docs/UX_FEEDBACK_REQUEST.md))

### 📋 Planned Features

- Enhanced trade event visualization
- Multi-broker support
- Advanced analytics and reporting
- Mobile-responsive improvements

## 🏗️ Architecture Overview

- **Frontend**: React 18 + TypeScript + Vite + Tailwind CSS
- **Backend**: Python FastAPI with Clean Architecture (Hexagonal)
- **Database**: SQLite (dev) / PostgreSQL (prod) + Redis cache
- **Market Data**: YFinance integration
- **Architecture**: Domain-Driven Design with dependency injection

### Clean Architecture Layers

The system follows a clean architecture with three main layers:

1. **Domain Layer** (`backend/domain/`): Pure business logic

   - Value Objects: MarketQuote, PositionState, TriggerConfig, GuardrailConfig, TradeIntent
   - Domain Services: PriceTrigger, GuardrailEvaluator (pure functions)
   - Entities: Position, Order, Trade, Dividend (with commission/dividend aggregates)
   - No infrastructure dependencies

2. **Application Layer** (`backend/application/`): Orchestration

   - Orchestrators: LiveTradingOrchestrator, SimulationOrchestrator
   - Ports: Interfaces for market data, orders, repositories, event logging, config
   - Use Cases: SubmitOrderUC, ExecuteOrderUC, ProcessDividendUC (with commission/dividend tracking)
   - Uses domain services, depends on ports (not concrete implementations)

3. **Infrastructure Layer** (`backend/infrastructure/`): Concrete implementations
   - Adapters: Implement application ports (YFinance, SQL repositories, etc.)
   - Repositories: SQL, Memory, Redis implementations
   - Config Store: Commission rate management
   - External Services: Market data providers, broker APIs

**Key Design**:

- Live trading and simulation share the same domain logic (PriceTrigger, GuardrailEvaluator)
- Commissions and dividends are first-class, traceable, and correctly reflected in portfolio state
- Config is separate from state (commission rates in Config store, not embedded in logic)

**See**:

- [Architecture Documentation](docs/architecture/system_architecture_v1.md)
- [Clean Architecture Details](backend/docs/ARCHITECTURE_CLEANUP.md)
- [Commissions & Dividends Implementation](backend/docs/COMMISSIONS_DIVIDENDS_IMPLEMENTATION.md)

---

## ✅ **Phase 1 Verification**

**First, verify the system is working:**

```bash
# 1. Start backend
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 2. In another terminal, run verification
python verify_phase1.py
```

**See**: [Phase 1 Verification Guide](PHASE1_VERIFY.md) for details

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

**📖 [Documentation Index](docs/DOCUMENTATION_INDEX.md)** - Master navigation hub for all documentation

### Quick Links

- **[Onboarding Guide](docs/ONBOARDING.md)** ⭐ **Start here if you're new**
- **[Quick Start](docs/QUICK_START.md)** - Get running in 5 minutes
- **[Architecture Overview](docs/architecture/README.md)** - System architecture
- **[API Documentation](docs/api/README.md)** - API reference
- **[Developer Notes](docs/DEVELOPER_NOTES.md)** - Development guidelines
- **[Product Specification](docs/product/volatility_trading_spec_v1.md)** - Product requirements (✅ Implemented)
- **[Unimplemented Features](docs/product/unimplemented/README.md)** - Planned features documentation
- **[Documentation Structure Guide](docs/DOCUMENTATION_STRUCTURE_GUIDE.md)** - Understanding the docs organization

### Documentation Structure

- **Architecture**: [System Context](docs/architecture/context.md), [Domain Model](docs/architecture/domain-model.md), [Trading Cycle](docs/architecture/trading-cycle.md)
- **API**: [OpenAPI Spec](docs/api/openapi.yaml), [Migration Guide](docs/api/MIGRATION.md)
- **Development**: [Test Plan](docs/dev/test-plan.md), [CI/CD](docs/dev/ci-cd.md)
- **Product**: [Product Spec](docs/product/volatility_trading_spec_v1.md), [UX Design](docs/UX_DESIGN_DOCUMENT.md)

See [Documentation Index](docs/DOCUMENTATION_INDEX.md) for complete documentation structure.

## 🔌 API Reference

**Base URL:** `http://localhost:8000`

### Interactive Documentation

Visit **http://localhost:8000/docs** for interactive Swagger UI with full API documentation.

### Key Endpoints

**Portfolio-Scoped Endpoints** (Current - Recommended):

- `POST /api/tenants/{tenant_id}/portfolios` - Create portfolio
- `GET /api/tenants/{tenant_id}/portfolios/{portfolio_id}/overview` - Get overview
- `GET /api/tenants/{tenant_id}/portfolios/{portfolio_id}/positions` - List positions
- `POST /api/tenants/{tenant_id}/portfolios/{portfolio_id}/positions` - Create position

**Legacy Endpoints** (Deprecated):

- `/v1/positions/*` - Use portfolio-scoped endpoints instead

See [API Documentation](docs/api/README.md) and [Migration Guide](docs/api/MIGRATION.md) for details.

## 🧪 Testing & Quality

```bash
# Run tests
cd backend
python -m pytest -q

# Lint
python -m ruff check backend

# Type check
python -m mypy backend
```

## 🐛 Troubleshooting

### Common Issues

**"No module named app" (pytest)**

- Ensure `pyproject.toml` has `pythonpath = ["backend"]`
- Or run: `PYTHONPATH=backend python -m pytest -q`

**"Port already in use"**

- Backend: `pkill -f uvicorn` or use `--port 8001`
- Frontend: Use `npm run dev -- --port 3001`

**"Missing idempotency key"**

- Use header: `Idempotency-Key: <value>` (hyphen, not underscore)

See [Onboarding Guide](docs/ONBOARDING.md) for more troubleshooting tips.

---

## 📝 Additional Notes

### Architecture Details

- **Domain Layer**: Uses Python dataclasses (no validation overhead, library-agnostic)
- **API Layer**: Uses Pydantic models (validation + JSON schema/OpenAPI)
- **Persistence**: Default in-memory repos; SQL/Redis adapters available
- **Time**: Testable time via `infrastructure/time/clock.py`

### Switching Persistence

**Redis idempotency:**

```bash
pip install '.[redis]'
# Update app/di.py to use RedisIdempotencyRepo
```

**SQL (SQLite/Postgres):**

```bash
pip install '.[sql]'
# Configure engine in infrastructure/persistence/sql/models.py
# Update app/di.py to use SQL repositories
```

---

_Last updated: 2025-01-27_
