# Test Implementation Plan

**Date**: January 2025  
**Status**: Planning Phase  
**Priority Order**: 1 → 2 → 3 → 4 → 5

---

## Overview

This document outlines a comprehensive test implementation plan organized by priority. The goal is to achieve high test coverage across all layers of the application, ensuring reliability and maintainability.

---

## Priority 1: Fix and Update Existing Tests ✅

**Goal**: Ensure all existing tests pass and work correctly with recent changes.

### 1.1 Audit Existing Tests

**Status**: ⚠️ **IN PROGRESS**

**Tasks**:

- [ ] Run full test suite: `pytest backend/tests/`
- [ ] Identify all failing tests
- [ ] Document failures and root causes
- [ ] Fix broken tests due to:
  - [ ] New entity fields (commission, dividends)
  - [ ] API signature changes
  - [ ] Database schema changes
  - [ ] Dependency injection changes

**Files to Review**:

- `backend/tests/unit/domain/test_position_entity.py` - Check new fields
- `backend/tests/unit/domain/test_order_entity.py` - Check commission fields
- `backend/tests/unit/domain/test_trade_entity.py` - Check new fields
- `backend/tests/unit/application/test_submit_order_uc.py` - Check config_repo
- `backend/tests/unit/application/test_execute_order_uc.py` - Check aggregates
- `backend/tests/unit/application/test_process_dividend_uc.py` - Check aggregates
- `backend/tests/integration/test_orders_api.py` - Check API changes
- `backend/tests/integration/test_positions_api.py` - Check API changes

**Estimated Effort**: 2-3 days

### 1.2 Update Entity Tests for New Fields

**Status**: ⚠️ **IN PROGRESS**

**Tasks**:

- [ ] Update `test_position_entity.py`:
  - [ ] Test `total_commission_paid` field
  - [ ] Test `total_dividends_received` field
  - [ ] Test default values (0.0)
  - [ ] Test increment operations
- [ ] Update `test_order_entity.py`:
  - [ ] Test `commission_rate_snapshot` field
  - [ ] Test `commission_estimated` field
  - [ ] Test nullable behavior
- [ ] Update `test_trade_entity.py`:
  - [ ] Test `commission_rate_effective` field
  - [ ] Test `status` field
  - [ ] Test default values

**Estimated Effort**: 1 day

### 1.3 Update Use Case Tests

**Status**: ⚠️ **IN PROGRESS**

**Tasks**:

- [ ] Update `test_submit_order_uc.py`:
  - [ ] Test commission rate snapshot
  - [ ] Test commission estimation
  - [ ] Test config_repo integration
- [ ] Update `test_execute_order_uc.py`:
  - [ ] Test `total_commission_paid` increment
  - [ ] Test commission aggregation
- [ ] Update `test_process_dividend_uc.py`:
  - [ ] Test `total_dividends_received` increment
  - [ ] Test dividend aggregation

**Estimated Effort**: 1 day

### 1.4 Update Integration Tests

**Status**: ⚠️ **IN PROGRESS**

**Tasks**:

- [ ] Update `test_orders_api.py`:
  - [ ] Test order creation with commission fields
  - [ ] Test order fill with commission tracking
- [ ] Update `test_positions_api.py`:
  - [ ] Test position creation with new fields
  - [ ] Test position updates with aggregates
- [ ] Update `test_dividend_api.py`:
  - [ ] Test dividend processing with aggregates

**Estimated Effort**: 1 day

**Total Priority 1 Effort**: 5-6 days

---

## Priority 2: Unit Tests for All Entities ✅

**Goal**: Comprehensive unit tests for all domain entities.

### 2.1 Position Entity Tests

**Status**: ✅ **PARTIAL** (needs new fields)

**Test Cases**:

- [x] Basic creation
- [x] Creation with anchor price
- [x] Creation with dividend settings
- [x] Set anchor price
- [x] Get effective cash
- [x] Adjust anchor for dividend
- [x] Add/clear dividend receivable
- [ ] **NEW**: Test `total_commission_paid` increment
- [ ] **NEW**: Test `total_dividends_received` increment
- [ ] **NEW**: Test default values for aggregates
- [ ] **NEW**: Test commission aggregation across multiple trades
- [ ] **NEW**: Test dividend aggregation across multiple payments

