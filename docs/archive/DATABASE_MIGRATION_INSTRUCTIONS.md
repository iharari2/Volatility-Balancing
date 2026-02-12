# Database Migration Instructions

## Issue

The database schema is missing the new `tenant_id` and `portfolio_id` columns required for portfolio-scoped state. The error shows:

```
sqlite3.OperationalError: no such column: portfolios.tenant_id
```

## Solution

### Option 1: Run Migration Script (Recommended for existing data)

1. **Stop the backend server** (if running):

   - Press `Ctrl+C` in the terminal where the server is running
   - Or kill the process

2. **Run the migration script**:

   ```bash
   cd backend
   python scripts/migrate_to_portfolio_scoped.py
   ```

3. **Restart the backend server**:
   ```bash
   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

### Option 2: Recreate Database (If you don't need existing data)

1. **Stop the backend server**

2. **Delete the existing database**:

   ```bash
   rm vb.sqlite
   # or on Windows:
   del vb.sqlite
   ```

3. **Restart the backend server**:
   ```bash
   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```
   The server will automatically create the database with the new schema.

## What the Migration Does

The migration script will:

- Add `tenant_id`, `type`, `trading_state`, `trading_hours_policy` to `portfolios` table
- Add `tenant_id`, `portfolio_id`, `asset_symbol`, `avg_cost` to `positions` table
- Add `tenant_id`, `portfolio_id` to `orders` table
- Add `tenant_id`, `portfolio_id` to `trades` table
- Add `tenant_id`, `portfolio_id` to `events` table (nullable)
- Create `portfolio_cash` table
- Create `portfolio_config` table
- Migrate existing data to set default values

## Verification

After migration, verify the schema:

```bash
sqlite3 vb.sqlite ".schema portfolios"
```

You should see `tenant_id`, `type`, `trading_state`, and `trading_hours_policy` columns.

## Troubleshooting

### Database is locked

- Make sure the backend server is stopped
- Close any other connections to the database
- Wait a few seconds and try again

### Migration fails

- Check the error message
- The script is idempotent - you can run it multiple times
- If columns already exist, it will skip them













