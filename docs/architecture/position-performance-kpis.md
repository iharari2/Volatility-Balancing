# Position Performance KPIs

## Overview

Each position cell should measure its performance **relative to the underlying stock**. This allows users to see if the trading strategy adds value beyond simply holding the stock.

## Core KPIs

### 1. Position Return

**Definition**: Total return of the position cell (cash + stock).

```
position_return = ((current_total_value - initial_total_value) / initial_total_value) × 100

Where:
  current_total_value = current_cash + (current_qty × current_price)
  initial_total_value = initial_cash + (initial_qty × initial_price)
```

**Display**:

- Percentage with sign (+5.2% or -2.1%)
- Color coding: Green for positive, red for negative
- Trend indicator: Up/down arrow

### 2. Stock Return

**Definition**: Return of the underlying stock (price change only), measured from the same starting point as position return.

```
stock_return = ((current_price - initial_price) / initial_price) × 100

Where:
  initial_price = anchor_price at position creation (starting price)
  current_price = current market price
```

**Important**: Stock return is compared to position return from the same point in time (position creation). Both returns are measured from the initial state.

**Display**:

- Percentage with sign
- Color coding: Green/red
- Used as baseline for comparison

### 3. Alpha (Outperformance)

**Definition**: Excess return of position over stock return.

```
alpha = position_return - stock_return
```

**Interpretation**:

- **Positive Alpha**: Strategy outperformed buy-and-hold
- **Negative Alpha**: Strategy underperformed buy-and-hold
- **Zero Alpha**: Strategy matched buy-and-hold

**Display**:

- Percentage with sign (+2.2% alpha or -0.5% alpha)
- Strong visual indicator (badge, highlight)
- Icon: ✓ for positive, ✗ for negative

### 4. Cash Efficiency

**Definition**: Percentage of position value in stock (vs cash).

```
cash_utilization = (stock_value / total_value) × 100
```

**Display**:

- Percentage (e.g., "60% in stock, 40% cash")
- Visual bar or pie chart
- Indicator if outside guardrail limits

### 5. Trading Activity Metrics

- **Number of Trades**: Total buy/sell transactions
- **Total Commissions**: Cumulative commission paid
- **Total Dividends**: Cumulative dividends received
- **Average Trade Size**: Mean trade value
- **Win Rate**: Percentage of profitable trades (if applicable)

## Portfolio-Level Aggregation

### Weighted Portfolio Metrics

```
portfolio_return = Σ(position_return × position_weight)
portfolio_alpha = Σ(alpha × position_weight)
portfolio_cash_efficiency = Σ(cash_utilization × position_weight)

Where:
  position_weight = position_total_value / portfolio_total_value
```

### Portfolio Diversification

- **Number of Positions**: Count of active position cells
- **Concentration**: Largest position % of total
- **Allocation Spread**: Standard deviation of position weights

## GUI Display

### Position Cell Card

```
┌─────────────────────────────────────┐
│ AAPL Position Cell                  │
├─────────────────────────────────────┤
│ Value Breakdown:                    │
│   Cash:    $10,000  (40%)           │
│   Stock:   $15,000  (60%)           │
│   Total:   $25,000                  │
├─────────────────────────────────────┤
│ Performance vs Stock:                │
│   Position: +5.2%  ↑                 │
│   Stock:    +3.0%  ↑                 │
│   Alpha:    +2.2%  ✓ Outperforming  │
├─────────────────────────────────────┤
│ Trading Activity:                   │
│   Trades: 12 | Commissions: $15.20  │
│   Dividends: $125.00                │
└─────────────────────────────────────┘
```

### Performance Chart

Show time series comparing:

- Position total value (blue line) - from initial total value at position creation
- Stock value if buy-and-hold (gray line) - from initial price at position creation
- Alpha (green/red area between lines) - difference between position and stock returns

**Note**: Both lines start from the same point in time (position creation) to ensure fair comparison.

### Performance Table