**File**: `backend/tests/unit/domain/test_position_entity.py`

**Estimated Effort**: 0.5 day

### 2.2 Order Entity Tests

**Status**: ✅ **PARTIAL** (needs commission fields)

**Test Cases**:

- [x] Basic creation
- [x] Creation with all fields
- [x] Status validation
- [x] Side validation
- [ ] **NEW**: Test `commission_rate_snapshot` field
- [ ] **NEW**: Test `commission_estimated` field
- [ ] **NEW**: Test nullable behavior
- [ ] **NEW**: Test commission calculation logic

**File**: `backend/tests/unit/domain/test_order_entity.py`

**Estimated Effort**: 0.5 day

### 2.3 Trade Entity Tests

**Status**: ✅ **PARTIAL** (needs new fields)

**Test Cases**:

- [x] Basic creation
- [x] Creation with zero commission
- [x] Creation with negative commission
- [ ] **NEW**: Test `commission_rate_effective` field
- [ ] **NEW**: Test `status` field (executed, cancelled, rejected)
- [ ] **NEW**: Test default status value
- [ ] **NEW**: Test status transitions

**File**: `backend/tests/unit/domain/test_trade_entity.py`

**Estimated Effort**: 0.5 day

### 2.4 Dividend Entity Tests

**Status**: ✅ **COMPLETE**

**Test Cases**:

- [x] All dividend entity tests exist
- [x] DividendReceivable tests exist

**File**: `backend/tests/unit/domain/test_dividend_entities.py`

**Estimated Effort**: 0 days (already complete)

### 2.5 Event Entity Tests

**Status**: ✅ **COMPLETE**

**Test Cases**:

- [x] Event creation tests exist

**File**: `backend/tests/unit/domain/test_event_entity.py`

**Estimated Effort**: 0 days (already complete)

### 2.6 Optimization Entity Tests

**Status**: ✅ **COMPLETE**

**Test Cases**:

- [x] OptimizationConfig tests exist
- [x] OptimizationResult tests exist
- [x] ParameterCombination tests exist

**File**: `backend/tests/unit/domain/test_optimization_entities.py`

**Estimated Effort**: 0 days (already complete)

### 2.7 Portfolio Entity Tests

**Status**: ❌ **MISSING**

**Test Cases**:

- [ ] Basic portfolio creation
- [ ] Portfolio with positions
- [ ] Portfolio state management
- [ ] Portfolio updates

**File**: `backend/tests/unit/domain/test_portfolio_entity.py` (NEW)

**Estimated Effort**: 0.5 day

### 2.8 Simulation Entity Tests

**Status**: ❌ **MISSING**

**Test Cases**:

- [ ] SimulationResult creation
- [ ] SimulationResult metrics
- [ ] Trade log management

**File**: `backend/tests/unit/domain/test_simulation_entity.py` (NEW)

**Estimated Effort**: 0.5 day

**Total Priority 2 Effort**: 2.5 days

---

## Priority 3: Integration Tests ✅

**Goal**: Test interactions between components and external systems.

### 3.1 API Integration Tests

**Status**: ✅ **PARTIAL**

**Existing Tests**:

- [x] `test_orders_api.py` - Order API endpoints
- [x] `test_positions_api.py` - Position API endpoints
- [x] `test_dividend_api.py` - Dividend API endpoints
- [x] `test_optimization_api.py` - Optimization API endpoints
- [x] `test_health.py` - Health check endpoint

**New Tests Needed**:

- [ ] **NEW**: Test commission fields in order API responses
- [ ] **NEW**: Test aggregate fields in position API responses
- [ ] **NEW**: Test anchor price auto-reset via API
- [ ] **NEW**: Test portfolio management API endpoints
- [ ] **NEW**: Test trading API endpoints
- [ ] **NEW**: Test simulation API endpoints

**Files**:

- `backend/tests/integration/test_orders_api.py` (UPDATE)
- `backend/tests/integration/test_positions_api.py` (UPDATE)
- `backend/tests/integration/test_portfolio_api.py` (NEW)
- `backend/tests/integration/test_trading_api.py` (NEW)
- `backend/tests/integration/test_simulation_api.py` (NEW)

**Estimated Effort**: 2 days

