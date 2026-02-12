# Use Cases

Detailed user flows for the Volatility-Balancing application.

## Table of Contents

1. [Portfolio Management](#1-portfolio-management)
2. [Position Management](#2-position-management)
3. [Trading](#3-trading)
4. [Simulation](#4-simulation)
5. [Analysis & Reporting](#5-analysis--reporting)
6. [Dividends](#6-dividends)

---

## 1. Portfolio Management

### UC1.1: Create Portfolio

**Actor:** User
**Goal:** Create a new portfolio to organize positions

**Flow:**
```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐     ┌──────────────┐
│ Portfolios  │────▶│ Click Create │────▶│ Enter Name  │────▶│ Set Initial  │
│ Page        │     │ Portfolio    │     │ Description │     │ Cash         │
└─────────────┘     └──────────────┘     └─────────────┘     └──────┬───────┘
                                                                    │
                    ┌──────────────┐     ┌─────────────┐            │
                    │ Portfolio    │◀────│ Configure   │◀───────────┘
                    │ Created      │     │ Strategy    │
                    └──────────────┘     └─────────────┘
```

**Steps:**
1. Navigate to Portfolios page
2. Click "Create Portfolio" button
3. Enter portfolio name and description
4. Set starting cash amount
5. Configure default strategy parameters (triggers, guardrails)
6. Click "Create"
7. System creates portfolio and redirects to portfolio dashboard

**Validation:**
- Name is required
- Starting cash must be > 0

---

### UC1.2: Delete Portfolio

**Actor:** User
**Goal:** Remove a portfolio and its positions

**Preconditions:**
- Portfolio exists
- No active trades in progress

**Flow:**
1. Navigate to Portfolios page
2. Click delete icon on portfolio card
3. Confirm deletion in dialog
4. System deletes portfolio and all associated positions
5. User sees updated portfolio list

**Business Rules:**
- Deletion is permanent (no soft delete)
- All positions within portfolio are also deleted

---

## 2. Position Management

### UC2.1: Create Position

**Actor:** User
**Goal:** Add a new position (stock + cash) to a portfolio

**Flow:**
```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐     ┌──────────────┐
│ Positions   │────▶│ Click Add    │────▶│ Enter       │────▶│ Enter Qty or │
│ Page        │     │ Position     │     │ Ticker      │     │ Dollar Amount│
└─────────────┘     └──────────────┘     └─────────────┘     └──────┬───────┘
                                                                    │
                    ┌──────────────┐     ┌─────────────┐            │
                    │ Position     │◀────│ Set Anchor  │◀───────────┘
                    │ Created      │     │ Price       │
                    └──────────────┘     └─────────────┘
```

**Steps:**
1. Navigate to Portfolio > Positions tab
2. Click "Add Position"
3. Enter stock ticker (e.g., AAPL)
4. System fetches current market price
5. Enter quantity OR dollar amount to invest
6. Allocate cash for this position
7. Set anchor price (defaults to current market price)
8. Click "Create"
9. Position appears in list with PAUSED status

**Validation:**
- Ticker must be valid (market data available)
- Cash allocation must not exceed portfolio cash
- Quantity must be > 0

**Post-conditions:**
- Position created with status PAUSED
- Anchor price set
- Cash deducted from portfolio

---

### UC2.2: Start Trading

**Actor:** User
**Goal:** Enable automated trading for a position

**Preconditions:**
- Position exists
- Anchor price is set
- Position has cash allocated

**Flow:**
1. Navigate to Position detail or Positions list
2. Click "Start Trading" button
3. System validates position is ready
4. Position status changes to ACTIVE
5. Trading worker begins monitoring position

**Business Rules:**
- Position must have anchor price set
- Position must have sufficient cash for at least one trade

---

### UC2.3: Adjust Position Cash

**Actor:** User
**Goal:** Add or withdraw cash from a position

**Flow:**
```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│ Position    │────▶│ Click Deposit│────▶│ Enter       │────▶ Cash Updated
│ Detail      │     │ or Withdraw  │     │ Amount      │
└─────────────┘     └──────────────┘     └─────────────┘
```

**Validation:**
- Deposit: Amount must be available in portfolio
- Withdraw: Amount must not exceed position cash

---

## 3. Trading

### UC3.1: Manual Trade Execution

**Actor:** User
**Goal:** Manually trigger a position evaluation and potential trade

**Flow:**
```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐     ┌──────────────┐
│ Trading     │────▶│ Click Run    │────▶│ System      │────▶│ If Trigger:  │
│ Console     │     │ Manual Cycle │     │ Evaluates   │     │ Execute Trade│
└─────────────┘     └──────────────┘     └─────────────┘     └──────┬───────┘
                                                                    │
                                         ┌─────────────┐            │
                                         │ Log Event   │◀───────────┘
                                         │ to Timeline │
                                         └─────────────┘
```

**Steps:**
1. Navigate to Trading Console
2. Click "Run Manual Cycle"
3. System fetches current market price for all active positions
4. For each position:
   - Calculate price change from anchor
   - Check if trigger threshold exceeded
   - If triggered, calculate order size using formula
   - Apply guardrails (min/max allocation)
   - Execute trade if valid
5. Display results in Activity Log

---

### UC3.2: Automated Trading Cycle

**Actor:** Trading Worker (automated)
**Goal:** Continuously monitor and trade positions

**Flow:**
```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│ Worker      │────▶│ Fetch Market │────▶│ Evaluate    │
│ Timer Fires │     │ Prices       │     │ Each Pos    │
└─────────────┘     └──────────────┘     └──────┬──────┘
       ▲                                        │
       │           ┌──────────────┐     ┌───────▼──────┐
       │           │ Log to       │◀────│ Execute      │
       └───────────│ Audit Trail  │     │ Trades       │
                   └──────────────┘     └──────────────┘
```

**Business Rules:**
- Worker runs at configurable interval (default 60s)
- Only evaluates ACTIVE positions
- Respects market hours policy (open only vs. after hours)
- Each decision logged to audit trail

---

### UC3.3: Trade Decision Flow

**Actor:** System
**Goal:** Determine if a trade should execute

```
                    ┌─────────────────┐
                    │ Get Current     │
                    │ Market Price    │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │ Calculate %     │
                    │ Change from     │
                    │ Anchor          │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
     ┌────────▼───────┐      │     ┌────────▼────────┐
     │ Price Down     │      │     │ Price Up        │
     │ > Threshold?   │      │     │ > Threshold?    │
     └────────┬───────┘      │     └────────┬────────┘
              │              │              │
         YES  │         NO   │         YES  │
              │              │              │
     ┌────────▼───────┐      │     ┌────────▼────────┐
     │ BUY Trigger    │      │     │ SELL Trigger    │
     └────────┬───────┘      │     └────────┬────────┘
              │              │              │
              └──────────────┼──────────────┘
                             │
                    ┌────────▼────────┐
                    │ Calculate Order │
                    │ Size (Formula)  │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │ Apply Guardrails│
                    │ (Min/Max Alloc) │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
     ┌────────▼───────┐      │     ┌────────▼────────┐
     │ Valid Order?   │      │     │ Blocked by      │
     │ Execute Trade  │      │     │ Guardrail       │
     └────────────────┘      │     └─────────────────┘
                             │
                    ┌────────▼────────┐
                    │ No Trigger      │
                    │ HOLD            │
                    └─────────────────┘
```

---

## 4. Simulation

### UC4.1: Run Backtest Simulation

**Actor:** User
**Goal:** Test trading strategy on historical data

**Flow:**
```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐     ┌──────────────┐
│ Simulation  │────▶│ Select       │────▶│ Choose Date │────▶│ Configure    │
│ Lab         │     │ Ticker       │     │ Range       │     │ Parameters   │
└─────────────┘     └──────────────┘     └─────────────┘     └──────┬───────┘
                                                                    │
┌─────────────┐     ┌──────────────┐     ┌─────────────┐            │
│ Export to   │◀────│ View Results │◀────│ Run         │◀───────────┘
│ Excel       │     │ & Metrics    │     │ Simulation  │
└─────────────┘     └──────────────┘     └─────────────┘
```

**Steps:**
1. Navigate to Simulation Lab
2. Select ticker symbol
3. Choose date range (start and end dates)
4. Select resolution (1min, 5min, 15min, 30min, 1hour, daily)
5. Configure:
   - Initial cash
   - Trigger thresholds (up/down %)
   - Guardrails (min/max stock %)
6. Click "Run Simulation"
7. View progress bar
8. View results:
   - Total return vs. buy-and-hold
   - Number of trades
   - P&L chart over time
   - Trade-by-trade log
9. Optionally export to Excel

**Validation:**
- End date must be after start date
- Dates must be in the past
- Valid ticker with historical data

---

### UC4.2: Compare Simulation to Buy-and-Hold

**Actor:** User
**Goal:** Evaluate if strategy beats passive holding

**Output Metrics:**
- Strategy Total Return %
- Buy-and-Hold Return %
- Alpha (Strategy - Buy-and-Hold)
- Max Drawdown
- Sharpe Ratio
- Number of Trades

---

## 5. Analysis & Reporting

### UC5.1: View Position Cockpit

**Actor:** User
**Goal:** Monitor real-time position status and recent activity

**Flow:**
1. Navigate to Position Cockpit
2. View:
   - Current market data (price, OHLC)
   - Position state (qty, cash, allocation %)
   - Anchor price and distance to triggers
   - Recent activity table
   - P&L vs. buy-and-hold

---

### UC5.2: Export to Excel

**Actor:** User
**Goal:** Download position/simulation data for external analysis

**Flow:**
1. Navigate to relevant page (Positions, Simulation, Analytics)
2. Click "Export" button
3. Select export format (Excel)
4. System generates file with:
   - Summary sheet
   - Timeline/trade log sheet
   - Configuration sheet
5. File downloads automatically

---

### UC5.3: View Audit Trail

**Actor:** User
**Goal:** Review all trading decisions and their reasoning

**Flow:**
1. Navigate to Audit Trail page
2. Filter by:
   - Position/Asset
   - Date range
   - Event type (trigger, trade, dividend)
   - Trace ID
3. Expand event to see:
   - Input parameters
   - Calculation details
   - Output/decision
4. Copy trace ID for debugging

---

### UC5.4: Generate Portfolio Report

**Actor:** User
**Goal:** Generate comprehensive portfolio performance report

**Flow:**
```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐     ┌──────────────┐
│ Analytics   │────▶│ Select       │────▶│ Choose Date │────▶│ Generate     │
│ Page        │     │ Portfolio    │     │ Range       │     │ Report       │
└─────────────┘     └──────────────┘     └─────────────┘     └──────┬───────┘
                                                                    │
                    ┌──────────────┐     ┌─────────────┐            │
                    │ Download     │◀────│ View Report │◀───────────┘
                    │ PDF/Excel    │     │ Preview     │
                    └──────────────┘     └─────────────┘
```

**Report Contents:**

| Section | Data Included |
|---------|---------------|
| **Summary** | Total value, P&L, return %, period |
| **Performance** | Return vs. benchmark, alpha, Sharpe ratio |
| **Positions** | Per-position breakdown, allocation % |
| **Trades** | Trade history, commission total |
| **Dividends** | Dividend income, tax withheld |
| **Risk Metrics** | Max drawdown, volatility |

**Export Formats:**
- Excel (.xlsx) - Full data with multiple sheets
- PDF - Formatted report for sharing

---

### UC5.5: View Position Performance

**Actor:** User
**Goal:** Analyze individual position performance over time

**Flow:**
1. Navigate to Position Detail page
2. Select date range for analysis
3. View:
   - P&L chart (absolute and %)
   - Position return vs. stock return (buy-and-hold)
   - Alpha generated
   - Trade markers on chart
   - Dividend events
4. Export position-specific report

**Metrics Displayed:**

| Metric | Description |
|--------|-------------|
| Position Return | Total return including trades |
| Stock Return | Buy-and-hold return for comparison |
| Alpha | Position Return - Stock Return |
| Trade Count | Number of executed trades |
| Win Rate | % of profitable trades |
| Avg Trade P&L | Average profit/loss per trade |
| Total Commission | Sum of all commissions paid |
| Dividend Income | Net dividends received |

---

## 6. Dividends

### UC6.1: Process Ex-Dividend Date

**Actor:** System (automated) or User (manual)
**Goal:** Handle ex-dividend date for a position

**Flow:**
```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐     ┌──────────────┐
│ Ex-Dividend │────▶│ Adjust       │────▶│ Create      │────▶│ Update       │
│ Date        │     │ Anchor Price │     │ Receivable  │     │ Position     │
└─────────────┘     └──────────────┘     └─────────────┘     └──────────────┘
```

**Steps:**
1. System detects ex-dividend date (from market data or manual input)
2. For each affected position:
   - **Adjust anchor price**: `new_anchor = old_anchor - dividend_per_share`
   - Calculate dividend amounts:
     - `gross_amount = shares_held × dividend_per_share`
     - `withholding_tax = gross_amount × tax_rate`
     - `net_amount = gross_amount - withholding_tax`
   - Create DividendReceivable record (status: PENDING)
   - Update `position.dividend_receivable += net_amount`
3. Log event to audit trail

**Why Anchor Adjustment?**
```
Without adjustment:
  Day before ex-div: Price = $100, Anchor = $100 (no trigger)
  Ex-div day:        Price = $98 (market drops by $2 dividend)
                     Anchor = $100 → -2% change → FALSE BUY TRIGGER

With adjustment:
  Ex-div day:        Price = $98
                     Anchor = $98 (adjusted down by $2)
                     → 0% change → No false trigger (correct!)
```

**Business Rules:**
- Anchor adjustment is automatic and mandatory
- Prevents false buy triggers from dividend-related price drops
- Dividend receivable is tracked separately from cash

---

### UC6.2: Process Dividend Payment

**Actor:** System (automated) or User (manual)
**Goal:** Credit dividend payment to position cash

**Flow:**
```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐     ┌──────────────┐
│ Payment     │────▶│ Find Pending │────▶│ Credit Net  │────▶│ Update       │
│ Date        │     │ Receivable   │     │ to Cash     │     │ Totals       │
└─────────────┘     └──────────────┘     └─────────────┘     └──────────────┘
```

**Steps:**
1. System detects payment date (or user triggers manually)
2. Find DividendReceivable with status PENDING
3. Process payment:
   - `position.cash += receivable.net_amount`
   - `position.dividend_receivable -= receivable.net_amount`
   - `position.total_dividends_received += receivable.net_amount`
   - `receivable.status = PAID`
   - `receivable.paid_at = now()`
4. Log event to audit trail

**Business Rules:**
- Only net amount (after tax) is credited to cash
- Withholding tax is tracked for reporting
- Payment typically occurs ~30 days after ex-dividend date

---

### UC6.3: View Dividend History

**Actor:** User
**Goal:** Review all dividend activity for a position or portfolio

**Flow:**
1. Navigate to Position Detail > Dividends tab
2. View dividend history table:

| Date | Type | Gross | Tax | Net | Status |
|------|------|-------|-----|-----|--------|
| 2024-01-15 | Ex-Dividend | $200.00 | $50.00 | $150.00 | Pending |
| 2024-01-10 | Payment | - | - | $145.00 | Paid |
| 2023-10-15 | Ex-Dividend | $190.00 | $47.50 | $142.50 | Paid |

3. View summary metrics:
   - Total dividends received (YTD)
   - Total withholding tax paid
   - Pending receivables
   - Dividend yield %

---

### UC6.4: Dividend Flow Diagram

**Complete Dividend Lifecycle:**

```
                         ANNOUNCEMENT
                              │
                              ▼
                    ┌─────────────────┐
                    │ Dividend        │
                    │ Announced       │
                    │ (ex_date,       │
                    │  pay_date, dps) │
                    └────────┬────────┘
                             │
            ─────────────────┼───────────────── EX-DIVIDEND DATE
                             │
                             ▼
                    ┌─────────────────┐
                    │ 1. Adjust       │
                    │    Anchor Price │
                    │    (-dps)       │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ 2. Create       │
                    │    Receivable   │
                    │    (PENDING)    │
                    │                 │
                    │ gross = qty×dps │
                    │ tax = gross×25% │
                    │ net = gross-tax │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ 3. Update       │
                    │    Position     │
                    │    .dividend_   │
                    │    receivable   │
                    └────────┬────────┘
                             │
            ─────────────────┼───────────────── PAYMENT DATE (~30 days)
                             │
                             ▼
                    ┌─────────────────┐
                    │ 4. Credit Cash  │
                    │    += net_amt   │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ 5. Clear        │
                    │    Receivable   │
                    │    (PAID)       │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ 6. Update       │
                    │    Totals       │
                    │    total_div_   │
                    │    received     │
                    └─────────────────┘
```

---

## Use Case Matrix

| Use Case | Actor | Priority | Status |
|----------|-------|----------|--------|
| UC1.1 Create Portfolio | User | High | Implemented |
| UC1.2 Delete Portfolio | User | Medium | Implemented |
| UC2.1 Create Position | User | High | Implemented |
| UC2.2 Start Trading | User | High | Implemented |
| UC2.3 Adjust Cash | User | Medium | Implemented |
| UC3.1 Manual Trade | User | High | Implemented |
| UC3.2 Auto Trading | System | High | Implemented |
| UC3.3 Trade Decision | System | High | Implemented |
| UC4.1 Run Simulation | User | High | Implemented |
| UC4.2 Compare Returns | User | Medium | Implemented |
| UC5.1 Position Cockpit | User | High | Implemented |
| UC5.2 Export Excel | User | Medium | Implemented |
| UC5.3 Audit Trail | User | Medium | Implemented |
| UC5.4 Portfolio Report | User | Medium | Implemented |
| UC5.5 Position Performance | User | Medium | Implemented |
| UC6.1 Process Ex-Dividend | System | High | Implemented |
| UC6.2 Process Payment | System | High | Implemented |
| UC6.3 Dividend History | User | Medium | Implemented |
| UC6.4 Dividend Flow | System | High | Implemented |
