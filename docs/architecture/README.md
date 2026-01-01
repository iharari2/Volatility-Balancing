# Architecture Documentation

This directory contains comprehensive architectural documentation for the Volatility Balancing system, organized using the C4 model and Clean Architecture principles.

## 📐 Documentation Structure

### System Context & Containers

- **[System Context](context.md)** - High-level system boundaries, users, and external systems
- **[Containers](containers.md)** - Major applications and services
- **[Deployment](deployment.md)** - Infrastructure and deployment architecture

### Components & Domain

- **[Component Architecture](component_architecture.md)** - Detailed component relationships and dependencies
- **[Domain Model](domain-model.md)** - Core business entities and value objects
- **[Persistence](persistence.md)** - Database schema and data models

### Behavior & Processes

- **[Trading Cycle](trading-cycle.md)** - Live trading orchestration and flow
- **[Simulation](simulation.md)** - Backtesting and simulation behavior
- **[State Machines](state-machines.md)** - State transitions and lifecycle management

### Position Model

- **[Position Cell Model](position-cell-model.md)** - Position as self-contained trading cell (cash + stock)
- **[Position Performance KPIs](position-performance-kpis.md)** - Performance measurement (position vs stock)

### Cross-Cutting Concerns

- **[Audit & Logging](audit.md)** - Event logging, audit trails, and traceability
- **[Commissions & Dividends](commissions_dividends_architecture.md)** - Commission calculation and dividend processing

### Clean Architecture

- **[Clean Architecture Overview](../architecture/clean_architecture_overview.md)** - Clean architecture implementation details
  - Domain layer (pure business logic)
  - Application layer (use cases)
  - Infrastructure layer (adapters)
  - Presentation layer (API/UI)

## 🗺️ Architecture Navigation

### For Understanding the System

**Start Here:**

1. [System Context](context.md) - Understand what the system does and who uses it
2. [Domain Model](domain-model.md) - Learn the core business concepts
3. [Trading Cycle](trading-cycle.md) - See how trading works end-to-end

**Then Explore:**

- [Component Architecture](component_architecture.md) - How components interact
- [State Machines](state-machines.md) - State transitions and lifecycles
- [Persistence](persistence.md) - Data storage and retrieval

### For Development

**Code Organization:**

1. [Clean Architecture Overview](../architecture/clean_architecture_overview.md) - Architectural principles
2. [Component Architecture](component_architecture.md) - Component structure
3. [Domain Model](domain-model.md) - Domain entities and value objects

**Understanding Flows:**

1. [Trading Cycle](trading-cycle.md) - Live trading flow
2. [Simulation](simulation.md) - Backtesting flow
3. [State Machines](state-machines.md) - State management

### For Operations

**Deployment:**

1. [Deployment](deployment.md) - Infrastructure and deployment
2. [Containers](containers.md) - Application containers

**Monitoring:**

1. [Audit & Logging](audit.md) - Event logging and audit trails

## 🏗️ Architecture Principles

### Clean Architecture

The system follows Clean Architecture with clear separation of concerns:

```
┌─────────────────────────────────────┐
│     Presentation Layer              │
│  (FastAPI Routes, React UI)        │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│     Application Layer                │
│  (Use Cases, Orchestrators)         │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│     Domain Layer                     │
│  (Entities, Value Objects, Services)│
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│     Infrastructure Layer             │
│  (Repositories, Adapters, External) │
└─────────────────────────────────────┘
```

**Key Principles:**

- **Dependency Rule**: Dependencies point inward (Domain has no dependencies)
- **Independence**: Business logic independent of frameworks, UI, and databases
- **Testability**: Easy to test business logic in isolation
- **Flexibility**: Easy to swap implementations

### Portfolio-Scoped Architecture

All data is scoped to tenants and portfolios:

- **Multi-Tenancy**: Complete tenant isolation
- **Portfolio Scoping**: All positions, cash, orders, and trades belong to portfolios
- **Composite Keys**: Database uses `(tenant_id, portfolio_id, ...)` composite keys
- **API Design**: All endpoints require `tenant_id` and `portfolio_id`

### Domain-Driven Design

- **Entities**: Portfolio, Position, Order, Trade
- **Value Objects**: MarketQuote, TriggerConfig, GuardrailConfig
- **Domain Services**: PriceTrigger, GuardrailEvaluator
- **Repositories**: PortfolioRepo, PositionsRepo, OrdersRepo

## 📊 Architecture Diagrams

### High-Level System Architecture

```
┌─────────────┐         ┌─────────────┐
│   React     │────────▶│   FastAPI   │
│   Frontend  │         │   Backend   │
└─────────────┘         └──────┬──────┘
                                │
                ┌───────────────┼───────────────┐
                │               │               │
         ┌──────▼──────┐ ┌──────▼──────┐ ┌──────▼──────┐
         │ PostgreSQL  │ │   Redis     │ │  YFinance   │
         │  Database   │ │   Cache     │ │ Market Data │
         └─────────────┘ └─────────────┘ └─────────────┘
```

### Clean Architecture Layers

See [Clean Architecture Overview](../architecture/clean_architecture_overview.md) for detailed layer diagrams.

## 🔄 Data Flow

### Trading Cycle Flow

1. **Market Data** → Price updates from YFinance
2. **Trigger Evaluation** → Domain service evaluates price triggers
3. **Guardrail Check** → Domain service checks guardrails
4. **Order Creation** → Application layer creates order
5. **Order Execution** → Infrastructure executes via broker
6. **Position Update** → Repository updates position
7. **Event Logging** → Audit trail records all events

See [Trading Cycle](trading-cycle.md) for detailed flow.

## 📁 Archive

Historical and superseded documentation is in the [archive/](archive/) directory:

- Old architecture documents
- Superseded designs
- Historical reference material

## 🔗 Related Documentation

- [API Documentation](../api/README.md) - API endpoints and contracts
- [Developer Notes](../DEVELOPER_NOTES.md) - Development guidelines
- [Product Specification](../product/volatility_trading_spec_v1.md) - Product requirements

## 📝 Document Maintenance

When updating architecture documentation:

1. Keep diagrams current with code
2. Update related documents
3. Archive old versions if major changes
4. Add "Last updated" dates
5. Link to related documents

---

_Last updated: 2025-01-XX_