### 3.2 Database Integration Tests

**Status**: ❌ **MISSING**

**Test Cases**:

- [ ] Test SQL repository CRUD operations
- [ ] Test commission/dividend field persistence
- [ ] Test database migrations
- [ ] Test transaction handling
- [ ] Test concurrent access
- [ ] Test data integrity constraints

**File**: `backend/tests/integration/test_database_integration.py` (NEW)

**Estimated Effort**: 1.5 days

### 3.3 Market Data Integration Tests

**Status**: ❌ **MISSING**

**Test Cases**:

- [ ] Test YFinance adapter
- [ ] Test market data fetching
- [ ] Test price data validation
- [ ] Test after-hours handling
- [ ] Test error handling (network failures, invalid tickers)
- [ ] Test caching behavior

**File**: `backend/tests/integration/test_market_data_integration.py` (NEW)

**Estimated Effort**: 1 day

### 3.4 End-to-End Workflow Tests

**Status**: ❌ **MISSING**

**Test Cases**:

- [ ] Complete order lifecycle (submit → fill → position update)
- [ ] Complete dividend workflow (announce → ex-date → payment)
- [ ] Complete trading cycle (evaluate → trigger → order → fill)
- [ ] Complete simulation workflow

**File**: `backend/tests/integration/test_workflows.py` (NEW)

**Estimated Effort**: 2 days

**Total Priority 3 Effort**: 6.5 days

---

## Priority 4: Use Case Tests ✅

**Goal**: Comprehensive tests for all application use cases.

### 4.1 Position Management Use Cases

**Status**: ⚠️ **PARTIAL**

#### 4.1.1 Create New Asset and Add to Portfolio

**Test Cases**:

- [ ] Create position with ticker and initial values
- [ ] Create position with market price fetch
- [ ] Create position with custom anchor price
- [ ] Create position with order policy
- [ ] Create position with guardrails
- [ ] Create position with $5000 cash + $5000 asset defaults
- [ ] Create position - verify anchor = market price
- [ ] Create position - handle invalid ticker
- [ ] Create position - handle market data fetch failure
- [ ] Create position - verify commission aggregates initialized to 0
- [ ] Create position - verify dividend aggregates initialized to 0

**File**: `backend/tests/unit/application/test_create_position_uc.py` (NEW)

**Estimated Effort**: 1 day

#### 4.1.2 Update Position

**Test Cases**:

- [ ] Update position cash amount
- [ ] Update position quantity
- [ ] Update anchor price
- [ ] Update order policy
- [ ] Update guardrails
- [ ] Update position - preserve aggregates

**File**: `backend/tests/unit/application/test_update_position_uc.py` (NEW)

**Estimated Effort**: 0.5 day

### 4.2 Trading Use Cases

**Status**: ⚠️ **PARTIAL**

#### 4.2.1 Submit Order Use Case

**Status**: ✅ **EXISTS** (needs commission tests)

**Test Cases**:

- [x] Basic order submission
- [x] Idempotency handling
- [x] Daily cap enforcement
- [ ] **NEW**: Test commission rate snapshot
- [ ] **NEW**: Test commission estimation
- [ ] **NEW**: Test config_repo integration
- [ ] **NEW**: Test tenant-specific commission rates
- [ ] **NEW**: Test asset-specific commission rates

**File**: `backend/tests/unit/application/test_submit_order_uc.py` (UPDATE)

**Estimated Effort**: 0.5 day

#### 4.2.2 Execute Order Use Case

**Status**: ✅ **EXISTS** (needs aggregate tests)

**Test Cases**:

- [x] Fill buy order
- [x] Fill sell order
- [x] Commission handling
- [x] Guardrail validation
- [ ] **NEW**: Test `total_commission_paid` increment
- [ ] **NEW**: Test commission aggregation
- [ ] **NEW**: Test `commission_rate_effective` in Trade
- [ ] **NEW**: Test trade status tracking

**File**: `backend/tests/unit/application/test_execute_order_uc.py` (UPDATE)

**Estimated Effort**: 0.5 day

#### 4.2.3 Evaluate Position Use Case

**Status**: ❌ **MISSING**

**Test Cases**:

