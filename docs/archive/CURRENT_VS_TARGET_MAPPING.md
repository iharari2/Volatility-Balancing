# Current vs Target State Mapping

## Quick Reference

### Current State → Target State

| Current                                              | Target                                      | Status                                    |
| ---------------------------------------------------- | ------------------------------------------- | ----------------------------------------- |
| `portfolio_cash.cash_balance`                        | `position.cash`                             | ✅ Code updated, ⏳ Data migration needed |
| `PortfolioCash` entity                               | Remove/deprecate                            | ⏳ Pending removal                        |
| `PortfolioCashRepo`                                  | Remove/deprecate                            | ⏳ Pending removal                        |
| `Position.cash = 0.0` (always)                       | `Position.cash = actual_value`              | ✅ Completed                              |
| `portfolio_total_cash = portfolio_cash.cash_balance` | `portfolio_total_cash = SUM(position.cash)` | ⏳ Needs computation in PortfolioService  |
| `ExecuteOrderUC` uses `portfolio_cash`               | `ExecuteOrderUC` uses `position.cash`       | ✅ Completed                              |
| `EvaluatePositionUC` uses `portfolio_cash`           | `EvaluatePositionUC` uses `position.cash`   | ✅ Completed                              |
| `ProcessDividendUC` uses `portfolio_cash`            | `ProcessDividendUC` uses `position.cash`    | ✅ Completed                              |
| `/cash/deposit` endpoint                             | Remove or move to position-level            | ❌ Needs update                           |
| `/cash/withdraw` endpoint                            | Remove or move to position-level            | ❌ Needs update                           |
| `CashTab` (portfolio-level)                          | Remove or show per-position cash            | ❌ Needs update                           |

### Already Correct ✅

| Item                                          | Status |
| --------------------------------------------- | ------ |
| `PositionModel.portfolio_id` (mandatory FK)   | ✅     |
| `PositionModel.asset_symbol`                  | ✅     |
| `PositionModel.qty`                           | ✅     |
| `PositionModel.anchor_price`                  | ✅     |
| `PositionModel.total_commission_paid`         | ✅     |
| `PositionModel.total_dividends_received`      | ✅     |
| Orders reference `position_id`                | ✅     |
| Trades reference `position_id`                | ✅     |
| UI navigation: Tenant → Portfolio → Positions | ✅     |

## File-by-File Changes

### Backend Domain

- ✅ `backend/domain/entities/position.py` - Added `cash` field
- ⏳ `backend/domain/entities/portfolio_cash.py` - Mark as deprecated (pending)

### Backend Infrastructure

- ✅ `backend/infrastructure/persistence/sql/models.py` - Updated `PositionModel.cash` comment
- ✅ `backend/infrastructure/persistence/sql/positions_repo_sql.py` - Reads/writes `cash` properly
- ⏳ `backend/infrastructure/persistence/sql/portfolio_cash_repo_sql.py` - Mark deprecated (pending)

### Backend Use Cases

- ✅ `backend/application/use_cases/execute_order_uc.py` - Uses `position.cash`
- ✅ `backend/application/use_cases/evaluate_position_uc.py` - Uses `position.cash`
- ✅ `backend/application/use_cases/process_dividend_uc.py` - Uses `position.cash`

### Backend Services

- ⏳ `backend/application/services/portfolio_service.py` - Compute totals from positions (in progress)

### Backend Routes

- `backend/app/routes/portfolios.py` - Remove cash endpoints or move to position-level
- `backend/app/routes/positions.py` - Return `cash` in responses

### Frontend

- `frontend/src/services/portfolioScopedApi.ts` - Update interface
- `frontend/src/features/positions/tabs/CashTab.tsx` - Remove or redesign
- `frontend/src/features/positions/tabs/PositionsTab.tsx` - Show per-position cash








