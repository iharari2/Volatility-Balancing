# Trading Flow Decomposition & Testing Strategy

## Overview
This document breaks down the live trading flow into discrete, testable steps with clear testing strategies for each step. Each step should be tested independently before integration.

---

## Flow Diagram

```
1. Position Discovery
   ↓
2. Market Data Fetching
   ↓
3. Configuration Loading
   ↓
4. Position Evaluation (EvaluatePositionUC)
   ├─ 4a. Anchor Price Check/Reset
   ├─ 4b. Trigger Evaluation
   ├─ 4c. Order Proposal Calculation
   ├─ 4d. Guardrail Validation
   └─ 4e. Timeline Logging
   ↓
5. Order Submission (SubmitOrderUC)
   ├─ 5a. Order Creation
   ├─ 5b. Idempotency Check
   └─ 5c. Order Persistence
   ↓
6. Order Execution (ExecuteOrderUC)
   ├─ 6a. Guardrail Re-validation
   ├─ 6b. Position State Update
   ├─ 6c. Trade Record Creation
   └─ 6d. Event Logging
   ↓
7. Position State Persistence
```

---

## Step 1: Position Discovery

**Purpose**: Find the position and its associated tenant/portfolio IDs.

**Code Location**: 
- `LiveTradingOrchestrator.run_cycle_for_position()` (lines 137-166)
- `ContinuousTradingService._monitor_position()` (lines 250-280)

**Inputs**:
- `position_id: str`

**Outputs**:
- `position: Position` entity
- `tenant_id: str`
- `portfolio_id: str`
- `portfolio: Portfolio` entity (optional)

**Dependencies**:
- `IPositionRepository.get()`
- `PortfolioRepo.list_all()`

**Testing Strategy**:
1. **Unit Test**: Mock repositories, test position lookup across portfolios
2. **Integration Test**: Use real SQLite DB, verify position found in correct portfolio
3. **Edge Cases**:
   - Position doesn't exist → should return None/raise
   - Position exists but portfolio not found → should handle gracefully
   - Multiple portfolios with same position_id → should find first match

**Test Script**: `backend/scripts/test_step1_position_discovery.py`

---

## Step 2: Market Data Fetching

**Purpose**: Get current market price for the position's asset.

**Code Location**:
- `LiveTradingOrchestrator.run_cycle_for_position()` (line 126)
- `ContinuousTradingService._monitor_position()` (line 260)

**Inputs**:
- `ticker: str` (from position.asset_symbol)

**Outputs**:
- `quote: MarketQuote` with `price: Decimal`, `timestamp: datetime`

**Dependencies**:
- `IMarketDataProvider.get_latest_quote()`

**Testing Strategy**:
1. **Unit Test**: Mock market data provider, return fixed price
2. **Integration Test**: Use real YFinance adapter, verify price format (Decimal)
3. **Edge Cases**:
   - Market closed → should return last known price or handle gracefully
   - Network error → should retry or use cached value
   - Invalid ticker → should raise clear error

**Test Script**: `backend/scripts/test_step2_market_data.py`

---

## Step 3: Configuration Loading

**Purpose**: Load trigger, guardrail, and order policy configurations.

**Code Location**:
- `LiveTradingOrchestrator.run_cycle_for_position()` (lines 405-428)
- Config providers in `app/di.py` (lines 356-415)

**Inputs**:
- `tenant_id: str`
- `portfolio_id: str`
- `position_id: str`

**Outputs**:
- `trigger_config: TriggerConfig`
- `guardrail_config: GuardrailConfig`
- `order_policy_config: OrderPolicyConfig`

**Dependencies**:
- `trigger_config_provider()`
- `guardrail_config_provider()`
- `order_policy_config_provider()`

**Testing Strategy**:
1. **Unit Test**: Mock config providers, verify correct configs returned
2. **Integration Test**: Use real ConfigRepo, verify configs match position settings
3. **Edge Cases**:
   - Config not found → should fallback to position.order_policy
   - Invalid config format → should raise clear error
   - Missing tenant_id/portfolio_id → should handle gracefully

**Test Script**: `backend/scripts/test_step3_config_loading.py`

---

