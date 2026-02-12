# Trade Execution Issues - Investigation Report

**Date:** 2024-12-19  
**Issue:** Trades running for >1 week with ZIM and AAPL, but no successful buy/sell actions logged and no cash balance changes observed.

## Executive Summary

Multiple critical bugs prevent trades from executing in the continuous trading service. The primary issue is an incorrect method call that causes evaluation to fail silently, preventing any trades from being submitted. Additionally, execution events are not being logged even when trades do execute.

## Issues Found

### 🔴 CRITICAL: Issue #1 - Incorrect Method Call in Continuous Trading Service

**Location:** `backend/application/services/continuous_trading_service.py:295`

**Problem:**
The `evaluate()` method is called with incorrect parameters:

```python
evaluation = eval_uc.evaluate(position_id, current_price)
```

**Expected Signature:**
```python
def evaluate(
    self, tenant_id: str, portfolio_id: str, position_id: str, current_price: float
) -> Dict[str, Any]:
```

**Impact:**
- This causes a `TypeError` when the method is called
- The exception is caught by the generic exception handler (line 495-498)
- Evaluation fails silently, preventing any trigger detection or order proposals
- No trades can be executed because evaluation never succeeds

**Evidence:**
- The code has `tenant_id` and `portfolio_id` available earlier (lines 227-238)
- The method signature requires 4 parameters but only 2 are provided
- This is a simple parameter mismatch bug

**Fix Required:**
Change line 295 from:
```python
evaluation = eval_uc.evaluate(position_id, current_price)
```
To:
```python
evaluation = eval_uc.evaluate(tenant_id, portfolio_id, position_id, current_price)
```

---

### 🟡 HIGH: Issue #2 - Missing EXECUTION_RECORDED Event Logging

**Location:** `backend/application/services/continuous_trading_service.py:403-415`

**Problem:**
After successfully executing a trade (line 403-405), the code does NOT log an `EXECUTION_RECORDED` event. The code only logs:
- `ORDER_CREATED` event (line 372-388)
- But no `EXECUTION_RECORDED` event after successful fill

**Expected Behavior:**
According to the audit logging guide (`backend/docs/AUDIT_LOGGING_GUIDE.md`), the event flow should be:
```
PriceEvent → TriggerEvaluated → GuardrailEvaluated → OrderCreated → ExecutionRecorded → PositionUpdated
```

**Current State:**
- `ORDER_CREATED` is logged ✓
- `EXECUTION_RECORDED` is NOT logged ✗
- `POSITION_UPDATED` is NOT logged ✗

**Impact:**
- No audit trail of successful trade executions
- Cannot track which trades were actually filled
- Makes debugging and reconciliation impossible

**Fix Required:**
Add `EXECUTION_RECORDED` event logging after successful execution (around line 411):

```python
if fill_response.status == "filled":
    status.total_trades += 1
    
    # Log execution event
    if event_logger:
        execution_event = event_logger.log(
            EventType.EXECUTION_RECORDED,
            asset_id=position.asset_symbol,
            trace_id=trace_id,
            parent_event_id=order_event.event_id if 'order_event' in locals() else None,
            source="continuous_trading",
            payload={
                "position_id": position_id,
                "order_id": submit_response.order_id,
                "trade_id": None,  # ExecuteOrderUC creates trade but doesn't return trade_id
                "filled_qty": fill_response.filled_qty,
                "price": current_price,
                "status": fill_response.status,
            },
        )
```

**Note:** The `ExecuteOrderUC.execute()` method creates a Trade entity and saves it, but doesn't return the trade_id. We may need to modify `ExecuteOrderUC` to return the trade_id in the response, or query it from the trades repo.

---

### 🟡 HIGH: Issue #3 - Missing POSITION_UPDATED Event Logging

**Location:** `backend/application/services/continuous_trading_service.py:411-415`

**Problem:**
After a successful trade execution, the position's cash and qty are updated by `ExecuteOrderUC`, but no `POSITION_UPDATED` event is logged to track the state change.

**Expected Behavior:**
After execution, log a `POSITION_UPDATED` event showing:
- Pre-trade cash and qty
- Post-trade cash and qty
- Cash change amount
- Qty change amount

**Impact:**
- No visibility into position state changes
- Cannot track cash balance changes over time
- Makes it impossible to verify trades actually affected position state

**Fix Required:**
Add `POSITION_UPDATED` event logging after successful execution. We need to:
1. Reload position after execution to get updated state
2. Calculate pre-trade state (reverse the changes)
3. Log the position update event

