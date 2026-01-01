#!/bin/bash
# Helper script to run the position status migration
# Usage: ./run_migration.sh

echo "=========================================="
echo "Position Status Column Migration"
echo "=========================================="
echo ""
echo "IMPORTANT: Make sure the backend server is STOPPED before running this migration."
echo ""
read -p "Press Enter to continue or Ctrl+C to cancel..."
echo ""

cd "$(dirname "$0")/../../../../.."
python -m backend.infrastructure.persistence.sql.migrations.add_position_status_column

if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "Migration completed successfully!"
    echo "You can now start the backend server."
    echo "=========================================="
else
    echo ""
    echo "=========================================="
    echo "Migration failed. Common causes:"
    echo "1. Server is still running (database locked)"
    echo "2. Database file permissions issue"
    echo "3. Database file not found"
    echo ""
    echo "Please stop the server and try again."
    echo "=========================================="
    exit 1
fi







