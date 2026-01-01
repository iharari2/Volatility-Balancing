# Next Steps - Verify Trades Are Executing

## ✅ What We've Fixed

1. **Code fixes applied:**
   - Fixed `evaluate()` method call (now includes tenant_id, portfolio_id)
   - Fixed `submit_order()` method call
   - Added EXECUTION_RECORDED event logging
   - Added POSITION_UPDATED event logging
   - Added trade_id to FillOrderResponse

2. **Trading started:**
   - Continuous trading started for `pos_f0c83651` (AAPL)
   - Continuous trading started for `pos_c955d000` (ZIM)

## ⚠️  Critical: Fix Portfolio State

**The portfolio state must be RUNNING for trades to execute!**

Run this to fix it:
```bash
cd backend
python scripts/fix_portfolio_state.py
```

This will set portfolio `pf_e009a8b4` (Blue Chips) to RUNNING state.

## Monitor Trading Activity

### Option 1: Use the Monitoring Script

```bash
# Monitor a specific position for 60 seconds
python scripts/monitor_trading.py pos_f0c83651

# Monitor for longer (5 minutes)
python scripts/monitor_trading.py pos_f0c83651 --duration 300

# List all active positions
python scripts/monitor_trading.py --all
```

### Option 2: Check Trading Status via API

```bash
# Check status
curl http://localhost:8000/v1/trading/status/pos_f0c83651

# List all active
curl http://localhost:8000/v1/trading/active
```

### Option 3: Check Database Directly

```bash
# Check recent events
sqlite3 vb.sqlite "SELECT type, created_at, message FROM events WHERE position_id = 'pos_f0c83651' ORDER BY created_at DESC LIMIT 10;"

# Check recent trades
sqlite3 vb.sqlite "SELECT side, qty, price, executed_at FROM trades WHERE position_id = 'pos_f0c83651' ORDER BY executed_at DESC LIMIT 5;"

# Check cash balance changes
sqlite3 vb.sqlite "SELECT id, cash, qty, updated_at FROM positions WHERE id = 'pos_f0c83651';"
```

## What to Look For

### ✅ Signs Trades Are Working:

1. **Trading Status shows trades:**
   ```json
   {
     "total_trades": 1,  // Should increase
     "total_checks": 5,  // Should increase every 5 minutes
     "total_errors": 0
   }
   ```

2. **Events in database:**
   - `EXECUTION_RECORDED` events (new - added by our fix)
   - `POSITION_UPDATED` events (new - added by our fix)
   - `ORDER_CREATED` events
   - `TRIGGER_EVALUATED` events

3. **Trades in database:**
   - Rows in `trades` table
   - `side` = 'BUY' or 'SELL'
   - `executed_at` timestamp

4. **Cash/Qty changes:**
   - `cash` balance changes after BUY (decreases) or SELL (increases)
   - `qty` changes after BUY (increases) or SELL (decreases)

### ❌ If Trades Still Don't Execute:

1. **Check portfolio state:**
   ```bash
   sqlite3 vb.sqlite "SELECT id, name, trading_state FROM portfolios WHERE id = 'pf_e009a8b4';"
   ```
   Must be `RUNNING`

2. **Check for errors:**
   ```bash
   curl http://localhost:8000/v1/trading/status/pos_f0c83651
   ```
   Look at `last_error` field

3. **Check trigger conditions:**
   - Price must move > threshold from anchor
   - AAPL anchor: $273.67, threshold likely 3% → buy at <$265.46, sell at >$281.88
   - ZIM anchor: $19.56, threshold likely 3% → buy at <$18.97, sell at >$20.15

4. **Check guardrails:**
   - Enough cash for BUY
   - Enough qty for SELL
   - Not hitting min/max allocation limits

5. **Check logs:**
   - Look at server console output
   - Should see "🔍 Evaluating position..." messages
   - Should see "✅ Auto-trade executed..." if trades happen

## Expected Timeline

- **Immediate:** Trading service starts monitoring
- **Within 5 minutes:** First evaluation cycle runs
- **When trigger fires:** Trade executes (if conditions met)
- **After trade:** Cash/qty change, events logged

## Troubleshooting

If after fixing portfolio state and waiting 10+ minutes you still see no trades:

1. **Verify evaluation is working:**
   ```bash
   python scripts/diagnose_trading_issue.py pos_f0c83651
   ```

2. **Manually trigger a cycle:**
   ```bash
   curl -X POST "http://localhost:8000/v1/trading/cycle?position_id=pos_f0c83651"
   ```

3. **Check if triggers are firing:**
   - Current price vs anchor price
   - Threshold percentage
   - Price must move significantly to trigger

4. **Check application logs** for detailed error messages



