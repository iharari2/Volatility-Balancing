# 🚀 Volatility Trading System Demo Guide

This guide shows you how to demonstrate the volatility trading system we've built.

## 🎯 What We've Built

A complete volatility trading system that:

- ✅ Tracks anchor prices for positions
- ✅ Detects price movements using ±3% thresholds
- ✅ Triggers buy/sell signals based on volatility
- ✅ Updates anchor prices after trades
- ✅ Provides complete audit trails
- ✅ Offers REST API for integration

## 🚀 Demo Options

### Option 1: Quick Command Line Demo

```bash
cd backend
python quick_demo.py
```

### Option 2: Full Interactive Demo

```bash
cd backend
python demo.py
```

### Option 3: Web Interface Demo

1. Open `backend/demo_web.html` in your browser
2. Make sure the server is running on http://localhost:8000
3. Click through the interactive interface

### Option 4: Manual API Testing

Use curl, Postman, or any HTTP client to test the API endpoints.

## 🔧 Prerequisites

1. **Start the server:**

   ```bash
   cd backend
   python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

2. **Verify server is running:**
   ```bash
   curl http://localhost:8000/v1/healthz
   ```

## 📋 Demo Script

### Step 1: Create a Position

```bash
curl -X POST "http://localhost:8000/v1/positions" \
  -H "Content-Type: application/json" \
  -d '{"ticker": "AAPL", "qty": 0, "cash": 10000}'
```

**Expected Response:**

```json
{
  "id": "pos_abc123",
  "ticker": "AAPL",
  "qty": 0.0,
  "cash": 10000.0
}
```

### Step 2: Set Anchor Price

```bash
curl -X POST "http://localhost:8000/v1/positions/pos_abc123/anchor?price=150.0"
```

**Expected Response:**

```json
{
  "position_id": "pos_abc123",
  "anchor_price": 150.0,
  "message": "Anchor price set to $150.00"
}
```

### Step 3: Test Volatility Triggers

**Test BUY trigger (price drops 3%+):**

```bash
curl -X POST "http://localhost:8000/v1/positions/pos_abc123/evaluate?current_price=145.0"
```

**Expected Response:**

```json
{
  "position_id": "pos_abc123",
  "current_price": 145.0,
  "anchor_price": 150.0,
  "trigger_detected": true,
  "trigger_type": "BUY",
  "reasoning": "Price $145.00 ≤ buy threshold $145.50 ($150.00 × 97.0%)"
}
```

**Test SELL trigger (price rises 3%+):**

```bash
curl -X POST "http://localhost:8000/v1/positions/pos_abc123/evaluate?current_price=155.0"
```

**Expected Response:**

```json
{
  "position_id": "pos_abc123",
  "current_price": 155.0,
  "anchor_price": 150.0,
  "trigger_detected": true,
  "trigger_type": "SELL",
  "reasoning": "Price $155.00 ≥ sell threshold $154.50 ($150.00 × 103.0%)"
}
```

**Test no trigger (price within range):**

```bash
curl -X POST "http://localhost:8000/v1/positions/pos_abc123/evaluate?current_price=152.0"
```

**Expected Response:**

```json
{
  "position_id": "pos_abc123",
  "current_price": 152.0,
  "anchor_price": 150.0,
  "trigger_detected": false,
  "trigger_type": null,
  "reasoning": "Price $152.00 within threshold range [$145.50, $154.50]"
}
```

### Step 4: View Audit Trail

```bash
curl -X GET "http://localhost:8000/v1/positions/pos_abc123/events"
```

**Expected Response:**

```json
{
  "position_id": "pos_abc123",
  "events": [
    {
      "id": "evt_eval_pos_abc123_xyz789",
      "position_id": "pos_abc123",
      "type": "threshold_crossed",
      "inputs": {
        "current_price": 145.0,
        "anchor_price": 150.0,
        "threshold_pct": 0.03
      },
      "outputs": {
        "trigger_detected": true,
        "trigger_type": "BUY",
        "reasoning": "Price $145.00 ≤ buy threshold $145.50 ($150.00 × 97.0%)"
      },
      "message": "Price $145.00 ≤ buy threshold $145.50 ($150.00 × 97.0%)",
      "ts": "2025-09-14T14:30:00.000Z"
    }
  ]
}
```

## 🎭 Demo Scenarios

### Scenario 1: Basic Volatility Detection

1. Create position with $10,000 cash
2. Set anchor price to $150
3. Test prices: $145 (BUY), $152 (no trigger), $155 (SELL)
4. Show how triggers work at different price levels

### Scenario 2: Order Execution and Anchor Updates

1. Create position and set anchor
2. Submit a BUY order at $145
3. Fill the order
4. Show anchor price updates to $145
5. Test new triggers with updated anchor

### Scenario 3: Real-time Monitoring

1. Set up position with anchor
2. Simulate price movements over time
3. Show how system responds to each price change
4. Demonstrate audit trail accumulation

## 🔍 Key Features to Highlight

### 1. **Volatility Thresholds**

- Buy trigger: Price ≤ Anchor × (1 - 3%) = Anchor × 0.97
- Sell trigger: Price ≥ Anchor × (1 + 3%) = Anchor × 1.03
- Configurable thresholds via OrderPolicy

### 2. **Anchor Price Management**

- Automatically updated after each trade execution
- Provides reference point for future volatility calculations
- Tracks last trade price and date

### 3. **Event Logging**

- Complete audit trail of all evaluations
- Detailed reasoning for each decision
- Input/output data for debugging
- Timestamped events

### 4. **API Design**

- RESTful endpoints for all operations
- Clear error handling and status codes
- Idempotent operations where appropriate
- Comprehensive response data

## 🎯 Demo Talking Points

1. **"This system automatically detects when stock prices move significantly"**

   - Show the ±3% threshold calculation
   - Demonstrate trigger detection at different price levels

2. **"Every decision is logged with complete reasoning"**

   - Show the audit trail
   - Explain the reasoning messages

3. **"The system adapts to new price levels after trades"**

   - Show anchor price updates
   - Demonstrate how triggers change with new anchor

4. **"It's built for integration and automation"**
   - Show the REST API
   - Explain how it could connect to real market data

## 🚨 Troubleshooting

### Server won't start

- Check if port 8000 is already in use
- Make sure all dependencies are installed
- Check for syntax errors in the code

### API calls fail

- Verify server is running on http://localhost:8000
- Check the API endpoint URLs
- Ensure JSON format is correct

### No triggers detected

- Make sure anchor price is set
- Check that price movements are ≥3%
- Verify the calculation logic

## 🎉 Success Criteria

A successful demo should show:

- ✅ Position creation and management
- ✅ Anchor price setting and tracking
- ✅ Volatility trigger detection
- ✅ Clear reasoning for each decision
- ✅ Complete audit trail
- ✅ API integration working smoothly

The system demonstrates a working volatility trading engine that can detect price movements and trigger appropriate actions based on configurable thresholds!

