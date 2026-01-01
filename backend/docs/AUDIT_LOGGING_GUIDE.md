# Audit Trail Logging Guide

## Overview

The Volatility Balancing system includes a comprehensive audit trail logging system that provides complete traceability of trading activity from market data ingestion through position updates.

## Architecture

### Unified Event Model

All events follow a unified `EventRecord` model with:

- `event_id`: Unique identifier for the event
- `event_type`: Type of event (PriceEvent, TriggerEvaluated, etc.)
- `trace_id`: Links all events in a single trading cycle
- `parent_event_id`: Links events in a parent-child chain
- `tenant_id`, `portfolio_id`, `asset_id`: Multi-tenant support
- `payload`: Event-specific data
- `created_at`: Timestamp

### Event Types

- **PRICE_EVENT**: Market price data received
- **TRIGGER_EVALUATED**: Price trigger evaluation result
- **GUARDRAIL_EVALUATED**: Guardrail check result
- **ORDER_CREATED**: Order submitted to broker
- **EXECUTION_RECORDED**: Trade execution recorded
- **POSITION_UPDATED**: Position state changed
- **DIVIDEND_PAID**: Dividend payment processed

### Logging Infrastructure

- **JsonFileEventLogger**: Writes events to JSONL file (`backend/logs/audit_trail.jsonl`)
- **CompositeEventLogger**: Logs to both unified logger and old EventsRepo (backward compatibility)
- **UnifiedEventLoggerAdapter**: Bridges old IEventLogger interface to new unified system

## Usage

### Viewing Audit Trails

#### Streamlit GUI

Launch the audit viewer:

```bash
streamlit run ui/audit_viewer.py
```

Features:

- Filter by tenant, portfolio, asset, trace_id, date range
- View events in Timeline, By Trace, or Tree mode
- Export to CSV or JSON
- Collapsible JSON payloads
- Color-coded event types

#### CLI Tool

Print audit trail for a specific trace:

```bash
python tools/print_audit_trail.py --trace-id <uuid>
```

Options:

- `--trace-id`: Required trace ID
- `--log-file`: Path to log file (default: `backend/logs/audit_trail.jsonl`)
- `--json`: Output as JSON instead of formatted text

Example output:

```
[09:00:00] PriceEvent price=96.9 anchor=100
[09:00:00] TriggerEvaluated BUY trigger fired: BELOW_THRESHOLD
[09:00:00] GuardrailEvaluated Guardrail allowed BUY 20: within limits
[09:00:01] OrderCreated Order abc123 BUY 20 @ 96.9 commission_est 1.94
[09:00:02] ExecutionRecorded Execution xyz789 BUY 20 @ 96.9 commission 1.94
[09:00:02] PositionUpdated Position qty 0→20 cash 10000→8070.06
```

## Logging Points

Events are logged at these critical points:

1. **Price Ingestion** (orchestrators)

   - When market data is fetched
   - Includes price, anchor price, timestamp

2. **Trigger Evaluation** (orchestrators)

   - After PriceTrigger.evaluate()
   - Includes trigger decision, direction, reason

3. **Guardrail Evaluation** (orchestrators)

   - After GuardrailEvaluator.evaluate()
   - Includes allowed/denied, reason, trade intent

4. **Order Creation** (orchestrators, use cases)

   - When order is submitted
   - Includes order_id, trade_intent, commission estimate

5. **Execution Recording** (use cases)

   - When trade is executed
   - Includes trade_id, actual commission, fill details

6. **Position Update** (use cases)
   - After position state changes
   - Includes before/after state comparison

## Trace ID Management

Each trading cycle gets a unique `trace_id` that links all related events:

- Live trading: New trace_id per cycle
- Simulation: Uses `simulation_run_id` as trace_id

Events are linked via `parent_event_id` to show the flow:

```
PriceEvent → TriggerEvaluated → GuardrailEvaluated → OrderCreated → ExecutionRecorded → PositionUpdated
```

## Configuration

Log file location: `backend/logs/audit_trail.jsonl`

The log directory is created automatically on first use.

## Integration

The unified event logger is integrated into:

- `LiveTradingOrchestrator`: Logs all live trading events
- `SimulationOrchestrator`: Logs all simulation events
- DI Container: Provides unified logger to orchestrators

## Backward Compatibility

The system maintains backward compatibility:

- Old `EventsRepo` still works
- `CompositeEventLogger` logs to both systems
- Existing code using old interface continues to work

## Future Enhancements

- Database-backed event storage
- Real-time event streaming
- Event aggregation and analytics
- Visual DAG of event relationships
- Price charts with trigger points overlaid


















