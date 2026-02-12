# Trade Tracking Documentation

## Overview

This document defines a unified trade tracking view that allows users to understand the complete lifecycle of trading activity: from market price changes through trigger evaluation, guardrail checks, order submission, execution, and position impact.

---

## The Trade Lifecycle (Conceptual Flow)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        MARKET DATA ARRIVES                               │
│  • Price update (yfinance, broker, etc.)                                │
│  • OHLCV data captured                                                  │
└──────────────────────────────┬──────────────────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      TRIGGER EVALUATION                                  │
│  • Compare price to anchor: delta_pct = (price - anchor) / anchor       │
│  • Check thresholds: UP (e.g., +5%), DOWN (e.g., -5%)                   │
│  • Result: FIRED (BUY/SELL direction) or NO_TRIGGER                     │
└──────────────────────────────┬──────────────────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      GUARDRAIL EVALUATION                                │
│  • Allocation limits: min_stock_pct ≤ stock% ≤ max_stock_pct            │
│  • Cash sufficiency for BUY                                             │
│  • Daily order cap check                                                │
│  • Result: ALLOWED + trade_intent OR BLOCKED + reason                   │
└──────────────────────────────┬──────────────────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      ACTION DECISION                                     │
│  • BUY: Trigger fired UP, guardrails passed → submit buy order          │
│  • SELL: Trigger fired DOWN, guardrails passed → submit sell order      │
│  • HOLD: No trigger fired                                               │
│  • SKIP: Trigger fired but guardrails blocked                           │
└──────────────────────────────┬──────────────────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      ORDER SUBMISSION (if BUY/SELL)                      │
│  • Create internal Order record                                         │
│  • Submit to broker                                                     │
│  • Status: created → submitted → pending → working                      │
└──────────────────────────────┬──────────────────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      ORDER EXECUTION                                     │
│  • Broker fills order (market order = immediate)                        │
│  • Create Trade/Fill record                                             │
│  • Status: working → partial → filled                                   │
│  • OR: rejected / cancelled                                             │
└──────────────────────────────┬──────────────────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      POSITION IMPACT                                     │
│  • Update qty: qty ± fill_qty                                           │
│  • Update cash: cash ∓ (fill_qty × price) - commission                  │
│  • Update anchor (optional): reset to new price after trade             │
│  • Update totals: total_commission_paid, value metrics                  │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Unified Trade Tracking Table Design

### Goal
A single table view that shows **one row per evaluation** with all relevant data from each stage, enabling users to:
1. See the complete story for each evaluation point
2. Filter by action type (BUY, SELL, HOLD, SKIP)
3. Understand why a decision was made
4. Track order lifecycle from submission to fill
5. See the impact on position state

### Proposed Column Groups

#### Group 1: Time & Identity
| Column | Type | Description |
|--------|------|-------------|
| `timestamp` | DateTime | When the evaluation occurred |
| `date` | Date | Date only (for daily grouping) |
| `position_id` | String | Position being evaluated |
| `symbol` | String | Asset ticker (e.g., VOO) |
| `mode` | Enum | LIVE or SIMULATION |
| `trace_id` | String | Correlates related events |

#### Group 2: Market Data
| Column | Type | Description |
|--------|------|-------------|
| `price` | Float | Effective price used for evaluation |
| `open` | Float | Day's open price |
| `high` | Float | Day's high price |
| `low` | Float | Day's low price |
| `close` | Float | Day's close price |
| `volume` | Integer | Trading volume |

#### Group 3: Trigger Evaluation
| Column | Type | Description |
|--------|------|-------------|
| `anchor_price` | Float | Current volatility anchor |
| `delta_pct` | Float | % change from anchor: `(price - anchor) / anchor × 100` |
| `trigger_up_threshold` | Float | Upper threshold (e.g., 5.0 = +5%) |
| `trigger_down_threshold` | Float | Lower threshold (e.g., -5.0 = -5%) |
| `trigger_fired` | Boolean | Did price cross a threshold? |
| `trigger_direction` | Enum | UP, DOWN, or NONE |
| `trigger_reason` | Text | Human explanation: "Price +6.2% above anchor (threshold +5%)" |

#### Group 4: Guardrail Evaluation
| Column | Type | Description |
|--------|------|-------------|
| `min_stock_pct` | Float | Minimum allowed stock allocation (e.g., 20%) |
| `max_stock_pct` | Float | Maximum allowed stock allocation (e.g., 80%) |
| `current_stock_pct` | Float | Stock % before potential trade |
| `guardrail_allowed` | Boolean | Would trade pass guardrails? |
| `guardrail_block_reason` | Text | If blocked: "Already at max allocation 80%" |

