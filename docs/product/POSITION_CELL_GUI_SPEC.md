# Position Cell GUI Specification

## Overview

The GUI should present each position as a **self-contained trading cell** that combines cash and stock, with independent strategy application and performance measurement.

**See [Screen Structure](SCREEN_STRUCTURE.md) for the three-screen architecture:**

- **Portfolio Screen**: List portfolios and aggregated information
- **Position Screen**: Detailed position information per position cell
- **Trade Screen**: Real-time trading data flow, events, and algorithm behavior

## Core Design Principles

1. **Position = Cell**: Each position is displayed as a unified cell combining cash and stock
2. **Independent Trading**: Each position trades independently with its own cash
3. **Performance Comparison**: Show position performance vs stock performance
4. **Strategy Per Position**: Each position has its own strategy configuration
5. **Visual Clarity**: Clear visual representation of cash + stock components

## Position Cell Display

### Cell Card Layout

```
┌─────────────────────────────────────────────┐
│ AAPL Position Cell                    [ACTIVE] │
├─────────────────────────────────────────────┤
│                                             │
│  Current Market Data:                       │
│  ┌─────────────────────────────────────┐   │
│  │ Price:      $155.20  ↑ +$0.20 (+0.13%)│ │
│  │ Open:       $154.50                   │   │
│  │ High:       $155.50  |  Low: $154.00 │   │
│  │ Close:      $155.00                   │   │
│  │ Volume:     45.2M                     │   │
│  │ Bid/Ask:    $155.18 / $155.22         │   │
│  │ Market:     Open ✓                    │   │
│  └─────────────────────────────────────┘   │
│                                             │
│  Value Breakdown:                          │
│  ┌─────────────────────────────────────┐   │
│  │ Cash:    $10,000  ████████░░ 40%     │   │
│  │ Stock:   $15,000  ████████████ 60%   │   │
│  │ Total:   $25,000                     │   │
│  └─────────────────────────────────────┘   │
│                                             │
│  Performance vs Stock:                      │
│  ┌─────────────────────────────────────┐   │
│  │ Position Return:  +5.2%  ↑           │   │
│  │ Stock Return:     +3.0%  ↑           │   │
│  │ Alpha:            +2.2%  ✓           │   │
│  │ Status:           Outperforming      │   │
│  └─────────────────────────────────────┘   │
│                                             │
│  Strategy: Volatility Trading               │
│  • Triggers: ±3%                            │
│  • Guardrails: 25% - 75%                    │
│  • Rebalance: 1.67x                         │
│                                             │
│  [Configure] [Trade] [View Details]         │
└─────────────────────────────────────────────┘
```

### Key Visual Elements

1. **Current Market Data**

   - Current price (prominently displayed)
   - Price change (absolute and percentage)
   - OHLC (Open, High, Low, Close)
   - Volume
   - Bid/Ask spread
   - Market hours status (Open/Closed)
   - Last update timestamp

2. **Value Breakdown**

   - Horizontal bar or pie chart showing cash vs stock
   - Percentages clearly displayed
   - Total value prominently shown

3. **Performance Metrics**

   - Position return (large, prominent)
   - Stock return (for comparison)
   - Alpha (highlighted if positive)
   - Visual indicators (arrows, colors)

4. **Strategy Status**
   - Active/Paused indicator
   - Key strategy parameters
   - Quick access to configure

## Position List View

### Grid Layout

Display positions as cards in a responsive grid:

```
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│ AAPL        │  │ MSFT        │  │ GOOGL       │
│ $155.20 ↑   │  │ $380.50 ↑   │  │ $142.30 ↓   │
│ +0.13%      │  │ +0.25%      │  │ -0.15%      │
│             │  │             │  │             │
│ $25,000     │  │ $30,000     │  │ $20,000     │
│ Cash: 40%   │  │ Cash: 30%   │  │ Cash: 50%   │
│ Stock: 60%  │  │ Stock: 70%  │  │ Stock: 50%  │
│             │  │             │  │             │
│ +5.2% ↑     │  │ +2.1% ↑     │  │ -1.5% ↓     │
│ α +2.2% ✓   │  │ α -0.5% ✗   │  │ α -3.2% ✗   │
│             │  │             │  │             │
│ [Details]   │  │ [Details]   │  │ [Details]   │
└─────────────┘  └─────────────┘  └─────────────┘
```

### List View (Alternative)

Table format with key metrics:

