# Cash Reconciliation Plan: Moving Cash to PositionCell

## Current State Audit (2-minute assessment)

### Database Schema

- ✅ **PositionModel** has `cash` column (nullable=False, default=0.0) - marked as "legacy"
- ✅ **PortfolioCashModel** exists (`portfolio_cash` table) - actively used
- ✅ **PositionModel** has `portfolio_id` (mandatory FK) ✅
- ✅ **PositionModel** has `asset_symbol`, `qty`, `anchor_price`, `total_commission_paid`, `total_dividends_received` ✅
- ❌ **No Account table** ✅
- ❌ **PortfolioModel** has NO cash field ✅

### Current Implementation

- All business logic uses `portfolio_cash` table
- `Position` entity has NO `cash` field (removed in migration)
- `PositionModel` has `cash` column but it's always set to 0.0
- Portfolio totals computed from `portfolio_cash.cash_balance` + position values

### Target State Model

```
Portfolio
  - portfolio_id ✅
  - tenant_id ✅
  - metadata (name, description) ✅
  - optional: portfolio-level default config profile ✅

PositionCell (per asset per portfolio)
  - position_id ✅
  - portfolio_id ✅ (mandatory FK)
  - asset_symbol ✅
  - qty ✅
  - cash ✅ (MUST LIVE HERE - currently in portfolio_cash)
  - anchor_price ✅
  - total_commission_paid ✅
  - total_dividends_received ✅

Derived (never stored)
  - portfolio_total_cash = SUM(position.cash) ❌ (currently from portfolio_cash)
  - portfolio_total_value = SUM(position.cash + position.qty * price) ❌
```

## Reconciliation Strategy: Option A (Preferred)

### Step 1: Data Migration

Distribute `portfolio_cash.cash_balance` to positions using one of these policies:

**Policy Options:**

1. **Single-position portfolio**: Move all cash to that one position
2. **Multiple positions - Equal distribution**: `cash_per_position = total_cash / num_positions`
3. **Multiple positions - Proportional to position value**: Distribute by current market value
4. **Multiple positions - First position gets all**: Simple but may not be ideal

**Recommended: Equal distribution** (simplest, most predictable)

### Step 2: Code Changes Required

#### A. Domain Entity (`backend/domain/entities/position.py`)

- ✅ Add `cash: float = 0.0` field back to `Position` entity
- ✅ Update `get_effective_cash()` method (removed portfolio_cash parameter, now uses `position.cash`)
- ✅ Update `clear_dividend_receivable()` to add cleared dividend to `position.cash`

#### B. Repository (`backend/infrastructure/persistence/sql/positions_repo_sql.py`)

- ✅ Update `_new_row_from_entity()` to set `cash=p.cash` (was setting to 0.0)
- ✅ Update `_apply_entity_to_row()` to set `cash=p.cash` (was not updating)
- ✅ Update `_to_entity()` to read `cash=row.cash` (was not reading)
- ✅ Update `create()` method to accept `cash` parameter

#### C. Use Cases (All must be updated)

1. **ExecuteOrderUC** (`backend/application/use_cases/execute_order_uc.py`)

   - ✅ Remove `portfolio_cash_repo` dependency
   - ✅ Change `portfolio_cash.withdraw()` → `position.cash -= amount`
   - ✅ Change `portfolio_cash.deposit()` → `position.cash += amount`
   - ✅ Remove `portfolio_cash_repo.save()` calls
   - ✅ Update all cash calculations and event logging to use `position.cash`

2. **EvaluatePositionUC** (`backend/application/use_cases/evaluate_position_uc.py`)

   - ✅ Remove `portfolio_cash_repo` dependency
   - ✅ Replace all `portfolio_cash.cash_balance` references with `position.cash`
   - ✅ Update cash calculations to use `position.cash`
   - ✅ Update all helper methods: `_check_triggers()`, `_check_auto_rebalancing()`, `_calculate_order_proposal()`, `_apply_guardrail_trimming()`, `_validate_order()`, `_calculate_post_trade_allocation()`, `_log_evaluation_event()`

3. **ProcessDividendUC** (`backend/application/use_cases/process_dividend_uc.py`)

   - ✅ Remove `portfolio_cash_repo` dependency
   - ✅ Change `portfolio_cash.deposit()` → `position.cash += net_amount`
   - ✅ Update `get_effective_cash()` calls to use no parameters
   - ✅ Update all cash balance references in events and return values

4. **PortfolioService** (`backend/application/services/portfolio_service.py`)
   - ❌ Remove `portfolio_cash_repo` dependency
   - ❌ Remove `deposit_cash()` and `withdraw_cash()` methods (or move to position-level)
   - ❌ Update `create_portfolio()` to set `position.cash` instead of creating `portfolio_cash`
   - ❌ Update `get_portfolio_summary()` to compute `SUM(position.cash)` instead of reading `portfolio_cash`

#### D. API Routes

1. **Portfolios Route** (`backend/app/routes/portfolios.py`)

   - ❌ Remove `/cash/deposit` and `/cash/withdraw` endpoints (or change to position-level)
   - ❌ Update `get_portfolio_summary()` to compute totals from positions

