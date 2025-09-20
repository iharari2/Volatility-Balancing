# Volatility-Triggered Buy/Sell with Guardrails — Functional Specification

## 1. Summary (What & Why)

**What:** Auto-manage a blue-chip equity position using user-defined % thresholds around the last executed trade price. When price rises by ≥X%, **sell**; when it falls by ≥X%, **buy**. Trade size is formula-driven and then trimmed to respect guardrails (cash vs. asset bands). Multiple orders can occur per day; some days none.

**Why:** Deliver semi-passive mean-reversion captures while keeping portfolio within user-tolerant risk bounds and providing auditable reasoning.

---

## 2. Key Definitions & Defaults

- **Anchor price (P_anchor):** Last executed trade price.
- **Trigger threshold (τ):** Default ±3% relative to P_anchor.
- **Commission:** Default 0.01% of order notional.
- **Minimum order threshold (min_notional):** Configurable; default $100.
- **Rebalance ratio (r):** Default 0.5 (50% of available resources).
- **Guardrails (g_low, g_high):** Asset% ∈ [25%, 75%].
- **Portfolio state:**
  - A_t = price × shares
  - C_t = Cash value
  - V_t = A_t + C_t

---

## 3. Triggers

- **Sell trigger:** P ≥ P_anchor × (1 + τ)
- **Buy trigger:** P ≤ P_anchor × (1 − τ)
- After trade: reset P_anchor := execution_price.
- **Multiple same-day trades** allowed. Hidden cap = 5/day.

---

## 4. Order Sizing

### 4.1 Default Formula (Proportional Strategy)

```
ΔQ_raw = (P_anchor / P - 1) × r × ((A + C) / P)
```

- **Key improvement**: The `-1` term makes the formula proportional to price deviation
- **Zero at anchor**: When P = P_anchor, ΔQ_raw = 0 (no trade)
- **Proportional scaling**: Trade size scales with actual price change percentage
- Sell trigger → order −ΔQ_raw (capped by holdings)
- Buy trigger → order +ΔQ_raw (capped by cash & guardrails)
- Fractional shares allowed by default

### 4.2 Extensible Strategy System

The system supports multiple order sizing strategies that can be selected per position:

#### Available Strategies:

1. **Proportional** (Default): `ΔQ_raw = (P_anchor / P - 1) × r × ((A + C) / P)`

   - Scales with price deviation from anchor
   - Zero order size when price equals anchor
   - Most conservative and intuitive

2. **Fixed Percentage**: Uses fixed percentage of available resources

   - BUY: `ΔQ_raw = (cash × r) / P`
   - SELL: `ΔQ_raw = -(shares × r)`
   - Consistent trade sizes regardless of price deviation

3. **Original**: `ΔQ_raw = (P_anchor / P) × r × ((A + C) / P)`
   - The original aggressive strategy
   - Based on total portfolio value
   - More aggressive than proportional strategy

#### Strategy Selection:

- Configurable per position via `order_sizing_strategy` parameter
- Default: "proportional"
- Can be changed without affecting existing positions

---

## 5. Guardrails

- Enforce Asset% ∈ [25%, 75%] post-trade.
- If proposed q breaches guardrail, trim so A'/V' = nearest bound.
- If drifted outside bounds without a trade, auto-rebalance to boundary.

---

## 6. Order Validation

Skip if:

- Notional < min_notional
- Insufficient cash/shares after trim
- Market closed / halted
- In-flight duplicate order

---

## 7. Fees & Accounting

- Commission = notional × 0.0001.
- Buy: C := C − (q×P) − commission.
- Sell: C := C + |q|×P − commission.

---

## 8. Eventing & Reasoning

Every evaluation stores an **Event** with:

- **Type:** `threshold_crossed`, `order_submitted`, `order_trimmed_guardrail`, `order_rejected_min`, `order_filled`, `anchor_updated`, `auto_guardrail_rebalance`, `ex_div_announced`, `ex_div_effective`, `anchor_adjusted_for_dividend`, `dividend_cash_received`
- **Inputs:** P, P_anchor, τ, r, A, C, V, g_low, g_high, min_notional, commission_rate, DPS, withholding_tax_rate, price_source
- **Outputs:** side, quantity, reasoning string, final post-trade state
- **Timeline UI** shows plain-language reasoning.

---

## 9. Ex-Dividend Handling

### Objectives

- Prevent false triggers on ex-div day.
- Correctly adjust portfolio economics.
- Make adjustments transparent.

### Rules

- **Anchor adjustment:** On ex-date with dividend per share (DPS = d), set:
  - `P_anchor := P_anchor − d`
- **Dividend receivable:**
  - Gross = DPS × shares_at_record
  - Net = Gross − (Gross × withholding_tax_rate)
  - Default withholding_tax_rate = 25% (configurable)