| Position | Total Value | Position Return | Stock Return | Alpha | Status |
| -------- | ----------- | --------------- | ------------ | ----- | ------ |
| AAPL     | $25,000     | +5.2%           | +3.0%        | +2.2% | ✓      |
| MSFT     | $30,000     | +2.1%           | +2.6%        | -0.5% | ✗      |
| GOOGL    | $20,000     | -1.5%           | +1.7%        | -3.2% | ✗      |

**Note**: Both Position Return and Stock Return are measured from the same starting point (position creation) to ensure fair comparison. Stock Return uses the initial price (anchor price at creation), not the current anchor price.

## Calculation Examples

### Example 1: Profitable Position

**Initial State** (at position creation):

- Cash: $10,000
- Qty: 100 shares
- Initial price (anchor at creation): $150
- Initial total value: $10,000 + (100 × $150) = $25,000

**Current State:**

- Cash: $8,500 (after buying 10 more shares)
- Qty: 110 shares
- Current price: $155
- Current total value: $8,500 + (110 × $155) = $25,550

**Calculations:**

- Position return: ((25,550 - 25,000) / 25,000) × 100 = **+2.2%**
  - Measured from initial total value ($25,000) at position creation
- Stock return: ((155 - 150) / 150) × 100 = **+3.3%**
  - Measured from initial price ($150) at position creation (same starting point as position return)
- Alpha: 2.2% - 3.3% = **-1.1%** (underperformed stock)

### Example 2: Outperforming Position

**Initial State** (at position creation):

- Cash: $5,000
- Qty: 50 shares
- Initial price (anchor at creation): $200
- Initial total value: $5,000 + (50 × $200) = $15,000

**Current State:**

- Cash: $12,000 (after selling 20 shares at profit)
- Qty: 30 shares
- Current price: $210
- Current total value: $12,000 + (30 × $210) = $18,300

**Calculations:**

- Position return: ((18,300 - 15,000) / 15,000) × 100 = **+22.0%**
  - Measured from initial total value ($15,000) at position creation
- Stock return: ((210 - 200) / 200) × 100 = **+5.0%**
  - Measured from initial price ($200) at position creation (same starting point as position return)
- Alpha: 22.0% - 5.0% = **+17.0%** (strongly outperformed stock)

## Implementation Notes

### Baseline Calculation

For accurate performance measurement, track:

- **Initial snapshot** (at position creation):
  - Initial cash
  - Initial qty
  - Initial price (anchor price at creation)
  - Initial total value = initial_cash + (initial_qty × initial_price)
- **Current snapshot**:
  - Current cash
  - Current qty
  - Current price (market price)
  - Current total value = current_cash + (current_qty × current_price)
- **Stock baseline**: What buy-and-hold would have returned from initial_price to current_price

**Key Point**: Both position return and stock return must be measured from the same starting point (position creation) to ensure fair comparison.

### Handling Cash Deposits/Withdrawals

When cash is deposited or withdrawn:

- Adjust initial total value for future calculations
- Or track deposits/withdrawals separately and exclude from return calculation
- Document approach in UI

### Dividend Adjustments

- Include dividends in position return (they add to cash)
- Stock return should use price-adjusted returns (accounting for dividends)
- Or show dividends separately

## API Response Format

```json
{
  "position_id": "pos-123",
  "asset": "AAPL",
  "values": {
    "cash": 10000,
    "stock_value": 15500,
    "total_value": 25500
  },
  "performance": {
    "position_return_pct": 5.2,
    "stock_return_pct": 3.0, // Calculated from initial_price (anchor at creation) to current_price
    "alpha_pct": 2.2,
    "initial_value": 24200,
    "initial_price": 150.0, // Anchor price at position creation (used for stock return calculation)
    "current_value": 25500
  },
  "trading_activity": {
    "total_trades": 12,
    "total_commissions": 15.2,
    "total_dividends": 125.0
  }
}
```

---

_Last updated: 2025-01-XX_







