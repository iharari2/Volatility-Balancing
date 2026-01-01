# Engine/Console Separation Architecture

## Core Principle

**Trading must run even if no user is logged in and the GUI is completely down.**

The system is designed with a clear separation between:

- **Engine (Data Plane)**: Backend that runs trading cycles automatically
- **Console (Control Plane)**: React GUI that monitors and controls the engine

## Architecture Layers

### Engine Layer (Backend)

The engine runs independently and knows how to:

- Fetch market data
- Run `LiveTradingOrchestrator` cycles
- Place orders / record trades
- Log all events to audit trail

**Invoked by:**

- Scheduler / background worker (primary)
- Optional manual call from API (secondary)

### Console Layer (React Frontend)

The React app calls backend APIs to:

- Configure portfolios/strategies
- Manually trigger a cycle or simulation
- Read state, metrics, audit trails

**Key point:** If the React app is closed, the engine still runs.

## Implementation

### Trading Worker

The `TradingWorker` (`backend/application/services/trading_worker.py`) is a background service that:

1. Runs in a separate thread (daemon)
2. Periodically scans for active positions
3. Executes trading cycles via `LiveTradingOrchestrator`
4. Logs all events with `source="worker"`

**Configuration:**

- `TRADING_WORKER_INTERVAL_SECONDS`: How often to run cycles (default: 60 seconds)
- `TRADING_WORKER_ENABLED`: Enable/disable worker (default: true)

**Lifecycle:**

- Starts automatically when backend starts (`@app.on_event("startup")`)
- Stops gracefully on backend shutdown (`@app.on_event("shutdown")`)

### LiveTradingOrchestrator

The orchestrator supports two execution modes:

1. **`run_cycle(source="worker")`**: Runs cycle for all active positions
2. **`run_cycle_for_position(position_id, source="api/manual")`**: Runs cycle for a single position

Both methods:

- Use the same logic
- Log to the same audit trail
- Distinguish source via `source` parameter

### API Endpoints

#### Manual Cycle Trigger

```http
POST /v1/trading/cycle?position_id={optional}
```

- If `position_id` provided: Runs cycle for that position only
- If omitted: Runs cycle for all active positions
- Source is marked as `"api/manual"` in audit trail

#### Worker Status

```http
GET /v1/trading/worker/status
```

Returns:

```json
{
  "running": true,
  "enabled": true,
  "interval_seconds": 60
}
```

## Event Logging

All trading cycles, regardless of trigger source, log events to the unified audit trail:

- **PriceEvent**: Market data fetched
- **TriggerEvaluated**: Price trigger evaluation
- **GuardrailEvaluated**: Guardrail check
- **OrderCreated**: Order submitted
- **ExecutionRecorded**: Trade executed (via use cases)
- **PositionUpdated**: Position state changed (via use cases)

Events include a `source` field:

- `"worker"`: Scheduled cycle from background worker
- `"api/manual"`: Manual trigger from API/GUI
- `"continuous_trading"`: From ContinuousTradingService (legacy)

## React GUI Integration

### Trading Console

The React Trading Console:

- **Does NOT** own the trading loop
- **Does** call `POST /v1/trading/cycle` for manual "run now" actions
- **Does** display status from `GET /v1/trading/worker/status`
- **Does** read audit trail to show recent cycles

### UI Indicators

The GUI should clearly mark cycles as:

- **"Auto (worker)"**: Scheduled cycles from background worker
- **"Manual (console)"**: Manually triggered cycles

### Offline Operation

The GUI works even if never opened during a trading day:

- When opened later, it reads:
  - Current position state
  - Audit trail log
  - Recent trades and orders

## Configuration

### Active Positions

Positions are considered "active for trading" if they:

- Exist in the position repository
- Are returned by `IPositionRepository.get_active_positions_for_trading()`

Currently, this uses the position's `is_active` flag or similar repository logic.

### Future: Auto-Trading Flag

A future enhancement could add an explicit `auto_trading_enabled` flag to:

- Portfolio level: Enable/disable auto-trading for entire portfolio
- Position level: Enable/disable auto-trading for specific position

This would allow fine-grained control over which positions participate in scheduled cycles.

## Testing

### Manual Testing

1. Start backend: `python -m uvicorn app.main:app --reload`
2. Check worker status: `GET /v1/trading/worker/status`
3. Trigger manual cycle: `POST /v1/trading/cycle`
4. View audit trail: Streamlit GUI or CLI tool

### Verify Independence

1. Start backend
2. Create a position
3. Close all browser windows (GUI)
4. Wait for worker interval (60s default)
5. Check audit trail: Should see events with `source="worker"`

## Environment Variables

```bash
# Trading worker configuration
TRADING_WORKER_INTERVAL_SECONDS=60  # How often to run cycles (seconds)
TRADING_WORKER_ENABLED=true         # Enable/disable worker
```

## Summary

- ✅ Trading runs automatically via background worker
- ✅ Worker starts on backend startup, stops on shutdown
- ✅ Manual cycles available via API endpoint
- ✅ All cycles log to unified audit trail with source tracking
- ✅ React GUI is control panel only, not required for trading
- ✅ System continues operating even if GUI is closed
















