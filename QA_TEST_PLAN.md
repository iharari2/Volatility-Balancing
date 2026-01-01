# QA Test Plan - Volatility Balancing System

**QA Leader:** Auto (AI Assistant)  
**Date:** January 2025  
**Status:** Active  
**Version:** 1.0

---

## Executive Summary

This document defines the comprehensive Quality Assurance strategy for the Volatility Balancing trading system. The plan ensures all system requirements are met, all features operate correctly, and the system maintains high reliability standards.

### System Overview

- **Backend:** FastAPI with Clean Architecture (Domain/Application/Infrastructure layers)
- **Frontend:** React 18 + TypeScript
- **Database:** SQLite (dev) / PostgreSQL (prod) + Redis cache
- **Market Data:** YFinance integration
- **Key Features:**
  - Portfolio & Position Management
  - Order Execution & Trade Processing
  - Dividend Processing
  - Parameter Optimization
  - Simulation & Backtesting
  - Excel Export & Reporting
  - Real-time Trading Worker

---

## Test Strategy

### Testing Pyramid

```
        /\
       /  \  E2E Tests (10%)
      /____\
     /      \  Integration Tests (30%)
    /________\
   /          \  Unit Tests (60%)
  /____________\
```

### Test Categories

1. **Unit Tests** (60% of effort)
   - Domain entities and value objects
   - Use cases and business logic
   - Domain services (PriceTrigger, GuardrailEvaluator)
   - Infrastructure adapters

2. **Integration Tests** (30% of effort)
   - API endpoint testing
   - Database operations
   - Market data integration
   - End-to-end workflows

3. **E2E Tests** (10% of effort)
   - Complete user workflows
   - Multi-component interactions
   - System-level validation

---

## Test Requirements by Feature

### 1. Portfolio Management

**Requirements:**
- Create, read, update, delete portfolios
- Multi-tenant support (tenant_id, portfolio_id)
- Portfolio cash balance management
- Portfolio state persistence

**Test Coverage:**
- ✅ Unit: Portfolio entity creation/validation
- ⚠️ Unit: Portfolio cash operations
- ❌ Integration: Portfolio API endpoints
- ❌ E2E: Complete portfolio lifecycle

**Priority:** HIGH

---

### 2. Position Management

**Requirements:**
- Create positions with asset_symbol, qty, anchor_price
- Update position quantities and anchor prices
- Track commission aggregates (total_commission_paid)
- Track dividend aggregates (total_dividends_received)
- Position state validation

**Test Coverage:**
- ✅ Unit: Position entity (partial - needs aggregate tests)
- ⚠️ Integration: Position API (needs portfolio-scoped updates)
- ❌ E2E: Position creation → evaluation → trading cycle

**Priority:** HIGH

---

### 3. Order Management

**Requirements:**
- Idempotent order submission (Idempotency-Key header)
- Order status tracking (submitted, filled, cancelled, rejected)
- Commission rate snapshot and estimation
- Daily cap enforcement (max 5 orders/day)
- Order validation (guardrails, cash/shares availability)

**Test Coverage:**
- ✅ Unit: Order entity (partial - needs commission fields)
- ✅ Unit: SubmitOrderUC (partial - needs commission tests)
- ⚠️ Integration: Order API (needs portfolio-scoped updates)
- ❌ E2E: Order submission → fill → position update

**Priority:** HIGH

---

### 4. Trade Execution

**Requirements:**
- Execute buy/sell orders
- Update position cash and quantity
- Update anchor price to execution price
- Track commission (commission_rate_effective)
- Update total_commission_paid aggregate
- Trade status tracking

**Test Coverage:**
- ✅ Unit: Trade entity (partial - needs status field)
- ✅ Unit: ExecuteOrderUC (partial - needs aggregate tests)
- ⚠️ Integration: Trade execution via API
- ❌ E2E: Complete trade lifecycle

**Priority:** HIGH

---

### 5. Dividend Processing

**Requirements:**
- Announce dividend (ex-date, payment date, amount)
- Process ex-dividend date (adjust anchor price)
- Process dividend payment (credit cash)
- Track total_dividends_received aggregate
- Dividend receivable management

**Test Coverage:**
- ✅ Unit: Dividend entities (complete)
- ✅ Unit: ProcessDividendUC (partial - needs aggregate tests)
- ✅ Integration: Dividend API (complete)
- ❌ E2E: Complete dividend workflow

**Priority:** MEDIUM

---

### 6. Parameter Optimization

**Requirements:**
- Create optimization configurations
- Run single/multi-parameter optimization
- Track optimization progress
- Generate heatmap data
- Export optimization results