- [ ] Evaluate position - no anchor price
- [ ] Evaluate position - buy trigger
- [ ] Evaluate position - sell trigger
- [ ] Evaluate position - no trigger
- [ ] Evaluate position - anchor price anomaly detection (>50%)
- [ ] Evaluate position - anchor price auto-reset
- [ ] Evaluate position - order sizing calculation
- [ ] Evaluate position - guardrail trimming
- [ ] Evaluate position - auto-rebalancing
- [ ] Evaluate position - with market data
- [ ] Evaluate position - after-hours handling

**File**: `backend/tests/unit/application/test_evaluate_position_uc.py` (NEW)

**Estimated Effort**: 1.5 days

### 4.3 Continuous Trading Use Cases

**Status**: ❌ **MISSING**

#### 4.3.1 Live Trading Orchestrator

**Test Cases**:

- [ ] Run trading cycle - no positions
- [ ] Run trading cycle - single position
- [ ] Run trading cycle - multiple positions
- [ ] Run trading cycle - trigger detection
- [ ] Run trading cycle - order submission
- [ ] Run trading cycle - event logging
- [ ] Run trading cycle - error handling
- [ ] Run trading cycle - partial failures

**File**: `backend/tests/unit/application/test_live_trading_orchestrator.py` (NEW)

**Estimated Effort**: 1.5 days

#### 4.3.2 Simulation Orchestrator

**Test Cases**:

- [ ] Run simulation - historical replay
- [ ] Run simulation - timestamp iteration
- [ ] Run simulation - state loading
- [ ] Run simulation - order submission
- [ ] Run simulation - event logging
- [ ] Run simulation - multiple positions
- [ ] Run simulation - error handling

**File**: `backend/tests/unit/application/test_simulation_orchestrator.py` (NEW)

**Estimated Effort**: 1.5 days

### 4.4 Dividend Use Cases

**Status**: ✅ **EXISTS** (needs aggregate tests)

**Test Cases**:

- [x] Announce dividend
- [x] Process ex-dividend date
- [x] Process dividend payment
- [x] Get dividend status
- [ ] **NEW**: Test `total_dividends_received` increment
- [ ] **NEW**: Test dividend aggregation
- [ ] **NEW**: Test multiple dividend payments

**File**: `backend/tests/unit/application/test_process_dividend_uc.py` (UPDATE)

**Estimated Effort**: 0.5 day

### 4.5 Optimization Use Cases

**Status**: ✅ **EXISTS**

**Test Cases**:

- [x] Create optimization config
- [x] Run optimization
- [x] Get optimization progress
- [x] Get optimization results

**File**: `backend/tests/unit/application/test_parameter_optimization_uc.py`

**Estimated Effort**: 0 days (already complete)

**Total Priority 4 Effort**: 7.5 days

---

## Priority 5: Analysis Tests ✅

**Goal**: Test analysis, reporting, and export functionality.

### 5.1 Portfolio Analysis Tests

**Status**: ❌ **MISSING**

**Test Cases**:

- [ ] Calculate portfolio total value
- [ ] Calculate portfolio P&L
- [ ] Calculate portfolio returns
- [ ] Calculate asset allocation percentages
- [ ] Calculate commission totals
- [ ] Calculate dividend totals
- [ ] Portfolio performance metrics
- [ ] Risk metrics calculation

**File**: `backend/tests/unit/application/test_portfolio_analysis.py` (NEW)

**Estimated Effort**: 1 day

### 5.2 Trade Analysis Tests

**Status**: ❌ **MISSING**

**Test Cases**:

- [ ] Analyze trade history
- [ ] Calculate trade statistics
- [ ] Calculate win/loss ratio
- [ ] Calculate average trade size
- [ ] Calculate commission impact
- [ ] Trade performance by ticker
- [ ] Trade performance by time period

**File**: `backend/tests/unit/application/test_trade_analysis.py` (NEW)

**Estimated Effort**: 1 day

### 5.3 Export Tests

**Status**: ✅ **EXISTS**

**Test Cases**:

- [x] Excel export regression tests exist
- [ ] **NEW**: Test export with commission data
- [ ] **NEW**: Test export with dividend data
- [ ] **NEW**: Test export with aggregates

**File**: `backend/tests/regression/test_export_regression.py` (UPDATE)

**Estimated Effort**: 0.5 day