| Asset | Price   | Change | Total Value | Cash | Stock | Position Return | Stock Return | Alpha   | Status |
| ----- | ------- | ------ | ----------- | ---- | ----- | --------------- | ------------ | ------- | ------ |
| AAPL  | $155.20 | +0.13% | $25,000     | 40%  | 60%   | +5.2% ↑         | +3.0% ↑      | +2.2% ✓ | Active |
| MSFT  | $380.50 | +0.25% | $30,000     | 30%  | 70%   | +2.1% ↑         | +2.6% ↑      | -0.5% ✗ | Active |
| GOOGL | $142.30 | -0.15% | $20,000     | 50%  | 50%   | -1.5% ↓         | +1.7% ↑      | -3.2% ✗ | Paused |

## Position Detail View

### Expanded Cell View

When clicking on a position cell, show detailed view:

```
┌─────────────────────────────────────────────────────┐
│ AAPL Position Cell - Detailed View                  │
├─────────────────────────────────────────────────────┤
│                                                      │
│  Current Market Data:                               │
│  ┌──────────────────────────────────────────────┐  │
│  │ Current Price:      $155.20  ↑ +$0.20 (+0.13%)│  │
│  │ Open:               $154.50                   │  │
│  │ High:               $155.50                   │  │
│  │ Low:                $154.00                   │  │
│  │ Close (Prev):       $155.00                   │  │
│  │ Volume:             45.2M                      │  │
│  │ Bid:                $155.18                   │  │
│  │ Ask:                $155.22                   │  │
│  │ Spread:             $0.04 (0.03%)             │  │
│  │ Market Status:      Open ✓                    │  │
│  │ Last Update:        14:32:15                   │  │
│  └──────────────────────────────────────────────┘  │
│                                                      │
│  Value Components:                                   │
│  ┌──────────────────────────────────────────────┐  │
│  │ Cash Balance:        $10,000                  │  │
│  │ Stock Holdings:      100 shares @ $155.20     │  │
│  │ Stock Value:         $15,520                  │  │
│  │ Total Value:         $25,520                  │  │
│  │ Allocation:          39% cash, 61% stock     │  │
│  └──────────────────────────────────────────────┘  │
│                                                      │
│  Performance Chart:                                  │
│  ┌──────────────────────────────────────────────┐  │
│  │  [Line chart: Position value vs Stock value] │  │
│  │  Blue line: Position total value             │  │
│  │  Gray line: Stock value (buy-and-hold)       │  │
│  │  Green area: Alpha (outperformance)           │  │
│  └──────────────────────────────────────────────┘  │
│                                                      │
│  Performance Metrics:                                │
│  • Position Return:  +5.2% (since creation)         │
│  • Stock Return:     +3.0% (price change)           │
│  • Alpha:            +2.2% (outperformance)          │
│  • Initial Value:    $24,200                         │
│  • Current Value:    $25,500                         │
│                                                      │
│  Trading Activity:                                   │
│  • Total Trades: 12                                  │
│  • Total Commissions: $15.20                         │
│  • Total Dividends: $125.00                          │
│  • Last Trade: 2 hours ago                           │
│                                                      │
│  Strategy Configuration:                             │
│  • Trigger Up: +3.0%                                 │
│  • Trigger Down: -3.0%                               │
│  • Min Stock %: 25%                                  │
│  • Max Stock %: 75%                                 │
│  • Rebalance Ratio: 1.67x                            │
│                                                      │
│  [Edit Strategy] [Deposit Cash] [Withdraw Cash]     │
│  [View Trades] [View Events] [Export Data]          │
└─────────────────────────────────────────────────────┘
```

## Trading View

### Real-Time Position Monitoring

Show active positions with live updates:

```
┌─────────────────────────────────────────────────────┐
│ Trading Console - Active Positions                  │
├─────────────────────────────────────────────────────┤
│                                                      │
│  AAPL Position Cell                                  │
│  ┌──────────────────────────────────────────────┐   │
│  │ Current Price: $155.20  (Last: $155.00)      │   │
│  │ Anchor: $150.00  |  Deviation: +3.47%       │   │
│  │                                                 │   │
│  │ Trigger Status: ⚠️ SELL TRIGGER APPROACHING   │   │
│  │   (At +3.0%: $154.50)                          │   │
│  │                                                 │   │
│  │ Guardrail Status: ✓ Within limits (60%)       │   │
│  │                                                 │   │
│  │ Position: $25,500  |  Return: +5.2%           │   │
│  │ Stock:    $15,500  |  Return: +3.0%           │   │
│  │ Alpha:    +2.2% ✓                              │   │
│  └──────────────────────────────────────────────┘   │
│                                                      │
│  [Pause Trading] [View Details] [Configure]         │
└─────────────────────────────────────────────────────┘
```

## Performance Dashboard

### Portfolio Overview

