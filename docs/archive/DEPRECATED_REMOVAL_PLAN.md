# Deprecated Functionality Removal Plan

## ✅ Completed Removals

### 1. Positions API (`/v1/positions`)

- ✅ `POST /v1/positions` - REMOVED (returns 410 Gone)
- ✅ `GET /v1/positions` - REMOVED (returns 410 Gone)
- ✅ `GET /v1/positions/{position_id}` - REMOVED (returns 410 Gone)
- ✅ `DELETE /v1/positions/{position_id}` - REMOVED (returns 410 Gone)
- ✅ `POST /v1/positions/{position_id}/evaluate` - REMOVED (returns 410 Gone)
- ✅ `POST /v1/positions/{position_id}/evaluate/market` - REMOVED (returns 410 Gone)
- ✅ `POST /v1/positions/{position_id}/anchor` - REMOVED (returns 410 Gone)
- ✅ `PUT /v1/positions/{position_id}/anchor-price` - REMOVED (returns 410 Gone)
- ✅ `GET /v1/positions/{position_id}/events` - REMOVED (returns 410 Gone)
- ✅ `POST /v1/positions/{position_id}/orders/auto-size` - REMOVED (returns 410 Gone)
- ✅ `POST /v1/positions/update-anchor-prices` - REMOVED (returns 410 Gone)
- ✅ `POST /v1/positions/auto-setup` - REMOVED (returns 410 Gone)
- ✅ `POST /v1/positions/clear-positions` - REMOVED (returns 410 Gone)

### 2. Orders API (`/v1/positions/{position_id}/orders`)

- ✅ `POST /v1/positions/{position_id}/orders` - REMOVED
- ✅ `GET /v1/positions/{position_id}/orders` - REMOVED

### 3. Legacy Helper Functions

- ✅ `_find_position_legacy()` - REMOVED
- ✅ `_get_portfolio_cash_legacy()` - REMOVED

### 4. Other Deprecated Code

- ✅ `CompositeEventLogger` - REMOVED (file deleted, not used in DI)

## Replacement Endpoints

All functionality should use portfolio-scoped endpoints:

- `POST /api/tenants/{tenant_id}/portfolios/{portfolio_id}` - Create portfolio with positions
- `GET /api/tenants/{tenant_id}/portfolios/{portfolio_id}/overview` - Get portfolio overview
- `GET /api/tenants/{tenant_id}/portfolios/{portfolio_id}/positions` - List positions
- `GET /api/tenants/{tenant_id}/portfolios/{portfolio_id}/positions/{position_id}` - Get position
- `POST /api/tenants/{tenant_id}/portfolios/{portfolio_id}/positions/{position_id}/orders` - Submit order
- `GET /api/tenants/{tenant_id}/portfolios/{portfolio_id}/positions/{position_id}/orders` - List orders

## ⚠️ Remaining Legacy Code (Not Deprecated, But Needs Update)

These endpoints are not marked as deprecated but use legacy position lookup patterns. They should be updated to require tenant_id/portfolio_id:

- `backend/app/routes/trading.py` - `/trading/start/{position_id}` - Uses legacy lookup (marked with TODO)
- `backend/app/routes/excel_export.py` - Excel export endpoints - Use legacy lookup (marked with TODO)

These are still functional but should be migrated to portfolio-scoped endpoints in the future.

## Test Updates Required

All integration tests in `backend/tests/integration/` that use `/v1/positions` or `/v1/positions/{position_id}/orders` need to be updated to use portfolio-scoped endpoints.

## Removal Summary

✅ **Completed:**

1. ✅ Removed all deprecated `/v1/positions` endpoints (now return 410 Gone)
2. ✅ Removed legacy `/v1/positions/{position_id}/orders` endpoints
3. ✅ Removed legacy helper functions (`_find_position_legacy`, `_get_portfolio_cash_legacy`)
4. ✅ Removed `CompositeEventLogger` (not used)

⏳ **Next Steps:**

1. Update integration tests to use portfolio-scoped endpoints
2. Update trading.py and excel_export.py to require tenant_id/portfolio_id (or mark as deprecated if not needed)
3. Run tests to verify everything works









