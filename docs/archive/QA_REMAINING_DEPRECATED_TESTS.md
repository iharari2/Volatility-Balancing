# Remaining Deprecated Tests Analysis

**Date:** January 2025

---

## Summary

**Total Remaining:** ~7-8 tests + 1 fixture

---

## Tests Still Using Deprecated Endpoints

### 1. `test_orders_api.py` (4 items)

#### `order_id` fixture (Line 10)

- **Uses:** `POST /v1/positions/{position_id}/orders`
- **Needs:** Update to use portfolio-scoped endpoint
- **Impact:** Affects all tests using `order_id` fixture

#### `test_submit_order_success` (Line 18)

- **Uses:** `POST /v1/positions/{position_id}/orders`
- **Needs:** Add `tenant_id`, `portfolio_id` fixtures and use new endpoint

#### `test_submit_order_with_idempotency_key` (Line 30)

- **Uses:** `POST /v1/positions/{position_id}/orders`
- **Needs:** Add `tenant_id`, `portfolio_id` fixtures and use new endpoint

#### `test_submit_order_invalid_side` (Line 45)

- **Uses:** `POST /v1/positions/{position_id}/orders`
- **Needs:** Add `tenant_id`, `portfolio_id` fixtures and use new endpoint

---

### 2. `test_dividend_api.py` (2 tests)

#### `test_dividend_workflow_integration` (Line 118)

- **Uses:**
  - `POST /v1/positions/{position_id}/anchor`
  - `GET /v1/positions/{position_id}`
- **Needs:** Add `tenant_id`, `portfolio_id` fixtures and verify via new API

#### `test_dividend_status_with_receivables` (Line 155)

- **Uses:** Direct container access (may need portfolio context)
- **Needs:** Check if it needs portfolio fixtures

---

### 3. `test_positions_api.py` (1-2 tests)

#### `test_clear_all_positions` (Line 267)

- **Uses:**
  - `GET /v1/positions/{position_id}`
  - `POST /v1/clear-positions`
- **Needs:** Add `tenant_id`, `portfolio_id` fixtures

#### `test_create_position_invalid_order_policy` (Line 60)

- **Uses:** `POST /v1/positions`
- **Status:** ⚠️ **INTENTIONAL** - This test is specifically testing the deprecated endpoint's validation behavior
- **Action:** May want to keep as-is or update to test new endpoint validation

---

## Tests Using Legacy Endpoints (Already Updated with Portfolio Fixtures)

These tests use legacy endpoints but already have portfolio fixtures and verify via new API:

- ✅ `test_set_anchor_price_success`
- ✅ `test_evaluate_position_success`
- ✅ `test_evaluate_position_with_market_data`
- ✅ `test_list_events`
- ✅ `test_list_events_with_limit`
- ✅ `test_auto_size_order_success`
- ✅ `test_auto_size_order_with_market_data`
- ✅ `test_auto_sized_order_success`
- ✅ `test_auto_sized_order_with_idempotency`
- ✅ `test_auto_sized_order_with_market_data`

---

## Tests Intentionally Testing Deprecated Endpoints

These tests in `test_main_app.py` are intentionally testing deprecated endpoint behavior:

- `test_router_integration` - Tests 410 Gone responses
- `test_request_validation` - Tests deprecated endpoint validation
- `test_response_format_consistency` - Tests deprecated endpoint responses
- `test_error_response_format` - Tests deprecated endpoint error handling
- `test_content_type_handling` - Tests deprecated endpoint content types
- `test_http_methods_support` - Tests deprecated endpoint methods

**Status:** ✅ **KEEP AS-IS** - These are testing deprecated endpoint behavior intentionally

---

## Priority Order for Updates

1. **High Priority:**

   - `order_id` fixture (affects multiple tests)
   - `test_submit_order_success`
   - `test_submit_order_with_idempotency_key`
   - `test_submit_order_invalid_side`

2. **Medium Priority:**

   - `test_dividend_workflow_integration`
   - `test_clear_all_positions`

3. **Low Priority:**
   - `test_dividend_status_with_receivables` (needs investigation)
   - `test_create_position_invalid_order_policy` (may be intentional)

---

**Total Tests Updated So Far:** 22  
**Remaining to Update:** ~7-8 tests + 1 fixture








