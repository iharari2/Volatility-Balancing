# GUI High-Level Design

## Position Cell Model

**Core Principle**: Each position is a **self-contained trading cell** combining cash and stock.

- **Position Cell** = Cash + Stock
- **Total Value** = Cash + (Qty × Current Price)
- **Strategy** applied independently per position
- **Performance** measured as position return vs stock return

See [Position Cell Model](../architecture/position-cell-model.md) for detailed architecture.

## Functionality

### Create and Manage Portfolio

- Create portfolio
- Add/change/delete position cells (asset + cash + trade configuration)
- Delete will move to archive but preserve in database for records
- User inputs for each new position cell:
  - **Ticker**: Asset symbol
  - **Cash**: Starting cash balance for this position
  - **Qty**: Starting shares (or system computes from $ value)
- Trade config for each position (default):
  - Buy/Sell trigger: ±3%
  - Guardrails: 25% min, 75% max stock allocation
  - Rebalance ratio: 1.66667
  - Min qty: 1
  - Commission: 0.0001%
  - Dividend tax: 25%
  - Trade after hours: Yes
- Position management: Simple approach - any change creates a log entry and sets new value

### Trade

**Position Cell Trading View:**

- Start/suspend/resume/stop trade for each position cell independently
- Monitor trend and market "live" data (price, bid/ask, etc.) per position
- **Position Cell Data Display** (per position):
  - Asset Ticker
  - Market Data: Open, Close, High, Low, Volume
  - Position Cell Components:
    - **Cash**: Current cash balance
    - **Stock**: Qty × Current Price
    - **Total Value**: Cash + Stock Value
    - **Allocation**: Cash % and Stock % of total
  - Trading Data:
    - Anchor price
    - Current qty
    - Buy/sell trigger prices
    - Guardrail H/L limits
    - Reason for action
- **Performance Metrics** (per position):
  - Position return % (total value change)
  - Stock return % (price change)
  - Alpha % (outperformance: position return - stock return)
- Transaction details and open orders tracking per position
- Key events (ex-dividend, market open/close) per position
- Data source: Yahoo Finance or similar
- Update frequency: Configurable by user (e.g., 6 min for trading, 1 day for simulation)
- Multiple sampling frequencies per day, not real-time but frequent updates
- Refresh frequency should be configurable and displayed

### Analysis

**Position Cell Performance Analysis:**

- Compare portfolio performance to market index
- **Per-Position Cell Analysis**:
  - Compare position performance to stock performance
  - Show position return vs stock return
  - Calculate and display alpha (outperformance)
  - Visualize performance over time (position vs stock chart)
- Asset data in simulation needs to be real market data (Yahoo Finance or similar)
- Per-position analysis of events, results, transactions, and dividends
- Export should include time series of events with explanations for each execution attempt
- Export raw data to Excel for debugging and offline analysis per position
- Export data per position with configurable frequency (e.g., every 6 min if that's the sampling rate)
- Debug checkbox: Check for all events, uncheck for only successful transactions
- **Export Data Per Position Cell**:
  - Market data: Date & time, Open, Close, High, Low, Volume, Bid, Ask, Dividend rate, Dividend value
  - Position cell data:
    - Cash balance
    - Asset qty
    - Stock value (qty × price)
    - Total value (cash + stock)
    - Allocation % (cash % and stock %)
    - Anchor price
  - Performance data:
    - Position return %
    - Stock return %
    - Alpha %
  - Algo data: Current price, buy/sell triggers, guardrail limits
  - Transaction data: Action, qty, $, commission, reason (trigger threshold, guardrail, etc.)

Simulation and Optimization

- Run scenario (change trading config) on virtual position and past data and analyze performance. The values should be the same attributes we use for trade configuration
- Optimization goal: Maximize return
- Create parameter range table for optimization
- Generate sensitivity heat maps across parameters showing return vs parameter value
- Visualize heat maps - do NOT optimize automatically, just create and display the heat map
- Export simulation results raw data to excel like in analysis above. Including detailed report of time series of the columns listed in analysis

Simulation used real historical values. Need to maintain high data quality.

About

- application details
-

## Screen Structure

The application has three main screens:

1. **Portfolio Screen**: List portfolios and show aggregated information across all positions
2. **Position Screen**: Show detailed information for each position cell (market data, cash, anchor, performance, activities)
3. **Trade Screen**: Show detailed data flow, market events, algorithm behaviors, and events history

See [Screen Structure Specification](SCREEN_STRUCTURE.md) for detailed requirements.

## Key Notes

- All positions in portfolio/trade/analysis need to be synchronized - all views represent the same portfolio so they need to share the same assets, quantities and events.

## Position Cell Model

**Core Principle**: Each position is displayed and managed as a **self-contained trading cell** that combines cash and stock.

### Position Cell Display Requirements

1. **Unified Cell View**: Show position as single cell combining:

   - Cash component (liquid balance)
   - Stock component (shares × price)
   - Total value (cash + stock)

2. **Performance Comparison**: Always show:

   - Position return (total value change)
   - Stock return (price change)
   - Alpha (outperformance: position return - stock return)

3. **Strategy Per Position**: Each position cell has:

   - Independent strategy configuration
   - Independent trigger thresholds
   - Independent guardrails
   - Independent trading status (active/paused)

4. **Trading Per Position**: All trading actions scoped to position:
   - Deposit/withdraw cash to/from position
   - Buy/sell stock for position
   - Orders use position's cash/stock

See [Position Cell GUI Specification](POSITION_CELL_GUI_SPEC.md) for detailed UI/UX requirements.

See [Position Cell Model](../architecture/position-cell-model.md) for architecture details.

See [Position Performance KPIs](../architecture/position-performance-kpis.md) for performance measurement.