### 5.4 Reporting Tests

**Status**: ❌ **MISSING**

**Test Cases**:

- [ ] Generate position reports
- [ ] Generate trade reports
- [ ] Generate performance reports
- [ ] Generate commission reports
- [ ] Generate dividend reports
- [ ] Report formatting
- [ ] Report data accuracy

**File**: `backend/tests/unit/application/test_reporting.py` (NEW)

**Estimated Effort**: 1 day

**Total Priority 5 Effort**: 3.5 days

---

## Additional Test Categories

### Domain Services Tests (High Priority)

**Status**: ❌ **MISSING**

**Test Cases**:

- [ ] `PriceTrigger.evaluate()` - all scenarios
- [ ] `GuardrailEvaluator.evaluate()` - all scenarios
- [ ] Edge cases and boundary conditions

**Files**:

- `backend/tests/unit/domain/services/test_price_trigger.py` (NEW)
- `backend/tests/unit/domain/services/test_guardrail_evaluator.py` (NEW)

**Estimated Effort**: 2 days

### Value Objects Tests

**Status**: ❌ **MISSING**

**Test Cases**:

- [ ] MarketQuote validation
- [ ] PositionState validation
- [ ] TriggerConfig validation
- [ ] GuardrailConfig validation
- [ ] TriggerDecision validation
- [ ] GuardrailDecision validation
- [ ] TradeIntent validation

**File**: `backend/tests/unit/domain/value_objects/test_value_objects.py` (NEW)

**Estimated Effort**: 1 day

### Infrastructure Adapter Tests

**Status**: ❌ **MISSING**

**Test Cases**:

- [ ] Position repo adapter
- [ ] Market data adapter
- [ ] Order service adapter
- [ ] Event logger adapter
- [ ] Simulation adapters
- [ ] Type converters

**Files**:

- `backend/tests/unit/infrastructure/adapters/test_adapters.py` (NEW)
- `backend/tests/unit/infrastructure/adapters/test_converters.py` (NEW)

**Estimated Effort**: 2 days

### Config Store Tests

**Status**: ❌ **MISSING**

**Test Cases**:

- [ ] Get/set config values
- [ ] Commission rate hierarchy (GLOBAL → TENANT → ASSET)
- [ ] Default values
- [ ] In-memory implementation

**File**: `backend/tests/unit/infrastructure/persistence/memory/test_config_repo_mem.py` (NEW)

**Estimated Effort**: 0.5 day

---

## Test Infrastructure

### Test Utilities

**Status**: ⚠️ **PARTIAL**

**Needed**:

- [ ] Market data mocks
- [ ] Position fixtures
- [ ] Order fixtures
- [ ] Trade fixtures
- [ ] Database test fixtures
- [ ] API test client utilities

**Files**:

- `backend/tests/fixtures/` (ENHANCE)
- `backend/tests/conftest.py` (ENHANCE)

**Estimated Effort**: 1 day

### Test Coverage

**Status**: ❌ **NOT MEASURED**

**Tasks**:

- [ ] Set up coverage tool (pytest-cov)
- [ ] Generate coverage reports
- [ ] Set coverage targets (80% minimum)
- [ ] Track coverage by module
- [ ] Add coverage to CI/CD

**Estimated Effort**: 0.5 day

---

## Implementation Timeline

### Phase 1: Foundation (Week 1-2)

- **Priority 1**: Fix existing tests (5-6 days)
- **Priority 2**: Entity unit tests (2.5 days)
- **Total**: ~8-9 days

### Phase 2: Integration (Week 3-4)

- **Priority 3**: Integration tests (6.5 days)
- **Total**: ~7 days

### Phase 3: Use Cases (Week 5-6)

- **Priority 4**: Use case tests (7.5 days)
- **Total**: ~8 days

### Phase 4: Analysis & Polish (Week 7)

- **Priority 5**: Analysis tests (3.5 days)
- **Domain Services**: (2 days)
- **Value Objects**: (1 day)
- **Adapters**: (2 days)
- **Config Store**: (0.5 day)
- **Total**: ~9 days

### Phase 5: Infrastructure (Week 8)

- **Test Utilities**: (1 day)
- **Coverage Setup**: (0.5 day)
- **Documentation**: (0.5 day)
- **Total**: ~2 days

