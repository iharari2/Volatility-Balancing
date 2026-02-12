# Simulation Setup and Usage Guide

## Overview

The simulation system is now fully operational and supports:
1. **Standalone simulations** - Run simulations for any ticker without creating a position
2. **Position-based simulations** - Run simulations using an existing position's configuration

## Quick Start: 1-Year AAPL Simulation

### Option 1: Using the Test Script

Run the provided test script:

```bash
python test_aapl_simulation.py
```

This script will:
- Run a complete 1-year AAPL simulation
- Use 30-minute intraday intervals
- Start with $10,000 initial cash
- Display comprehensive results

### Option 2: Using the API Directly

```bash
curl -X POST http://localhost:8000/v1/simulation/run \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "AAPL",
    "start_date": "2023-12-23T00:00:00Z",
    "end_date": "2024-12-23T23:59:59Z",
    "initial_cash": 10000.0,
    "include_after_hours": false,
    "intraday_interval_minutes": 30,
    "position_config": {
      "trigger_threshold_pct": 0.03,
      "rebalance_ratio": 1.6667,
      "commission_rate": 0.0001,
      "min_notional": 100.0,
      "allow_after_hours": false,
      "guardrails": {
        "min_stock_alloc_pct": 0.25,
        "max_stock_alloc_pct": 0.75
      }
    }
  }'
```

### Option 3: Using the Audit Viewer UI

1. Start the backend:
   ```bash
   cd backend
   python -m uvicorn app.main:app --reload
   ```

2. Start the audit viewer:
   ```bash
   streamlit run ui/audit_viewer.py
   ```

3. In the sidebar:
   - Leave "Position ID" empty
   - Enter "AAPL" in the "Ticker Symbol" field
   - Set start date to 1 year ago
   - Set end date to today
   - Click "🚀 Run Simulation"

## API Endpoints

### Standalone Simulation (No Position Required)

**POST** `/v1/simulation/run`

```json
{
  "ticker": "AAPL",
  "start_date": "2023-12-23T00:00:00Z",
  "end_date": "2024-12-23T23:59:59Z",
  "initial_cash": 10000.0,
  "include_after_hours": false,
  "intraday_interval_minutes": 30,
  "position_config": {
    "trigger_threshold_pct": 0.03,
    "rebalance_ratio": 1.6667,
    "commission_rate": 0.0001,
    "min_notional": 100.0,
    "allow_after_hours": false,
    "guardrails": {
      "min_stock_alloc_pct": 0.25,
      "max_stock_alloc_pct": 0.75
    }
  }
}
```

### Position-Based Simulation

**POST** `/v1/positions/{position_id}/simulation/run`

Uses the position's ticker and configuration automatically.

## Response Format

```json
{
  "simulation_id": "uuid-here",
  "ticker": "AAPL",
  "start_date": "2023-12-23T00:00:00+00:00",
  "end_date": "2024-12-23T23:59:59+00:00",
  "initial_cash": 10000.0,
  "total_trading_days": 252,
  "algorithm_return_pct": 15.5,
  "buy_hold_return_pct": 12.3,
  "excess_return": 3.2,
  "algorithm_trades": 45,
  "algorithm_pnl": 1550.0,
  "buy_hold_pnl": 1230.0,
  "sharpe_ratio": 1.25,
  "max_drawdown": -5.2,
  "volatility": 18.4
}
```

## Configuration Parameters

### Position Config

- **trigger_threshold_pct**: Price movement threshold to trigger trades (default: 0.03 = 3%)
- **rebalance_ratio**: Ratio for rebalancing trades (default: 1.6667)
- **commission_rate**: Commission rate per trade (default: 0.0001 = 0.01%)
- **min_notional**: Minimum trade size in dollars (default: 100.0)
- **allow_after_hours**: Whether to allow after-hours trading (default: false)

### Guardrails

- **min_stock_alloc_pct**: Minimum stock allocation percentage (default: 0.25 = 25%)
- **max_stock_alloc_pct**: Maximum stock allocation percentage (default: 0.75 = 75%)

### Simulation Settings

- **intraday_interval_minutes**: Time interval for intraday data (1, 5, 15, 30, 60 minutes)
  - For 1-year simulations, 30 minutes is recommended for balance between detail and performance
  - For shorter periods, you can use 1-5 minute intervals
  - For longer periods, consider 60 minutes or daily data

## Performance Notes

- **1-year simulations** with 30-minute intervals typically take 2-5 minutes
- **Longer periods** or **shorter intervals** will take proportionally longer
- The simulation uses real historical market data from yfinance
- Results are cached and can be retrieved later using the simulation_id

## Troubleshooting

### "Simulation timed out"
- Reduce the date range
- Increase `intraday_interval_minutes` (e.g., from 30 to 60)
- Check backend logs for errors

### "No market data available"
- Verify the ticker symbol is correct
- Check internet connection (yfinance requires internet)
- Try a different ticker to verify market data service is working

### "Position not found" (for position-based simulations)
- Verify the position_id exists
- Check that the position has a valid ticker/asset_symbol

## Example: Complete 1-Year AAPL Simulation

See `test_aapl_simulation.py` for a complete working example that:
- Sets up a 1-year date range
- Configures optimal parameters
- Handles errors gracefully
- Displays results in a readable format

Run it with:
```bash
python test_aapl_simulation.py
```

Make sure the backend is running first!