#### Group 5: Action Decision
| Column | Type | Description |
|--------|------|-------------|
| `action` | Enum | **BUY**, **SELL**, **HOLD**, **SKIP** |
| `action_reason` | Text | Full explanation of decision |
| `intended_qty` | Float | Shares intended to trade (if BUY/SELL) |
| `intended_value` | Float | Notional value of intended trade |

**Action Meanings:**
- **BUY**: Trigger fired UP + guardrails passed → order submitted
- **SELL**: Trigger fired DOWN + guardrails passed → order submitted
- **HOLD**: No trigger fired (price within band)
- **SKIP**: Trigger fired but guardrails blocked the trade

#### Group 6: Order Status
| Column | Type | Description |
|--------|------|-------------|
| `order_id` | String | Internal order ID (null if HOLD/SKIP) |
| `order_status` | Enum | created, submitted, pending, working, partial, **filled**, rejected, cancelled |
| `broker_order_id` | String | Broker's order identifier |
| `broker_status` | String | Broker's status string |
| `submitted_at` | DateTime | When order was sent to broker |
| `rejection_reason` | Text | If rejected: why |

#### Group 7: Execution Details
| Column | Type | Description |
|--------|------|-------------|
| `fill_qty` | Float | Total shares executed (cumulative across all fills) |
| `avg_fill_price` | Float | Weighted average execution price |
| `fill_value` | Float | fill_qty × avg_fill_price |
| `commission` | Float | Total commission charged (all fills) |
| `executed_at` | DateTime | When last fill occurred |
| `execution_status` | Enum | FILLED, PARTIAL, NONE |
| `fill_count` | Integer | Number of fills (1 for market orders, potentially >1 for limit) |

**Partial Fill Detail (Expandable Sub-rows)**

When `fill_count > 1`, user can expand to see individual fills:
| Column | Type | Description |
|--------|------|-------------|
| `fill_id` | String | Individual fill identifier |
| `fill_seq` | Integer | Fill sequence (1, 2, 3...) |
| `partial_qty` | Float | Shares in this fill |
| `partial_price` | Float | Execution price for this fill |
| `partial_commission` | Float | Commission for this fill |
| `partial_executed_at` | DateTime | When this fill occurred |

#### Group 8: Position Impact (Before → After)
| Column | Type | Description |
|--------|------|-------------|
| `qty_before` | Float | Shares before this evaluation |
| `qty_after` | Float | Shares after (if executed) |
| `cash_before` | Float | Cash before |
| `cash_after` | Float | Cash after (includes commission deduction) |
| `stock_value_before` | Float | qty_before × price |
| `stock_value_after` | Float | qty_after × price |
| `total_value_before` | Float | stock_value + cash before |
| `total_value_after` | Float | stock_value + cash after |
| `stock_pct_before` | Float | Allocation % before |
| `stock_pct_after` | Float | Allocation % after |

#### Group 9: Returns & Performance
| Column | Type | Description |
|--------|------|-------------|
| `return_since_anchor` | Float | % return since anchor was set: `(price - anchor) / anchor × 100` |
| `return_since_start` | Float | % return since position inception |
| `daily_return` | Float | % change from previous day's close |
| `cumulative_return` | Float | Total % return since position start |

#### Group 10: Dividend Events
| Column | Type | Description |
|--------|------|-------------|
| `dividend_declared` | Boolean | Was a dividend declared on this date? |
| `dividend_ex_date` | Date | Ex-dividend date |
| `dividend_pay_date` | Date | Payment date |
| `dividend_rate` | Float | Dividend per share |
| `dividend_gross` | Float | Gross dividend: qty × rate |
| `dividend_tax` | Float | Withholding tax amount |
| `dividend_net` | Float | Net dividend received (added to cash) |
| `dividend_applied` | Boolean | Has dividend been credited to position? |

#### Group 11: Anchor Tracking
| Column | Type | Description |
|--------|------|-------------|
| `anchor_reset` | Boolean | Was anchor reset on this evaluation? |
| `anchor_old_value` | Float | Previous anchor before reset |
| `anchor_reset_reason` | Text | Why anchor was reset (e.g., "Post-trade reset", "Manual reset") |

---

## Example Rows

