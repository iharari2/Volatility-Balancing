# Remaining Implementation Tasks

Based on the wireframes, here's what still needs to be completed:

## ✅ Completed

1. **Global Layout** - TopBar and Sidebar on all pages
2. **Overview Page** - Summary cards, asset allocation chart, recent trades, trigger events
3. **Portfolios Page** - List view with 3-step creation wizard
4. **Trading Console** - State controls, cycle summary, orders tables
5. **Settings Page** - Tenant defaults and system settings

## ✅ All Tasks Completed!

### 1. ✅ Positions & Config Page Enhancements

**Status:** ✅ Complete

- [x] **Positions Tab:**
  - ✅ Added "Weight%" column (percentage of total portfolio)
  - ✅ Added "P&L" column with percentage
  - ✅ Added "Actions" column with [Adjust] and [Details] buttons
  - ✅ Added Cash row in table (showing cash balance, not a position)
  - ✅ Added "Export Positions Excel" button above table
- [x] **Cash & Limits Tab:**
  - ✅ Verified structure matches wireframe exactly
  - ✅ Guardrails section matches: Min Stock %, Max Stock %, Max Trade Size
- [x] **Strategy Config Tab:**
  - ✅ Added per-asset commission overrides table (as shown in wireframe)
  - ✅ Market hours section matches wireframe format (radio buttons)
- [x] **Dividends Tab:**
  - ✅ Implemented dividend management interface
  - ✅ Shows dividend history and upcoming dividends tables

### 2. ✅ Simulation Lab Page

**Status:** ✅ Complete Rewrite

- [x] **Left Panel - Simulation Setup:**
  - ✅ Asset dropdown selector
  - ✅ Date Range picker (start/end dates)
  - ✅ Strategy selection (Use Portfolio Config / Template / Custom Overrides)
  - ✅ Simulation Mode (Single Run / Parameter Sweep)
  - ✅ "Run Simulation" button
- [x] **Right Panel - Results:**
  - ✅ KPI cards: Final Value, Return, Max Drawdown, Volatility
  - ✅ Equity Curve Chart (using Recharts)
  - ✅ Price w/ Trigger Points Chart (using Recharts)
  - ✅ Trades table (Time, Action, Qty, Price, Commission)
  - ✅ Export buttons (Excel, JSON Logs)

### 3. ✅ Analytics & Reports Page

**Status:** ✅ Complete Rewrite

- [x] **KPI Cards (6 cards):**
  - ✅ Return
  - ✅ Volatility
  - ✅ Max Drawdown
  - ✅ Sharpe-like metric
  - ✅ Commission Total
  - ✅ Dividend Total
- [x] **Charts Section:**
  - ✅ Portfolio Value Over Time (line chart)
  - ✅ Stock Allocation Over Time (area chart)
  - ✅ Buy & Hold Comparison Line (comparison chart)
  - ✅ Rolling Returns Chart
- [x] **Export Button:**
  - ✅ "Export Full Analysis to Excel" button

### 4. ✅ Audit Trail Page

**Status:** ✅ Enhanced

- [x] **Left Panel - Filters:**
  - ✅ Asset dropdown (not just text input)
  - ✅ Date Range picker (start/end dates)
  - ✅ Trace ID search field
  - ✅ Source dropdown (Any / worker / manual / simulation)
- [x] **Right Panel - Trace List:**
  - ✅ Table with columns: Time, Asset, Summary, Trace ID
  - ✅ Summary shows brief description (e.g., "BUY 10 @ 196.4 (Allowed)")
  - ✅ Clickable rows to view timeline
- [x] **Timeline View (when trace selected):**
  - ✅ Expandable event list showing:
    - PriceEvent
    - TriggerEvaluated
    - GuardrailEvaluated
    - OrderCreated
    - ExecutionRecorded
    - PositionUpdated
  - ✅ Each event shows payload in expandable format
- [x] **Actions:**
  - ✅ "Export Trace JSON" button
  - ✅ "Copy Trace ID" button

## ✅ Implementation Status

### ✅ All High Priority Tasks Completed

1. ✅ **Positions Page** - All tabs complete, Positions table fully enhanced
2. ✅ **Simulation Lab** - Complete left/right panel layout with all features
3. ✅ **Analytics Page** - All KPI cards and charts implemented

### ✅ All Medium Priority Tasks Completed

4. ✅ **Audit Trail** - Enhanced filters and timeline view fully implemented
5. ✅ **Dividends Tab** - Full implementation complete

## Notes

- All pages should maintain the global layout (TopBar + Sidebar)
- All API calls should include `tenant_id` and `portfolio_id` from context
- Charts should use Recharts (already in dependencies)
- Export functionality should integrate with existing Excel export services
- All components should follow the wireframe structure exactly

## ✅ Implementation Complete

- ✅ **Positions Page Enhancements:** Complete
- ✅ **Simulation Lab Rewrite:** Complete
- ✅ **Analytics Page Rewrite:** Complete
- ✅ **Audit Trail Enhancements:** Complete
- ✅ **Total:** All tasks completed!

See `IMPLEMENTATION_COMPLETE.md` for detailed summary of all changes.
