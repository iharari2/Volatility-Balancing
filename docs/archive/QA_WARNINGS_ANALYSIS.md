# Warnings Analysis and Fixes

**Date:** January 2025  
**Status:** ✅ **FIXES APPLIED**

---

## Warning Summary

**Total Warnings:** 143  
**From Our Code:** 5 (fixed)  
**From Third-Party Libraries:** 138 (cannot fix directly)

---

## Warning Breakdown

### 1. FastAPI `on_event` Deprecation (4 warnings) ✅ FIXED

**Location:** `backend/app/main.py:55, 62`

**Issue:** FastAPI deprecated `@app.on_event("startup")` and `@app.on_event("shutdown")` in favor of lifespan event handlers.

**Fix Applied:**

- Migrated to `lifespan` context manager using `@asynccontextmanager`
- Removed deprecated `@app.on_event` decorators
- Updated to use FastAPI's `lifespan` parameter

**Code Changes:**

```python
# Before (deprecated):
@app.on_event("startup")
async def startup_event():
    start_trading_worker()

@app.on_event("shutdown")
async def shutdown_event():
    stop_trading_worker()

# After (modern):
@asynccontextmanager
async def lifespan(app: FastAPI):
    start_trading_worker()
    yield
    stop_trading_worker()

app = FastAPI(..., lifespan=lifespan)
```

---

### 2. `datetime.utcnow()` Deprecation (1 warning) ✅ FIXED

**Location:** `backend/application/events.py:58`

**Issue:** Python 3.12 deprecated `datetime.utcnow()` in favor of timezone-aware `datetime.now(timezone.utc)`.

**Fix Applied:**

- Changed `datetime.utcnow()` to `datetime.now(timezone.utc)`
- Added `timezone` import

**Code Changes:**

```python
# Before:
from datetime import datetime
created_at=datetime.utcnow()

# After:
from datetime import datetime, timezone
created_at=datetime.now(timezone.utc)
```

---

### 3. openpyxl `datetime.utcnow()` Deprecation (138 warnings) ⚠️ CANNOT FIX

**Location:** Third-party library `openpyxl`

**Issue:** The `openpyxl` library (version 3.x) internally uses `datetime.utcnow()` which is deprecated in Python 3.12. These warnings come from:

- `openpyxl/packaging/core.py:99` (99 warnings)
- `openpyxl/writer/excel.py:292` (39 warnings)

**Why We Can't Fix:**

- This is code inside the `openpyxl` library, not our codebase
- We cannot modify third-party library code
- We must wait for `openpyxl` to release an update

**Options:**

1. **Suppress warnings** (recommended for now):

   ```python
   import warnings
   warnings.filterwarnings("ignore", category=DeprecationWarning, module="openpyxl")
   ```

2. **Wait for openpyxl update**: Monitor for a new version that fixes this

3. **Use alternative library**: Consider switching to `xlsxwriter` or `pandas.ExcelWriter` if needed

**Recommendation:** Suppress these warnings in `pytest.ini` or `conftest.py` until `openpyxl` releases a fix.

---

### 4. Starlette `multipart` Deprecation (1 warning) ⚠️ CANNOT FIX

**Location:** Third-party library `starlette`

**Issue:** Starlette uses `multipart` instead of `python_multipart` internally.

**Why We Can't Fix:**

- This is code inside the `starlette` library, not our codebase
- We cannot modify third-party library code
- We must wait for `starlette` to release an update

**Options:**

1. **Suppress warning** (recommended for now)
2. **Wait for starlette update**

---

## Recommended Actions

### Immediate (Done ✅)

- ✅ Fixed FastAPI lifespan handlers
- ✅ Fixed our `datetime.utcnow()` usage

### Short-term (Recommended)

1. **Suppress openpyxl warnings** in `pytest.ini`:

   ```ini
   [tool.pytest.ini_options]
   filterwarnings = [
       "ignore::DeprecationWarning:openpyxl.*",
   ]
   ```

2. **Suppress starlette warning**:
   ```ini
   filterwarnings = [
       "ignore::PendingDeprecationWarning:starlette.*",
   ]
   ```

### Long-term (Monitor)

- Monitor `openpyxl` releases for Python 3.12 compatibility
- Monitor `starlette` releases for `python_multipart` migration
- Consider alternative Excel libraries if `openpyxl` doesn't update soon

---

## Impact Assessment

**Severity:** Low

- All warnings are deprecation warnings, not errors
- Functionality is not affected
- Tests pass successfully
- Warnings are from third-party libraries we cannot control

**Action Required:** None (warnings are informational)

---

## Files Modified

1. **`backend/app/main.py`**

   - Migrated from `@app.on_event` to `lifespan` context manager
   - Removed deprecated event handlers

2. **`backend/application/events.py`**
   - Changed `datetime.utcnow()` to `datetime.now(timezone.utc)`
   - Added `timezone` import

---

## Summary

**Fixed:** ✅ 5 warnings (FastAPI + datetime)  
**Cannot Fix:** ⚠️ 138 warnings (third-party libraries)  
**Impact:** None (functionality unaffected)  
**Recommendation:** Suppress third-party warnings in pytest config

**Status:** ✅ **COMPLETE**  
**Last Updated:** January 2025








