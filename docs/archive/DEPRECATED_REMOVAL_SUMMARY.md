# Deprecated Functionality Removal Summary

## ✅ Successfully Removed

### Deprecated Endpoints (Now Return 410 Gone)

All the following endpoints have been removed and now return HTTP 410 (Gone) with a message directing users to the portfolio-scoped alternatives:

1. **POST /v1/positions** - Removed (use `POST /api/tenants/{tenant_id}/portfolios/{portfolio_id}`)
2. **GET /v1/positions** - Removed (use `GET /api/tenants/{tenant_id}/portfolios/{portfolio_id}/positions`)
3. **GET /v1/positions/{position_id}** - Removed
4. **DELETE /v1/positions/{position_id}** - Removed
5. **POST /v1/positions/{position_id}/evaluate** - Removed
6. **POST /v1/positions/{position_id}/evaluate/market** - Removed
7. **POST /v1/positions/{position_id}/anchor** - Removed
8. **PUT /v1/positions/{position_id}/anchor-price** - Removed
9. **GET /v1/positions/{position_id}/events** - Removed
10. **POST /v1/positions/{position_id}/orders/auto-size** - Removed
11. **POST /v1/positions/update-anchor-prices** - Removed
12. **POST /v1/positions/auto-setup** - Removed
13. **POST /v1/positions/clear-positions** - Removed
14. **POST /v1/positions/{position_id}/orders** - Removed (use portfolio-scoped endpoint)
15. **GET /v1/positions/{position_id}/orders** - Removed (use portfolio-scoped endpoint)

### Removed Helper Functions

- `_find_position_legacy()` - Removed from `backend/app/routes/positions.py`
- `_get_portfolio_cash_legacy()` - Removed from `backend/app/routes/positions.py`
- `_find_position_legacy()` - Removed from `backend/app/routes/orders.py`

### Removed Files

- `backend/infrastructure/adapters/composite_event_logger.py` - Deleted (not used in DI container)

## 📝 Notes

- All removed endpoints return HTTP 410 (Gone) with a helpful error message directing users to the replacement endpoint
- Integration tests will need to be updated to use portfolio-scoped endpoints
- Some endpoints in `trading.py` and `excel_export.py` still use legacy position lookup but are not marked as deprecated (they have TODO comments for future migration)

## 🔄 Migration Path

For any code or tests using the removed endpoints:

1. **Creating Positions**: Use `POST /api/tenants/{tenant_id}/portfolios/{portfolio_id}` with holdings in the request body
2. **Getting Positions**: Use `GET /api/tenants/{tenant_id}/portfolios/{portfolio_id}/positions/{position_id}`
3. **Submitting Orders**: Use `POST /api/tenants/{tenant_id}/portfolios/{portfolio_id}/positions/{position_id}/orders`
4. **Listing Orders**: Use `GET /api/tenants/{tenant_id}/portfolios/{portfolio_id}/positions/{position_id}/orders`