**Test Coverage:**
- ✅ Unit: Optimization entities (complete)
- ✅ Unit: ParameterOptimizationUC (complete)
- ✅ Integration: Optimization API (complete)
- ❌ E2E: Complete optimization workflow

**Priority:** MEDIUM

---

### 7. Simulation & Backtesting

**Requirements:**
- Run historical simulations
- Process simulation timestamps
- Generate simulation results
- Export simulation data

**Test Coverage:**
- ⚠️ Unit: Simulation orchestrator (partial)
- ⚠️ Integration: Simulation API (partial)
- ❌ E2E: Complete simulation workflow

**Priority:** MEDIUM

---

### 8. Market Data Integration

**Requirements:**
- Fetch real-time market prices
- Fetch historical OHLC data
- Handle market data errors gracefully
- Cache market data appropriately
- Support after-hours trading

**Test Coverage:**
- ❌ Unit: YFinance adapter
- ❌ Integration: Market data API
- ❌ E2E: Market data → position evaluation

**Priority:** HIGH

---

### 9. Excel Export

**Requirements:**
- Export positions data
- Export trades data
- Export simulation results
- Export optimization results
- Professional formatting

**Test Coverage:**
- ✅ Regression: Export services (fixed)
- ⚠️ Integration: Export API (partial)
- ❌ E2E: Complete export workflow

**Priority:** MEDIUM

---

### 10. Trading Worker

**Requirements:**
- Continuous position evaluation
- Automatic order submission
- Error handling and recovery
- Status monitoring

**Test Coverage:**
- ❌ Unit: Trading worker logic
- ❌ Integration: Worker API interaction
- ❌ E2E: Worker → trading cycle

**Priority:** HIGH

---

## Test Execution Plan

### Phase 1: Foundation (Week 1)

**Goal:** Fix all existing test failures and establish baseline

1. **Execute Full Test Suite**
   ```bash
   cd backend
   python -m pytest tests/ -v --tb=short > test_results_$(date +%Y%m%d).txt
   ```

2. **Categorize Failures**
   - Portfolio-scoped migration issues
   - Missing field updates (commission/dividend aggregates)
   - Test-implementation mismatches
   - Missing dependencies

3. **Fix Critical Failures**
   - Priority 1: Core functionality (positions, orders, trades)
   - Priority 2: Commission/dividend tracking
   - Priority 3: API integration tests

**Success Criteria:**
- ✅ All existing tests pass
- ✅ Test execution time < 60 seconds
- ✅ Zero critical failures

---

### Phase 2: Coverage Expansion (Week 2-3)

**Goal:** Add missing test coverage for critical features

1. **Unit Test Coverage**
   - Portfolio entity tests
   - Commission/dividend aggregate tests
   - Domain service tests (PriceTrigger, GuardrailEvaluator)
   - Value object tests

2. **Integration Test Coverage**
   - Portfolio API endpoints
   - Position API endpoints (portfolio-scoped)
   - Order API endpoints (portfolio-scoped)
   - Market data API endpoints
   - Trading API endpoints

3. **E2E Test Coverage**
   - Complete trading cycle
   - Dividend workflow
   - Simulation workflow
   - Optimization workflow

**Success Criteria:**
- ✅ Unit test coverage > 80%
- ✅ Integration test coverage > 70%
- ✅ All API endpoints tested
- ✅ All critical workflows tested

---

### Phase 3: Quality & Performance (Week 4)

**Goal:** Ensure system reliability and performance

1. **Error Handling Tests**
   - Invalid input validation
   - Network failure handling
   - Database error handling
   - Market data error handling

2. **Performance Tests**
   - API response times
   - Database query performance
   - Market data fetch performance
   - Simulation execution time

3. **Security Tests**
   - Input sanitization
   - SQL injection prevention
   - Authentication/authorization (if applicable)
   - Data validation

**Success Criteria:**
- ✅ All error scenarios handled gracefully
- ✅ API response times < 500ms (p95)
- ✅ No security vulnerabilities

---

## Test Execution Commands

### Run All Tests
```bash
cd backend
python -m pytest tests/ -v
```

### Run by Category
```bash
# Unit tests only
python -m pytest tests/unit/ -v

# Integration tests only
python -m pytest tests/integration/ -v

# Regression tests only
python -m pytest tests/regression/ -v
```

### Run with Coverage
```bash
python -m pytest tests/ --cov=backend --cov-report=html --cov-report=term
```

### Run Specific Test File
```bash
python -m pytest tests/unit/domain/test_position_entity.py -v
```

### Run Tests in Parallel
```bash
python -m pytest tests/ -n auto
```

