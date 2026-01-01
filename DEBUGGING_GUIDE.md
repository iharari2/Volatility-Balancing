# Debugging Guide - Why Trades Aren't Executing

## Quick Diagnostic Steps

### 1. Run the Diagnostic Script

```bash
cd backend
python scripts/diagnose_trading_issue.py <position_id>
```

This will check:
- ✅ Position exists and has anchor_price
- ✅ Portfolio is in RUNNING state
- ✅ Continuous trading service is running
- ✅ Evaluation works correctly
- ✅ Triggers are detected

### 2. Check Common Issues

#### Issue: Position has no anchor_price
**Symptom:** Diagnostic shows "Position has NO anchor_price set"

**Fix:**
- Set anchor_price when creating position, OR
- Use API to update position anchor_price

#### Issue: Portfolio not in RUNNING state
**Symptom:** Diagnostic shows "Portfolio is NOT in RUNNING state"

**Fix:**
- Update portfolio trading_state to "RUNNING"
- Use API: `PUT /v1/portfolios/{portfolio_id}` with `trading_state: "RUNNING"`

#### Issue: Continuous trading not started
**Symptom:** Diagnostic shows "Continuous trading service is NOT running"

**Fix:**
- Start trading: `POST /v1/trading/start/{position_id}`

#### Issue: No trigger detected
**Symptom:** Evaluation shows "No trigger detected"

**Check:**
- Current price vs anchor price
- Trigger threshold percentage
- Price must move > threshold to trigger

**Example:**
- Anchor: $100
- Threshold: 3%
- Buy trigger: Price < $97 (3% down)
- Sell trigger: Price > $103 (3% up)

#### Issue: Order validation failed
**Symptom:** Order proposal exists but validation.valid = false

**Check:**
- Guardrails (min/max stock allocation)
- Cash balance (enough cash for BUY)
- Position quantity (enough qty for SELL)
- Order policy (min_qty, min_notional)

### 3. Check Application Logs

Look for:
- Error messages in console output
- Exception stack traces
- "Error evaluating position" messages
- Guardrail breach messages

### 4. Verify Code Fixes Are Applied

Check that these fixes are in place:

1. **Evaluate call has all 4 parameters:**
   ```python
   # Should be:
   evaluation = eval_uc.evaluate(tenant_id, portfolio_id, position_id, current_price)
   # NOT:
   evaluation = eval_uc.evaluate(position_id, current_price)
   ```

2. **Submit order call has all 5 parameters:**
   ```python
   # Should be:
   submit_response = submit_uc.execute(tenant_id, portfolio_id, position_id, order_request, idempotency_key)
   ```

3. **Event logging is present:**
   - EXECUTION_RECORDED events after trades
   - POSITION_UPDATED events after cash/qty changes

### 5. Manual Testing

Test evaluation manually:

```python
from app.di import container
from application.use_cases.evaluate_position_uc import EvaluatePositionUC

eval_uc = EvaluatePositionUC(
    positions=container.positions,
    events=container.events,
    market_data=container.market_data,
    clock=container.clock,
    portfolio_repo=container.portfolio_repo,
)

# Find position
position = None
tenant_id = "default"
portfolio_id = None
for portfolio in container.portfolio_repo.list_all(tenant_id=tenant_id):
    pos = container.positions.get(tenant_id, portfolio.id, "YOUR_POSITION_ID")
    if pos:
        position = pos
        portfolio_id = portfolio.id
        break

# Get current price
price_data = container.market_data.get_price(position.asset_symbol, force_refresh=True)
current_price = price_data.price

# Evaluate
result = eval_uc.evaluate(tenant_id, portfolio_id, position.id, current_price)
print(result)
```

### 6. Check Database

Query events table:
```sql
SELECT * FROM events 
WHERE position_id = 'YOUR_POSITION_ID' 
ORDER BY created_at DESC 
LIMIT 20;
```

Look for:
- PRICE_EVENT entries
- TRIGGER_EVALUATED entries
- ORDER_CREATED entries
- EXECUTION_RECORDED entries (should exist after fix)
- Error events

Query trades table:
```sql
SELECT * FROM trades 
WHERE position_id = 'YOUR_POSITION_ID' 
ORDER BY executed_at DESC;
```

Query positions table:
```sql
SELECT id, asset_symbol, qty, cash, anchor_price 
FROM positions 
WHERE id = 'YOUR_POSITION_ID';
```

Check if cash/qty are changing.

## Common Error Messages

### "No anchor price set - cannot evaluate triggers"
- **Cause:** Position.anchor_price is None
- **Fix:** Set anchor_price on position

### "Position not found"
- **Cause:** Position doesn't exist or wrong tenant_id/portfolio_id
- **Fix:** Verify position exists and IDs are correct

### "Portfolio is not RUNNING"
- **Cause:** Portfolio.trading_state != "RUNNING"
- **Fix:** Set portfolio trading_state to "RUNNING"

### "Guardrail breach"
- **Cause:** Trade would violate guardrails
- **Fix:** Check guardrail settings, adjust if needed

### "Evaluation failed" / TypeError
- **Cause:** Method called with wrong parameters (should be fixed now)
- **Fix:** Verify code fixes are applied

## Still Not Working?

If all checks pass but trades still don't execute:

1. **Check trigger thresholds:**
   - Are they too high? (e.g., 10% threshold means price must move 10%)
   - Try lowering threshold temporarily to test

2. **Check market data:**
   - Is price data being fetched correctly?
   - Is price_data.is_market_hours correct?
   - Are after-hours trades allowed?

3. **Check order policy:**
   - Is min_qty too high?
   - Is min_notional too high?
   - Is action_below_min set to "reject"?

4. **Enable debug logging:**
   - Add print statements in continuous_trading_service.py
   - Check console output for detailed flow

5. **Test with manual cycle:**
   - Use API: `POST /v1/trading/cycle?position_id=YOUR_POSITION_ID`
   - This runs one cycle manually and returns trace_id
   - Check events for that trace_id



