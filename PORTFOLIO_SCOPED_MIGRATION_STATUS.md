# Portfolio-Scoped State Migration Status

## ✅ Completed

### Database Schema

- ✅ Added `tenant_id` to all portfolio-related tables (portfolios, positions, orders, trades, events)
- ✅ Added `portfolio_id` to positions, orders, trades
- ✅ Created `portfolio_cash` table
- ✅ Created `portfolio_config` table
- ✅ Removed `cash` from `PositionModel` (moved to `portfolio_cash`)

### Domain Entities

- ✅ Updated `Position` entity (removed cash, added tenant_id/portfolio_id, asset_symbol)
- ✅ Created `PortfolioCash` entity
- ✅ Created `PortfolioConfig` entity
- ✅ Updated `Portfolio` entity (added tenant_id, type, trading_state, trading_hours_policy)
- ✅ Updated `Order` entity (added tenant_id, portfolio_id)
- ✅ Updated `Trade` entity (added tenant_id, portfolio_id)

### Repositories

- ✅ Updated `PositionsRepo` interface to require tenant_id + portfolio_id
- ✅ Updated `PortfolioRepo` interface to require tenant_id
- ✅ Created `PortfolioCashRepo` and `PortfolioConfigRepo`
- ✅ Updated all SQL repository implementations

### Services & Use Cases

- ✅ Updated `PortfolioService` to use new repositories
- ✅ Added `get_portfolio_overview()` method
- ✅ Updated `create_portfolio()` to persist cash+positions+config
- ✅ Updated `ExecuteOrderUC` to use portfolio_cash
- ✅ Updated `EvaluatePositionUC` to use portfolio_cash and asset_symbol
- ✅ Updated `ProcessDividendUC` to use portfolio_cash and asset_symbol
- ✅ Updated `SubmitOrderUC` to require tenant_id + portfolio_id

### API Routes

- ✅ Updated all portfolio routes to `/api/tenants/{tenant_id}/portfolios/{portfolio_id}/...`
- ✅ Added `/overview` endpoint
- ✅ Updated orders routes to require tenant_id + portfolio_id
- ✅ Updated dividends routes to require tenant_id + portfolio_id

### Frontend

- ✅ Updated `portfolioApi` to require tenantId and portfolioId
- ✅ Updated `CreatePortfolioWizard` to use new API format
- ✅ Updated `PortfolioOverviewPage` to call overview endpoint
- ✅ Updated `TenantPortfolioContext` to use overview endpoint

### Adapters

- ✅ Updated `PositionRepoAdapter` to iterate over portfolios
- ✅ Updated converters to use portfolio_cash

## ⚠️ Partially Complete / Needs Work

### Legacy Routes (Deprecated)

- ⚠️ `/v1/positions` route still uses old interface - **SHOULD BE DEPRECATED**
  - Positions should be created via portfolio API only
  - This route will break with new schema

### Use Cases Still Need Updates

- ⚠️ `SimulationUnifiedUC` - still references `position.cash`
- ⚠️ `ContinuousTradingService` - still uses `position.ticker` (should use asset_symbol)

### Test Files

- ⚠️ All test files need updates to use tenant_id + portfolio_id
- ⚠️ Tests still create positions with cash parameter

### Excel Export Routes

- ⚠️ Excel export routes still use old position interface

## 🔴 Critical Issues

1. **Legacy `/positions` route** - Will fail with new schema. Should be removed or updated.
2. **Simulation use cases** - Still reference position.cash which no longer exists
3. **Test files** - All tests need migration to use tenant_id + portfolio_id

## Migration Guide

### For Developers

1. **Creating Positions**: Use portfolio API, not `/positions` route

   ```python
   POST /api/tenants/{tenant_id}/portfolios/{portfolio_id}
   # Include holdings in request body
   ```

2. **Accessing Cash**: Get from portfolio_cash, not position

   ```python
   cash = portfolio_cash_repo.get(tenant_id, portfolio_id)
   balance = cash.cash_balance
   ```

3. **Accessing Ticker**: Use `position.asset_symbol` (or `position.ticker` property for backward compat)

4. **All Repository Calls**: Must include tenant_id + portfolio_id
   ```python
   positions = positions_repo.list_all(tenant_id, portfolio_id)
   position = positions_repo.get(tenant_id, portfolio_id, position_id)
   ```

## Next Steps

1. Remove or update legacy `/positions` route
2. Update simulation use cases
3. Update all test files
4. Update excel export routes
5. Add migration script for existing data