- **Valuation:** Use `C_effective = Cash + DividendReceivable` in formulas & guardrails.
- **Pay date:** Move receivable → Cash, clear receivable.

### Events

- `ex_div_announced` {ex_date, pay_date, dps, currency}
- `ex_div_effective` {gross, net, receivable_created}
- `anchor_adjusted_for_dividend` {old_anchor, dps, new_anchor}
- `dividend_cash_received` {amount_net, receivable_cleared}

### UX

- Position Card badge: “Ex-dividend $0.82/sh; Receivable $82.00; Anchor adjusted to $149.18.”
- Cash panel shows Receivable + Paid.

---

## 10. Price Feed Policy

- **Reference price:** Last trade (if age ≤3s & within ±1% of mid); otherwise mid-quote.
- **Execution drift check:** If price moves >20bps from evaluation → submit, re-evaluate.
- **Outlier filter:** Ignore ticks >10σ vs. 1-min volatility.
- **After hours:** Triggers off by default.
- **Events include:** `price_source`, tick age, last trade, mid.

---

## 11. UX (MVP Screens)

### 11.1 Core Trading Interface

- **Strategy Config:** thresholds, rebalance ratio, commission, min order, guardrails, order sizing strategy, fractional toggle, max orders/day, withholding rate, after-hours toggle.
- **Position Card:** current price, anchor, next action, proposed vs. trimmed qty, projected Asset%.
- **Event Timeline:** inputs → decision → outputs.
- **Performance View:** asset return, portfolio return, P&L, fees, turnover, guardrail breaches.

### 11.2 Initial Position Setup

- **Position Creation Interface:**
  - Input method toggle: Dollar amount vs. Unit quantity
  - Dollar input field with real-time unit conversion display
  - Unit input field with real-time dollar value display
  - Current market price display for reference
  - Position value preview before confirmation
  - Validation for minimum position sizes

### 11.3 Parameter Configuration Panel

- **Trading Parameters:**
  - Threshold setting: ±X% input with slider (default 3%)
  - Rebalance ratio: decimal input with validation (default 0.5)
  - Order sizing strategy: dropdown selection (default "proportional")
  - After hours trading: toggle switch (default ON)
- **Guardrail Settings:**
  - Asset percentage bounds: dual slider or separate inputs (default 25%-75%)
  - Visual preview of guardrail zones
  - Real-time validation of settings
- **Order Parameters:**
  - Minimum order threshold: dollar input (default $100)
  - Commission rate: percentage input (default 0.01%)
  - Maximum orders per day: integer input (default 5)
- **Dividend Settings:**
  - Withholding tax rate: percentage input (default 25%)
  - Ex-dividend handling preferences

### 11.4 Excel Export & Debug Features

- **Export Configuration:**
  - Date range selector for export period
  - Position selection (single or multiple)
  - Export format options (Excel, CSV)
- **Excel Workbook Structure:**
  - **Summary Sheet:** Overview of all positions and key metrics
  - **Position Sheets:** One sheet per position with detailed transaction log
- **Transaction Log Columns (per position sheet):**
  - **Timestamp:** Date and time of evaluation/transaction
  - **Market Data:**
    - Current price
    - Price source (last trade, mid-quote, etc.)
    - Price age (seconds since last update)
    - Market status (open/closed/after-hours)
  - **Position Data:**
    - Shares held
    - Cash balance
    - Total portfolio value
    - Asset percentage
    - Anchor price
    - Distance from anchor (%)
  - **Transaction Details:**
    - Trigger type (buy/sell/none)
    - Raw order quantity
    - Trimmed order quantity
    - Order side (buy/sell)
    - Order price
    - Order status (submitted/filled/rejected)
    - Commission charged
    - Reasoning/decision logic
  - **Guardrail Status:**
    - Pre-trade asset %
    - Post-trade asset %
    - Guardrail breach status
    - Auto-rebalance triggered (Y/N)
  - **Event Details:**
    - Event type
    - Event description
    - Input parameters used
    - Output results
    - Rejection reasons (if applicable)

### 11.5 Enhanced Position Management

- **Position Dashboard:**
  - Real-time position value updates
  - Visual guardrail status indicators
  - Next trigger price calculations
  - Recent transaction history
- **Configuration Management:**

  - Save/load configuration presets
  - Configuration validation and warnings
  - Reset to defaults option
  - Configuration history/audit trail

  ***

## 12. Excel Export & Debug Capabilities

### 12.1 Export Functionality

- **Trigger-based exports:** Automatic export after each trading session
- **Manual exports:** On-demand export with custom date ranges
- **Real-time data:** Export includes all evaluation events, not just executed trades
- **Multi-format support:** Excel (.xlsx) and CSV formats
- **Position filtering:** Export single position or all positions