2. **Positions Route** (`backend/app/routes/positions.py`)
   - ✅ Update to return `position.cash` in responses

#### E. Frontend

1. **PortfolioScopedApi** (`frontend/src/services/portfolioScopedApi.ts`)

   - ❌ Remove `depositCash()` and `withdrawCash()` methods (or change to position-level)
   - ✅ Update `PortfolioPosition` interface to include `cash` field

2. **CashTab** (`frontend/src/features/positions/tabs/CashTab.tsx`)

   - ❌ Remove or redesign (cash is now per-position, not portfolio-level)

3. **PositionsTab** (`frontend/src/features/positions/tabs/PositionsTab.tsx`)
   - ✅ Update to display `position.cash` per position
   - ✅ Update portfolio totals to sum `position.cash`

### Step 3: Migration Script

Create script to:

1. Read all `portfolio_cash` records
2. For each portfolio, get all positions
3. Distribute cash to positions (using chosen policy)
4. Update `position.cash` in database
5. (Optional) Mark `portfolio_cash` records as migrated or delete them

### Step 4: Non-Negotiable Invariants (Enforcement)

✅ **PositionCell.portfolio_id is mandatory** - Already enforced
✅ **All orders/trades reference position_id** - Already enforced
✅ **Execution updates only PositionCell state** - Now uses `position.cash` (completed)
⏳ **Portfolio is a read-model aggregate over positions** - Must compute from positions (PortfolioService pending)
✅ **UI navigation: Tenant → Portfolio → Positions → Trades/Audit** - Already correct

## Implementation Checklist

### Phase 1: Data Model Updates

- [x] Add `cash` field to `Position` entity
- [x] Update `PositionModel` to properly read/write `cash` (removed "legacy" comment)
- [x] Update repository to handle `cash` field

### Phase 2: Business Logic Updates

- [x] Update `ExecuteOrderUC` to use `position.cash`
- [x] Update `EvaluatePositionUC` to use `position.cash`
- [x] Update `ProcessDividendUC` to use `position.cash`
- [ ] Update `PortfolioService` to compute totals from positions
- [x] Remove `portfolio_cash_repo` dependencies from use cases

### Phase 3: API Updates

- [ ] Update portfolio summary endpoint to compute from positions
- [ ] Remove or redesign cash deposit/withdraw endpoints
- [ ] Update position endpoints to return `cash`

### Phase 4: Frontend Updates

- [ ] Update `PortfolioPosition` interface
- [ ] Update `PositionsTab` to show per-position cash
- [ ] Update portfolio totals calculation
- [ ] Remove or redesign `CashTab`

### Phase 5: Data Migration

- [ ] Create migration script
- [ ] Test migration on dev database
- [ ] Run migration on production
- [ ] Verify data integrity

### Phase 6: Cleanup

- [ ] Remove `PortfolioCash` entity (or mark deprecated)
- [ ] Remove `PortfolioCashRepo` (or mark deprecated)
- [ ] Remove `portfolio_cash` table (or keep read-only for audit)
- [ ] Update documentation

## Migration Script Template

```python
def migrate_cash_to_positions(engine: Engine, distribution_policy: str = "equal"):
    """
    Migrate cash from portfolio_cash to position.cash

    distribution_policy: "equal" | "proportional" | "first_position"
    """
    with Session(engine) as session:
        # Get all portfolio_cash records
        portfolio_cash_records = session.query(PortfolioCashModel).all()

        for pc in portfolio_cash_records:
            # Get all positions for this portfolio
            positions = session.query(PositionModel).filter(
                PositionModel.tenant_id == pc.tenant_id,
                PositionModel.portfolio_id == pc.portfolio_id
            ).all()

            if not positions:
                # No positions - skip or create a CASH position?
                continue

            total_cash = pc.cash_balance

            if distribution_policy == "equal":
                cash_per_position = total_cash / len(positions)
                for pos in positions:
                    pos.cash = cash_per_position
            elif distribution_policy == "proportional":
                # Calculate total position value
                # Distribute proportionally
                # (Implementation depends on having current prices)
                pass
            elif distribution_policy == "first_position":
                positions[0].cash = total_cash
                for pos in positions[1:]:
                    pos.cash = 0.0

            session.commit()
            print(f"Migrated ${total_cash:.2f} from portfolio_cash to {len(positions)} positions")
```

## Risk Assessment

### Low Risk

- Database schema already has `position.cash` column
- No data loss (cash is preserved, just moved)

### Medium Risk

- Large codebase changes (many use cases to update)
- Need to test all trading flows
- Frontend UI changes needed

### High Risk

- Concurrent transactions during migration
- Need to ensure atomic migration
- Rollback plan needed if migration fails

## Rollback Plan

1. Keep `portfolio_cash` table read-only during transition
2. Add feature flag to switch between old/new model
3. If issues arise, can revert code changes and use `portfolio_cash` again
4. Migration script should be idempotent and reversible








