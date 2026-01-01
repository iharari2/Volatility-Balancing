# Quick Start - WSL Verification

**Goal**: Run Phase 1 verification tests in WSL  
**Time**: 5 minutes

---

## 🚀 **3 Simple Steps**

### **Step 1: Open TWO WSL Terminals**

**Terminal 1** - For backend (keep this running):
- Press `Win + R`
- Type: `wsl`
- Press Enter

**Terminal 2** - For verification (open after Step 2):
- Press `Win + R` again
- Type: `wsl`
- Press Enter

---

### **Step 2: Start Backend (Terminal 1)**

Copy and paste these commands one by one:

```bash
cd /home/iharari/Volatility-Balancing/backend
source .venv/bin/activate
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Wait for this message:**
```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**✅ Keep Terminal 1 running!**

---

### **Step 3: Run Verification (Terminal 2)**

In the **NEW terminal** (Terminal 2):

```bash
cd /home/iharari/Volatility-Balancing
pip3 install requests
python3 verify_phase1.py
```

**Expected output:**
```
✅ Backend is running
✅ Position created successfully!
✅ Order submitted successfully!
✅ Order filled successfully!
✅ Simulation completed successfully!
🎉 ALL TESTS PASSED!
```

---

## ❌ **If Something Goes Wrong**

### **Error: "Cannot connect to backend"**

**Check Terminal 1:**
- Is backend still running?
- Do you see "Application startup complete"?
- Are there any error messages?

**Test manually:**
```bash
curl http://localhost:8000/v1/healthz
```

Should return: `{"status":"ok"}`

---

### **Error: "ModuleNotFoundError: requests"**

**Fix:**
```bash
pip3 install requests
```

---

### **Error: "No such file or directory"**

**Find your project:**
```bash
find ~ -name "verify_phase1.py"
```

Then `cd` to that directory.

---

## 📋 **Complete Command List**

### **Terminal 1 (Backend):**
```bash
cd /home/iharari/Volatility-Balancing/backend
source .venv/bin/activate
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### **Terminal 2 (Verification):**
```bash
cd /home/iharari/Volatility-Balancing
pip3 install requests
python3 verify_phase1.py
```

---

## ✅ **Success Checklist**

Before running verification:

- [ ] ✅ Terminal 1: Backend is running
- [ ] ✅ Terminal 1: Shows "Application startup complete"
- [ ] ✅ Terminal 2: In project directory
- [ ] ✅ Terminal 2: `requests` library installed
- [ ] ✅ Test: `curl http://localhost:8000/v1/healthz` returns `{"status":"ok"}`

---

**That's it!** If you still have issues, see [WSL_VERIFY_STEPS.md](WSL_VERIFY_STEPS.md) for detailed troubleshooting.




































