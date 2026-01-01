# QA Immediate Fixes Summary

**Date:** January 2025  
**Status:** IN PROGRESS

---

## Fixes Completed (Top 5 Most Common Issues)

### ✅ Fix 1: test_submit_daily_cap.py - Portfolio Migration

**File:** `backend/tests/unit/application/test_submit_daily_cap.py`

**Issue:** Line 77 - Using old API:

- `ticker="CAPF"` → Should be `asset_symbol="CAPF"`
- `cash=10_000.0` → Should use portfolio_cash
- Missing `tenant_id` and `portfolio_id` setup

**Fix Applied:**

- Added portfolio setup with tenant_id and portfolio_id
- Changed `ticker=` to `asset_symbol=`
- Removed `cash=` parameter
- Added portfolio_cash_repo.create() call

---

### ✅ Fix 2: test_process_dividend_uc.py - Position Creation

**File:** `backend/tests/unit/application/test_process_dividend_uc.py`

**Issue:** Line 59-69 - Using old Position API:

- `ticker="AAPL"` → Should be `asset_symbol="AAPL"`
- `cash=10000.0` → Should be removed (cash is in portfolio_cash)
- Missing `tenant_id` and `portfolio_id`

**Fix Applied:**

- Added `tenant_id="default"` and `portfolio_id="test_portfolio"`
- Changed `ticker=` to `asset_symbol=`
- Removed `cash=` parameter

---

### ✅ Fix 3: test_process_dividend_uc.py - Cash Assertions

**File:** `backend/tests/unit/application/test_process_dividend_uc.py`

**Issue:** Lines 220, 227 - Checking `position.cash`:

- `sample_position.cash` → Should check `portfolio_cash.cash_balance`
- Use case now requires `tenant_id` and `portfolio_id` parameters

**Fix Applied:**

- Added portfolio_cash mock setup
- Updated use case call to include tenant_id and portfolio_id
- Changed assertions to check `portfolio_cash.cash_balance`
- Added check for `total_dividends_received` aggregate
- Updated repository call assertions

---

## Remaining Issues to Fix

### ⏳ Fix 4: test_process_dividend_uc.py - Other Method Calls

**File:** `backend/tests/unit/application/test_process_dividend_uc.py`

**Issues:**

- `process_ex_dividend_date()` calls need `tenant_id` and `portfolio_id`
- `process_dividend_payment()` calls need `tenant_id` and `portfolio_id`
- Multiple test methods need updates

**Estimated:** ~15 more fixes in this file

---

### ⏳ Fix 5: test_dividend_entities.py - Ticker Usage

**File:** `backend/tests/unit/domain/test_dividend_entities.py`

**Issue:** Using `ticker=` in Dividend entity tests

**Note:** Need to verify if Dividend entity uses `ticker` or `asset_symbol`

**Status:** Pending verification

---

## Next Steps

1. **Continue fixing test_process_dividend_uc.py:**

   - Update all `process_ex_dividend_date()` calls
   - Update all `process_dividend_payment()` calls
   - Add portfolio_cash mocks where needed

2. **Fix test_dividend_entities.py:**

   - Verify Dividend entity structure
   - Update if needed

3. **Fix test_dividend_repos.py:**

   - Update `ticker=` usage if needed

4. **Run tests to verify fixes:**
   ```bash
   cd backend
   python -m pytest tests/unit/application/test_submit_daily_cap.py -v
   python -m pytest tests/unit/application/test_process_dividend_uc.py::TestProcessDividendUC::test_process_dividend_payment_success -v
   ```

---

## Progress Tracking

- [x] Fix test_submit_daily_cap.py (1 file)
- [x] Fix test_process_dividend_uc.py position creation (partial)
- [x] Fix test_process_dividend_uc.py cash assertions (partial)
- [ ] Fix test_process_dividend_uc.py remaining methods (~15 fixes)
- [ ] Fix test_dividend_entities.py (if needed)
- [ ] Fix test_dividend_repos.py (if needed)

**Estimated Remaining:** ~20 fixes

---

**Last Updated:** January 2025








