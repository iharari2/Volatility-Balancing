# 🎮 Play Guide - Volatility Balancing System

**Quick guide to run and explore the trading system**

---

## 🚀 **Quick Start (2 Terminals)**

### **Terminal 1: Backend**

```bash
cd /home/iharari/Volatility-Balancing/backend
source .venv/bin/activate
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Wait for**: `Application startup complete`

### **Terminal 2: Frontend**

```bash
cd /home/iharari/Volatility-Balancing/frontend
npm install  # Only needed first time
npm run dev
```

**Wait for**: `Local: http://localhost:3000`

### **Open Browser**

Go to: **http://localhost:3000**

---

## 🎯 **What You Can Do**

### **1. Create a Position**

1. Go to **Positions** page
2. Click **"Create Position"**
3. Enter:
   - **Ticker**: `AAPL`, `MSFT`, `GOOGL`, etc.
   - **Initial Cash**: `$10,000`
   - **Trading Parameters**:
     - Trigger Threshold: `3%` (default)
     - Rebalance Ratio: `1.6667` (default)
     - Commission Rate: `0.0001` (0.01%)
   - **Guardrails**:
     - Min Stock Allocation: `25%`
     - Max Stock Allocation: `75%`
     - Max Orders Per Day: `5`
4. Click **"Create"**

### **2. Monitor Positions**

- View all positions on the **Dashboard**
- See:
  - Current cash
  - Number of shares
  - Total value
  - Anchor price
  - P&L

### **3. Evaluate & Trade**

1. Click on a position
2. Click **"Evaluate Position"** to check if triggers are met
3. If trigger detected:
   - System will propose a BUY or SELL order
   - Review the order proposal
   - Click **"Submit Order"** to execute
4. Fill the order:
   - Orders start as "submitted"
   - Click **"Fill Order"** to simulate execution
   - Position will update automatically

### **4. Run Simulations**

1. Go to **Simulation** page
2. Configure:
   - **Ticker**: `AAPL`
   - **Date Range**: Last 7 days (yfinance limitation)
   - **Initial Cash**: `$10,000`
   - **Trading Parameters**: Same as position config
3. Click **"Run Simulation"**
4. View results:
   - Algorithm performance vs Buy & Hold
   - Trade log
   - Daily returns
   - Performance metrics

### **5. Parameter Optimization**

1. Go to **Optimization** page
2. Create a new optimization config:
   - **Ticker**: `AAPL`
   - **Date Range**: Last 7 days
   - **Parameters to Optimize**:
     - Trigger Threshold: `0.02` to `0.05` (step 0.01)
     - Rebalance Ratio: `1.5` to `2.0` (step 0.1)
   - **Metrics**: Select Sharpe Ratio, Total Return, etc.
3. Click **"Start Optimization"**
4. Watch progress in real-time
5. View results:
   - Best parameter combinations
   - Heatmap visualization
   - Performance comparison

### **6. Export Data**

1. Go to **Excel Export** page
2. Export:
   - Position data
   - Trade history
   - Simulation results
   - Optimization results
3. Download Excel files with professional formatting

---

## 🧪 **Try These Scenarios**

### **Scenario 1: Basic Trading**

1. Create position for `AAPL` with `$10,000`
2. Set anchor price to current market price
3. Manually evaluate with different prices:
   - Price 3% below anchor → Should trigger BUY
   - Price 3% above anchor → Should trigger SELL
4. Submit and fill orders
5. Watch position update

### **Scenario 2: Simulation Backtest**

1. Run simulation for `AAPL` over last 7 days
2. Compare algorithm vs buy & hold
3. Check trade log to see when trades executed
4. Analyze performance metrics

### **Scenario 3: Parameter Optimization**

1. Optimize trigger threshold (0.02 to 0.05)
2. Find best threshold for Sharpe ratio
3. View heatmap to see parameter sensitivity
4. Export results to Excel

### **Scenario 4: Multiple Positions**

1. Create positions for different tickers:
   - `AAPL` (Apple)
   - `MSFT` (Microsoft)
   - `GOOGL` (Google)
2. Monitor all positions on dashboard
3. Evaluate each position independently
4. See how different stocks behave

---

## 📊 **Key Features to Explore**

### **Dashboard**

- Overview of all positions
- System status
- Quick actions

### **Positions**

- Create new positions
- View position details
- Set anchor prices
- Evaluate triggers
- Submit orders

### **Trading**

- Real-time price evaluation
- Order submission
- Order filling
- Trade history

### **Simulation**

- Backtest trading strategies
- Compare performance
- Analyze trade patterns

### **Optimization**

- Find best parameters
- Visualize parameter space
- Compare configurations

### **Excel Export**

- Export all data
- Professional formatting
- Multiple report types

---

## 🔍 **Understanding the System**

### **Volatility Balancing Strategy**

The system uses a **semi-passive trading strategy**:

1. **Anchor Price**: Set when position is created or after a trade
2. **Trigger Threshold**: ±3% from anchor price
3. **Buy Signal**: Price drops 3% below anchor
4. **Sell Signal**: Price rises 3% above anchor
5. **Rebalance Ratio**: When buying, buy 1.6667x the trigger amount

### **Guardrails**

- **Min/Max Stock Allocation**: Keep 25-75% in stock
- **Max Orders Per Day**: Limit to 5 orders per day
- **Min Notional**: Minimum order size ($100 default)

### **Order Flow**

1. **Submit Order**: Create order (status: "submitted")
2. **Fill Order**: Execute order (status: "filled")
3. **Update Position**: Cash and shares update automatically
4. **Update Anchor**: Anchor price updates to fill price

---

## 🐛 **Troubleshooting**

### **Backend Not Starting**

```bash
# Check if port 8000 is in use
sudo lsof -i :8000

# Kill process if needed
sudo kill -9 <PID>

# Or use different port
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

### **Frontend Not Connecting**

- Make sure backend is running on port 8000
- Check browser console for errors
- Verify API URL in frontend config

### **No Market Data**

- YFinance API might be rate-limited
- Try different tickers
- Check internet connection

### **Simulation Fails**

- Date range must be within last 30 days (yfinance limitation)
- Use 7 days or less for faster results
- Check ticker symbol is valid

---

## 📝 **API Endpoints (For Testing)**

### **Health Check**

```bash
curl http://localhost:8000/v1/healthz
```

### **Create Position**

```bash
curl -X POST http://localhost:8000/v1/positions \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "AAPL",
    "qty": 0.0,
    "cash": 10000.0
  }'
```

### **Get Position**

```bash
curl http://localhost:8000/v1/positions/{position_id}
```

### **Evaluate Position**

```bash
curl -X POST "http://localhost:8000/v1/positions/{position_id}/evaluate?current_price=150.0"
```

### **Submit Order**

```bash
curl -X POST http://localhost:8000/v1/positions/{position_id}/orders \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: test123" \
  -d '{
    "side": "BUY",
    "qty": 10.0,
    "price": 150.0
  }'
```

### **Fill Order**

```bash
curl -X POST http://localhost:8000/v1/orders/{order_id}/fill \
  -H "Content-Type: application/json" \
  -d '{
    "qty": 10.0,
    "price": 150.0,
    "commission": 0.15
  }'
```

---

## 🎉 **Have Fun!**

Explore the system, try different scenarios, and see how the volatility balancing strategy works. All data is stored locally in SQLite, so you can experiment freely!

**Pro Tip**: Start with a simulation to see how the strategy performs before creating real positions.

---

**Last Updated**: January 2025  
**Status**: Ready to Play! 🚀



































