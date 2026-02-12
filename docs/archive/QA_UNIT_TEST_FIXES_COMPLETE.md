# Unit Test Fixes - Complete Summary

**Date:** January 2025  
**Status:** IN PROGRESS

---

## Files Fixed

### ✅ test_submit_daily_cap.py

- Fixed `test_daily_cap_at_fill_is_enforced()`
- Added portfolio setup
- Changed `ticker=` to `asset_symbol=`
- Removed `cash=` parameter

### ✅ test_process_dividend_uc.py

- Fixed `sample_position` fixture (ticker → asset_symbol, removed cash)
- Fixed `test_process_ex_dividend_date_success()` - added tenant_id/portfolio_id
- Fixed `test_process_ex_dividend_date_no_position()` - added tenant_id/portfolio_id
- Fixed `test_process_ex_dividend_date_no_dividend_today()` - added tenant_id/portfolio_id
- Fixed `test_process_dividend_payment_success()` - added portfolio_cash mock, tenant_id/portfolio_id
- Fixed `test_process_dividend_payment_receivable_not_found()` - added tenant_id/portfolio_id
- Fixed `test_process_dividend_payment_wrong_position()` - added tenant_id/portfolio_id
- Fixed `test_get_dividend_status()` - added tenant_id/portfolio_id, portfolio_cash mock
- Fixed `test_get_dividend_status_no_position()` - added tenant_id/portfolio_id
- Fixed `test_process_dividend_payment_increments_aggregate()` - added tenant_id/portfolio_id, portfolio_cash
- Fixed `test_process_dividend_payment_aggregates_multiple_payments()` - added tenant_id/portfolio_id, portfolio_cash
- Fixed `test_process_dividend_payment_aggregate_starts_at_zero()` - added tenant_id/portfolio_id, portfolio_cash
- Fixed `test_dividend_aggregate_independent_from_commission()` - added tenant_id/portfolio_id, portfolio_cash

### ✅ process_dividend_uc.py (Implementation Fix)

- Fixed `get_dividend_status()` method signature to include tenant_id and portfolio_id
- Fixed `positions_repo.get()` call to use tenant_id/portfolio_id

---

## Files Verified (No Changes Needed)

### ✅ test_execute_order_uc.py

- Already uses portfolio-scoped API correctly
- Uses `asset_symbol=`, has tenant_id/portfolio_id
- Uses `portfolio_cash_repo` correctly

### ✅ test_submit_order_uc.py

- Already uses portfolio-scoped API correctly
- Uses `asset_symbol=`, has tenant_id/portfolio_id

### ✅ test_order_entity.py

- Already fixed (all Order() calls have tenant_id/portfolio_id)

### ✅ test_position_entity.py

- Already has comprehensive tests including aggregates

### ✅ test_trade_entity.py

- Already uses tenant_id/portfolio_id correctly

### ✅ test_dividend_entities.py

- Uses `ticker=` correctly (Dividend entity uses ticker, not asset_symbol)

### ✅ test_dividend_repos.py

- Uses `ticker=` correctly (Dividend entity uses ticker)

### ✅ test_optimization_entities.py

- Uses `ticker=` correctly (OptimizationConfig uses ticker)

### ✅ test_parameter_optimization_uc.py

- Uses `ticker=` correctly (CreateOptimizationRequest uses ticker)

---

## Remaining Files to Check

### ⏳ test_order_policy_uc.py

- Need to verify all Order/Position creations

### ⏳ test_idempotency_entity.py

- Need to verify entity structure matches tests

### ⏳ test_event_entity.py

- Need to verify no issues

### ⏳ test_optimization_criteria.py

- Need to verify no issues

### ⏳ test_config_repo_sql.py

- Need to verify no issues

### ⏳ test_merged_cell_fix.py

- Need to verify no issues

### ⏳ test_idempotency_repo.py

- Need to verify no issues

### ⏳ test_price_trigger_golden.py

- Need to verify no issues

---

## Summary

**Fixed:** 2 files (test_submit_daily_cap.py, test_process_dividend_uc.py)  
**Verified:** 9 files (no changes needed)  
**Remaining:** 8 files to check

**Total Fixes Applied:** ~15 method calls updated

---

**Next Steps:**

1. Check remaining 8 files
2. Run full test suite to verify fixes
3. Fix any remaining issues found

---

**Last Updated:** January 2025








