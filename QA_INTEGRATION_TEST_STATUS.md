# Integration Test Fixes - Status Update

**Date:** January 2025  
**Status:** 🔄 IN PROGRESS

---

## Test Results

**Total:** 101 tests  
**Passed:** 49 (up from 44) ✅  
**Failed:** 25 (down from 30)  
**Errors:** 27 (same)  
**Deselected:** 2

**Progress:** +5 tests passing

---

## ✅ Fixed Issues

### 1. trigger_config_provider Missing Arguments (3 failures → 0)

- ✅ Fixed `_check_triggers` method
- ✅ Fixed `_calculate_order_proposal` method
- ✅ Fixed conditional expression in `evaluate` method

### 2. guardrail_config_provider Missing Arguments (1 failure → 0)

- ✅ Fixed `_check_auto_rebalancing` method

### 3. ExecuteOrderUC Missing portfolio_cash_repo (2 failures → 0)

- ✅ Fixed both instantiations in `test_golden_scenarios.py`

### 4. VolatilityData Unexpected Keyword (2 failures → 0)

- ✅ Fixed `_calculate_volatility_data` method

### 5. \_find_position_legacy Not Defined (2 failures → 0)

- ✅ Created helper function in `positions.py`

---

## ⏳ Remaining Issues

### 1. 405 Method Not Allowed (27 errors)

**Root Cause:** Tests using deprecated `/v1/positions` endpoint

**Solution:** Update test fixtures to use new portfolio API:

```python
# OLD
response = client.post("/v1/positions", json={"ticker": "AAPL", ...})

# NEW
response = client.post(
    "/api/tenants/default/portfolios",
    json={
        "name": "Test Portfolio",
        "starting_cash": {"currency": "USD", "amount": 10000.0},
        "holdings": [{"asset": "AAPL", "qty": 100.0, "anchor_price": 150.0}]
    }
)
portfolio_id = response.json()["portfolio_id"]
# Then get position_id from portfolio
```

**Affected Files:**

- `test_positions_api.py` - position_id fixture
- `test_orders_api.py` - position_id fixture
- `test_dividend_api.py` - position_id fixture

---

### 2. 410 Gone Errors (3 failures)

**Issue:** Tests expect 404 but get 410 (deprecated endpoint)

**Solution:** Update test expectations or use new endpoints

**Affected Tests:**

- `test_get_position_not_found`
- `test_set_anchor_price_not_found`
- `test_evaluate_position_not_found`

---

### 3. Endpoint Path Mismatches (1 failure)

**Issue:** Test expects `/v1/positions/{position_id}/orders` but API uses different path

**Solution:** Update test to use correct endpoint:

- New: `/api/tenants/{tenant_id}/portfolios/{portfolio_id}/positions/{position_id}/orders`

---

### 4. Error Message Mismatches (1 failure)

**Issue:** Test expects `"position_not_found"` but gets `"Not Found"`

**Solution:** Update assertion to match actual error message

---

## Summary

**Code Fixes:** ✅ 9 issues fixed  
**Test Updates Needed:** ~32 issues (API endpoint migration)

**Next Steps:**

1. Create helper function for test portfolio creation
2. Update all test fixtures to use new portfolio API
3. Fix remaining endpoint path mismatches
4. Update error message expectations

---

**Status:** 🔄 **IN PROGRESS**  
**Last Updated:** January 2025








