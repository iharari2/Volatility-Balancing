# Domain Model

## Core Entities

### Portfolio

A collection of position cells for a tenant.

- `id`: Portfolio identifier
- `tenant_id`: Tenant identifier
- `name`: Portfolio name
- `description`: Optional description
- `type`: LIVE/SIM/SANDBOX
- `trading_state`: READY/RUNNING/PAUSED/ERROR/NOT_CONFIGURED
- `trading_hours_policy`: OPEN_ONLY/OPEN_PLUS_AFTER_HOURS

### Position (Position Cell)

A self-contained trading cell combining cash and stock.

- `id`: Position identifier
- `tenant_id`: Tenant identifier
- `portfolio_id`: Portfolio identifier
- `asset_symbol`: Asset ticker symbol
- `qty`: Number of shares (stock component)
- `cash`: Cash balance (cash component)
- `anchor_price`: Reference price for volatility triggers
- `avg_cost`: Average cost basis
- `dividend_receivable`: Pending dividend amount
- `total_commission_paid`: Cumulative commissions
- `total_dividends_received`: Cumulative dividends
- `guardrails`: Guardrail policy
- `order_policy`: Order policy configuration

**Position Cell Value:**

```
total_value = cash + (qty × current_price)
```

### PortfolioConfig

Portfolio-level configuration defaults.

- `tenant_id`: Tenant identifier
- `portfolio_id`: Portfolio identifier
- `trigger_up_pct`: Upward trigger threshold
- `trigger_down_pct`: Downward trigger threshold
- `min_stock_pct`: Minimum stock allocation
- `max_stock_pct`: Maximum stock allocation
- `max_trade_pct_of_position`: Maximum trade size
- `commission_rate_pct`: Commission rate

### Order

A trading order for a position.

- `id`: Order identifier
- `tenant_id`: Tenant identifier
- `portfolio_id`: Portfolio identifier
- `position_id`: Position identifier
- `side`: BUY/SELL
- `qty`: Order quantity
- `status`: PENDING/FILLED/CANCELLED/REJECTED
- `idempotency_key`: Idempotency key

### Trade

An executed trade for a position.

- `id`: Trade identifier
- `tenant_id`: Tenant identifier
- `portfolio_id`: Portfolio identifier
- `position_id`: Position identifier
- `order_id`: Order identifier
- `side`: BUY/SELL
- `qty`: Trade quantity
- `price`: Execution price
- `commission`: Commission paid
- `executed_at`: Execution timestamp

## Value Objects

### PositionState

Immutable snapshot of position state.

- `ticker`: Asset symbol
- `qty`: Quantity
- `cash`: Cash balance
- `dividend_receivable`: Pending dividend
- `anchor_price`: Anchor price

### MarketQuote

Market price data.

- `ticker`: Asset symbol
- `price`: Current price
- `timestamp`: Price timestamp
- `currency`: Currency code

### TriggerConfig

Trigger threshold configuration.

- `up_threshold_pct`: Upward trigger threshold
- `down_threshold_pct`: Downward trigger threshold

### GuardrailConfig

Guardrail limits.

- `min_stock_pct`: Minimum stock allocation
- `max_stock_pct`: Maximum stock allocation
- `max_trade_pct_of_position`: Maximum trade size
- `max_orders_per_day`: Daily order limit

## Domain Services

### PriceTrigger

Pure function to evaluate price triggers.

```python
def evaluate(anchor_price: float, current_price: float, config: TriggerConfig) -> TriggerDecision
```

### GuardrailEvaluator

Pure function to evaluate guardrails.

```python
def evaluate(position_state: PositionState, trade_intent: TradeIntent, config: GuardrailConfig) -> GuardrailDecision
```

## Position Cell Model

Each position is treated as an independent trading cell:

- **Cash Component**: Liquid cash balance
- **Stock Component**: Shares of the asset
- **Total Value**: Cash + (Qty × Price)
- **Strategy**: Applied independently
- **Performance**: Measured vs stock performance

See [Position Cell Model](position-cell-model.md) for detailed documentation.

---

_Last updated: 2025-01-XX_
