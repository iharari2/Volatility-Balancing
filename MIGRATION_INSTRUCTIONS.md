# Database Migration Instructions

## Problem
The database schema is missing new columns added for commission and dividend tracking:
- `positions.total_commission_paid`
- `positions.total_dividends_received`
- `orders.commission_rate_snapshot`
- `orders.commission_estimated`
- `trades.commission_rate_effective`
- `trades.status`

## Solution

### Step 1: Stop the Server
Stop the running uvicorn server (press `CTRL+C` in the terminal where it's running).

### Step 2: Run the Migration
From the project root directory, run:

```bash
python backend/infrastructure/persistence/sql/migrations/add_commission_dividend_columns.py
```

Or if you need to specify a custom database URL:

```bash
SQL_URL=sqlite:///./vb.sqlite python backend/infrastructure/persistence/sql/migrations/add_commission_dividend_columns.py
```

### Step 3: Restart the Server
Start the server again:

```bash
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Alternative: Recreate Database (Development Only)

If you're in development and don't mind losing data, you can delete the database file and let it recreate:

```bash
# Stop the server first!
rm vb.sqlite  # or wherever your database file is
# Then restart the server - it will auto-create with the new schema
```

## What the Migration Does

The migration script:
1. Checks if each column already exists
2. Adds missing columns with appropriate defaults:
   - `total_commission_paid` → 0.0
   - `total_dividends_received` → 0.0
   - `commission_rate_snapshot` → NULL (optional)
   - `commission_estimated` → NULL (optional)
   - `commission_rate_effective` → NULL (optional)
   - `status` → 'executed' (for trades)

Existing data will be preserved with default values.





