### Run with Verbose Output
```bash
python -m pytest tests/ -vv --tb=long
```

---

## Failure Tracking & Resolution

### Failure Categories

1. **CRITICAL** - System cannot operate
   - Core functionality broken
   - Data corruption risk
   - Security vulnerabilities
   - **Resolution Time:** Immediate

2. **HIGH** - Major feature broken
   - API endpoints failing
   - Business logic errors
   - Data integrity issues
   - **Resolution Time:** < 24 hours

3. **MEDIUM** - Feature partially working
   - Edge cases not handled
   - Performance issues
   - Missing validations
   - **Resolution Time:** < 1 week

4. **LOW** - Minor issues
   - UI/UX improvements
   - Documentation gaps
   - Code quality issues
   - **Resolution Time:** < 1 month

### Failure Resolution Process

1. **Identify** - Document failure with:
   - Test name and location
   - Error message and stack trace
   - Expected vs actual behavior
   - Steps to reproduce

2. **Categorize** - Assign priority and category

3. **Assign** - Assign to appropriate developer/team

4. **Fix** - Implement fix with test coverage

5. **Verify** - Re-run tests to confirm fix

6. **Document** - Update test documentation

---

## Test Coverage Requirements

### Minimum Coverage Targets

| Layer | Current | Target | Priority |
|-------|---------|--------|----------|
| Domain Entities | 70% | 95% | HIGH |
| Domain Services | 30% | 90% | HIGH |
| Use Cases | 50% | 85% | HIGH |
| API Routes | 60% | 85% | HIGH |
| Infrastructure | 30% | 75% | MEDIUM |
| Integration | 40% | 75% | MEDIUM |

### Coverage Measurement

```bash
# Generate coverage report
python -m pytest tests/ --cov=backend --cov-report=html

# View report
open htmlcov/index.html
```

---

## Continuous Testing

### Pre-Commit Checks

1. Run unit tests
2. Run linting (ruff)
3. Run type checking (mypy)
4. Check test coverage threshold

### CI/CD Integration

1. **On Push** - Run full test suite
2. **On PR** - Run tests + coverage check
3. **On Merge** - Run tests + integration tests
4. **Daily** - Run full suite + performance tests

### Test Reporting

- Daily test execution summary
- Weekly coverage report
- Monthly quality metrics
- Failure trend analysis

---

## Test Data Management

### Test Fixtures

- **Portfolio fixtures** - Standard test portfolios
- **Position fixtures** - Pre-configured positions
- **Market data mocks** - Consistent test data
- **Order fixtures** - Test order scenarios

### Test Isolation

- Each test runs in isolation
- Database transactions rolled back
- In-memory repositories for speed
- Mock external services

---

## Requirements Verification Matrix

| Requirement | Test Coverage | Status | Notes |
|-------------|---------------|--------|-------|
| Portfolio creation | ✅ Unit, ⚠️ Integration | PARTIAL | Needs API tests |
| Position management | ✅ Unit, ⚠️ Integration | PARTIAL | Needs portfolio-scoped updates |
| Order submission | ✅ Unit, ⚠️ Integration | PARTIAL | Needs commission tests |
| Trade execution | ✅ Unit, ⚠️ Integration | PARTIAL | Needs aggregate tests |
| Dividend processing | ✅ Unit, ✅ Integration | COMPLETE | Needs aggregate tests |
| Parameter optimization | ✅ Unit, ✅ Integration | COMPLETE | - |
| Simulation | ⚠️ Partial | IN PROGRESS | Needs E2E tests |
| Market data | ❌ None | MISSING | High priority |
| Excel export | ✅ Regression | COMPLETE | - |
| Trading worker | ❌ None | MISSING | High priority |

---

## Success Metrics

### Quality Metrics

- **Test Pass Rate:** > 95%
- **Code Coverage:** > 80% overall
- **Critical Coverage:** > 90% for core features
- **Test Execution Time:** < 60 seconds
- **Failure Resolution Time:** < 24 hours (critical)

### System Reliability

- **Uptime:** > 99%
- **API Error Rate:** < 0.1%
- **Data Integrity:** 100% (no data loss)
- **Performance:** P95 response time < 500ms

---

## Next Steps

1. ✅ **Create QA Test Plan** (DONE)
2. ⏳ **Execute full test suite** (IN PROGRESS)
3. ⏳ **Categorize and fix failures** (PENDING)
4. ⏳ **Expand test coverage** (PENDING)
5. ⏳ **Set up continuous testing** (PENDING)
6. ⏳ **Verify all requirements** (PENDING)

---

**Last Updated:** January 2025  
**Next Review:** Weekly  
**Status:** ACTIVE









