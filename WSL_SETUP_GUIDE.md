# WSL Setup Guide - Running Verification Tests

**For**: Windows Subsystem for Linux (WSL)  
**Purpose**: Step-by-step guide to run Phase 1 verification tests

---

## 🔍 **Step 1: Open WSL Terminal**

### **Option A: From Windows**
1. Press `Win + R`
2. Type: `wsl`
3. Press Enter

### **Option B: From Windows Terminal**
1. Open Windows Terminal
2. Click dropdown arrow → Select "Ubuntu" (or your WSL distro)

### **Option C: From Start Menu**
1. Search for "Ubuntu" in Start Menu
2. Click to open

**Verify you're in WSL:**
```bash
pwd
# Should show: /home/iharari or similar Linux path
```

---

## 📂 **Step 2: Navigate to Project Directory**

```bash
# Navigate to your project
cd /home/iharari/Volatility-Balancing

# Verify you're in the right place
ls -la
# Should see: backend/, frontend/, docs/, verify_phase1.py, etc.
```

**If you get "No such file or directory":**
```bash
# Find your project
find ~ -name "Volatility-Balancing" -type d 2>/dev/null

# Or check Windows mount
ls /mnt/c/Users/*/Documents/Volatility-Balancing
```

---

## 🐍 **Step 3: Check Python Installation**

```bash
# Check Python version (need 3.11+)
python3 --version

# If not installed or wrong version:
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip
```

**Expected Output:**
```
Python 3.11.x
```

---

## 📦 **Step 4: Install Required Python Package**

The verification script needs the `requests` library:

```bash
# Install requests globally (or in virtual environment)
pip3 install requests

# Or if you get permission errors:
pip3 install --user requests
```

**Verify installation:**
```bash
python3 -c "import requests; print('✅ requests installed')"
```

---

## 🚀 **Step 5: Start Backend Server**

### **Option A: If Backend is Already Set Up**

```bash
# Navigate to backend
cd backend

# Activate virtual environment (if exists)
source .venv/bin/activate

# Start backend
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Keep this terminal open!** The backend needs to keep running.

### **Option B: If Backend Needs Setup**

```bash
# Navigate to backend
cd backend

# Create virtual environment
python3 -m venv .venv

# Activate it
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Start backend
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Wait for this message:**
```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

---

## ✅ **Step 6: Test Backend is Running**

**Open a NEW WSL terminal** (keep backend running in first terminal):

```bash
# Test health endpoint
curl http://localhost:8000/v1/healthz

# Expected output:
# {"status":"ok"}
```

**If curl doesn't work:**
```bash
# Install curl
sudo apt install curl

# Or use Python to test
python3 -c "import requests; print(requests.get('http://localhost:8000/v1/healthz').json())"
```

---

## 🧪 **Step 7: Run Verification Script**

In the **NEW terminal** (backend still running in first terminal):

```bash
# Navigate to project root
cd /home/iharari/Volatility-Balancing

# Make script executable (if needed)
chmod +x verify_phase1.py

# Run verification
python3 verify_phase1.py
```

**Expected Output:**
```
============================================================
PHASE 1 VERIFICATION - Volatility Balancing System
============================================================
Testing: System Running, Account Creation, Trading, Simulation
============================================================

============================================================
TEST 1: System Health Check
============================================================
✅ Backend is running: {'status': 'ok'}

============================================================
TEST 2: Position Creation (Account Creation)
============================================================
ℹ️  Creating position for AAPL with $10000.0 cash...
✅ Position created successfully!
...
```

---

## 🔧 **Troubleshooting**

### **Problem 1: "Cannot connect to backend"**

**Check:**
```bash
# Is backend running?
ps aux | grep uvicorn

# Is port 8000 in use?
netstat -tuln | grep 8000
# Or:
ss -tuln | grep 8000
```

**Solution:**
- Make sure backend is running in another terminal
- Check backend terminal for errors
- Try accessing: `curl http://localhost:8000/v1/healthz`

---

### **Problem 2: "ModuleNotFoundError: No module named 'requests'"**

**Solution:**
```bash
# Install requests
pip3 install requests

# Or use virtual environment
cd backend
source .venv/bin/activate
pip install requests
```

---

### **Problem 3: "Permission denied" when running script**

**Solution:**
```bash
# Make executable
chmod +x verify_phase1.py

# Or run with Python directly
python3 verify_phase1.py
```

---

### **Problem 4: "Backend not found" or connection errors**

**Check backend is accessible:**
```bash
# Test from WSL
curl http://localhost:8000/v1/healthz

# If that works but script doesn't, check:
# - Backend is bound to 0.0.0.0 (not 127.0.0.1)
# - Firewall isn't blocking
# - Port 8000 is correct
```

