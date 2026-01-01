# Cash Reconciliation Progress

## ✅ Completed

1. **Domain Entity** - Added `cash` field to `Position` entity

   - ✅ Added `cash: float = 0.0` to `Position` dataclass
   - ✅ Updated `get_effective_cash()` to use `position.cash` (removed `portfolio_cash` parameter)
   - ✅ Updated `clear_dividend_receivable()` to add cleared dividend to `position.cash`

2. **Repository** - Updated `positions_repo_sql.py` to read/write `cash` properly

   - ✅ Updated `_to_entity()` to read `cash=row.cash`
   - ✅ Updated `_new_row_from_entity()` to write `cash=p.cash`
   - ✅ Updated `_apply_entity_to_row()` to update `cash=p.cash`
   - ✅ Updated `create()` method to accept `cash` parameter

3. **Model Comments** - Updated `PositionModel.cash` comment to reflect new model

   - ✅ Changed from "legacy" to "Cash lives in PositionCell (per target state model)"

4. **ExecuteOrderUC** - Updated to use `position.cash` instead of `portfolio_cash`

   - ✅ Removed `portfolio_cash_repo` dependency from constructor
   - ✅ Removed all `portfolio_cash` retrieval and save calls
   - ✅ Changed `portfolio_cash.withdraw()` → `position.cash -= amount`
   - ✅ Changed `portfolio_cash.deposit()` → `position.cash += amount`
   - ✅ Updated all cash calculations to use `position.cash`

5. **EvaluatePositionUC** - Updated to use `position.cash`

   - ✅ Removed `portfolio_cash_repo` dependency from constructor
   - ✅ Updated `_check_triggers()` - removed `portfolio_cash` parameter
   - ✅ Updated `_check_auto_rebalancing()` - removed `portfolio_cash` parameter
   - ✅ Updated `_calculate_order_proposal()` - removed `portfolio_cash` parameter
   - ✅ Updated `_apply_guardrail_trimming()` - removed `portfolio_cash` parameter
   - ✅ Updated `_validate_order()` - removed `portfolio_cash` parameter
   - ✅ Updated `_calculate_post_trade_allocation()` - removed `portfolio_cash` parameter
   - ✅ Updated `_log_evaluation_event()` - uses `position.cash`
   - ✅ Replaced all `portfolio_cash.cash_balance` references with `position.cash`

6. **ProcessDividendUC** - Updated to use `position.cash`
   - ✅ Removed `portfolio_cash_repo` dependency from constructor
   - ✅ Removed all `portfolio_cash` retrieval and save calls
   - ✅ Changed `portfolio_cash.deposit()` → `position.cash += net_amount`
   - ✅ Updated `get_effective_cash()` call to use no parameters
   - ✅ Updated all cash balance references to use `position.cash`

## 🔄 In Progress

7. **PortfolioService** - Compute totals from positions, remove `portfolio_cash_repo` dependency
   - ⏳ Remove `portfolio_cash_repo` from constructor
   - ⏳ Update `create_portfolio()` to distribute cash to positions instead of creating `portfolio_cash`
   - ⏳ Update `get_portfolio_summary()` to compute `SUM(position.cash)` instead of reading `portfolio_cash`
   - ⏳ Remove or update `deposit_cash()` and `withdraw_cash()` methods

## ⏳ Pending

8. **API Routes** - Update/remove cash endpoints

   - ⏳ Update portfolio summary endpoint to compute from positions
   - ⏳ Remove or redesign `/cash/deposit` and `/cash/withdraw` endpoints
   - ⏳ Update position endpoints to return `cash` field

9. **Frontend** - Update interfaces and components

   - ⏳ Update `PortfolioPosition` interface to include `cash` field
   - ⏳ Update `PositionsTab` to show per-position cash
   - ⏳ Update portfolio totals calculation to sum `position.cash`
   - ⏳ Remove or redesign `CashTab` (cash is now per-position)

10. **Migration Script** - Create script to move cash from `portfolio_cash` to positions

    - ⏳ Create migration script with distribution policy (equal/proportional/first_position)
    - ⏳ Test migration on dev database
    - ⏳ Document rollback procedure

11. **Dependency Injection & Instantiations** - Update all code that creates use cases
    - ⏳ Update all `ExecuteOrderUC` instantiations (remove `portfolio_cash_repo` parameter)
    - ⏳ Update all `EvaluatePositionUC` instantiations (remove `portfolio_cash_repo` parameter)
    - ⏳ Update all `ProcessDividendUC` instantiations (remove `portfolio_cash_repo` parameter)
    - ⏳ Update dependency injection containers
    - ⏳ Update all test files

## Notes

- ✅ **Core use cases completed** - All three main use cases (ExecuteOrderUC, EvaluatePositionUC, ProcessDividendUC) now use `position.cash`
- ⚠️ **Breaking changes** - All code that instantiates these use cases needs to be updated
- ⚠️ **Tests need updates** - All test files need to be updated to remove `portfolio_cash_repo` parameters
- ⚠️ **Data migration required** - Existing data in `portfolio_cash` table needs to be migrated to `position.cash`








