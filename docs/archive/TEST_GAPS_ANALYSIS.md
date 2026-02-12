# Test Gaps Analysis

**Date**: January 2025  
**Status**: Analysis Complete

---

## Executive Summary

This document identifies gaps in test coverage for recently implemented features:

1. **Clean Architecture** components (domain services, orchestrators, value objects, adapters)
2. **Commissions & Dividends** implementation (new fields, config store, aggregates)

---

## 🔴 Critical Gaps (No Tests)

### 1. Domain Services

**Status**: ❌ **NO TESTS**

#### `PriceTrigger` (`backend/domain/services/price_trigger.py`)

- ✅ Should test: Price change calculations
- ✅ Should test: Up threshold triggers (sell)
- ✅ Should test: Down threshold triggers (buy)
- ✅ Should test: No anchor price handling
- ✅ Should test: Zero anchor price handling
- ✅ Should test: Edge cases (exact threshold, boundary conditions)

#### `GuardrailEvaluator` (`backend/domain/services/guardrail_evaluator.py`)

- ✅ Should test: Allocation bounds checking
- ✅ Should test: Trade intent generation
- ✅ Should test: Buy vs sell guardrail logic
- ✅ Should test: Zero/negative equity handling
- ✅ Should test: `max_trade_pct_of_position` enforcement
- ✅ Should test: `max_daily_notional` enforcement (if implemented)
- ✅ Should test: Simulated allocation calculations

**Priority**: 🔴 **HIGH** - Core business logic, no tests

---

### 2. Orchestrators

**Status**: ❌ **NO TESTS**

#### `LiveTradingOrchestrator` (`backend/application/orchestrators/live_trading.py`)

- ✅ Should test: Full cycle execution
- ✅ Should test: Position iteration
- ✅ Should test: Event logging
- ✅ Should test: Error handling
- ✅ Should test: Integration with domain services
- ✅ Should test: Order submission flow

#### `SimulationOrchestrator` (`backend/application/orchestrators/simulation.py`)

- ✅ Should test: Historical replay
- ✅ Should test: Timestamp iteration
- ✅ Should test: State loading
- ✅ Should test: Event logging
- ✅ Should test: Integration with domain services
- ✅ Should test: Simulated order submission

**Priority**: 🔴 **HIGH** - Critical workflows, no tests

---

### 3. Value Objects

**Status**: ❌ **NO TESTS**

#### New Value Objects (all in `backend/domain/value_objects/`)

- `MarketQuote` - No tests
- `PositionState` - No tests
- `TriggerConfig` - No tests
- `GuardrailConfig` - No tests
- `TriggerDecision` - No tests
- `GuardrailDecision` - No tests
- `TradeIntent` - No tests

**Priority**: 🟡 **MEDIUM** - Data structures, but should validate invariants

---

### 4. Infrastructure Adapters

**Status**: ❌ **NO TESTS**

#### All 7 Adapters (in `backend/infrastructure/adapters/`)

- `position_repo_adapter.py` - No tests
- `market_data_adapter.py` - No tests
- `historical_data_adapter.py` - No tests
- `order_service_adapter.py` - No tests
- `event_logger_adapter.py` - No tests
- `sim_order_service_adapter.py` - No tests
- `sim_position_repo_adapter.py` - No tests

**Priority**: 🟡 **MEDIUM** - Integration layer, should test conversions

---

### 5. Type Converters

**Status**: ❌ **NO TESTS**

#### `converters.py` (`backend/infrastructure/adapters/converters.py`)

- ✅ Should test: `position_to_position_state` conversion
- ✅ Should test: `position_state_to_position` conversion
- ✅ Should test: `price_data_to_market_quote` conversion
- ✅ Should test: `market_quote_to_price_data` conversion
- ✅ Should test: `order_policy_to_trigger_config` conversion
- ✅ Should test: `guardrail_policy_to_guardrail_config` conversion
- ✅ Should test: Decimal/float precision handling
- ✅ Should test: None/null handling

**Priority**: 🟡 **MEDIUM** - Critical for data integrity

---

### 6. Config Store

