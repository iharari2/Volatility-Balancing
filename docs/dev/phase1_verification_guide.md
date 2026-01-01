# Phase 1 Verification Guide

**Date**: January 2025  
**Purpose**: Verify system is running and performs account creation, trading, and simulation correctly  
**Status**: Verification Checklist

---

## 🎯 **Verification Goals**

Verify that the system correctly performs:
1. ✅ **System Running** - Backend and frontend are operational
2. ✅ **Account Creation** - Positions can be created (this is the "account" in the system)
3. ✅ **Trading** - Orders can be submitted and executed
4. ✅ **Simulation** - Backtesting simulations work correctly

---

## 🚀 **Quick Verification**

### **Option 1: Automated Test Script (Recommended)**

Run the verification script:

```bash
# Make sure backend is running first
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# In another terminal, run verification
python verify_phase1.py
```

The script will test:
- ✅ Health check
- ✅ Position creation
- ✅ Get position details
- ✅ Submit order
- ✅ Fill order
- ✅ Evaluate position
- ✅ Run simulation
- ✅ List positions

### **Option 2: Manual Testing via API**

#### **1. Check System is Running**

```bash
curl http://localhost:8000/v1/healthz
```

**Expected Response**:
```json
{"status":"ok"}
```

#### **2. Create Position (Account Creation)**

```bash
curl -X POST http://localhost:8000/v1/positions \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "AAPL",
    "qty": 0.0,
    "cash": 10000.0,
    "order_policy": {
      "trigger_threshold_pct": 0.03,
      "rebalance_ratio": 1.6667,
      "commission_rate": 0.0001
    },
    "guardrails": {
      "min_stock_alloc_pct": 0.25,
      "max_stock_alloc_pct": 0.75,
      "max_orders_per_day": 5
    }
  }'
```

**Expected Response**:
```json
{
  "id": "pos_abc123...",
  "ticker": "AAPL",
  "qty": 0.0,
  "cash": 10000.0,
  "anchor_price": 150.25
}
```

**Save the `id` for next steps!**

#### **3. Get Position Details**

```bash
curl http://localhost:8000/v1/positions/{position_id}
```

Replace `{position_id}` with the ID from step 2.

#### **4. Submit Order (Trading)**

```bash
curl -X POST http://localhost:8000/v1/positions/{position_id}/orders \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: test_order_123" \
  -d '{
    "side": "BUY",
    "qty": 10.0
  }'
```

**Expected Response**:
```json
{
  "order_id": "ord_xyz789...",
  "accepted": true,
  "position_id": "pos_abc123..."
}
```

**Save the `order_id` for next step!**

#### **5. Fill Order (Trading Execution)**

```bash
curl -X POST http://localhost:8000/v1/orders/{order_id}/fill \
  -H "Content-Type: application/json" \
  -d '{
    "price": 150.0,
    "filled_qty": 10.0,
    "commission": 0.15
  }'
```

**Expected Response**:
```json
{
  "order_id": "ord_xyz789...",
  "status": "filled",
  "filled_qty": 10.0,
  "position_qty": 10.0,
  "position_cash": 8484.85
}
```

#### **6. Evaluate Position (Auto-sizing)**

```bash
curl -X POST "http://localhost:8000/v1/positions/{position_id}/evaluate?price=155.0"
```

**Expected Response**:
```json
{
  "trigger_detected": true,
  "current_price": 155.0,
  "order_proposal": {
    "side": "SELL",
    "raw_qty": 2.5,
    "trimmed_qty": 2.5,
    "notional": 387.5,
    "validation": {
      "valid": true
    }
  }
}
```

#### **7. Run Simulation**

```bash
curl -X POST http://localhost:8000/v1/simulation/run \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "AAPL",
    "start_date": "2024-12-01",
    "end_date": "2024-12-31",
    "initial_cash": 10000.0,
    "position_config": {
      "trigger_threshold_pct": 0.03,
      "rebalance_ratio": 1.6667,
      "commission_rate": 0.0001
    },
    "include_after_hours": false
  }'
```

**Expected Response** (may take 30-60 seconds):
```json
{
  "simulation_id": "...",
  "ticker": "AAPL",
  "algorithm_metrics": {
    "total_return_pct": 5.2,
    "total_trades": 12,
    "max_drawdown_pct": -2.1
  },
  "buy_hold_metrics": {
    "total_return_pct": 3.8
  },
  "comparison": {
    "excess_return_pct": 1.4
  }
}
```