### Example 1: Trigger Fired → BUY Executed
```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ TIMESTAMP          │ 2026-02-05 14:30:00                                               │
│ SYMBOL             │ VOO                                                               │
│ MODE               │ LIVE                                                              │
├────────────────────┼──────────────────────────────────────────────────────────────────┤
│ PRICE              │ $478.50                                                           │
│ ANCHOR             │ $455.00                                                           │
│ DELTA %            │ +5.16%                                                            │
├────────────────────┼──────────────────────────────────────────────────────────────────┤
│ TRIGGER THRESHOLD  │ ±5.0%                                                             │
│ TRIGGER FIRED      │ YES                                                               │
│ TRIGGER DIRECTION  │ UP (price above anchor)                                           │
│ TRIGGER REASON     │ "Price $478.50 is +5.16% above anchor $455.00 (threshold: +5%)"  │
├────────────────────┼──────────────────────────────────────────────────────────────────┤
│ GUARDRAIL MIN/MAX  │ 20% / 80%                                                         │
│ CURRENT STOCK %    │ 45%                                                               │
│ GUARDRAIL ALLOWED  │ YES                                                               │
│ BLOCK REASON       │ (none)                                                            │
├────────────────────┼──────────────────────────────────────────────────────────────────┤
│ ACTION             │ BUY                                                               │
│ ACTION REASON      │ "Buy triggered: rebalance to target 80% allocation"              │
│ INTENDED QTY       │ 15.5 shares                                                       │
├────────────────────┼──────────────────────────────────────────────────────────────────┤
│ ORDER ID           │ ord_abc123                                                        │
│ ORDER STATUS       │ filled                                                            │
│ BROKER ORDER ID    │ APCA-12345                                                        │
├────────────────────┼──────────────────────────────────────────────────────────────────┤
│ FILL QTY           │ 15.5 shares                                                       │
│ FILL PRICE         │ $478.52                                                           │
│ COMMISSION         │ $0.74                                                             │
│ EXECUTED AT        │ 2026-02-05 14:30:02                                               │
├────────────────────┼──────────────────────────────────────────────────────────────────┤
│ POSITION BEFORE    │ 50.0 shares, $9,500 cash, $22,925 stock, $32,425 total (70.7%)   │
│ POSITION AFTER     │ 65.5 shares, $2,081.90 cash, $31,343.06 stock, $33,424.96 (93.8%)│
└────────────────────────────────────────────────────────────────────────────────────────┘
```

### Example 2: Trigger Fired → SKIP (Guardrail Blocked)
```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ TIMESTAMP          │ 2026-02-05 15:00:00                                               │
│ SYMBOL             │ VOO                                                               │
│ MODE               │ LIVE                                                              │
├────────────────────┼──────────────────────────────────────────────────────────────────┤
│ PRICE              │ $482.00                                                           │
│ ANCHOR             │ $455.00                                                           │
│ DELTA %            │ +5.93%                                                            │
├────────────────────┼──────────────────────────────────────────────────────────────────┤
│ TRIGGER FIRED      │ YES                                                               │
│ TRIGGER DIRECTION  │ UP                                                                │
│ TRIGGER REASON     │ "Price $482.00 is +5.93% above anchor $455.00"                   │
├────────────────────┼──────────────────────────────────────────────────────────────────┤
│ GUARDRAIL MIN/MAX  │ 20% / 80%                                                         │
│ CURRENT STOCK %    │ 93.8%                                                             │
│ GUARDRAIL ALLOWED  │ NO                                                                │
│ BLOCK REASON       │ "Already at 93.8% stock allocation, exceeds max 80%"             │
├────────────────────┼──────────────────────────────────────────────────────────────────┤
│ ACTION             │ SKIP                                                              │
│ ACTION REASON      │ "Trigger fired but guardrail blocked: allocation at max"         │
│ INTENDED QTY       │ (none)                                                            │
├────────────────────┼──────────────────────────────────────────────────────────────────┤
│ ORDER ID           │ (none)                                                            │
│ ORDER STATUS       │ (none)                                                            │
├────────────────────┼──────────────────────────────────────────────────────────────────┤
│ FILL QTY           │ (none)                                                            │
│ EXECUTION STATUS   │ NONE                                                              │
├────────────────────┼──────────────────────────────────────────────────────────────────┤
│ POSITION BEFORE    │ 65.5 shares, $2,081.90 cash, $31,571.00 stock, $33,652.90 (93.8%)│
│ POSITION AFTER     │ (no change)                                                       │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

### Example 3: No Trigger → HOLD
```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ TIMESTAMP          │ 2026-02-05 16:00:00                                               │
│ SYMBOL             │ VOO                                                               │
│ MODE               │ LIVE                                                              │
├────────────────────┼──────────────────────────────────────────────────────────────────┤
│ PRICE              │ $460.00                                                           │
│ ANCHOR             │ $455.00                                                           │
│ DELTA %            │ +1.10%                                                            │
├────────────────────┼──────────────────────────────────────────────────────────────────┤
│ TRIGGER THRESHOLD  │ ±5.0%                                                             │
│ TRIGGER FIRED      │ NO                                                                │
│ TRIGGER DIRECTION  │ NONE                                                              │
│ TRIGGER REASON     │ "Price within band: +1.10% (threshold ±5%)"                       │
├────────────────────┼──────────────────────────────────────────────────────────────────┤
│ GUARDRAIL ALLOWED  │ (not evaluated - no trigger)                                      │
├────────────────────┼──────────────────────────────────────────────────────────────────┤
│ ACTION             │ HOLD                                                              │
│ ACTION REASON      │ "No trigger - price inside volatility band"                       │
├────────────────────┼──────────────────────────────────────────────────────────────────┤
│ ORDER ID           │ (none)                                                            │
│ EXECUTION STATUS   │ NONE                                                              │
├────────────────────┼──────────────────────────────────────────────────────────────────┤
│ POSITION           │ 65.5 shares, $2,081.90 cash (no change)                          │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