**Status**: ❌ **NO TESTS**

#### `InMemoryConfigRepo` (`backend/infrastructure/persistence/memory/config_repo_mem.py`)

- ✅ Should test: `get_config_value` with defaults
- ✅ Should test: `set_config_value`
- ✅ Should test: `get_commission_rate` hierarchy (GLOBAL → TENANT → TENANT_ASSET)
- ✅ Should test: Default commission rate
- ✅ Should test: Tenant-specific rates
- ✅ Should test: Asset-specific rates

**Priority**: 🟡 **MEDIUM** - Used by SubmitOrderUC

---

## 🟡 Partial Coverage Gaps

### 7. Commission Tracking in Use Cases

**Status**: ⚠️ **PARTIAL**

#### `SubmitOrderUC` (`backend/application/use_cases/submit_order_uc.py`)

- ❌ Missing: Test commission rate snapshot
- ❌ Missing: Test commission estimation calculation
- ❌ Missing: Test config store integration
- ✅ Existing: Basic order submission tests

#### `ExecuteOrderUC` (`backend/application/use_cases/execute_order_uc.py`)

- ❌ Missing: Test `total_commission_paid` increment
- ❌ Missing: Test commission aggregation
- ✅ Existing: Basic commission handling (decreases cash)

**Priority**: 🟡 **MEDIUM** - New fields not tested

---

### 8. Dividend Aggregates

**Status**: ⚠️ **PARTIAL**

#### `ProcessDividendUC` (`backend/application/use_cases/process_dividend_uc.py`)

- ❌ Missing: Test `total_dividends_received` increment
- ✅ Existing: Comprehensive dividend workflow tests

**Priority**: 🟡 **MEDIUM** - New field not tested

---

### 9. Entity Field Updates

**Status**: ⚠️ **PARTIAL**

#### `Order` Entity

- ❌ Missing: Test `commission_rate_snapshot` field
- ❌ Missing: Test `commission_estimated` field
- ✅ Existing: Basic order creation tests

#### `Position` Entity

- ❌ Missing: Test `total_commission_paid` field
- ❌ Missing: Test `total_dividends_received` field
- ✅ Existing: Basic position tests

#### `Trade` Entity

- ❌ Missing: Test `commission_rate_effective` field
- ❌ Missing: Test `status` field
- ✅ Existing: Basic trade creation tests

**Priority**: 🟡 **MEDIUM** - New fields not validated

---

## ✅ Well-Tested Areas

1. **Existing Use Cases**: `SubmitOrderUC`, `ExecuteOrderUC`, `ProcessDividendUC` have good coverage
2. **Domain Entities**: Basic entity tests exist
3. **Integration Tests**: API endpoints have integration tests
4. **Dividend Workflow**: Comprehensive dividend tests exist

---

## 📊 Test Coverage Summary

| Component                                          | Status      | Priority  | Estimated Effort |
| -------------------------------------------------- | ----------- | --------- | ---------------- |
| Domain Services (PriceTrigger, GuardrailEvaluator) | ❌ No tests | 🔴 HIGH   | 2-3 days         |
| Orchestrators (Live, Simulation)                   | ❌ No tests | 🔴 HIGH   | 2-3 days         |
| Value Objects (7 new VOs)                          | ❌ No tests | 🟡 MEDIUM | 1 day            |
| Infrastructure Adapters (7 adapters)               | ❌ No tests | 🟡 MEDIUM | 2-3 days         |
| Type Converters                                    | ❌ No tests | 🟡 MEDIUM | 1 day            |
| Config Store                                       | ❌ No tests | 🟡 MEDIUM | 0.5 day          |
| Commission Tracking (UCs)                          | ⚠️ Partial  | 🟡 MEDIUM | 1 day            |
| Dividend Aggregates                                | ⚠️ Partial  | 🟡 MEDIUM | 0.5 day          |
| Entity Field Updates                               | ⚠️ Partial  | 🟡 MEDIUM | 1 day            |

**Total Estimated Effort**: ~12-15 days

---

## 🎯 Recommended Test Implementation Order

