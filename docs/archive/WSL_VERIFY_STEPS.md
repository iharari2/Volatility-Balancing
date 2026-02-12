# WSL Verification - Step by Step Instructions

**For**: Running Phase 1 verification tests in WSL  
**Time**: 5-10 minutes

---

## 🎯 **Goal**

Verify the system works correctly:
- ✅ System is running
- ✅ Account/Position creation works
- ✅ Trading (order submit + fill) works
- ✅ Simulation works

---

## 📋 **Step-by-Step Instructions**

### **STEP 1: Open WSL Terminal**

1. Press `Win + R`
2. Type: `wsl`
3. Press Enter

You should see a Linux prompt like:
```
iharari@DESKTOP-XXXXX:~$
```

---

### **STEP 2: Navigate to Project**

```bash
cd /home/iharari/Volatility-Balancing
```

**Verify you're in the right place:**
```bash
ls
# Should see: backend/ frontend/ docs/ verify_phase1.py
```

**If you get "No such file or directory":**
```bash
# Find where the project is
find ~ -name "verify_phase1.py" 2>/dev/null

# Or check if it's in Windows filesystem
ls /mnt/c/Users/*/Volatility-Balancing/verify_phase1.py
```

---

### **STEP 3: Check Python**

```bash
python3 --version
```

**Expected**: `Python 3.11.x` or similar

**If Python not found:**
```bash
sudo apt update
sudo apt install python3 python3-pip
```

---

### **STEP 4: Install Requests Library**

```bash
pip3 install requests
```

**If you get permission errors:**
```bash
pip3 install --user requests
```

**Verify it worked:**
```bash
python3 -c "import requests; print('OK')"
```

Should print: `OK`

---

### **STEP 5: Start Backend (Terminal 1)**

**Keep this terminal open!**

```bash
# Navigate to backend
cd /home/iharari/Volatility-Balancing/backend

# Check if virtual environment exists
ls .venv

# If .venv exists, activate it:
source .venv/bin/activate

# If .venv doesn't exist, create it:
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies (if needed)
pip install -e ".[dev]"

# Start backend server
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Wait for this message:**
```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

**✅ Keep this terminal running!**

---

### **STEP 6: Test Backend (New Terminal)**

**Open a NEW WSL terminal** (keep Terminal 1 running):

```bash
# Test if backend is running
curl http://localhost:8000/v1/healthz
```

**Expected output:**
```json
{"status":"ok"}
```

**If curl doesn't work:**
```bash
# Install curl
sudo apt install curl

# Or test with Python
python3 -c "import requests; print(requests.get('http://localhost:8000/v1/healthz').json())"
```

---

### **STEP 7: Run Verification Script**

**In the NEW terminal** (Terminal 2):

```bash
# Navigate to project root
cd /home/iharari/Volatility-Balancing

# Run verification
python3 verify_phase1.py
```

**Expected output:**
```
============================================================
PHASE 1 VERIFICATION - Volatility Balancing System
============================================================
✅ Backend is running: {'status': 'ok'}
✅ Position created successfully!
✅ Order submitted successfully!
✅ Order filled successfully!
✅ Position evaluation successful!
✅ Simulation completed successfully!
============================================================
Results: 8/8 tests passed
🎉 ALL TESTS PASSED!
```

---

## 🔧 **Troubleshooting**

### **Error: "Cannot connect to backend"**

**Check:**
1. Is backend running in Terminal 1?
2. Do you see "Application startup complete" in Terminal 1?
3. Test manually: `curl http://localhost:8000/v1/healthz`

**Fix:**
- Make sure backend is started with `--host 0.0.0.0` (not `127.0.0.1`)
- Check Terminal 1 for errors

---

### **Error: "ModuleNotFoundError: No module named 'requests'"**

**Fix:**
```bash
pip3 install requests
# Or:
pip3 install --user requests
```

---

### **Error: "Permission denied"**

**Fix:**
```bash
# Make script executable
chmod +x verify_phase1.py

# Or just run with Python
python3 verify_phase1.py
```

---

### **Error: "No such file or directory"**

**Fix:**
```bash
# Find the project
find ~ -name "Volatility-Balancing" -type d

# Or check Windows mount
ls /mnt/c/Users/*/Volatility-Balancing
```

---

### **Error: "Port 8000 already in use"**

**Fix:**
```bash
# Find what's using the port
sudo lsof -i :8000

# Kill it
sudo kill -9 <PID>

# Or use different port (update verify_phase1.py BASE_URL)
```

---

## 📝 **Quick Reference Commands**

### **Start Backend:**
```bash
cd /home/iharari/Volatility-Balancing/backend
source .venv/bin/activate
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### **Test Backend:**
```bash
curl http://localhost:8000/v1/healthz
```

### **Run Verification:**
```bash
cd /home/iharari/Volatility-Balancing
python3 verify_phase1.py
```

---

## ✅ **Success Checklist**

Before running verification, make sure:

- [ ] ✅ WSL terminal is open
- [ ] ✅ Python 3 is installed (`python3 --version`)
- [ ] ✅ `requests` is installed (`pip3 install requests`)
- [ ] ✅ Backend is running in Terminal 1
- [ ] ✅ Health check works (`curl http://localhost:8000/v1/healthz`)
- [ ] ✅ You're in project directory (`cd /home/iharari/Volatility-Balancing`)

---

## 🎯 **What Each Test Does**

1. **Health Check** - Verifies backend is running
2. **Position Creation** - Creates a test position (AAPL, $10,000)
3. **Get Position** - Retrieves the position details
4. **Submit Order** - Submits a BUY order
5. **Fill Order** - Simulates order execution
6. **Evaluate Position** - Tests auto-sizing logic
7. **Simulation** - Runs a 30-day backtest
8. **List Positions** - Lists all positions

---

**Last Updated**: January 2025  
**Status**: Step-by-Step Guide - Ready to Use




































