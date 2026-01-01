# QA Test Cleanup Guide

**Purpose:** Systematic approach to clean, fix, and organize all tests in the Volatility Balancing system.

---

## Overview

This guide provides step-by-step instructions to:

1. **Identify** all test issues
2. **Categorize** failures by priority
3. **Fix** tests systematically
4. **Clean up** test code
5. **Verify** all tests pass
6. **Maintain** test quality

---

## Step 1: Assessment - Identify Current State

### 1.1 Run Full Test Suite

```bash
cd backend
python -m pytest tests/ -v --tb=short > test_audit_$(date +%Y%m%d).txt 2>&1
```

### 1.2 Analyze Test Results

```bash
# Count total tests
grep -c "test_" test_audit_*.txt

# Count passing tests
grep -c "PASSED" test_audit_*.txt

# Count failing tests
grep -c "FAILED" test_audit_*.txt

# Count errors
grep -c "ERROR" test_audit_*.txt

# List all failing tests
grep "FAILED" test_audit_*.txt | awk '{print $1}'
```

### 1.3 Generate Test Coverage Report

```bash
python -m pytest tests/ --cov=backend --cov-report=html --cov-report=term
```

**Review:**

- Which components have low coverage?
- Which tests are failing?
- What are the common failure patterns?

---

## Step 2: Categorize Issues

### 2.1 Create Issue Categories

Create a spreadsheet or document tracking:

| Category                | Description                        | Examples                          | Priority |
| ----------------------- | ---------------------------------- | --------------------------------- | -------- |
| **Portfolio Migration** | Tests using old API (ticker, cash) | Missing tenant_id/portfolio_id    | CRITICAL |
| **Missing Fields**      | Tests not checking new fields      | Commission/dividend aggregates    | HIGH     |
| **Broken Tests**        | Tests with syntax/logic errors     | Import errors, assertion failures | HIGH     |
| **Outdated Tests**      | Tests for removed features         | Old API endpoints                 | MEDIUM   |
| **Duplicate Tests**     | Tests testing same thing           | Redundant test cases              | LOW      |
| **Missing Tests**       | No tests for features              | Market data, trading worker       | HIGH     |

### 2.2 Prioritize Fixes

**Priority 1 (Critical - Fix First):**

- Tests that prevent other tests from running
- Tests for core functionality (positions, orders, trades)
- Portfolio-scoped migration issues

**Priority 2 (High - Fix Next):**

- Missing field tests (commission, dividends)
- Broken integration tests
- API endpoint tests

**Priority 3 (Medium - Fix Later):**

- Outdated tests
- Duplicate tests
- Low-priority feature tests

---

## Step 3: Fix Portfolio-Scoped Migration Issues

### 3.1 Pattern Recognition

**Old Pattern:**

```python
# OLD - Position creation
pos = container.positions.create(
    ticker="AAPL",
    qty=100.0,
    cash=10000.0
)

# OLD - Order creation
order = Order(
    id="ord_123",
    position_id="pos_456",
    side="BUY",
    qty=100.0
)

# OLD - Cash check
assert pos.cash == 1000.0
```

**New Pattern:**

```python
# NEW - Setup portfolio first
tenant_id = "default"
portfolio_id = "test_portfolio"
portfolio = Portfolio(
    id=portfolio_id,
    tenant_id=tenant_id,
    name="Test Portfolio"
)
container.portfolio_repo.save(portfolio)
container.portfolio_cash_repo.create(
    tenant_id=tenant_id,
    portfolio_id=portfolio_id,
    currency="USD",
    cash_balance=10000.0
)

# NEW - Position creation
pos = container.positions.create(
    tenant_id=tenant_id,
    portfolio_id=portfolio_id,
    asset_symbol="AAPL",  # Changed from ticker
    qty=100.0
    # cash removed - now in portfolio_cash
)

# NEW - Order creation
order = Order(
    id="ord_123",
    tenant_id=tenant_id,  # Added
    portfolio_id=portfolio_id,  # Added
    position_id="pos_456",
    side="BUY",
    qty=100.0
)

# NEW - Cash check
portfolio_cash = container.portfolio_cash_repo.get(
    tenant_id=tenant_id,
    portfolio_id=portfolio_id
)
assert portfolio_cash.cash_balance == 1000.0
```

### 3.2 Automated Fix Script

Create a helper function in `backend/tests/helpers/test_entities.py`:

```python
def create_test_portfolio(container, tenant_id="default", portfolio_id="test_portfolio", cash=10000.0):
    """Helper to create test portfolio with cash."""
    from domain.entities.portfolio import Portfolio

    portfolio = Portfolio(
        id=portfolio_id,
        tenant_id=tenant_id,
        name="Test Portfolio"
    )
    container.portfolio_repo.save(portfolio)
    container.portfolio_cash_repo.create(
        tenant_id=tenant_id,
        portfolio_id=portfolio_id,
        currency="USD",
        cash_balance=cash
    )
    return portfolio
```

### 3.3 Fix Files Systematically

**Files to Fix (in order):**