**Grand Total**: ~34-35 days (~7 weeks)

---

## Success Criteria

### Phase 1 Complete When:

- ✅ All existing tests pass
- ✅ All entity tests have >90% coverage
- ✅ All new fields are tested

### Phase 2 Complete When:

- ✅ All API endpoints have integration tests
- ✅ Database operations are tested
- ✅ Market data integration is tested
- ✅ End-to-end workflows are tested

### Phase 3 Complete When:

- ✅ All use cases have comprehensive tests
- ✅ Trading workflows are tested
- ✅ Continuous trading is tested
- ✅ Position management is tested

### Phase 4 Complete When:

- ✅ Analysis functions are tested
- ✅ Reporting is tested
- ✅ Domain services are tested
- ✅ All adapters are tested

### Phase 5 Complete When:

- ✅ Test coverage >80% overall
- ✅ Coverage reports automated
- ✅ Test documentation complete

---

## Test File Structure

```
backend/tests/
├── conftest.py                    # Shared fixtures
├── fixtures/                      # Test data fixtures
│   ├── mock_market_data.py
│   ├── position_fixtures.py      # NEW
│   ├── order_fixtures.py          # NEW
│   └── trade_fixtures.py          # NEW
├── unit/
│   ├── domain/
│   │   ├── entities/
│   │   │   ├── test_position_entity.py      # UPDATE
│   │   │   ├── test_order_entity.py         # UPDATE
│   │   │   ├── test_trade_entity.py         # UPDATE
│   │   │   ├── test_portfolio_entity.py      # NEW
│   │   │   └── test_simulation_entity.py    # NEW
│   │   ├── services/
│   │   │   ├── test_price_trigger.py        # NEW
│   │   │   └── test_guardrail_evaluator.py  # NEW
│   │   └── value_objects/
│   │       └── test_value_objects.py        # NEW
│   ├── application/
│   │   ├── use_cases/
│   │   │   ├── test_create_position_uc.py   # NEW
│   │   │   ├── test_update_position_uc.py   # NEW
│   │   │   ├── test_submit_order_uc.py      # UPDATE
│   │   │   ├── test_execute_order_uc.py     # UPDATE
│   │   │   ├── test_evaluate_position_uc.py # NEW
│   │   │   ├── test_live_trading_orchestrator.py # NEW
│   │   │   ├── test_simulation_orchestrator.py  # NEW
│   │   │   └── test_process_dividend_uc.py  # UPDATE
│   │   └── orchestrators/
│   │       ├── test_live_trading.py         # NEW
│   │       └── test_simulation.py          # NEW
│   └── infrastructure/
│       ├── adapters/
│       │   ├── test_adapters.py            # NEW
│       │   └── test_converters.py         # NEW
│       └── persistence/
│           └── memory/
│               └── test_config_repo_mem.py # NEW
├── integration/
│   ├── test_orders_api.py                  # UPDATE
│   ├── test_positions_api.py               # UPDATE
│   ├── test_portfolio_api.py               # NEW
│   ├── test_trading_api.py                 # NEW
│   ├── test_simulation_api.py              # NEW
│   ├── test_database_integration.py        # NEW
│   ├── test_market_data_integration.py     # NEW
│   └── test_workflows.py                   # NEW
└── regression/
    └── test_export_regression.py           # UPDATE
```

---

## Running Tests

### Run All Tests

```bash
pytest backend/tests/
```

### Run by Priority

```bash
# Priority 1: Existing tests
pytest backend/tests/unit/domain/test_*_entity.py

# Priority 2: Entity tests
pytest backend/tests/unit/domain/

# Priority 3: Integration tests
pytest backend/tests/integration/

# Priority 4: Use case tests
pytest backend/tests/unit/application/

# Priority 5: Analysis tests
pytest backend/tests/unit/application/test_*_analysis.py
```

### Run with Coverage

```bash
pytest backend/tests/ --cov=backend --cov-report=html
```

---

## Next Steps

1. **Review this plan** with the team
2. **Prioritize** based on business needs
3. **Start with Priority 1** - fix existing tests
4. **Set up CI/CD** to run tests on every commit
5. **Track progress** using this document

---

**Last Updated**: January 2025  
**Status**: Ready for Implementation
