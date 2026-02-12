# Quick Fix: Database Schema Update

## The Problem
Your database is missing new columns that were added for commission and dividend tracking.

## The Solution (Choose One)

### Option 1: Delete and Recreate (Fastest - Development Only)

**If you're in development and don't need to preserve data:**

1. Make sure the server is stopped (you already did this ✅)

2. Delete the database file. It's likely in one of these locations:
   ```bash
   # From project root:
   rm vb.sqlite
   
   # OR if it's in backend directory:
   rm backend/vb.sqlite
   
   # OR check where it is:
   ls -la *.sqlite
   ls -la backend/*.sqlite
   ```

3. Restart your server:
   ```bash
   cd backend
   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

   The server will automatically create a new database with all the correct columns!

### Option 2: Run Migration (Preserves Data)

**If you need to keep your existing data:**

1. Make sure the server is stopped ✅

2. Run the migration script:
   ```bash
   python backend/infrastructure/persistence/sql/migrations/add_commission_dividend_columns.py
   ```

3. Restart your server:
   ```bash
   cd backend
   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

## What Gets Added

The migration adds these columns:
- `positions.total_commission_paid` (default: 0.0)
- `positions.total_dividends_received` (default: 0.0)
- `orders.commission_rate_snapshot` (nullable)
- `orders.commission_estimated` (nullable)
- `trades.commission_rate_effective` (nullable)
- `trades.status` (default: 'executed')

## After Fixing

Once you've done either option, the 500 errors should be resolved and your API will work normally!





