```python
if fill_response.status == "filled":
    status.total_trades += 1
    
    # Reload position to get updated state
    updated_position = container.positions.get(
        tenant_id=tenant_id,
        portfolio_id=portfolio_id,
        position_id=position_id,
    )
    
    # Calculate pre-trade state
    if order_proposal["side"] == "BUY":
        pre_trade_cash = updated_position.cash + (fill_response.filled_qty * current_price) + fill_commission
        pre_trade_qty = updated_position.qty - fill_response.filled_qty
    else:  # SELL
        pre_trade_cash = updated_position.cash - (fill_response.filled_qty * current_price) + fill_commission
        pre_trade_qty = updated_position.qty + fill_response.filled_qty
    
    # Log position update event
    if event_logger:
        position_event = event_logger.log(
            EventType.POSITION_UPDATED,
            asset_id=position.asset_symbol,
            trace_id=trace_id,
            parent_event_id=execution_event.event_id if 'execution_event' in locals() else None,
            source="continuous_trading",
            payload={
                "position_id": position_id,
                "pre_trade_cash": pre_trade_cash,
                "pre_trade_qty": pre_trade_qty,
                "post_trade_cash": updated_position.cash,
                "post_trade_qty": updated_position.qty,
                "cash_change": updated_position.cash - pre_trade_cash,
                "qty_change": updated_position.qty - pre_trade_qty,
            },
        )
```

---

### 🟢 MEDIUM: Issue #4 - ExecuteOrderUC Doesn't Return Trade ID

**Location:** `backend/application/use_cases/execute_order_uc.py:348`

**Problem:**
The `ExecuteOrderUC.execute()` method creates a Trade entity (line 231-245) but the `FillOrderResponse` doesn't include the `trade_id`. This makes it impossible to link execution events to trade records.

**Current Response:**
```python
return FillOrderResponse(order_id=order.id, status="filled", filled_qty=q_req)
```

**Fix Required:**
Modify `FillOrderResponse` to include `trade_id` and update the return statement:

```python
# In application/dto/orders.py, add trade_id to FillOrderResponse
class FillOrderResponse(BaseModel):
    order_id: str
    status: str
    filled_qty: float
    trade_id: Optional[str] = None  # Add this field

# In execute_order_uc.py, update return:
return FillOrderResponse(
    order_id=order.id, 
    status="filled", 
    filled_qty=q_req,
    trade_id=trade.id  # Add this
)
```

---

### 🟢 LOW: Issue #5 - Missing Error Logging for Evaluation Failures

**Location:** `backend/application/services/continuous_trading_service.py:495-498`

**Problem:**
When evaluation fails (e.g., due to Issue #1), the error is caught and logged to console, but no structured event is logged to the audit trail. This makes it difficult to track why evaluations are failing.

**Fix Required:**
Add structured error event logging:

```python
except Exception as e:
    print(f"⚠️  Error evaluating position: {e}")
    status.total_errors += 1
    status.last_error = str(e)
    
    # Log error event
    if event_logger:
        event_logger.log(
            EventType.TRIGGER_EVALUATED,  # Or create ERROR event type
            asset_id=position.asset_symbol,
            trace_id=trace_id,
            source="continuous_trading",
            payload={
                "position_id": position_id,
                "error": str(e),
                "error_type": type(e).__name__,
            },
        )
```

---

## Root Cause Analysis

The primary root cause is **Issue #1** - the incorrect method call prevents any evaluation from succeeding. This means:

1. Triggers are never detected (evaluation fails before trigger check)
2. No order proposals are generated
3. No orders are submitted
4. No trades are executed
5. Cash balance never changes

Even if Issue #1 is fixed, Issues #2 and #3 would still prevent proper audit logging, making it appear as if trades aren't executing even when they are.

## Recommended Fix Priority

1. **IMMEDIATE:** Fix Issue #1 (incorrect method call) - This is blocking all trades
2. **HIGH:** Fix Issue #2 (EXECUTION_RECORDED logging) - Required for audit trail
3. **HIGH:** Fix Issue #3 (POSITION_UPDATED logging) - Required to track cash changes
4. **MEDIUM:** Fix Issue #4 (return trade_id) - Improves traceability
5. **LOW:** Fix Issue #5 (error logging) - Improves debugging

## Testing Plan

After fixes are applied:

1. **Unit Test:** Verify `evaluate()` is called with correct parameters
2. **Integration Test:** Verify trades execute and cash balance changes
3. **Audit Trail Test:** Verify all events are logged in correct sequence:
   - PRICE_EVENT
   - TRIGGER_EVALUATED
   - GUARDRAIL_EVALUATED
   - ORDER_CREATED
   - EXECUTION_RECORDED
   - POSITION_UPDATED
4. **End-to-End Test:** Run continuous trading for 1 hour and verify:
   - Trades are executed when triggers fire
   - Cash balance changes match trade amounts
   - All events are logged correctly

## Additional Notes

- The `LiveTradingOrchestrator` (used by other paths) correctly logs `EXECUTION_RECORDED` events (line 303-317 in `live_trading.py`)
- The `SimulationOrchestrator` doesn't need execution logging (simulations use different flow)
- The `ExecuteOrderUC` creates domain `Event` entities (line 289), but these are different from `EventRecord` entities used by the unified event logger
- Consider creating a helper method to standardize event logging across all execution paths



