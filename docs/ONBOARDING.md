# Onboarding Guide - Volatility Balancing

**Welcome!** This guide will help you get set up and start contributing to the Volatility Balancing project.

**Time to productive:** ~30 minutes

---

## 🎯 What You'll Learn

- How to set up your development environment
- How the project is organized
- How to make your first code change
- Where to find information
- How to get help

---

## 📋 Prerequisites

Before starting, ensure you have:

- **Python 3.11+** installed
- **Node.js 18+** and npm installed
- **Git** installed
- **PostgreSQL** (optional, SQLite works for development)
- **Code editor** (VS Code recommended)

---

## 🚀 Quick Setup (5 minutes)

### 1. Clone the Repository

```bash
git clone <repository-url>
cd Volatility-Balancing
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Linux/Mac:
source .venv/bin/activate
# On Windows:
.venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"
```

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install
```

### 4. Verify Setup

**Terminal 1 - Backend:**

```bash
cd backend
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
python -m uvicorn app.main:app --reload
```

**Terminal 2 - Frontend:**

```bash
cd frontend
npm run dev
```

**Verify:**

- Backend: http://localhost:8000/docs (Swagger UI)
- Frontend: http://localhost:3000

---

## 📚 Understanding the Project

### What is Volatility Balancing?

A semi-passive trading platform for volatility balancing with blue-chip equities. The system:

- Automatically trades based on price volatility thresholds
- Manages portfolios with multiple positions
- Provides simulation and backtesting capabilities
- Includes parameter optimization features

### Project Structure

```
Volatility-Balancing/
├── backend/              # Python FastAPI backend
│   ├── app/            # FastAPI routes and DI
│   ├── domain/         # Business logic (entities, value objects)
│   ├── application/    # Use cases and orchestration
│   ├── infrastructure/ # External adapters (DB, APIs)
│   └── tests/          # Test suite
│
├── frontend/            # React TypeScript frontend
│   ├── src/
│   │   ├── components/ # Reusable UI components
│   │   ├── pages/      # Page components
│   │   ├── hooks/      # Custom React hooks
│   │   └── types/      # TypeScript definitions
│
└── docs/                # Documentation
    ├── architecture/   # Architecture docs
    ├── api/            # API documentation
    ├── dev/            # Development guides
    └── product/        # Product specs
```

### Architecture Overview

The system follows **Clean Architecture** principles:

1. **Domain Layer** (`backend/domain/`)

   - Pure business logic
   - No external dependencies
   - Entities, value objects, domain services

2. **Application Layer** (`backend/application/`)

   - Use cases and orchestration
   - Depends on domain, uses ports (interfaces)

3. **Infrastructure Layer** (`backend/infrastructure/`)

   - Database, external APIs
   - Implements application ports

4. **Presentation Layer** (`backend/app/`, `frontend/`)
   - API routes, UI components

**Key Principle:** Dependencies point inward. Domain has no dependencies.

---

## 🗺️ Key Concepts

### Portfolio-Scoped Architecture

All data is scoped to **tenants** and **portfolios**:

- **Tenant**: Multi-tenant isolation (default: "default")
- **Portfolio**: Independent trading portfolio
- **Position**: Asset position within a portfolio
- **Order**: Trade order for a position
- **Trade**: Executed trade

### Trading Flow

1. **Market Data** → Price updates from YFinance
2. **Trigger Evaluation** → Check if price threshold met
3. **Guardrail Check** → Verify constraints (cash, allocation)
4. **Order Creation** → Create order if valid
5. **Order Execution** → Execute order (simulated or real)
6. **Position Update** → Update position state
7. **Event Logging** → Record in audit trail

### Key Entities

- **Portfolio**: Container for positions and cash
- **Position**: Asset holding (ticker, quantity, anchor price)
- **Order**: Trade request (BUY/SELL, quantity)
- **Trade**: Executed order (price, commission, timestamp)
- **TriggerConfig**: Price threshold settings
- **GuardrailConfig**: Risk constraints

---

## 💻 Your First Code Change

### 1. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make a Small Change

**Example: Add a comment to a domain entity**

```bash
# Edit backend/domain/entities/position.py
# Add a helpful comment
```

### 3. Run Tests

```bash
cd backend
python -m pytest -q
```

### 4. Check Code Quality

```bash
# Lint
python -m ruff check backend

# Type check
python -m mypy backend
```

### 5. Commit and Push

```bash
git add .
git commit -m "docs: Add comment to Position entity"
git push origin feature/your-feature-name
```

---

## 📖 Where to Find Information

### Documentation Structure

1. **[Documentation Index](DOCUMENTATION_INDEX.md)** - Master navigation hub
2. **[Architecture Docs](architecture/README.md)** - System architecture
3. **[API Docs](api/README.md)** - API reference
4. **[Developer Notes](DEVELOPER_NOTES.md)** - Development guidelines

### Common Questions

**"How does X work?"**

- See [Architecture Documentation](architecture/README.md)
- Check [Trading Cycle](architecture/trading-cycle.md) for trading flow
- Review [Domain Model](architecture/domain-model.md) for entities

**"Where is the code for Y?"**

- See [Component Architecture](architecture/component_architecture.md)
- Check [Clean Architecture Overview](architecture/clean_architecture_overview.md)

**"How do I use the API?"**

- See [API Documentation](api/README.md)
- Check [OpenAPI Spec](api/openapi.yaml)
- Use Swagger UI: http://localhost:8000/docs

**"What's the current status?"**

- See [Current Status Summary](dev/current_status_summary.md)
- Check [Development Plan Status](dev/development_plan_status.md)

---

## 🧪 Testing

### Running Tests

```bash
cd backend

