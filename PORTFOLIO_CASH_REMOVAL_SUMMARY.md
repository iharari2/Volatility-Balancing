# PortfolioCash Removal Summary

## ✅ Successfully Removed

### Entity and Repository

- ✅ `backend/domain/entities/portfolio_cash.py` - Deleted
- ✅ `backend/domain/ports/portfolio_cash_repo.py` - Deleted
- ✅ `backend/infrastructure/persistence/sql/portfolio_cash_repo_sql.py` - Deleted
- ✅ `PortfolioCashModel` from `backend/infrastructure/persistence/sql/models.py` - Removed

### Dependency Injection

- ✅ Removed `portfolio_cash_repo` from `backend/app/di.py`
- ✅ Removed `PortfolioCashRepo` imports and initialization

### Code Updates

- ✅ Updated `backend/application/services/portfolio_service.py` - Removed PortfolioCash dependency
- ✅ Updated `backend/infrastructure/adapters/position_repo_adapter.py` - Removed portfolio_cash_repo parameter
- ✅ Updated `backend/infrastructure/adapters/converters.py` - Now uses `position.cash` directly
- ✅ Updated `backend/app/routes/excel_export.py` - Uses `position.cash` instead of portfolio_cash_repo
- ✅ Updated `backend/app/routes/portfolios.py` - Removed portfolio_cash_repo from service initialization
- ✅ Updated `backend/conftest.py` - Sets cash on Position entity directly
- ✅ Updated `backend/app/di.py` - Removed portfolio_cash_repo from EvaluatePositionUC

### Frontend Updates

- ✅ Updated `frontend/src/services/portfolioScopedApi.ts` - Removed PortfolioCash interface, added getTotalCash method
- ✅ Updated `frontend/src/features/positions/PositionsAndConfigPage.tsx` - Calculates cash from positions
- ✅ Updated `frontend/src/features/positions/tabs/CashTab.tsx` - Uses CashSummary interface instead of PortfolioCash

### Documentation

- ✅ Updated `docs/architecture/persistence.md` - Removed PORTFOLIO_CASH from ER diagram

### Migration Scripts

- ✅ Updated `backend/scripts/migrate_to_portfolio_scoped.py` - Removed PortfolioCashModel import and migration functions

## 📝 Notes

### Historical Fields (Kept)

The following fields are kept as they are historical snapshot fields for tracking:

- `EvaluationTimelineModel.portfolio_cash_before` - Historical snapshot
- `EvaluationTimelineModel.portfolio_cash_after` - Historical snapshot

These fields track historical portfolio cash values for audit purposes and don't reference the PortfolioCash entity.

### Cash Storage

Cash is now stored directly in `Position.cash`:

- Each position has its own cash balance
- Portfolio total cash = sum of all position.cash values
- No separate portfolio-level cash entity

### Migration

If you have existing `portfolio_cash` table data, you'll need to manually migrate it to `Position.cash`:

1. For portfolios with single position: Move all cash to that position
2. For portfolios with multiple positions: Distribute cash equally or proportionally
3. Drop the `portfolio_cash` table after migration

## 🔄 API Changes

No API changes required - the portfolio overview endpoint already calculates cash from positions.

---

_Last updated: 2025-01-XX_







