# Database Migrations

## Adding the `status` Column to Positions Table

### Problem

The `positions` table is missing the `status` column, which is required for tracking whether a position is RUNNING or PAUSED.

### Solution

Run the migration script to add the column.

### Steps

1. **Stop the backend server** (if it's running)

   ```bash
   # Press Ctrl+C in the terminal where the server is running
   # Or kill the process if running in background
   ```

2. **Run the migration**

   ```bash
   cd /home/iharari/Volatility-Balancing
   python -m backend.infrastructure.persistence.sql.migrations.add_position_status_column
   ```

   Or use the helper script:

   ```bash
   ./backend/infrastructure/persistence/sql/migrations/run_migration.sh
   ```

3. **Verify the migration**
   The script will output:

   - `[OK] Successfully added 'status' column to 'positions' table` - Success
   - `[OK] Column 'status' already exists` - Already migrated
   - `[ERROR] Database is locked` - Server is still running, stop it first

4. **Start the backend server**
   ```bash
   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

### What the Migration Does

- Adds a `status` column to the `positions` table
- Sets default value of 'RUNNING' for all existing positions
- Creates an index on the `status` column for better query performance
- Handles both SQLite and PostgreSQL databases

### Troubleshooting

**Error: "database is locked"**

- The backend server is still running
- Stop the server completely before running the migration
- On Windows/WSL, make sure no other process has the database file open

**Error: "no such module"**

- Make sure you're in the project root directory
- Make sure the virtual environment is activated: `source .venv/bin/activate`

**Error: "Permission denied"**

- Check file permissions on the database file
- Make sure you have write access to the database directory







