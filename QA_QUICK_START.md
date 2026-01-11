# QA Quick Start Guide

## For QA Leader: Running Tests

### 1. Execute Full Test Suite

```bash
cd backend
python -m pytest tests/ -v > test_results.txt 2>&1
```

Or use the automated script:

```bash
cd backend
python run_qa_tests.py
```

### 2. View Test Results

```bash
# View summary
cat test_results.txt | grep -E "(PASSED|FAILED|ERROR)" | head -20

# Count failures
grep -c "FAILED" test_results.txt

# Count passes
grep -c "PASSED" test_results.txt
```

### 3. Generate Coverage Report

```bash
cd backend
python -m pytest tests/ --cov=backend --cov-report=html --cov-report=term
open htmlcov/index.html  # On macOS/Linux
```

### 4. Fix Common Issues

#### Issue: Portfolio-Scoped Migration

**Problem:** Tests using old API signatures

**Fix Pattern:**
```python
# OLD
pos = container.positions.create(ticker="AAPL", qty=100.0, cash=10000.0)

# NEW
tenant_id = "default"
portfolio_id = "test_portfolio"
# Create portfolio first
portfolio = Portfolio(id=portfolio_id, tenant_id=tenant_id, name="Test")
container.portfolio_repo.save(portfolio)
container.portfolio_cash_repo.create(tenant_id=tenant_id, portfolio_id=portfolio_id, currency="USD", cash_balance=10000.0)
pos = container.positions.create(tenant_id=tenant_id, portfolio_id=portfolio_id, asset_symbol="AAPL", qty=100.0)
```

#### Issue: Missing Aggregate Field Tests

**Problem:** Commission/dividend aggregates not tested

**Fix:** Add tests like:
```python
def test_order_commission_snapshot(self):
    """Test commission rate snapshot in order."""
    order = Order(
        id="ord_123",
        tenant_id="default",
        portfolio_id="test_portfolio",
        position_id="pos_456",
        side="BUY",
        qty=100.0,
        commission_rate_snapshot=0.001,  # 0.1%
        commission_estimated=1.5
    )
    assert order.commission_rate_snapshot == 0.001
    assert order.commission_estimated == 1.5
```

### 5. Test Categories

```bash
# Unit tests only
python -m pytest tests/unit/ -v

# Integration tests only
python -m pytest tests/integration/ -v

# Specific test file
python -m pytest tests/unit/domain/test_position_entity.py -v

# Run with markers
python -m pytest tests/ -m "not slow" -v
```

### 6. Continuous Testing

Set up pre-commit hook:

```bash
# Install pre-commit
pip install pre-commit

# Create .pre-commit-config.yaml
cat > .pre-commit-config.yaml << EOF
repos:
  - repo: local
    hooks:
      - id: pytest
        name: pytest
        entry: pytest
        language: system
        types: [python]
        args: ["tests/", "-v", "--tb=short"]
EOF

pre-commit install
```

---

## How to Verify Gate 1

**Gate 1 Verification: Deterministic Tick + Timeline (Offline-Friendly)**

Goal: Prove the trading tick loop works end-to-end locally without network flakiness, and that each tick writes exactly one timeline/audit row.

**Prereqs**

- From repo root
- Python env active
- No server needs to be running for tests

**Step A: Run tests (offline)**

```bash
pytest -q
```

Expected:
- All default tests pass without requiring a running server.
- Any true end-to-end tests are excluded by default (e.g., marked e2e).

**Step B: Start backend in deterministic tick mode**

```bash
TICK_DETERMINISTIC=true PYTHONPATH=backend \
python -m uvicorn --app-dir backend app.main:app --reload --host 0.0.0.0 --port 8000
```

Sanity checks:

```bash
curl -s http://localhost:8000/v1/healthz | jq
curl -s http://localhost:8000/v1/market/state | jq
```

Expected:
- `/v1/healthz` returns `{"status":"ok"}`
- `/v1/market/state` returns a valid market state JSON

**Step C: Run the Gate 1 smoke script (no network required)**

In another terminal:

```bash
python backend/scripts/gate1_tick_smoke.py
```

Expected output characteristics:
- Runs ~10 ticks
- Prints one line per tick (tick#, price, action, trigger direction, order/trade info if any)
- Summary shows at least one BUY and one SELL within 10 ticks
- Fetches timeline via API and prints counts of BUY/SELL/HOLD + last 5 events

**Step D: Verify timeline endpoint directly**

The smoke script prints the position_id. You can also query manually:

```bash
curl -s "http://localhost:8000/v1/positions/<POSITION_ID>/timeline?limit=200" | jq
```

Expected:
- Timeline contains exactly one new row per tick (including HOLD).
- Timeline rows include at minimum:
  - `timestamp`
  - `action` (BUY/SELL/HOLD)
  - `trigger_direction`
  - `current_price`
  - guardrail limits
  - allocation after
  - any order/trade ids if present

---

## Test Execution Checklist

- [ ] Run full test suite
- [ ] Review failures
- [ ] Categorize failures (Critical/High/Medium/Low)
- [ ] Fix critical failures first
- [ ] Update test documentation
- [ ] Generate coverage report
- [ ] Update QA_TEST_STATUS.md
- [ ] Create tickets for remaining issues

---

## Quick Reference

| Command | Purpose |
|---------|---------|
| `pytest tests/ -v` | Run all tests with verbose output |
| `pytest tests/ --cov=backend` | Run with coverage |
| `pytest tests/ -k "test_position"` | Run tests matching pattern |
| `pytest tests/ -x` | Stop on first failure |
| `pytest tests/ --tb=short` | Short traceback format |
| `pytest tests/ -n auto` | Run in parallel |

---

## Getting Help

- See `QA_TEST_PLAN.md` for comprehensive test strategy
- See `QA_TEST_STATUS.md` for current status
- See `TEST_DEVELOPMENT_STATUS.md` for detailed test status
- See `TEST_FIXES_NEEDED.md` for known issues








