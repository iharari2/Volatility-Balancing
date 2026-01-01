# Position Cell Model

## Overview

The Position Cell Model treats each position as an independent trading cell that combines cash and stock. This model provides better isolation, clearer performance measurement, and more intuitive management.

## Core Concept

### Position as Cell

Each position is a **self-contained trading cell**:

- **Cash Component**: Liquid cash balance (`position.cash`)
- **Stock Component**: Shares of the asset (`position.qty`)
- **Total Value**: `cash + (qty × current_price)`
- **Strategy**: Applied independently per position

```
Position Cell = Cash + Stock
Total Value = Cash + (Qty × Price)
```

### Why This Model is Better

1. **Clear Ownership**: Cash belongs to the position, not the portfolio
2. **Independent Trading**: Each position trades independently with its own cash
3. **Performance Measurement**: Easy to compare position performance vs stock performance
4. **Simpler Mental Model**: One position = one cell = one strategy
5. **Better Isolation**: Positions don't share cash, reducing complexity

## Data Model

### Position Entity

```python
@dataclass
class Position:
    id: str
    tenant_id: str
    portfolio_id: str
    asset_symbol: str
    qty: float              # Stock component
    cash: float = 0.0       # Cash component
    anchor_price: Optional[float]
    avg_cost: Optional[float]
    # ... other fields
```

### Position Cell Metrics

For each position cell, we track:

**Value Components:**

- `cash`: Cash balance in the position
- `stock_value`: `qty × current_price`
- `total_value`: `cash + stock_value`

**Allocation:**

- `cash_pct`: `(cash / total_value) × 100`
- `stock_pct`: `(stock_value / total_value) × 100`

**Performance (vs Stock):**

- `position_return`: `((total_value - initial_value) / initial_value) × 100`
- `stock_return`: `((current_price - initial_price) / initial_price) × 100`
  - Where `initial_price` is the anchor price at position creation (starting price)
  - Both position return and stock return are measured from the same starting point
- `alpha`: `position_return - stock_return` (outperformance)

## GUI Design

### Position Cell View

Each position should be displayed as a **unified cell** showing:

```
┌─────────────────────────────────────┐
│ AAPL Position Cell                 │
├─────────────────────────────────────┤
│ Market: $155.20 ↑ +0.13%            │
│ O: $154.50 | H: $155.50 | L: $154.00│
│ Volume: 45.2M | Market: Open ✓      │
├─────────────────────────────────────┤
│ Cash:        $10,000  (40%)        │
│ Stock:       $15,000  (60%)         │
│ Total Value: $25,000                │
├─────────────────────────────────────┤
│ Performance vs Stock:               │
│ Position: +5.2%                     │
│ Stock:    +3.0%                      │
│ Alpha:    +2.2% ✓                   │
├─────────────────────────────────────┤
│ Strategy: Volatility Trading         │
│ Trigger: ±3% | Guardrails: 25-75%   │
└─────────────────────────────────────┘
```

### Key Display Elements

1. **Current Market Data**

   - Current price (prominently displayed)
   - Price change (absolute and percentage)
   - OHLC (Open, High, Low, Close)
   - Volume
   - Bid/Ask spread
   - Market hours status (Open/Closed)
   - Last update timestamp

2. **Combined Cash + Stock View**

   - Show both components side-by-side
   - Visual representation (pie chart or bar)
   - Percentage allocation

3. **Performance Comparison**

   - Position performance (total return)
   - Stock performance (price return)
   - Alpha (outperformance)
   - Visual indicators (green/red, up/down arrows)

4. **Strategy Application**

   - Show active strategy per position
   - Display trigger thresholds
   - Show guardrail limits
   - Indicate if strategy is active/paused

5. **Trading Actions**
   - All trading actions scoped to the position cell
   - Deposit/withdraw cash to/from position
   - Buy/sell stock for position
   - Set anchor price
   - Configure strategy

## Performance Measurement

### Position Performance KPIs

For each position cell, measure:

1. **Total Return**

   ```
   position_return = ((current_total_value - initial_total_value) / initial_total_value) × 100
   ```

2. **Stock Return** (for comparison)

   ```
   stock_return = ((current_price - initial_price) / initial_price) × 100

   Where:
     initial_price = anchor_price at position creation (starting price)
     current_price = current market price
   ```

   **Important**: Stock return is compared to position return from the same point in time (position creation). Both returns are measured from the initial state.

3. **Alpha** (outperformance)

   ```
   alpha = position_return - stock_return
   ```

4. **Cash Efficiency**

   ```
   cash_utilization = (stock_value / total_value) × 100
   ```