## Step 4: Position Evaluation (EvaluatePositionUC)

**Purpose**: Evaluate if a trigger has fired and calculate order proposal.

**Code Location**: 
- `EvaluatePositionUC.evaluate()` (lines 55-342)
- Called from orchestrator (line 177) and continuous service (line 295)

**Inputs**:
- `tenant_id: str`
- `portfolio_id: str`
- `position_id: str`
- `current_price: float`

**Outputs**:
- `evaluation_result: Dict` with:
  - `trigger_detected: bool`
  - `order_proposal: Dict | None`
  - `action: str` ("HOLD" | "BUY" | "SELL")
  - `reasoning: str`

**Sub-steps**:

### 4a. Anchor Price Check/Reset
- **Code**: `_check_and_reset_anchor_if_anomalous()` (line 344)
- **Test**: Verify anchor reset when price deviates >50% from anchor

### 4b. Trigger Evaluation
- **Code**: `PriceTrigger.evaluate()` (called internally)
- **Test**: Verify trigger fires when price crosses thresholds

### 4c. Order Proposal Calculation
- **Code**: `_calculate_order_proposal()` (line 450)
- **Test**: Verify qty calculation matches formula: `ΔQ = (P_anchor/P - 1) × r × ((A+C)/P)`

### 4d. Guardrail Validation
- **Code**: `_apply_guardrail_trimming()` (line 594)
- **Test**: Verify qty trimmed to respect min/max stock %, max trade %

### 4e. Timeline Logging
- **Code**: `_write_timeline_row()` (line 1128)
- **Test**: Verify timeline row written with all required fields

**Testing Strategy**:
1. **Unit Test**: Mock all dependencies, test each sub-step independently
2. **Integration Test**: Use real repos, verify end-to-end evaluation
3. **Type Safety**: Ensure all Decimal/float conversions work correctly
4. **Edge Cases**:
   - Price exactly at threshold → should trigger
   - Negative qty (SELL) → should be handled correctly
   - Guardrails prevent trade → should return valid=False

**Test Script**: `backend/scripts/test_step4_position_evaluation.py`

---

## Step 5: Order Submission (SubmitOrderUC)

**Purpose**: Create and persist an order record.

**Code Location**:
- `SubmitOrderUC.execute()` 
- Called via `LiveOrderServiceAdapter.submit_live_order()` (line 56)

**Inputs**:
- `tenant_id: str`
- `portfolio_id: str`
- `position_id: str`
- `request: CreateOrderRequest` (side, qty)
- `idempotency_key: str`

**Outputs**:
- `response: CreateOrderResponse` with `order_id: str`, `accepted: bool`

**Sub-steps**:

### 5a. Order Creation
- **Code**: `Order` entity creation
- **Test**: Verify order has correct side, qty, status="submitted"

### 5b. Idempotency Check
- **Code**: Idempotency port check
- **Test**: Verify duplicate idempotency_key returns existing order

### 5c. Order Persistence
- **Code**: `orders.save()`
- **Test**: Verify order saved to database

**Testing Strategy**:
1. **Unit Test**: Mock repos, verify order creation logic
2. **Integration Test**: Use real SQLite, verify order persisted correctly
3. **Edge Cases**:
   - Duplicate idempotency_key → should return existing order
   - Invalid side → should reject
   - Zero qty → should reject

**Test Script**: `backend/scripts/test_step5_order_submission.py`

---

## Step 6: Order Execution (ExecuteOrderUC)

**Purpose**: Fill the order, update position, create trade record.

**Code Location**:
- `ExecuteOrderUC.execute()` (line 61)
- Called from orchestrator (line 298) and continuous service (line 404)

**Inputs**:
- `order_id: str`
- `request: FillOrderRequest` (qty, price, commission)

**Outputs**:
- `response: FillOrderResponse` with `order_id`, `status`, `filled_qty`, `trade_id`

**Sub-steps**:

### 6a. Guardrail Re-validation
- **Code**: `GuardrailEvaluator.evaluate()` (line 150)
- **Test**: Verify guardrails checked again before execution

