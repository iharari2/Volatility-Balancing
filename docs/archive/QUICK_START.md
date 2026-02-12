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
# From repo root
make dev
#
# Or from repo root without Make:
PYTHONPATH=backend python -m uvicorn --app-dir backend app.main:app --reload --host 0.0.0.0 --port 8000
#
# Or from backend/
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

## **How to Verify Gate 1**

**Gate 1 Verification: Deterministic Tick + Timeline (Offline-Friendly)**

Goal: Prove the trading tick loop works end-to-end locally without network flakiness, and that each tick writes exactly one timeline/audit row.

**Prereqs**

- From repo root
- Python env active
- No server needs to be running for tests

**Step A: Run tests (offline)**

```bash
pytest -q
```

Expected:
- All default tests pass without requiring a running server.
- Any true end-to-end tests are excluded by default (e.g., marked e2e).

**Step B: Start backend in deterministic tick mode**

```bash
TICK_DETERMINISTIC=true PYTHONPATH=backend \
python -m uvicorn --app-dir backend app.main:app --reload --host 0.0.0.0 --port 8000
```

Sanity checks:

```bash
curl -s http://localhost:8000/v1/healthz | jq
curl -s http://localhost:8000/v1/market/state | jq
```

Expected:
- `/v1/healthz` returns `{"status":"ok"}`
- `/v1/market/state` returns a valid market state JSON

**Step C: Run the Gate 1 smoke script (no network required)**

In another terminal:

```bash
python backend/scripts/gate1_tick_smoke.py
```

Expected output characteristics:
- Runs ~10 ticks
- Prints one line per tick (tick#, price, action, trigger direction, order/trade info if any)
- Summary shows at least one BUY and one SELL within 10 ticks
- Fetches timeline via API and prints counts of BUY/SELL/HOLD + last 5 events

**Step D: Verify timeline endpoint directly**

The smoke script prints the position_id. You can also query manually:

```bash
curl -s "http://localhost:8000/v1/positions/<POSITION_ID>/timeline?limit=200" | jq
```

Expected:
- Timeline contains exactly one new row per tick (including HOLD).
- Timeline rows include at minimum:
  - `timestamp`
  - `action` (BUY/SELL/HOLD)
  - `trigger_direction`
  - `current_price`
  - guardrail limits
  - allocation after
  - any order/trade ids if present

---

## **Need Help?**

See **[PLAY_GUIDE.md](PLAY_GUIDE.md)** for detailed instructions and scenarios.

---

**Have fun exploring!** 🎉

