### Phase 1: Critical Business Logic (Week 1)

1. ✅ Domain Services (`PriceTrigger`, `GuardrailEvaluator`)
2. ✅ Type Converters (data integrity)

### Phase 2: Workflow Integration (Week 2)

3. ✅ Orchestrators (`LiveTradingOrchestrator`, `SimulationOrchestrator`)
4. ✅ Config Store

### Phase 3: Adapters & Value Objects (Week 3)

5. ✅ Infrastructure Adapters (all 7)
6. ✅ Value Objects (all 7)

### Phase 4: Commission/Dividend Gaps (Week 4)

7. ✅ Commission tracking in use cases
8. ✅ Dividend aggregates
9. ✅ Entity field validation

---

## 📝 Test File Structure Recommendations

```
backend/tests/
├── unit/
│   ├── domain/
│   │   ├── services/
│   │   │   ├── test_price_trigger.py          # NEW
│   │   │   └── test_guardrail_evaluator.py    # NEW
│   │   └── value_objects/
│   │       ├── test_market_quote.py           # NEW
│   │       ├── test_position_state.py        # NEW
│   │       ├── test_trigger_config.py        # NEW
│   │       ├── test_guardrail_config.py      # NEW
│   │       ├── test_trigger_decision.py      # NEW
│   │       ├── test_guardrail_decision.py   # NEW
│   │       └── test_trade_intent.py          # NEW
│   ├── application/
│   │   ├── orchestrators/
│   │   │   ├── test_live_trading.py          # NEW
│   │   │   └── test_simulation.py            # NEW
│   │   └── use_cases/
│   │       ├── test_submit_order_uc.py       # UPDATE (commission tests)
│   │       ├── test_execute_order_uc.py     # UPDATE (aggregate tests)
│   │       └── test_process_dividend_uc.py   # UPDATE (aggregate tests)
│   └── infrastructure/
│       ├── adapters/
│       │   ├── test_converters.py            # NEW
│       │   ├── test_position_repo_adapter.py # NEW
│       │   ├── test_market_data_adapter.py   # NEW
│       │   ├── test_historical_data_adapter.py # NEW
│       │   ├── test_order_service_adapter.py # NEW
│       │   ├── test_event_logger_adapter.py  # NEW
│       │   ├── test_sim_order_service_adapter.py # NEW
│       │   └── test_sim_position_repo_adapter.py # NEW
│       └── persistence/
│           └── memory/
│               └── test_config_repo_mem.py  # NEW
└── integration/
    └── test_orchestrators_integration.py     # NEW (optional)
```

---

## 🔍 Specific Test Cases Needed

### PriceTrigger Tests

```python
def test_price_trigger_no_anchor_price()
def test_price_trigger_zero_anchor_price()
def test_price_trigger_up_threshold_sell()
def test_price_trigger_down_threshold_buy()
def test_price_trigger_within_threshold()
def test_price_trigger_exact_threshold()
def test_price_trigger_negative_price_change()
```

### GuardrailEvaluator Tests

```python
def test_guardrail_evaluator_no_trigger()
def test_guardrail_evaluator_buy_within_bounds()
def test_guardrail_evaluator_sell_within_bounds()
def test_guardrail_evaluator_buy_exceeds_max_allocation()
def test_guardrail_evaluator_sell_below_min_allocation()
def test_guardrail_evaluator_zero_equity()
def test_guardrail_evaluator_max_trade_pct_enforcement()
```

### Commission Tracking Tests

```python
def test_submit_order_snapshots_commission_rate()
def test_submit_order_calculates_commission_estimated()
def test_execute_order_increments_total_commission_paid()
def test_commission_aggregation_multiple_trades()
```

### Dividend Aggregate Tests

```python
def test_process_dividend_increments_total_dividends_received()
def test_dividend_aggregation_multiple_payments()
```

---

## ✅ Next Steps

1. **Review this analysis** with the team
2. **Prioritize** based on business needs
3. **Create test files** following the structure above
4. **Implement tests** in priority order
5. **Update CI/CD** to ensure tests run on every commit

---

**Last Updated**: January 2025