### 12.2 Excel Workbook Structure

- **Summary Dashboard Sheet:**

  - Position overview table with key metrics
  - Portfolio performance summary
  - Trading activity summary by date range
  - Guardrail breach statistics
  - Fee and commission totals

- **Individual Position Sheets (one per position):**
  - **Sheet naming:** `{TICKER}_{POSITION_ID}` (e.g., "AAPL_pos_123")
  - **Data refresh:** Real-time updates during trading hours
  - **Historical data:** Configurable lookback period (default 30 days)

### 12.3 Transaction Log Format

Each position sheet contains detailed line items for every evaluation event:

| Column Category   | Column Name              | Description                    | Example                                                              |
| ----------------- | ------------------------ | ------------------------------ | -------------------------------------------------------------------- |
| **Timestamp**     | Date                     | Evaluation date                | 2024-01-15                                                           |
|                   | Time                     | Evaluation time                | 14:30:25                                                             |
|                   | Market_Status            | Market open/closed/after-hours | Open                                                                 |
| **Market Data**   | Current_Price            | Stock price at evaluation      | $150.25                                                              |
|                   | Price_Source             | Last trade vs mid-quote        | Last Trade                                                           |
|                   | Price_Age_Sec            | Seconds since price update     | 2.3                                                                  |
|                   | Price_Change_Pct         | % change from previous         | +0.15%                                                               |
| **Position Data** | Shares_Held              | Current share quantity         | 100.0                                                                |
|                   | Cash_Balance             | Available cash                 | $5,000.00                                                            |
|                   | Portfolio_Value          | Total portfolio value          | $20,025.00                                                           |
|                   | Asset_Percentage         | % in stocks                    | 75.2%                                                                |
|                   | Anchor_Price             | Current anchor price           | $148.50                                                              |
|                   | Distance_From_Anchor_Pct | % from anchor                  | +1.18%                                                               |
| **Transaction**   | Trigger_Type             | Buy/Sell/None                  | Sell                                                                 |
|                   | Raw_Order_Qty            | Calculated quantity            | -15.5                                                                |
|                   | Trimmed_Order_Qty        | After guardrail adjustment     | -12.0                                                                |
|                   | Order_Side               | Buy/Sell                       | Sell                                                                 |
|                   | Order_Price              | Execution price                | $150.25                                                              |
|                   | Order_Status             | Submitted/Filled/Rejected      | Filled                                                               |
|                   | Commission               | Commission charged             | $0.18                                                                |
|                   | Notional_Value           | Order dollar value             | $1,803.00                                                            |
| **Guardrails**    | Pre_Trade_Asset_Pct      | Asset % before trade           | 75.2%                                                                |
|                   | Post_Trade_Asset_Pct     | Asset % after trade            | 72.1%                                                                |
|                   | Guardrail_Breach         | Y/N                            | N                                                                    |
|                   | Auto_Rebalance           | Y/N                            | N                                                                    |
| **Reasoning**     | Decision_Logic           | Why this action was taken      | "Price 1.18% above anchor, selling 12 shares to maintain 75% target" |
|                   | Rejection_Reason         | Why order was rejected         | N/A                                                                  |
|                   | Event_Type               | Type of event logged           | threshold_crossed                                                    |

### 12.4 Export Configuration Options

- **Date Range:** Start/end date picker with presets (Today, Last 7 days, Last 30 days, Custom)
- **Position Selection:** Multi-select dropdown for specific positions
- **Data Granularity:** All events vs. only executed trades
- **Format Options:** Excel with formatting vs. raw CSV
- **Include Charts:** Optional embedded charts for price and position evolution

## 13. Success Metrics

- % time within guardrails
- Avg slippage (bps)
- Trade hit rate after triggers
- Turnover & fee drag
- % orders skipped by min_notional
- Dividend capture accuracy
- **Export usage:** % of users utilizing debug exports
- **Configuration adoption:** % of users customizing parameters
- **Position setup accuracy:** % of positions created without errors

---

## 14. Compliance & Risk

- Disclosures on turnover, fees, and tax.
- Execution policy: market vs. limit per region.
- Audit logs exportable; no PII beyond config.
- Settlement T+1 handling; no negative buying power.

---

## 15. Out of Scope (Next)

- Multi-asset guardrails
- Dynamic thresholds
- DRIP (reinvestment of dividends)
- Smart slicing (TWAP)
- Tax-lot optimization

---

## Defaults Recap

- Trigger threshold: ±3%
- Commission: 0.01%
- Min order: $100
- Rebalance ratio: 0.5
- Guardrails: [25%, 75%]
- Max orders/day: 5
- Withholding tax: 25%
- Reference price: Last trade (fresh, in-line)
