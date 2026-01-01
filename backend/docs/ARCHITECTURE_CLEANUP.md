# Architecture Cleanup - Trading vs Simulation Spec

**Date**: January 2025  
**Status**: In Progress  
**Purpose**: Document the new clean architecture implementation per the Trading vs Simulation Spec

---

## Overview

This document describes the new clean architecture implementation that separates domain logic, application orchestrators, and infrastructure adapters according to the Trading vs Simulation Spec.

## Architecture Layers

### 1. Domain Layer (`backend/domain/`)

**Pure business logic. No HTTP, no DB, no external APIs.**

#### Value Objects (`domain/value_objects/`)

New value objects created per spec:

- **`market.py`**: `MarketQuote` - Market quote with ticker, price, timestamp, currency
- **`position_state.py`**: `PositionState` - Position state (ticker, qty, cash, dividend_receivable, anchor_price)
- **`configs.py`**: 
  - `TriggerConfig` - Trigger thresholds (up_threshold_pct, down_threshold_pct)
  - `GuardrailConfig` - Guardrail limits (min_stock_pct, max_stock_pct, max_trade_pct_of_position, max_daily_notional)
- **`decisions.py`**:
  - `TriggerDecision` - Result of trigger evaluation (fired, direction, reason)
  - `GuardrailDecision` - Result of guardrail evaluation (allowed, reason, trade_intent)
- **`trade_intent.py`**: `TradeIntent` - Desired trade (side, qty, reason)

#### Domain Services (`domain/services/`)

Pure functional services:

- **`price_trigger.py`**: `PriceTrigger.evaluate()` - Pure function to evaluate price triggers
- **`guardrail_evaluator.py`**: `GuardrailEvaluator.evaluate()` - Pure function to evaluate guardrails and generate trade intents

**Key Principles**:
- No dependencies on infrastructure
- Deterministic for given inputs
- Easy to unit test
- Shared between live trading and simulation

### 2. Application Layer (`backend/application/`)

**Use cases, workflows, orchestration. Knows about domain and ports, but not concrete DB or HTTP.**

#### Ports (Interfaces) (`application/ports/`)

New ports created per spec:

- **`market_data.py`**:
  - `IMarketDataProvider` - Live market data
  - `IHistoricalPriceProvider` - Historical market data
- **`orders.py`**:
  - `IOrderService` - Live order submission
  - `ISimulationOrderService` - Simulated order submission
- **`repos.py`**:
  - `IPositionRepository` - Position repository operations
  - `ISimulationPositionRepository` - Simulation position repository
  - `IEventLogger` - Event logging

#### Orchestrators (`application/orchestrators/`)

- **`live_trading.py`**: `LiveTradingOrchestrator` - Orchestrates live trading cycles
- **`simulation.py`**: `SimulationOrchestrator` - Orchestrates simulation runs

**Key Principles**:
- Orchestrators use domain services (PriceTrigger, GuardrailEvaluator)
- Orchestrators depend on ports (interfaces), not concrete implementations
- Live trading and simulation use the same domain logic
- Differences are handled by different orchestrators and adapters

### 3. Infrastructure Layer (`backend/infrastructure/`)

**Actual IO: DB, Redis, external APIs, brokers, logging.**

**Status**: Adapters need to be created/updated to implement the new ports.

---

## Implementation Status

### ✅ Completed

1. **Domain Value Objects**: All value objects created per spec
2. **Domain Services**: PriceTrigger and GuardrailEvaluator implemented as pure functions
3. **Application Ports**: All interfaces defined
4. **Application Orchestrators**: LiveTradingOrchestrator and SimulationOrchestrator implemented
5. **Infrastructure Adapters**: All 7 adapters created and implemented
6. **Type Conversions**: All conversion utilities created
7. **Dependency Injection**: Orchestrators wired up in di.py
8. **Commissions & Dividends**: Full implementation per spec (see COMMISSIONS_DIVIDENDS_IMPLEMENTATION.md)

### ⏳ Optional / Future

1. **Migration**: Update existing use cases to use new orchestrators (coexists with old code)
2. **Tests**: Add comprehensive tests for new architecture
3. **Tenant Model**: Add tenant_id/portfolio_id support (deferred to future)

---

## Key Design Decisions

### 1. Decimal vs Float

- **Domain value objects use `Decimal`** for precision (as per spec)
- **Existing entities use `float`** for compatibility
- **Adapters will handle conversion** between float and Decimal

### 2. Pure Domain Services

- `PriceTrigger` and `GuardrailEvaluator` are static methods (pure functions)
- No state, no side effects
- Deterministic and testable

### 3. Separation of Concerns

- **Domain**: Pure business logic, no infrastructure dependencies
- **Application**: Orchestration using domain services and ports
- **Infrastructure**: Concrete implementations of ports

### 4. Shared Domain Logic

- Live trading and simulation use the same `PriceTrigger` and `GuardrailEvaluator`
- Only orchestrators and adapters differ between live and simulation

---

## Migration Path

1. ✅ Create domain value objects and services
2. ✅ Create application ports and orchestrators
3. ⏳ Create infrastructure adapters
4. ⏳ Update existing code to use new orchestrators
5. ⏳ Add tests for new architecture
6. ⏳ Deprecate old use cases (gradually)

---

## Example Usage

### Live Trading

```python
# Setup
orchestrator = LiveTradingOrchestrator(
    market_data=YFinanceMarketDataAdapter(),  # implements IMarketDataProvider
    order_service=LiveOrderServiceAdapter(),   # implements IOrderService
    position_repo=PositionRepoAdapter(),       # implements IPositionRepository
    event_logger=EventLoggerAdapter(),         # implements IEventLogger
    trigger_config_provider=lambda pos_id: TriggerConfig(...),
    guardrail_config_provider=lambda pos_id: GuardrailConfig(...),
)

# Run trading cycle
orchestrator.run_cycle()
```

### Simulation

```python
# Setup
orchestrator = SimulationOrchestrator(
    historical_data=HistoricalDataAdapter(),      # implements IHistoricalPriceProvider
    sim_order_service=SimOrderServiceAdapter(),     # implements ISimulationOrderService
    sim_position_repo=SimPositionRepoAdapter(),   # implements ISimulationPositionRepository
    event_logger=EventLoggerAdapter(),             # implements IEventLogger
)

# Run simulation
orchestrator.run_simulation(
    simulation_run_id="sim_123",
    position_id="pos_456",
    timestamps=[datetime(...), ...],
    trigger_config=TriggerConfig(...),
    guardrail_config=GuardrailConfig(...),
)
```

---

## Benefits

1. **Clean Separation**: Domain logic is independent of infrastructure
2. **Testability**: Domain services are pure functions, easy to test
3. **Reusability**: Same domain logic for live trading and simulation
4. **Maintainability**: Clear boundaries and responsibilities
5. **Flexibility**: Easy to swap implementations (e.g., different market data providers)

---

## Next Steps

1. Create infrastructure adapters implementing the ports
2. Add conversion utilities between entities and value objects
3. Update existing code to use new orchestrators
4. Add comprehensive tests
5. Update documentation

---

**Last Updated**: January 2025  
**Status**: Architecture foundation complete, adapters in progress

