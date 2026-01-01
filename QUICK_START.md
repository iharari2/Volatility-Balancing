# 🚀 Quick Start - Play with the System

**Get the system running in 2 minutes!**

---

## **Option 1: Automatic Start (Easiest)**

```bash
# From project root
./start.sh
```

This will:
- ✅ Start backend on port 8000
- ✅ Start frontend on port 3000
- ✅ Open browser to http://localhost:3000

**Press Ctrl+C to stop both servers**

---

## **Option 2: Manual Start (2 Terminals)**

### **Terminal 1: Backend**

```bash
cd backend
source .venv/bin/activate
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Wait for**: `Application startup complete`

### **Terminal 2: Frontend**

```bash
cd frontend
npm install  # Only first time
npm run dev
```

**Wait for**: `Local: http://localhost:3000`

---

## **Open Browser**

Go to: **http://localhost:3000**

---

## **First Steps**

1. **Create a Position**
   - Click "Positions" → "Create Position"
   - Ticker: `AAPL`
   - Cash: `$10,000`
   - Click "Create"

2. **Evaluate Position**
   - Click on the position
   - Click "Evaluate Position"
   - See if triggers are detected

3. **Run Simulation**
   - Go to "Simulation" page
   - Ticker: `AAPL`
   - Date Range: Last 7 days
   - Click "Run Simulation"
   - See results!

4. **Try Optimization**
   - Go to "Optimization" page
   - Create optimization config
   - Start optimization
   - View heatmap!

---

## **What to Explore**

- ✅ **Dashboard**: Overview of all positions
- ✅ **Positions**: Create and manage positions
- ✅ **Trading**: Submit and fill orders
- ✅ **Simulation**: Backtest strategies
- ✅ **Optimization**: Find best parameters
- ✅ **Excel Export**: Export all data

---

## **Need Help?**

See **[PLAY_GUIDE.md](PLAY_GUIDE.md)** for detailed instructions and scenarios.

---

**Have fun exploring!** 🎉




