5. **Trading Activity**
   - Number of trades
   - Total commissions paid
   - Total dividends received

### Portfolio-Level Aggregation

Portfolio metrics aggregate from position cells:

- **Total Portfolio Value**: Sum of all position total values
- **Portfolio Return**: Weighted average of position returns
- **Portfolio Alpha**: Weighted average of position alphas
- **Diversification**: Number of positions, allocation spread

## Strategy Application

### Per-Position Strategy

Each position cell has its own strategy configuration:

- **Trigger Thresholds**: Buy/sell trigger percentages
- **Guardrails**: Min/max stock allocation
- **Rebalance Ratio**: Order sizing multiplier
- **Commission Rate**: Trading cost
- **Trading Hours**: Market hours policy

### Strategy Independence

- Positions can have different strategies
- Strategies are applied independently
- No cross-position dependencies
- Each position trades with its own cash

## Trading Flow

### Position Cell Trading Cycle

1. **Market Data Update**

   - Get current price for position's asset
   - Update stock value: `qty × current_price`

2. **Trigger Evaluation**

   - Compare current price to anchor price
   - Calculate deviation: `(current_price - anchor_price) / anchor_price`
   - Check if trigger threshold exceeded

3. **Order Generation**

   - Calculate order size using strategy
   - Use position's cash for buy orders
   - Use position's stock for sell orders

4. **Execution**

   - Execute order
   - Update position cash (buy: decrease, sell: increase)
   - Update position qty (buy: increase, sell: decrease)
   - Update anchor price

5. **Performance Update**
   - Recalculate total value
   - Update performance metrics
   - Compare to stock performance

## GUI Implementation Guidelines

### Position List View

Show positions as cells in a grid or list:

```
┌──────────┐  ┌──────────┐  ┌──────────┐
│ AAPL    │  │ MSFT    │  │ GOOGL   │
│ $25,000 │  │ $30,000 │  │ $20,000 │
│ +5.2%   │  │ +2.1%   │  │ -1.5%   │
│ α +2.2% │  │ α -0.5% │  │ α -3.2% │
└──────────┘  └──────────┘  └──────────┘
```

### Position Detail View

Expand position cell to show:

- Cash and stock breakdown
- Performance chart (position vs stock)
- Trading history
- Strategy configuration
- Recent events

### Trading View

Show active positions with:

- Real-time price updates
- Trigger status (approaching/fired)
- Guardrail status
- Recent trades
- Performance indicators

## API Design

### Position Overview Endpoint

```json
{
  "position": {
    "id": "pos-123",
    "asset": "AAPL",
    "qty": 100,
    "cash": 10000,
    "anchor_price": 150.0,
    "avg_cost": 148.0
  },
  "market_data": {
    "current_price": 155.2,
    "price_change": 0.2,
    "price_change_pct": 0.13,
    "open": 154.5,
    "high": 155.5,
    "low": 154.0,
    "close": 155.0,
    "volume": 45200000,
    "bid": 155.18,
    "ask": 155.22,
    "spread": 0.04,
    "market_status": "OPEN",
    "last_update": "2025-01-20T14:32:15Z"
  },
  "values": {
    "cash": 10000,
    "stock_value": 15500,
    "total_value": 25500
  },
  "allocation": {
    "cash_pct": 39.2,
    "stock_pct": 60.8
  },
  "performance": {
    "position_return_pct": 5.2,
    "stock_return_pct": 3.0, // Calculated from initial_price (anchor at creation) to current_price
    "alpha_pct": 2.2,
    "initial_value": 24200,
    "initial_price": 150.0, // Anchor price at position creation (used for stock return calculation)
    "current_value": 25500
  },
  "strategy": {
    "trigger_up_pct": 3.0,
    "trigger_down_pct": -3.0,
    "min_stock_pct": 25.0,
    "max_stock_pct": 75.0,
    "status": "ACTIVE"
  }
}
```

## Benefits

1. **Clear Mental Model**: Position = Cell = Independent trading unit
2. **Better Performance Tracking**: Easy to see if strategy adds value
3. **Simpler Cash Management**: Cash belongs to position, not portfolio
4. **Independent Strategies**: Each position can have different config
5. **Better Isolation**: Positions don't interfere with each other
6. **Easier Debugging**: All position data in one place

## Migration Notes

- Cash moved from `PortfolioCash` to `Position.cash`
- Portfolio cash = sum of position cash values
- All trading scoped to individual positions
- Performance metrics calculated per position

---

_Last updated: 2025-01-XX_