### Example 4: Dividend Received
```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ TIMESTAMP          │ 2026-03-15 09:30:00 (Pay Date)                                    │
│ SYMBOL             │ VOO                                                               │
│ MODE               │ LIVE                                                              │
├────────────────────┼──────────────────────────────────────────────────────────────────┤
│ PRICE              │ $465.00                                                           │
│ DELTA %            │ +2.20% (within band)                                              │
├────────────────────┼──────────────────────────────────────────────────────────────────┤
│ TRIGGER FIRED      │ NO                                                                │
│ ACTION             │ HOLD                                                              │
├────────────────────┼──────────────────────────────────────────────────────────────────┤
│ DIVIDEND DECLARED  │ YES                                                               │
│ EX-DATE            │ 2026-03-12                                                        │
│ PAY DATE           │ 2026-03-15                                                        │
│ DIVIDEND RATE      │ $1.75/share                                                       │
│ GROSS DIVIDEND     │ $114.63 (65.5 x $1.75)                                            │
│ WITHHOLDING TAX    │ $28.66 (25%)                                                      │
│ NET DIVIDEND       │ $85.97                                                            │
│ APPLIED            │ YES                                                               │
├────────────────────┼──────────────────────────────────────────────────────────────────┤
│ CASH BEFORE        │ $2,081.90                                                         │
│ CASH AFTER         │ $2,167.87 (+$85.97)                                              │
│ TOTAL VALUE        │ $32,629.37 (+$85.97)                                             │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

### Example 5: Anchor Reset After Trade
```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ TIMESTAMP          │ 2026-02-06 10:00:00                                               │
│ SYMBOL             │ VOO                                                               │
│ MODE               │ LIVE                                                              │
├────────────────────┼──────────────────────────────────────────────────────────────────┤
│ PRICE              │ $480.00                                                           │
│ ANCHOR (before)    │ $455.00                                                           │
│ DELTA %            │ +5.49%                                                            │
├────────────────────┼──────────────────────────────────────────────────────────────────┤
│ TRIGGER FIRED      │ YES (UP)                                                          │
│ ACTION             │ BUY                                                               │
│ FILL QTY           │ 5.0 shares @ $480.02                                              │
├────────────────────┼──────────────────────────────────────────────────────────────────┤
│ ANCHOR RESET       │ YES                                                               │
│ ANCHOR OLD VALUE   │ $455.00                                                           │
│ ANCHOR NEW VALUE   │ $480.02                                                           │
│ RESET REASON       │ "Post-trade anchor reset to fill price"                          │
├────────────────────┼──────────────────────────────────────────────────────────────────┤
│ RETURNS                                                                                │
│ Return since anchor│ +5.49% (based on old anchor)                                      │
│ Return since start │ +12.3%                                                            │
│ Daily return       │ +0.8%                                                             │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

