#!/bin/bash
# Script to check database location and tables

echo "=== Checking Database Location ==="
echo ""

# Check common locations
echo "1. Checking backend/vb.sqlite..."
if [ -f "vb.sqlite" ]; then
    echo "   ✅ Found: vb.sqlite"
    echo "   Size: $(ls -lh vb.sqlite | awk '{print $5}')"
    echo ""
    echo "   Tables in database:"
    sqlite3 vb.sqlite ".tables" | tr ' ' '\n' | grep -v "^$"
    echo ""
    echo "   Timeline records count:"
    sqlite3 vb.sqlite "SELECT COUNT(*) FROM position_evaluation_timeline WHERE position_id='pos_c955d000';" 2>/dev/null || echo "   Table doesn't exist or error"
else
    echo "   ❌ Not found: vb.sqlite"
fi

echo ""
echo "2. Checking backend/data/trading.db..."
if [ -f "data/trading.db" ]; then
    echo "   ✅ Found: data/trading.db"
    echo "   Size: $(ls -lh data/trading.db | awk '{print $5}')"
    echo ""
    echo "   Tables in database:"
    sqlite3 data/trading.db ".tables" | tr ' ' '\n' | grep -v "^$"
    echo ""
    echo "   Timeline records count:"
    sqlite3 data/trading.db "SELECT COUNT(*) FROM position_evaluation_timeline WHERE position_id='pos_c955d000';" 2>/dev/null || echo "   Table doesn't exist or error"
else
    echo "   ❌ Not found: data/trading.db"
fi

echo ""
echo "3. Searching for all .sqlite and .db files..."
find . -name "*.sqlite" -o -name "*.db" 2>/dev/null | head -10

echo ""
echo "=== Environment Variables ==="
echo "SQL_URL: ${SQL_URL:-not set (default: sqlite:///./vb.sqlite)}"
echo "APP_PERSISTENCE: ${APP_PERSISTENCE:-not set (default: memory)}"



