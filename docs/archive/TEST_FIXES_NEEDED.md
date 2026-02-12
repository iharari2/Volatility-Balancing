# Test Fixes Needed for Portfolio-Scoped Migration

## Summary

Many test files need updates to match the new portfolio-scoped architecture. The main changes are:

1. **Position creation**: `ticker=` → `asset_symbol=`, add `tenant_id` and `portfolio_id`, remove `cash=`
2. **Order creation**: Add `tenant_id` and `portfolio_id`
3. **Trade creation**: Add `tenant_id` and `portfolio_id`
4. **Repository calls**: All `get()` and `list_all()` calls need `tenant_id` and `portfolio_id`
5. **Use case calls**: `SubmitOrderUC.execute()` and `ProcessDividendUC` methods need `tenant_id` and `portfolio_id`
6. **Cash assertions**: Check `portfolio_cash.cash_balance` instead of `position.cash`

## Files That Need Updates

### High Priority (Core Functionality)

1. `backend/tests/unit/application/test_execute_order_uc.py` - 11 tests
2. `backend/tests/unit/application/test_submit_order_uc.py` - 8 tests
3. `backend/tests/unit/application/test_process_dividend_uc.py` - 15 tests
4. `backend/tests/unit/application/test_order_policy_uc.py` - 2 tests
5. `backend/tests/unit/application/test_submit_daily_cap.py` - 2 tests

### Domain Entity Tests

6. `backend/tests/unit/domain/test_position_entity.py` - 28 tests
7. `backend/tests/unit/domain/test_order_entity.py` - 30 tests
8. `backend/tests/unit/domain/test_trade_entity.py` - 25 tests

### Integration Tests

9. `backend/tests/integration/test_golden_scenarios.py` - 4 tests
10. `backend/tests/integration/test_orders_api.py` - 20 tests
11. `backend/tests/integration/test_positions_api.py` - 18 tests
12. `backend/tests/integration/test_dividend_api.py` - 7 tests
13. `backend/tests/integration/test_orders_list.py` - 1 test
14. `backend/tests/regression/test_export_regression.py` - 5 tests

## Common Patterns to Fix

### Pattern 1: Position Creation

**Old:**

```python
pos = container.positions.create(ticker="AAPL", qty=100.0, cash=10000.0)
```

**New:**

```python
tenant_id = "default"
portfolio_id = "test_portfolio"
# Create portfolio and cash first
portfolio = Portfolio(id=portfolio_id, tenant_id=tenant_id, name="Test")
container.portfolio_repo.save(portfolio)
container.portfolio_cash_repo.create(tenant_id=tenant_id, portfolio_id=portfolio_id, currency="USD", cash_balance=10000.0)
pos = container.positions.create(tenant_id=tenant_id, portfolio_id=portfolio_id, asset_symbol="AAPL", qty=100.0)
```

### Pattern 2: Position Get

**Old:**

```python
pos = container.positions.get(position_id)
```

**New:**

```python
pos = container.positions.get(tenant_id="default", portfolio_id="test_portfolio", position_id=position_id)
```

### Pattern 3: Order Creation

**Old:**

```python
order = Order(id="ord_123", position_id="pos_456", side="BUY", qty=100.0)
```

**New:**

```python
order = Order(id="ord_123", tenant_id="default", portfolio_id="test_portfolio", position_id="pos_456", side="BUY", qty=100.0)
```

### Pattern 4: Trade Creation

**Old:**

```python
trade = Trade(id="trd_123", order_id="ord_456", position_id="pos_789", side="BUY", qty=100.0, price=150.0, commission=1.5)
```

**New:**

```python
trade = Trade(id="trd_123", tenant_id="default", portfolio_id="test_portfolio", order_id="ord_456", position_id="pos_789", side="BUY", qty=100.0, price=150.0, commission=1.5)
```

### Pattern 5: SubmitOrderUC.execute()

**Old:**

```python
submit_order_uc.execute(position_id, request, idempotency_key)
```

**New:**

```python
submit_order_uc.execute(tenant_id="default", portfolio_id="test_portfolio", position_id=position_id, request=request, idempotency_key=idempotency_key)
```

### Pattern 6: ProcessDividendUC calls

**Old:**

```python
dividend_uc.process_ex_dividend_date(position_id)
dividend_uc.process_dividend_payment(position_id, receivable_id)
dividend_uc.get_dividend_status(position_id)
```

**New:**

```python
dividend_uc.process_ex_dividend_date(tenant_id="default", portfolio_id="test_portfolio", position_id=position_id)
dividend_uc.process_dividend_payment(tenant_id="default", portfolio_id="test_portfolio", position_id=position_id, receivable_id=receivable_id)
dividend_uc.get_dividend_status(tenant_id="default", portfolio_id="test_portfolio", position_id=position_id)
```

### Pattern 7: Cash Assertions

**Old:**

```python
assert pos.cash == 1000.0
```

**New:**

```python
portfolio_cash = container.portfolio_cash_repo.get(tenant_id="default", portfolio_id="test_portfolio")
assert portfolio_cash.cash_balance == 1000.0
```

### Pattern 8: ExecuteOrderUC instantiation

**Old:**

```python
uc = ExecuteOrderUC(container.positions, container.orders, container.trades, container.events, container.clock, ...)
```

**New:**

```python
uc = ExecuteOrderUC(container.positions, container.orders, container.trades, container.events, container.portfolio_cash_repo, container.clock, ...)
```

## Helper Functions

A helper file `backend/tests/helpers/test_entities.py` has been created with:

- `create_test_position()` - Creates Position with correct signature
- `create_test_order()` - Creates Order with correct signature
- `create_test_trade()` - Creates Trade with correct signature

Use these helpers in tests to reduce boilerplate.

## Estimated Effort

- **133 test failures** need fixes
- Most are simple find/replace patterns
- Some require test setup (portfolio + cash creation)
- Estimated time: 2-3 hours for systematic fixes

## Next Steps

1. Fix `test_execute_order_uc.py` completely
2. Fix `test_submit_order_uc.py` completely
3. Fix domain entity tests
4. Fix integration tests
5. Run tests to verify