### Example 6: Order with Multiple Partial Fills (Expandable)
```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ TIMESTAMP          │ 2026-02-07 11:00:00                                               │
│ ACTION             │ SELL                                                              │
├────────────────────┼──────────────────────────────────────────────────────────────────┤
│ ORDER ID           │ ord_xyz789                                                        │
│ ORDER STATUS       │ filled                                                            │
│ FILL COUNT         │ 3                                                [Expand]         │
│ TOTAL FILL QTY     │ 10.0 shares                                                       │
│ AVG FILL PRICE     │ $475.50                                                           │
│ TOTAL COMMISSION   │ $0.48                                                             │
├────────────────────┼──────────────────────────────────────────────────────────────────┤
│ FILL DETAILS (Expanded)                                                                │
│ ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│ │ Fill #1 │ 4.0 shares @ $475.40 │ $0.19 commission │ 11:00:01                    │   │
│ │ Fill #2 │ 3.5 shares @ $475.55 │ $0.17 commission │ 11:00:03                    │   │
│ │ Fill #3 │ 2.5 shares @ $475.60 │ $0.12 commission │ 11:00:05                    │   │
│ └─────────────────────────────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Table Filtering & Aggregation

### Default View: Daily Aggregation
- **Days with actions (BUY/SELL/SKIP)**: Show all action rows
- **Days without actions (HOLD only)**: Show 1 summary row

### Filters Available
| Filter | Options |
|--------|---------|
| **Action** | BUY, SELL, HOLD, SKIP (multi-select) |
| **Date Range** | Start date → End date |
| **Mode** | LIVE, SIMULATION |
| **Order Status** | filled, rejected, pending, etc. |

### Default Filter Suggestion
For most users: **BUY, SELL, SKIP** (hide HOLD rows to focus on meaningful events)

---

## Comparison: Events vs Explainability vs Unified View

| Aspect | Events Table | Explainability | Unified Trade Tracking |
|--------|--------------|----------------|------------------------|
| **Purpose** | Raw audit trail | UI display DTO | Complete lifecycle view |
| **Granularity** | Per-event (many per evaluation) | Per-evaluation | Per-evaluation |
| **Order tracking** | Separate events | Execution fields only | Full order lifecycle |
| **Trigger detail** | In payload JSON | Summary fields | Dedicated columns |
| **Guardrail detail** | In payload JSON | allowed + reason | Dedicated columns |
| **Position impact** | Separate event | Before/after | Before/after with delta |
| **Queryable** | Hard (JSON parsing) | Medium | Easy (flat columns) |

---

## Data Source Mapping

The unified view pulls from:

| Column Group | Primary Source |
|--------------|----------------|
| Time & Identity | `PositionEvaluationTimeline` |
| Market Data | `PositionEvaluationTimeline` (OHLCV fields) |
| Trigger Evaluation | `PositionEvaluationTimeline` (trigger_* fields) |
| Guardrail Evaluation | `PositionEvaluationTimeline` (guardrail_* fields) |
| Action Decision | `PositionEvaluationTimeline` (action, trade_intent_*) |
| Order Status | `Order` entity (joined by order_id) |
| Execution Details | `Trade` entity (joined by order_id) |
| Position Impact | `PositionEvaluationTimeline` (qty/cash before/after) |

---

## Design Decisions (Confirmed)

| Question | Decision |
|----------|----------|
| **Dividends** | Include in unified view with full detail (Group 10) |
| **Partial fills** | Summary in main row + expandable sub-rows for individual fills |
| **Anchor resets** | Explicit tracking with old value and reset reason (Group 11) |
| **Performance metrics** | Include returns: since anchor, since start, daily, cumulative (Group 9) |

---

## Complete Column Summary

The unified table has **11 column groups** with approximately **55+ fields**:

| Group | Columns | Purpose |
|-------|---------|---------|
| 1. Time & Identity | 6 | When, what position, correlation |
| 2. Market Data | 6 | OHLCV + effective price |
| 3. Trigger Evaluation | 7 | Anchor comparison, thresholds, fired status |
| 4. Guardrail Evaluation | 5 | Allocation limits, allowed/blocked |
| 5. Action Decision | 4 | BUY/SELL/HOLD/SKIP + reason |
| 6. Order Status | 6 | Internal + broker order tracking |
| 7. Execution Details | 7+ | Fills with expandable partial detail |
| 8. Position Impact | 10 | Before/after qty, cash, value, allocation |
| 9. Returns | 4 | Performance metrics |
| 10. Dividends | 8 | Dividend tracking |
| 11. Anchor Tracking | 3 | Reset events |

---

## Next Steps (When Ready to Implement)

1. Create a SQL view or API endpoint that joins the data sources
2. Update frontend ExplainabilityTab to use the new unified structure
3. Add filtering controls for action types and date range
4. Consider adding export functionality (CSV/Excel)
