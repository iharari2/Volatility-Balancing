#!/bin/bash
# Restart trading for positions after portfolio state fix

echo "Restarting trading for positions..."

# Stop existing trading
curl -X POST http://localhost:8000/v1/trading/stop/pos_f0c83651
curl -X POST http://localhost:8000/v1/trading/stop/pos_c955d000

sleep 2

# Start trading again
echo "Starting trading for AAPL..."
curl -X POST http://localhost:8000/v1/trading/start/pos_f0c83651

echo "Starting trading for ZIM..."
curl -X POST http://localhost:8000/v1/trading/start/pos_c955d000

echo ""
echo "✅ Trading restarted!"
echo ""
echo "Monitor with:"
echo "  python scripts/monitor_trading.py pos_f0c83651 --duration 300"



