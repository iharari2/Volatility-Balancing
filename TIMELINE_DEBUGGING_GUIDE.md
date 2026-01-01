# Step-by-Step Guide: Debugging Empty Timeline Table

## Prerequisites
- Backend server is running on port 8000
- You have a position ID (e.g., `pos_c955d000` from your logs)
- Terminal access to run commands

---

## Step 1: Verify Backend Server is Running

**Check if the server is running:**
```bash
curl http://localhost:8000/v1/healthz
```

**Expected response:** `{"status": "ok"}`

**If not running, start it:**
```bash
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## Step 2: Find Your Position ID

**From your logs, you have:**
- Position ID: `pos_c955d000`
- Portfolio ID: `pf_e009a8b4`
- Tenant ID: `default`

**Or list all positions:**
```bash
curl http://localhost:8000/v1/positions
```

---

## Step 3: Manually Trigger an Evaluation

**Option A: Use the `/tick` endpoint (recommended - uses live market data):**
```bash
curl -X POST http://localhost:8000/v1/positions/pos_c955d000/tick
```

**Option B: Use the `/evaluate` endpoint (with specific price):**
```bash
curl -X POST "http://localhost:8000/v1/positions/pos_c955d000/evaluate?current_price=150.0"
```

**Option C: Use the `/evaluate/market` endpoint (uses live market data):**
```bash
curl -X POST http://localhost:8000/v1/positions/pos_c955d000/evaluate/market
```

---

## Step 4: Watch the Server Logs

**After triggering an evaluation, look for these log messages in your server console:**

### ✅ Success Indicators:
```
📝 Attempting to save timeline row for position pos_c955d000...
📝 Executing INSERT with X columns, action='HOLD'
✅✅✅ Timeline record saved successfully! ID: eval_xxxxx
✅✅✅ Timeline row saved successfully! Record ID: eval_xxxxx
```

### ❌ Failure Indicators:
```
⚠️  Failed to write timeline row: [error message]
❌❌❌ Timeline save failed with exception:
   Error type: [error type]
   Error message: [error details]
```

**If you see errors, copy the full error message and traceback.**

---

## Step 5: Check the Database Directly

**Find your database file:**
```bash
# Default location (check your SQL_URL env var)
ls -la backend/vb.sqlite
# Or
ls -la backend/data/trading.db
```

**Check if records exist:**
```bash
sqlite3 backend/vb.sqlite "SELECT COUNT(*) FROM position_evaluation_timeline;"
```

**List recent records:**
```bash
sqlite3 backend/vb.sqlite "SELECT id, position_id, evaluated_at, action, action_taken FROM position_evaluation_timeline ORDER BY evaluated_at DESC LIMIT 5;"
```

**Check the table schema:**
```bash
sqlite3 backend/vb.sqlite ".schema position_evaluation_timeline"
```

---

## Step 6: Verify Timeline Records via API

**Check if records are being returned:**
```bash
curl "http://localhost:8000/v1/tenants/default/portfolios/pf_e009a8b4/positions/pos_c955d000/timeline?limit=10"
```

**Expected response:** JSON array with timeline records (or empty array `[]` if no records)

---

## Step 7: Check Trading Worker Status

**If you want to check if automatic evaluations are running:**
```bash
curl http://localhost:8000/v1/trading/status
```

**Manually trigger a trading cycle:**
```bash
curl -X POST http://localhost:8000/v1/trading/cycle
```

---

## Common Issues and Solutions

### Issue 1: No logs showing "📝 Attempting to save..."
**Problem:** `_write_timeline_row` is not being called
**Solution:** Check if `evaluate()` method is actually being called. Look for evaluation logs.

### Issue 2: Logs show "❌❌❌ Timeline save failed"
**Problem:** Save is failing due to constraint or schema issues
**Solution:** 
- Check the error message for specific constraint violations
- Verify `action_taken` column has correct value: `NO_ACTION`, `ORDER_PROPOSED`, `ORDER_SUBMITTED`, or `ORDER_EXECUTED`
- Verify `action` column (if exists) has correct value: `BUY`, `SELL`, `HOLD`, or `SKIP`

### Issue 3: Records exist in database but API returns empty
**Problem:** `list_by_position` query is failing
**Solution:** Already fixed - should use `evaluated_at` instead of `timestamp`

### Issue 4: "no such column: timestamp" error
**Problem:** Query is using wrong column name
**Solution:** Already fixed - should use `evaluated_at` or fallback to `id`

---

## Quick Test Script

**Create a test script to verify everything works:**

```bash
# Save this as test_timeline.sh
#!/bin/bash

POSITION_ID="pos_c955d000"
BASE_URL="http://localhost:8000"

echo "1. Checking server health..."
curl -s $BASE_URL/v1/healthz
echo -e "\n"

echo "2. Triggering evaluation..."
curl -X POST "$BASE_URL/v1/positions/$POSITION_ID/tick"
echo -e "\n"

echo "3. Checking timeline records..."
curl -s "$BASE_URL/v1/tenants/default/portfolios/pf_e009a8b4/positions/$POSITION_ID/timeline?limit=5" | jq 'length'
echo -e "\n"

echo "4. Checking database directly..."
sqlite3 backend/vb.sqlite "SELECT COUNT(*) FROM position_evaluation_timeline WHERE position_id='$POSITION_ID';"
```

**Run it:**
```bash
chmod +x test_timeline.sh
./test_timeline.sh
```

---

## What to Report Back

If the table is still empty after following these steps, please provide:

1. **Server logs** showing:
   - Any "📝 Attempting to save..." messages
   - Any "✅✅✅ Timeline record saved..." messages
   - Any "❌❌❌ Timeline save failed..." messages with full error details

2. **Database query results:**
   ```bash
   sqlite3 backend/vb.sqlite "SELECT COUNT(*) FROM position_evaluation_timeline;"
   ```

3. **API response:**
   ```bash
   curl "http://localhost:8000/v1/tenants/default/portfolios/pf_e009a8b4/positions/pos_c955d000/timeline?limit=5"
   ```

4. **Table schema:**
   ```bash
   sqlite3 backend/vb.sqlite ".schema position_evaluation_timeline" | grep -E "(action|timestamp|evaluated_at)"
   ```

---

## Expected Flow

1. ✅ Server starts successfully
2. ✅ You trigger evaluation via API
3. ✅ Logs show "📝 Attempting to save timeline row..."
4. ✅ Logs show "✅✅✅ Timeline record saved successfully!"
5. ✅ Database query shows count > 0
6. ✅ API returns timeline records
7. ✅ UI displays timeline events

If any step fails, that's where we need to focus the debugging!