Aggregate view showing all position cells:

```
┌─────────────────────────────────────────────────────┐
│ Portfolio Performance Dashboard                      │
├─────────────────────────────────────────────────────┤
│                                                      │
│  Portfolio Summary:                                  │
│  • Total Value: $75,500                              │
│  • Total Cash: $25,000 (33%)                        │
│  • Total Stock: $50,500 (67%)                       │
│  • Portfolio Return: +2.1%                          │
│  • Weighted Alpha: +0.3%                            │
│                                                      │
│  Position Performance:                               │
│  ┌──────────────────────────────────────────────┐  │
│  │ [Bar chart: Alpha per position]                │  │
│  │ AAPL:  +2.2% (green bar)                       │  │
│  │ MSFT:  -0.5% (red bar)                          │  │
│  │ GOOGL: -3.2% (red bar)                          │  │
│  └──────────────────────────────────────────────┘  │
│                                                      │
│  Top Performers:                                     │
│  1. AAPL: +2.2% alpha                               │
│  2. MSFT: -0.5% alpha                               │
│  3. GOOGL: -3.2% alpha                              │
│                                                      │
│  [View All Positions] [Export Report]               │
└─────────────────────────────────────────────────────┘
```

## Data and Trade Per Position

### Key Requirements

1. **All data scoped to position**:

   - Cash balance: Position-specific
   - Stock holdings: Position-specific
   - Trading history: Position-specific
   - Performance metrics: Position-specific

2. **Strategy application per position**:

   - Each position has independent strategy config
   - Triggers evaluated per position
   - Guardrails checked per position
   - Orders generated per position

3. **Trading actions per position**:

   - Deposit/withdraw cash to/from position
   - Buy/sell stock for position
   - Set anchor price for position
   - Configure strategy for position

4. **Performance measurement per position**:
   - Position return (cash + stock total value change)
   - Stock return (price change only)
   - Alpha (position return - stock return)
   - Visual comparison (charts, indicators)

## Implementation Guidelines

### Component Structure

```
PositionCellCard
├── ValueBreakdown (Cash + Stock visualization)
├── PerformanceMetrics (Position vs Stock)
├── StrategyStatus (Active/Paused, config summary)
└── Actions (Configure, Trade, View Details)

PositionDetailView
├── ValueComponents (Detailed breakdown)
├── PerformanceChart (Time series)
├── TradingActivity (Trades, commissions, dividends)
├── StrategyConfiguration (Full config editor)
└── ActionButtons (Deposit, Withdraw, Configure, etc.)
```

### Data Flow

1. **Load Position Data**:

   ```
   GET /api/tenants/{tenant_id}/portfolios/{portfolio_id}/positions/{position_id}
   ```

2. **Calculate Performance**:

   - Position return: (current_total_value - initial_total_value) / initial_total_value
   - Stock return: (current_price - anchor_price) / anchor_price
   - Alpha: position_return - stock_return

3. **Display as Cell**:
   - Show cash + stock as unified cell
   - Display performance metrics
   - Show strategy status

### Visual Design

- **Color Coding**:

  - Green: Positive returns, outperforming
  - Red: Negative returns, underperforming
  - Gray: Neutral, paused

- **Icons**:

  - ✓: Positive alpha (outperforming)
  - ✗: Negative alpha (underperforming)
  - ↑: Positive return
  - ↓: Negative return
  - ⚠️: Warning (approaching trigger/guardrail)

- **Charts**:
  - Line chart: Position value vs Stock value over time
  - Bar chart: Alpha comparison across positions
  - Pie/Bar: Cash vs Stock allocation

## User Interactions

### Position Cell Actions

1. **View Details**: Expand to show full position information
2. **Configure Strategy**: Edit trigger thresholds, guardrails, etc.
3. **Deposit Cash**: Add cash to position
4. **Withdraw Cash**: Remove cash from position
5. **Set Anchor**: Manually set anchor price
6. **Start/Pause Trading**: Control trading activity
7. **View Trades**: See trading history
8. **Export Data**: Download position data for analysis

### Trading Actions

All trading actions are scoped to the position cell:

- Buy orders use position's cash
- Sell orders use position's stock
- Cash updates affect only that position
- Stock updates affect only that position

## API Requirements

### Position Overview Endpoint

Should return position cell data including:

- **Current market data**: Price, OHLC, volume, bid/ask, market status
- Cash and stock components
- Total value and allocation
- Performance metrics (position return, stock return, alpha)
- Strategy configuration
- Trading activity summary

See [Position Cell Model](../architecture/position-cell-model.md) for API response format.

---

_Last updated: 2025-01-XX_







