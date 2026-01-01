# QA Test Commands Quick Reference

## Common Commands

### Run Tests

```bash
# Correct command (note: pytest, not pythest)
python -m pytest tests/ -v

# From project root
cd backend
python -m pytest tests/ -v

# Or use pytest directly (if installed)
pytest tests/ -v
```

### Run Specific Test Categories

```bash
# Unit tests only
python -m pytest backend/tests/unit/ -v

# Integration tests only
python -m pytest backend/tests/integration/ -v

# Regression tests only
python -m pytest backend/tests/regression/ -v
```

### Run Specific Test File

```bash
# Run one test file
python -m pytest backend/tests/unit/domain/test_position_entity.py -v

# Run tests matching a pattern
python -m pytest backend/tests/ -k "test_position" -v
```

### Run with Coverage

```bash
# Generate coverage report
python -m pytest backend/tests/ --cov=backend --cov-report=html --cov-report=term

# View HTML report (Linux/Mac)
open htmlcov/index.html
# Or
xdg-open htmlcov/index.html
```

### Useful Options

```bash
# Stop on first failure
python -m pytest backend/tests/ -x

# Show short traceback
python -m pytest backend/tests/ -v --tb=short

# Show long traceback (more details)
python -m pytest backend/tests/ -v --tb=long

# Run in parallel (faster)
python -m pytest backend/tests/ -n auto

# Show only failures
python -m pytest backend/tests/ -v --tb=short | grep -A 5 FAILED

# Run with markers
python -m pytest backend/tests/ -m "not slow" -v
```

### Using the QA Test Script

```bash
# Run automated QA test script
cd backend
python run_qa_tests.py
```

---

## Troubleshooting

### Issue: "No module named pytest"

**Solution:**

```bash
# Install pytest
pip install pytest pytest-cov pytest-xdist

# Or install from requirements
pip install -r backend/requirements.txt
```

### Issue: "No module named backend"

**Solution:**

```bash
# Run from project root
cd /home/iharari/Volatility-Balancing
python -m pytest backend/tests/ -v

# Or set PYTHONPATH
export PYTHONPATH=/home/iharari/Volatility-Balancing:$PYTHONPATH
python -m pytest backend/tests/ -v
```

### Issue: Import errors in tests

**Solution:**

```bash
# Make sure you're in the right directory
cd /home/iharari/Volatility-Balancing/backend

# Check Python path
python -c "import sys; print(sys.path)"

# Run with explicit path
PYTHONPATH=/home/iharari/Volatility-Balancing python -m pytest tests/ -v
```

---

## Quick Test Execution

### Step 1: Navigate to Backend

```bash
cd ~/Volatility-Balancing/backend
```

### Step 2: Run Tests

```bash
# Quick test run
python -m pytest tests/ -v

# Or with coverage
python -m pytest tests/ --cov=backend --cov-report=term -v
```

### Step 3: Check Results

```bash
# Count passing tests
python -m pytest tests/ -v | grep -c "PASSED"

# Count failing tests
python -m pytest tests/ -v | grep -c "FAILED"

# List all failures
python -m pytest tests/ -v | grep "FAILED"
```

---

## Common Typo Fixes

| Wrong                 | Correct            |
| --------------------- | ------------------ |
| `pythest`             | `pytest`           |
| `pytest` (without -m) | `python -m pytest` |
| `test/`               | `tests/` (plural)  |

---

## Recommended Workflow

1. **Start with a quick check:**

   ```bash
   cd backend
   python -m pytest tests/ --collect-only -q
   ```

2. **Run unit tests first:**

   ```bash
   python -m pytest tests/unit/ -v
   ```

3. **Then integration tests:**

   ```bash
   python -m pytest tests/integration/ -v
   ```

4. **Generate full report:**
   ```bash
   python run_qa_tests.py
   ```

---

**Remember:** Always use `pytest` (not `pythest`) and run from the `backend` directory or use the full path!