1. `backend/tests/unit/domain/test_position_entity.py` ✅ (Already fixed)
2. `backend/tests/unit/domain/test_order_entity.py` ✅ (Already fixed)
3. `backend/tests/unit/domain/test_trade_entity.py`
4. `backend/tests/unit/application/test_submit_order_uc.py`
5. `backend/tests/unit/application/test_execute_order_uc.py`
6. `backend/tests/unit/application/test_process_dividend_uc.py`
7. `backend/tests/integration/test_orders_api.py`
8. `backend/tests/integration/test_positions_api.py`
9. `backend/tests/integration/test_golden_scenarios.py`

---

## Step 4: Add Missing Field Tests

### 4.1 Commission Field Tests

**For Order Entity:**

```python
def test_order_commission_rate_snapshot(self):
    """Test commission rate snapshot is captured."""
    order = Order(
        id="ord_123",
        tenant_id="default",
        portfolio_id="test_portfolio",
        position_id="pos_456",
        side="BUY",
        qty=100.0,
        commission_rate_snapshot=0.001  # 0.1%
    )
    assert order.commission_rate_snapshot == 0.001
```

**For Trade Entity:**

```python
def test_trade_commission_rate_effective(self):
    """Test commission rate effective in trade."""
    trade = Trade(
        id="trd_123",
        tenant_id="default",
        portfolio_id="test_portfolio",
        order_id="ord_456",
        position_id="pos_789",
        side="BUY",
        qty=100.0,
        price=150.0,
        commission=1.5,
        commission_rate_effective=0.001
    )
    assert trade.commission_rate_effective == 0.001
```

**For Position Entity:**

```python
def test_position_total_commission_paid_increment(self):
    """Test total_commission_paid increments correctly."""
    position = Position(...)
    assert position.total_commission_paid == 0.0

    position.total_commission_paid += 1.5
    assert position.total_commission_paid == 1.5

    position.total_commission_paid += 2.3
    assert position.total_commission_paid == 3.8
```

### 4.2 Dividend Aggregate Tests

```python
def test_position_total_dividends_received_increment(self):
    """Test total_dividends_received increments correctly."""
    position = Position(...)
    assert position.total_dividends_received == 0.0

    position.total_dividends_received += 61.50
    assert position.total_dividends_received == 61.50
```

### 4.3 Use Case Tests

**For ExecuteOrderUC:**

```python
def test_execute_order_updates_commission_aggregate(self):
    """Test that executing order updates total_commission_paid."""
    # Setup position
    position = create_test_position(...)
    assert position.total_commission_paid == 0.0

    # Execute order with commission
    execute_order_uc.execute(...)

    # Verify aggregate updated
    updated_position = position_repo.get(...)
    assert updated_position.total_commission_paid > 0.0
```

---

## Step 5: Fix Broken Tests

### 5.1 Common Issues and Fixes

**Issue: Import Errors**

```python
# Fix: Update imports
from domain.entities.position import Position  # Correct
# Not: from entities.position import Position
```

**Issue: Missing Required Parameters**

```python
# Fix: Add all required parameters
Order(
    id="ord_123",
    tenant_id="default",  # Required
    portfolio_id="test_portfolio",  # Required
    position_id="pos_456",
    side="BUY",
    qty=100.0
)
```

**Issue: Assertion Failures**

```python
# Fix: Use proper assertions
assert actual == expected, f"Expected {expected}, got {actual}"

# For floats, use approximate comparison
from pytest import approx
assert result == approx(100.0, rel=1e-3)
```

**Issue: Timestamp Comparisons**

```python
# Fix: Use fixed timestamps or ignore in comparison
fixed_time = datetime.now(timezone.utc)
order1.created_at = fixed_time
order2.created_at = fixed_time
assert order1 == order2
```

### 5.2 Test Each File Individually

```bash
# Test one file at a time
python -m pytest tests/unit/domain/test_order_entity.py -v

# Fix issues, then move to next file
python -m pytest tests/unit/domain/test_trade_entity.py -v
```

---

## Step 6: Remove Outdated Tests

### 6.1 Identify Outdated Tests

**Signs of outdated tests:**

- Tests for removed features
- Tests using deprecated APIs
- Tests that no longer make sense
- Commented-out tests

**Example:**

```python
# OLD - Remove this
def test_position_cash_field(self):
    """Test position cash field."""
    # This test is outdated - cash moved to portfolio_cash
    pass
```

### 6.2 Remove or Update

**Option 1: Remove if feature is gone**

```python
# Delete the entire test function
```

**Option 2: Update if feature changed**

```python
# Update to test new implementation
def test_portfolio_cash_balance(self):
    """Test portfolio cash balance."""
    portfolio_cash = container.portfolio_cash_repo.get(...)
    assert portfolio_cash.cash_balance == 10000.0
```

---

## Step 7: Remove Duplicate Tests

### 7.1 Identify Duplicates

```bash
# Search for similar test names
grep -r "def test_" tests/ | sort | uniq -d
```

### 7.2 Consolidate

**Before (Duplicate):**

