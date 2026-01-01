# Position Cockpit API Contract

## Overview

The Position Cockpit API provides position-centric endpoints for the Position Cockpit UI. All endpoints are scoped to `tenant_id`, `portfolio_id`, and `position_id` for security and data isolation.

## Base Path

All endpoints use the following base path pattern:

```
/v1/tenants/{tenant_id}/portfolios/{portfolio_id}/positions/{position_id}
```

## Endpoints

### 1. GET /cockpit

Get comprehensive position cockpit data including position details, baseline, current market data, trading status, and calculated deltas.

**Request:**

```
GET /v1/tenants/{tenant_id}/portfolios/{portfolio_id}/positions/{position_id}/cockpit
```

**Response:**

```json
{
  "position": {
    "id": "pos_abc123",
    "asset_symbol": "AAPL",
    "qty": 100.0,
    "cash": 5000.0,
    "anchor_price": 150.0,
    "avg_cost": 150.0,
    "total_commission_paid": 10.0,
    "total_dividends_received": 50.0
  },
  "baseline": {
    "baseline_price": 150.0,
    "baseline_qty": 100.0,
    "baseline_cash": 5000.0,
    "baseline_total_value": 20000.0,
    "baseline_stock_value": 15000.0,
    "baseline_timestamp": "2025-01-20T10:00:00Z"
  },
  "current_market_data": {
    "price": 155.0,
    "source": "Yahoo Finance",
    "timestamp": "2025-01-20T14:30:00Z",
    "is_market_hours": true
  },
  "trading_status": "RUNNING",
  "position_vs_baseline": {
    "pct": 2.5,
    "abs": 500.0
  },
  "stock_vs_baseline": {
    "pct": 3.33,
    "abs": 500.0
  }
}
```

**Response Fields:**

- `position`: Position details (id, asset_symbol, qty, cash, anchor_price, avg_cost, etc.)
- `baseline`: Latest baseline snapshot (null if no baseline set)
- `current_market_data`: Current market price data (null if unavailable)
- `trading_status`: "RUNNING" or "PAUSED"
- `position_vs_baseline`: Delta between current total position value and baseline total value
  - `pct`: Percentage change (can be null if baseline is 0)
  - `abs`: Absolute change in dollars (can be null if baseline is 0)
- `stock_vs_baseline`: Delta between current stock value and baseline stock value
  - `pct`: Percentage change (can be null if baseline is 0)
  - `abs`: Absolute change in dollars (can be null if baseline is 0)

**Error Responses:**

- `404`: Position not found
- `500`: Internal server error

---

### 2. GET /marketdata

Get recent market data for a position.

**Request:**

```
GET /v1/tenants/{tenant_id}/portfolios/{portfolio_id}/positions/{position_id}/marketdata?limit=50
```

**Query Parameters:**

- `limit` (optional, default: 50): Maximum number of recent data points to return

**Response:**

```json
{
  "position_id": "pos_abc123",
  "asset_symbol": "AAPL",
  "latest": {
    "price": 155.0,
    "source": "Yahoo Finance",
    "timestamp": "2025-01-20T14:30:00Z",
    "is_market_hours": true
  },
  "recent": [
    {
      "timestamp": "2025-01-20T14:30:00Z",
      "price": 155.0,
      "open": 154.5,
      "high": 155.5,
      "low": 154.0,
      "close": 155.0,
      "volume": 1000000
    },
    {
      "timestamp": "2025-01-20T14:25:00Z",
      "price": 154.8,
      "open": 154.5,
      "high": 155.0,
      "low": 154.5,
      "close": 154.8,
      "volume": 950000
    }
  ]
}
```

**Response Fields:**

- `position_id`: Position identifier
- `asset_symbol`: Asset symbol (e.g., "AAPL")
- `latest`: Most recent market data point
- `recent`: Array of recent market data points (up to `limit`)

**Error Responses:**

- `404`: Position not found
- `400`: Position has no asset symbol
- `500`: Internal server error

---

### 3. GET /events

Get events for position cockpit from PositionEvaluationTimeline.

**Request:**

```
GET /v1/tenants/{tenant_id}/portfolios/{portfolio_id}/positions/{position_id}/events?limit=500&event_type=PRICE_UPDATE
```

**Query Parameters:**

- `limit` (optional, default: 500): Maximum number of events to return
- `event_type` (optional): Filter by event type (e.g., "PRICE_UPDATE", "TRIGGER_EVALUATED", "DAILY_CHECK")

**Response:**

```json
{
  "position_id": "pos_abc123",
  "total_count": 150,
  "events": [
    {
      "id": "evt_xyz789",
      "timestamp": "2025-01-20T14:30:00Z",
      "evaluation_type": "PRICE_UPDATE",
      "effective_price": 155.0,
      "anchor_price": 150.0,
      "action": "NONE",
      "action_reason": null,
      "open_price": 154.5,
      "high_price": 155.5,
      "low_price": 154.0,
      "close_price": 155.0,
      "volume": 1000000,
      "trigger_direction": "NONE",
      "guardrail_check": "PASS",
      "position_qty_before": 100.0,
      "position_qty_after": 100.0,
      "position_cash_before": 5000.0,
      "position_cash_after": 5000.0,
      "total_value_after": 20500.0
    }
  ]
}
```

**Response Fields:**

- `position_id`: Position identifier
- `total_count`: Total number of events returned (after filtering)
- `events`: Array of timeline events with full evaluation details

**Event Types:**

- `DAILY_CHECK`: Daily position evaluation
- `PRICE_UPDATE`: Market price update
- `TRIGGER_EVALUATED`: Trigger threshold evaluation
- `GUARDRAIL_CHECK`: Guardrail validation
- `ORDER_SUBMITTED`: Order submission
- `ORDER_FILLED`: Order execution

**Error Responses:**

- `404`: Position not found
- `501`: Timeline repository not available
- `500`: Internal server error

---

## Baseline Delta Calculations

### Position vs Baseline

Compares the current total position value (cash + stock value) to the baseline total value:

```
position_vs_baseline.pct = ((current_total_value - baseline_total_value) / baseline_total_value) * 100
position_vs_baseline.abs = current_total_value - baseline_total_value
```

Where:

- `current_total_value = position.cash + (position.qty * current_price)`
- `baseline_total_value = baseline.baseline_cash + baseline.baseline_stock_value`

### Stock vs Baseline

Compares the current stock value to the baseline stock value:

```
stock_vs_baseline.pct = ((current_stock_value - baseline_stock_value) / baseline_stock_value) * 100
stock_vs_baseline.abs = current_stock_value - baseline_stock_value
```

Where:

- `current_stock_value = position.qty * current_price`
- `baseline_stock_value = baseline.baseline_stock_value`

**Note:** If baseline values are 0, the percentage delta will be `null`. Absolute deltas are always calculated when baseline exists.

---

## Security

All endpoints require:

- Valid `tenant_id`
- Valid `portfolio_id` that belongs to the tenant
- Valid `position_id` that belongs to the portfolio

The API enforces these relationships and returns 404 if any relationship is invalid.

---

## Rate Limiting

- Cockpit endpoint: Recommended refresh interval: 30 seconds
- Market data endpoint: Recommended refresh interval: 30 seconds
- Events endpoint: Recommended refresh interval: 10 seconds

---

## Notes

- All timestamps are in ISO 8601 format with timezone (UTC)
- All monetary values are in USD
- All quantities are in shares/units
- Market data may be unavailable during off-hours or for certain assets
- Baseline may be null if no baseline has been set for the position







