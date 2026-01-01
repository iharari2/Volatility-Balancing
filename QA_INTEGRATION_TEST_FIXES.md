# Integration Test Fixes - Initial Analysis

**Date:** January 2025  
**Status:** 🔄 IN PROGRESS

---

## Test Results

**Total:** 101 tests  
**Passed:** 44  
**Failed:** 30  
**Errors:** 27  
**Deselected:** 2

---

## Issues Categorized

### 1. ✅ Fixed: trigger_config_provider Missing Arguments (3 failures)

**Issue:** `TypeError: trigger_config_provider() missing 2 required positional arguments`

**Fixed:**

- Updated `evaluate_position_uc.py` line 347 to pass `tenant_id, portfolio_id, position.id`

**Files Fixed:**

- `backend/application/use_cases/evaluate_position_uc.py`

---

### 2. ✅ Fixed: ExecuteOrderUC Missing portfolio_cash_repo (2 failures)

**Issue:** `TypeError: ExecuteOrderUC.__init__() missing 1 required positional argument: 'portfolio_cash_repo'`

**Fixed:**

- Added `portfolio_cash_repo=container.portfolio_cash_repo` to both ExecuteOrderUC instantiations

**Files Fixed:**

- `backend/tests/integration/test_golden_scenarios.py` (2 locations)

---

### 3. ✅ Fixed: NameError: \_find_position_legacy (2 failures)

**Issue:** `NameError: name '_find_position_legacy' is not defined`

**Fixed:**

- Created `_find_position_legacy()` helper function in `positions.py` that searches across all portfolios

**Files Fixed:**

- `backend/app/routes/positions.py`

---

### 4. ✅ Fixed: VolatilityData Unexpected Keyword (2 failures)

**Issue:** `TypeError: VolatilityData.__init__() got an unexpected keyword argument 'volatility'`

**Fixed:**

- Updated to use correct parameters: `volatility_1min`, `volatility_5min`, `volatility_1hour`, `price_std_dev`

**Files Fixed:**

- `backend/infrastructure/market/market_data_storage.py`

---

### 5. ⏳ Pending: 405 Method Not Allowed Errors (Many tests)

**Issue:** Tests getting `405 Method Not Allowed` when trying to POST to `/v1/positions`

**Root Cause:** The `/v1/positions` endpoint has been deprecated (returns 410 Gone). New API requires:

- `POST /api/tenants/{tenant_id}/portfolios/{portfolio_id}` to create portfolio with positions

**Affected Tests:**

- `test_positions_api.py` - Multiple tests trying to POST to `/v1/positions`
- `test_orders_api.py` - Tests failing in setup (position_id fixture)
- `test_dividend_api.py` - Tests failing in setup (position_id fixture)

**Solution:** Update tests to use new portfolio-scoped API

---

### 6. ⏳ Pending: 410 Gone / 404 Errors

**Issue:** Some endpoints return 410 Gone or 404 Not Found

**Examples:**

- `GET /v1/positions/{position_id}` → 410 Gone
- `GET /v1/positions/{position_id}/orders` → 404 Not Found

**Solution:** Update tests to use new portfolio-scoped endpoints

---

### 7. ⏳ Pending: Endpoint Path Changes

**Issue:** Tests expect `/v1/positions/{position_id}/orders` but API schema shows different paths

**Solution:** Update test expectations to match new API structure

---

## Summary

**Fixed:** 9 issues (trigger_config_provider, ExecuteOrderUC, \_find_position_legacy, VolatilityData)  
**Remaining:** ~48 issues (mostly API endpoint migration)

**Next Steps:**

1. Update integration tests to use new portfolio-scoped API endpoints
2. Fix remaining endpoint path mismatches
3. Update test fixtures to create portfolios properly

---

**Status:** 🔄 **IN PROGRESS**  
**Last Updated:** January 2025