---

## ✅ **Verification Checklist**

### **System Running**
- [ ] Backend starts without errors
- [ ] Health check endpoint returns `{"status":"ok"}`
- [ ] API documentation accessible at `http://localhost:8000/docs`

### **Account Creation (Position Creation)**
- [ ] Can create position with ticker and cash
- [ ] Position is saved to database
- [ ] Anchor price is automatically fetched from market data
- [ ] Can retrieve position by ID
- [ ] Can list all positions
- [ ] Position persists after backend restart (if using SQL persistence)

### **Trading**
- [ ] Can submit BUY order
- [ ] Can submit SELL order
- [ ] Idempotency works (same key returns same order)
- [ ] Can fill order with price and quantity
- [ ] Position cash and quantity update after fill
- [ ] Can evaluate position for auto-sizing
- [ ] Auto-sizing detects triggers correctly
- [ ] Can list orders for a position
- [ ] Can list trades for a position

### **Simulation**
- [ ] Can run simulation for date range
- [ ] Simulation completes successfully
- [ ] Algorithm metrics are calculated
- [ ] Buy & hold metrics are calculated
- [ ] Comparison metrics show excess return
- [ ] Simulation results are saved (if using SQL persistence)
- [ ] Can retrieve simulation results later

---

## 🔍 **Troubleshooting**

### **Backend Not Starting**

**Error**: `Cannot connect to backend`

**Solutions**:
1. Check if backend is running:
   ```bash
   cd backend
   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

2. Check if port 8000 is available:
   ```bash
   # Windows
   netstat -ano | findstr :8000
   
   # Linux/Mac
   lsof -i :8000
   ```

3. Check for Python errors in backend logs

### **Position Creation Fails**

**Error**: `500 Internal Server Error` or database errors

**Solutions**:
1. Check database is accessible:
   ```bash
   # If using SQLite
   ls -la vb.sqlite
   ```

2. Enable SQL persistence:
   ```bash
   export APP_PERSISTENCE=sql
   export APP_AUTO_CREATE=true
   ```

3. Check backend logs for specific error

### **Order Submission Fails**

**Error**: `404 position_not_found` or `409 idempotency_conflict`

**Solutions**:
1. Verify position exists:
   ```bash
   curl http://localhost:8000/v1/positions
   ```

2. Use unique idempotency key:
   ```bash
   Idempotency-Key: test_order_$(date +%s)
   ```

3. Check daily order cap (max_orders_per_day guardrail)

### **Simulation Times Out**

**Error**: `Timeout` or takes too long

**Solutions**:
1. Use shorter date range (7-14 days instead of 30)
2. Increase timeout in request
3. Check market data is available for date range
4. Use smaller intraday_interval_minutes (30 instead of 5)

---

## 📊 **Expected Results**

### **Position Creation**
- ✅ Returns 201 Created
- ✅ Position ID is generated
- ✅ Anchor price is set (from market data)
- ✅ Cash and quantity match request

### **Order Submission**
- ✅ Returns 201 Created (or 200 for idempotent replay)
- ✅ Order ID is generated
- ✅ Order status is "submitted"
- ✅ Idempotency prevents duplicates

### **Order Fill**
- ✅ Returns 200 OK
- ✅ Order status changes to "filled"
- ✅ Position cash decreases (for BUY) or increases (for SELL)
- ✅ Position quantity updates correctly

### **Simulation**
- ✅ Returns 200 OK
- ✅ Algorithm metrics are positive/negative as expected
- ✅ Buy & hold metrics are calculated
- ✅ Excess return shows difference
- ✅ Total trades count is reasonable

---

## 🎯 **Success Criteria**

Phase 1 is **VERIFIED** when:

- ✅ **All automated tests pass** (verify_phase1.py)
- ✅ **Position creation works** end-to-end
- ✅ **Trading works** (submit + fill orders)
- ✅ **Simulation works** and completes successfully
- ✅ **No critical errors** in backend logs
- ✅ **Data persists** (if using SQL persistence)

---

## 📝 **Next Steps After Verification**

Once Phase 1 is verified:

1. **Document any issues** found during verification
2. **Fix any bugs** discovered
3. **Proceed to Phase 2**: Trading account integration (paper trading)
4. **Proceed to Phase 3**: Automated trading and real-time updates

---

**Last Updated**: January 2025  
**Status**: Verification Guide - Ready for Testing




































