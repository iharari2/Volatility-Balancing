# Phase 1 Verification - Quick Start

**Goal**: Verify system is running and performs account creation, trading, and simulation correctly

---

## 🚀 **Quick Test (2 minutes)**

### **For WSL Users:**

See **[WSL Verification Steps](WSL_VERIFY_STEPS.md)** for detailed instructions.

### **Step 1: Start Backend**

```bash
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Wait for: `Application startup complete`

### **Step 2: Run Verification**

In a **new terminal**:

```bash
# Install requests if needed
pip install requests

# Run verification
python verify_phase1.py
```

---

## ✅ **What Gets Tested**

1. ✅ **System Running** - Health check
2. ✅ **Account Creation** - Create position (this is the "account")
3. ✅ **Trading** - Submit order → Fill order → Evaluate position
4. ✅ **Simulation** - Run backtesting simulation

---

## 📋 **Expected Output**

```
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
🎉 ALL TESTS PASSED! Phase 1 is working correctly.
```

---

## 🔧 **If Tests Fail**

### **Backend Not Running**

- Make sure backend is started on port 8000
- Check for errors in backend terminal

### **Position Creation Fails**

- Check database file exists: `backend/vb.sqlite`
- Enable SQL persistence: `export APP_PERSISTENCE=sql`

### **Simulation Times Out**

- Normal for long date ranges
- Try shorter range (7 days instead of 30)

---

## 📖 **Full Documentation**

See [Phase 1 Verification Guide](docs/dev/phase1_verification_guide.md) for:

- Detailed test descriptions
- Manual API testing steps
- Troubleshooting guide
- Expected results

---

**Status**: Ready to Test  
**Time Required**: 2-5 minutes
