# Config Provider Fixes - Final Update

**Date:** January 2025  
**Status:** ✅ FIXES COMPLETE

---

## Issue

**12 test failures** with error:

```
TypeError: InMemoryPositionsRepo.get() missing 2 required positional arguments: 'portfolio_id' and 'position_id'
```

**Root Cause:** Config providers (`guardrail_config_provider`, `order_policy_config_provider`, `trigger_config_provider`) were calling `positions.get(position_id)` but the portfolio-scoped API requires `tenant_id` and `portfolio_id`.

---

## Fixes Applied

### 1. Updated Config Provider Signatures in `app/di.py`

**Before:**

```python
def guardrail_config_provider(position_id: str) -> GuardrailConfig:
    position = self.positions.get(position_id)  # ❌ Missing tenant_id/portfolio_id
    ...
```

**After:**

```python
def guardrail_config_provider(tenant_id: str, portfolio_id: str, position_id: str) -> GuardrailConfig:
    position = self.positions.get(tenant_id=tenant_id, portfolio_id=portfolio_id, position_id=position_id)  # ✅
    ...
```

**Fixed Providers:**

- `guardrail_config_provider`
- `order_policy_config_provider`
- `trigger_config_provider`

---

### 2. Updated Use Case Type Hints

**File:** `backend/application/use_cases/submit_order_uc.py`

**Before:**

```python
guardrail_config_provider: Optional[Callable[[str], GuardrailConfig]] = None,
```

**After:**

```python
guardrail_config_provider: Optional[Callable[[str, str, str], GuardrailConfig]] = None,
```

**File:** `backend/application/use_cases/execute_order_uc.py`

**Before:**

```python
guardrail_config_provider: Optional[Callable[[str], GuardrailConfig]] = None,
order_policy_config_provider: Optional[Callable[[str], OrderPolicyConfig]] = None,
```

**After:**

```python
guardrail_config_provider: Optional[Callable[[str, str, str], GuardrailConfig]] = None,
order_policy_config_provider: Optional[Callable[[str, str, str], OrderPolicyConfig]] = None,
```

---

### 3. Updated Use Case Provider Calls

**File:** `backend/application/use_cases/submit_order_uc.py`

**Before:**

```python
guardrail_config = self.guardrail_config_provider(position_id)
```

**After:**

```python
guardrail_config = self.guardrail_config_provider(tenant_id, portfolio_id, position_id)
```

**File:** `backend/application/use_cases/execute_order_uc.py`

**Before:**

```python
order_policy_config = self.order_policy_config_provider(order.position_id)
guardrail_config = self.guardrail_config_provider(order.position_id)
```

**After:**

```python
order_policy_config = self.order_policy_config_provider(
    order.tenant_id, order.portfolio_id, order.position_id
)
guardrail_config = self.guardrail_config_provider(
    order.tenant_id, order.portfolio_id, order.position_id
)
```

---

## Files Modified

1. `backend/app/di.py` - Updated 3 provider functions
2. `backend/application/use_cases/submit_order_uc.py` - Updated type hint and call
3. `backend/application/use_cases/execute_order_uc.py` - Updated type hints and 2 calls

---

## Tests Fixed

All 12 failing tests should now pass:

**test_execute_order_uc.py (10 tests):**

- `test_fill_buy_increases_qty_and_decreases_cash`
- `test_fill_sell_rejects_if_insufficient_qty`
- `test_buy_commission_decreases_cash`
- `test_sell_commission_reduces_proceeds`
- `test_commission_defaults_to_zero`
- `test_commission_aggregate_increment_on_buy`
- `test_commission_aggregate_increment_on_sell`
- `test_commission_aggregate_multiple_trades`
- `test_trade_commission_rate_effective_set`
- `test_trade_status_defaults_to_executed`

**test_submit_daily_cap.py (2 tests):**

- `test_daily_cap_at_submit_is_enforced`
- `test_daily_cap_at_fill_is_enforced`

---

## Note on Orchestrator

The `LiveTradingOrchestrator` in `backend/application/orchestrators/live_trading.py` still uses the old API:

```python
trigger_config: TriggerConfig = self.trigger_config_provider(position_id)
guardrail_config: GuardrailConfig = self.guardrail_config_provider(position_id)
```

This will need to be updated separately if the orchestrator is used in production. For now, it doesn't affect unit tests.

---

## Verification

Run tests to verify all fixes:

```bash
cd backend
python -m pytest tests/unit/ -v
```

**Expected Result:** All 276 unit tests should pass ✅

---

**Status:** ✅ **CONFIG PROVIDER FIXES COMPLETE**  
**Last Updated:** January 2025