# Run all tests
python -m pytest

# Run specific test file
python -m pytest tests/test_positions.py

# Run with coverage
python -m pytest --cov=domain --cov=application --cov=infrastructure
```

### Test Structure

- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test component interactions
- **API Tests**: Test HTTP endpoints

---

## 🔧 Development Workflow

### 1. Start Development Environment

```bash
# Terminal 1: Backend
cd backend
source .venv/bin/activate
python -m uvicorn app.main:app --reload

# Terminal 2: Frontend
cd frontend
npm run dev
```

### 2. Make Changes

- Backend changes auto-reload (uvicorn --reload)
- Frontend changes hot-reload (Vite)

### 3. Test Your Changes

```bash
# Backend tests
cd backend
python -m pytest

# Frontend tests (if configured)
cd frontend
npm test
```

### 4. Check Code Quality

```bash
# Backend
python -m ruff check backend
python -m mypy backend

# Frontend
cd frontend
npm run lint
```

---

## 🐛 Common Issues

### Backend Issues

**"Module not found"**

```bash
# Ensure virtual environment is activated
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# Reinstall dependencies
pip install -e ".[dev]"
```

**"Port already in use"**

```bash
# Use different port
python -m uvicorn app.main:app --reload --port 8001
```

**"Database errors"**

- SQLite is created automatically
- For PostgreSQL, ensure database exists and connection is configured

### Frontend Issues

**"Module not found"**

```bash
# Reinstall dependencies
rm -rf node_modules package-lock.json
npm install
```

**"Port already in use"**

```bash
# Use different port
npm run dev -- --port 3001
```

### WSL-Specific Issues

See [WSL Setup Guide](../WSL_SETUP_GUIDE.md) for WSL-specific troubleshooting.

---

## 🎓 Learning Path

### Week 1: Basics

- [ ] Complete setup
- [ ] Read [Architecture Overview](architecture/README.md)
- [ ] Review [Domain Model](architecture/domain-model.md)
- [ ] Make first small change

### Week 2: Deep Dive

- [ ] Study [Trading Cycle](architecture/trading-cycle.md)
- [ ] Review [Component Architecture](architecture/component_architecture.md)
- [ ] Understand [Clean Architecture](architecture/clean_architecture_overview.md)
- [ ] Read [Product Specification](product/volatility_trading_spec_v1.md)

### Week 3: Contributing

- [ ] Pick a small issue/task
- [ ] Understand the codebase area
- [ ] Make changes and test
- [ ] Submit PR

---

## 🤝 Getting Help

### Documentation

- **[Documentation Index](DOCUMENTATION_INDEX.md)** - Find what you need
- **[Architecture Docs](architecture/README.md)** - System design
- **[API Docs](api/README.md)** - API reference

### Code

- Review existing code (it's well-documented)
- Check test files for usage examples
- Review [Developer Notes](DEVELOPER_NOTES.md)

### Team

- Ask questions in team channels
- Review PRs to learn patterns
- Pair with experienced developers

---

## ✅ Onboarding Checklist

- [ ] Development environment set up
- [ ] Backend running (http://localhost:8000/docs)
- [ ] Frontend running (http://localhost:3000)
- [ ] Tests passing (`pytest`)
- [ ] Read [Architecture Overview](architecture/README.md)
- [ ] Read [Developer Notes](DEVELOPER_NOTES.md)
- [ ] Made first code change
- [ ] Understood project structure
- [ ] Know where to find documentation

---

## 🎉 Next Steps

1. **Explore the Codebase**

   - Start with domain entities
   - Review use cases
   - Check API routes

2. **Read Key Documentation**

   - [Architecture Overview](architecture/README.md)
   - [Trading Cycle](architecture/trading-cycle.md)
   - [Product Specification](product/volatility_trading_spec_v1.md)

3. **Pick a First Task**

   - Look for "good first issue" labels
   - Start with documentation improvements
   - Fix a small bug

4. **Join the Team**
   - Introduce yourself
   - Ask questions
   - Share what you learn

---

## 📚 Additional Resources

- [Quick Start Guide](QUICK_START.md) - Fast setup
- [Documentation Index](DOCUMENTATION_INDEX.md) - All documentation
- [Architecture README](architecture/README.md) - System architecture
- [API README](api/README.md) - API documentation
- [WSL Setup Guide](../WSL_SETUP_GUIDE.md) - WSL-specific help

---

**Welcome to the team! 🚀**

_Last updated: 2025-01-27_








