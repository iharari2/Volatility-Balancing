#!/usr/bin/env python3
"""
Start the backend with SQL persistence enabled.

This script sets the environment variables to use SQL persistence
and starts the FastAPI server.
"""

import os
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Set environment variables for SQL persistence
os.environ["APP_PERSISTENCE"] = "sql"
os.environ["APP_EVENTS"] = "sql"
os.environ["APP_AUTO_CREATE"] = "true"
os.environ["SQL_URL"] = "sqlite:///./vb.sqlite"

if __name__ == "__main__":
    import uvicorn
    from app.main import app

    print("🚀 Starting Volatility Balancing Backend with SQL Persistence")
    print("📊 Database: SQLite (vb.sqlite)")
    print("💾 Persistence: SQL (positions, orders, trades, events)")
    print("🔗 API: http://localhost:8000")
    print("📖 Docs: http://localhost:8000/docs")
    print()

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True, log_level="info")