**Verify backend startup:**
```bash
# In backend terminal, you should see:
# INFO:     Uvicorn running on http://0.0.0.0:8000
```

---

### **Problem 5: Database errors**

**Solution:**
```bash
# Check database file exists
ls -la backend/vb.sqlite

# If missing, backend will create it automatically
# Make sure APP_AUTO_CREATE=true in environment

# Or manually create:
cd backend
export APP_PERSISTENCE=sql
export APP_AUTO_CREATE=true
python3 -c "from app.di import container; print('DB initialized')"
```

---

### **Problem 6: Python path issues**

**Solution:**
```bash
# Use python3 explicitly
python3 verify_phase1.py

# Check Python path
which python3

# If virtual environment, activate it first
cd backend
source .venv/bin/activate
cd ..
python3 verify_phase1.py
```

---

## 📋 **Complete Step-by-Step Checklist**

### **Terminal 1: Backend**

```bash
# 1. Open WSL terminal
wsl

# 2. Navigate to project
cd /home/iharari/Volatility-Balancing/backend

# 3. Activate virtual environment (or create it)
source .venv/bin/activate
# OR: python3 -m venv .venv && source .venv/bin/activate

# 4. Install dependencies (if needed)
pip install -e ".[dev]"

# 5. Start backend
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 6. Wait for: "Application startup complete"
```

### **Terminal 2: Verification**

```bash
# 1. Open NEW WSL terminal
wsl

# 2. Navigate to project root
cd /home/iharari/Volatility-Balancing

# 3. Install requests (if needed)
pip3 install requests

# 4. Run verification
python3 verify_phase1.py

# 5. Review results
```

---

## 🎯 **Quick Test Commands**

### **Test 1: Backend Health**
```bash
curl http://localhost:8000/v1/healthz
```

### **Test 2: Create Position**
```bash
curl -X POST http://localhost:8000/v1/positions \
  -H "Content-Type: application/json" \
  -d '{"ticker":"AAPL","qty":0.0,"cash":10000.0}'
```

### **Test 3: Full Verification**
```bash
python3 verify_phase1.py
```

---

## 🔍 **Common WSL-Specific Issues**

### **Issue: Windows Path vs Linux Path**

**Problem**: Files are in Windows but accessed from WSL

**Solution**: Use Linux paths in WSL:
```bash
# Windows path: C:\Users\iharari\Volatility-Balancing
# WSL path: /mnt/c/Users/iharari/Volatility-Balancing

# Or better: Keep project in Linux filesystem
cd ~
# Project should be at: /home/iharari/Volatility-Balancing
```

### **Issue: Port Already in Use**

**Problem**: Port 8000 already in use

**Solution**:
```bash
# Find what's using port 8000
sudo lsof -i :8000
# Or:
sudo netstat -tulpn | grep 8000

# Kill the process
sudo kill -9 <PID>

# Or use different port
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
# Then update verify_phase1.py: BASE_URL = "http://localhost:8001/v1"
```

### **Issue: Permission Denied**

**Problem**: Can't write to database or files

**Solution**:
```bash
# Fix permissions
chmod 755 backend
chmod 644 backend/vb.sqlite 2>/dev/null || true

# Or run with proper user
whoami  # Should be your username, not root
```

---

## ✅ **Verification Checklist**

Before running tests, verify:

- [ ] ✅ WSL terminal is open
- [ ] ✅ Python 3.11+ is installed (`python3 --version`)
- [ ] ✅ `requests` library is installed (`pip3 install requests`)
- [ ] ✅ Backend is running in Terminal 1
- [ ] ✅ Health check works (`curl http://localhost:8000/v1/healthz`)
- [ ] ✅ Project directory is accessible
- [ ] ✅ `verify_phase1.py` exists in project root

---

## 🚀 **Quick Start (Copy-Paste)**

```bash
# Terminal 1: Start Backend
cd /home/iharari/Volatility-Balancing/backend
source .venv/bin/activate 2>/dev/null || python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]" 2>/dev/null || true
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Run Verification (wait for backend to start first!)
cd /home/iharari/Volatility-Balancing
pip3 install requests 2>/dev/null || true
python3 verify_phase1.py
```

---

## 📞 **Still Having Issues?**

### **Check Backend Logs**

Look at Terminal 1 (backend terminal) for errors:
- Database connection errors
- Import errors
- Port binding errors

### **Check Verification Script**

```bash
# Test script can import requests
python3 -c "import requests; print('OK')"

# Test script can reach backend
python3 -c "import requests; r = requests.get('http://localhost:8000/v1/healthz'); print(r.json())"
```

### **Run with Verbose Output**

```bash
# Add debug output
python3 -u verify_phase1.py 2>&1 | tee verification.log
```

---

**Last Updated**: January 2025  
**Status**: WSL Setup Guide - Ready to Use




