```python
def test_order_creation(self):
    order = Order(...)
    assert order.id == "ord_123"

def test_order_creation_basic(self):
    order = Order(...)
    assert order.id == "ord_123"
```

**After (Consolidated):**

```python
def test_order_creation(self):
    """Test basic order creation with all required fields."""
    order = Order(...)
    assert order.id == "ord_123"
    assert order.tenant_id == "default"
    assert order.portfolio_id == "test_portfolio"
```

---

## Step 8: Add Missing Tests

### 8.1 Identify Gaps

Use coverage report to find untested code:

```bash
python -m pytest tests/ --cov=backend --cov-report=html
open htmlcov/index.html
```

### 8.2 Priority Areas

1. **Market Data Integration** (0% coverage)

   - YFinance adapter
   - Market data fetching
   - Error handling

2. **Trading Worker** (0% coverage)

   - Worker startup/shutdown
   - Position evaluation loop
   - Error recovery

3. **Domain Services** (30% coverage)

   - PriceTrigger.evaluate()
   - GuardrailEvaluator.evaluate()

4. **Value Objects** (0% coverage)
   - MarketQuote validation
   - TriggerConfig validation
   - GuardrailConfig validation

---

## Step 9: Organize Test Structure

### 9.1 Current Structure

```
backend/tests/
├── conftest.py
├── fixtures/
├── helpers/
├── unit/
│   ├── domain/
│   ├── application/
│   └── infrastructure/
├── integration/
└── regression/
```

### 9.2 Best Practices

1. **One test file per module**

   - `test_position_entity.py` for `position.py`
   - `test_order_entity.py` for `order.py`

2. **Group related tests in classes**

   ```python
   class TestPositionCreation:
       def test_basic_creation(self): ...
       def test_with_anchor_price(self): ...

   class TestPositionUpdates:
       def test_update_anchor_price(self): ...
       def test_update_quantity(self): ...
   ```

3. **Use descriptive test names**

   ```python
   # Good
   def test_order_creation_with_commission_snapshot(self): ...

   # Bad
   def test_order1(self): ...
   ```

4. **Keep tests focused**
   - One assertion per test (when possible)
   - Test one behavior at a time

---

## Step 10: Verify All Tests Pass

### 10.1 Run Full Suite

```bash
cd backend
python -m pytest tests/ -v
```

### 10.2 Check Coverage

```bash
python -m pytest tests/ --cov=backend --cov-report=term
```

**Target:**

- All tests passing
- Coverage > 80%
- No warnings

### 10.3 Generate Final Report

```bash
python run_qa_tests.py
```

---

## Step 11: Maintain Test Quality

### 11.1 Pre-Commit Checks

Create `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: local
    hooks:
      - id: pytest
        name: pytest
        entry: pytest
        language: system
        types: [python]
        args: ['tests/', '-v', '--tb=short']
        pass_filenames: false
```

### 11.2 CI/CD Integration

Add to GitHub Actions or CI pipeline:

```yaml
- name: Run tests
  run: |
    cd backend
    python -m pytest tests/ -v --cov=backend --cov-report=xml

- name: Check coverage
  run: |
    coverage report --fail-under=80
```

### 11.3 Regular Reviews

- **Weekly:** Review failing tests
- **Monthly:** Review coverage reports
- **Quarterly:** Audit test quality

---

## Quick Reference: Cleanup Checklist

### Phase 1: Assessment

- [ ] Run full test suite
- [ ] Generate coverage report
- [ ] Categorize all failures
- [ ] Create issue tracking document

### Phase 2: Critical Fixes

- [ ] Fix portfolio-scoped migration issues
- [ ] Fix broken imports
- [ ] Fix missing required parameters
- [ ] Fix assertion failures

### Phase 3: Coverage

- [ ] Add commission field tests
- [ ] Add dividend aggregate tests
- [ ] Add missing use case tests
- [ ] Add API endpoint tests

### Phase 4: Cleanup

- [ ] Remove outdated tests
- [ ] Remove duplicate tests
- [ ] Organize test structure
- [ ] Update test documentation

### Phase 5: Verification

- [ ] All tests passing
- [ ] Coverage > 80%
- [ ] No warnings
- [ ] CI/CD integrated

---

## Common Commands

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific category
python -m pytest tests/unit/ -v
python -m pytest tests/integration/ -v

# Run specific file
python -m pytest tests/unit/domain/test_position_entity.py -v

# Run with coverage
python -m pytest tests/ --cov=backend --cov-report=html

# Run and stop on first failure
python -m pytest tests/ -x

# Run in parallel (faster)
python -m pytest tests/ -n auto

# Show only failures
python -m pytest tests/ -v --tb=short | grep -A 5 FAILED
```

---

## Getting Help

- See `QA_TEST_PLAN.md` for test strategy
- See `QA_TEST_STATUS.md` for current status
- See `TEST_FIXES_NEEDED.md` for known issues
- See `QA_QUICK_START.md` for quick commands

---

**Last Updated:** January 2025  
**Status:** ACTIVE