### 6b. Position State Update
- **Code**: Lines 215-226
- **Test**: Verify cash and qty updated correctly:
  - BUY: `qty += q_req`, `cash -= (q_req * price) + commission`
  - SELL: `qty -= q_req`, `cash += (q_req * price) - commission`

### 6c. Trade Record Creation
- **Code**: Lines 229-244
- **Test**: Verify trade record created with correct side, qty, price, commission

### 6d. Event Logging
- **Code**: Lines 247-280
- **Test**: Verify EXECUTION_RECORDED event logged

**Testing Strategy**:
1. **Unit Test**: Mock repos, verify state updates
2. **Integration Test**: Use real SQLite, verify:
   - Position cash/qty updated
   - Trade record created
   - Events logged
3. **Type Safety**: Ensure Decimal/float conversions work
4. **Edge Cases**:
   - Guardrail breach → should raise GuardrailBreach exception
   - Insufficient cash (BUY) → should be caught by guardrails
   - Negative qty (SELL) → should be caught by guardrails

**Test Script**: `backend/scripts/test_step6_order_execution.py`

---

## Step 7: Position State Persistence

**Purpose**: Ensure position state changes are persisted to database.

**Code Location**:
- `PositionRepository.save()` (called implicitly after ExecuteOrderUC)

**Inputs**:
- Updated `Position` entity

**Outputs**:
- Position saved to database

**Testing Strategy**:
1. **Integration Test**: Verify position reloaded from DB matches updated state
2. **Edge Cases**:
   - Concurrent updates → should handle locking/conflicts
   - Database error → should rollback transaction

**Test Script**: `backend/scripts/test_step7_position_persistence.py`

---

## End-to-End Test Strategy

### Test 1: Complete Happy Path
1. Create position with known state
2. Set trigger config to fire at current price
3. Run cycle
4. Verify:
   - Order created
   - Trade executed
   - Position updated
   - Events logged
   - Cash/qty changed correctly

### Test 2: Guardrail Blocking
1. Create position
2. Set guardrails to prevent trade
3. Run cycle
4. Verify:
   - Trigger detected
   - Order proposal created
   - Order rejected by guardrails
   - No trade executed
   - Position unchanged

### Test 3: Type Safety
1. Use Decimal prices throughout
2. Verify no TypeError from Decimal/float mixing
3. Verify JSON serialization works

---

## Test Script Template

Each test script should follow this structure:

```python
#!/usr/bin/env python3
"""Test Step X: [Step Name]"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.di import container

def test_step():
    """Test the step with real dependencies."""
    print("=" * 80)
    print(f"Testing Step X: [Step Name]")
    print("=" * 80)
    
    # Setup
    # ... create test data ...
    
    # Execute
    try:
        result = # ... call step function ...
        print(f"✅ Step X passed: {result}")
        return True
    except Exception as e:
        print(f"❌ Step X failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_step()
    sys.exit(0 if success else 1)
```

---

## Implementation Plan

1. **Create test scripts** for each step (Steps 1-7)
2. **Run each test independently** and fix issues
3. **Create integration test** that runs all steps in sequence
4. **Fix type mismatches** as they're discovered
5. **Add error handling** for edge cases
6. **Verify event logging** at each step
7. **Test with real positions** from database

---

## Common Issues to Watch For

1. **Type Mismatches**: Decimal vs float
   - Always convert: `float(decimal_value)` or `Decimal(str(float_value))`
   - Check: `_calculate_order_proposal()`, `_write_timeline_row()`, `ExecuteOrderUC.execute()`

2. **Missing tenant_id/portfolio_id**
   - Always search for position first
   - Store IDs for later use

3. **JSON Serialization**
   - Convert Decimal to float before JSON serialization
   - Use `_make_json_serializable()` helper

4. **OrderSide Type**
   - Use string literals `"BUY"` / `"SELL"`, not `OrderSide.BUY`
   - `OrderSide` is a `Literal` type, not an enum

5. **Event Logging**
   - Ensure all events logged with correct trace_id
   - Verify parent_event_id links events correctly

---

## Next Steps

1. Create test scripts for Steps 1-7
2. Run each test and fix issues
3. Once all steps pass individually, test end-to-end
4. Document any remaining issues
5. Create regression tests to prevent future issues



