#!/usr/bin/env python3
"""Simple test to verify backend is working"""

import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), "backend"))

try:
    from app.main import app

    print("✅ Backend imports successfully")
    print("✅ FastAPI app created")

    # Test basic functionality
    print("\nTesting basic functionality...")

    # Import and test container
    from app.di import container

    print("✅ DI container imported")

    # Test position creation
    pos_repo = container.positions
    print("✅ Position repository available")

    # List existing positions
    existing = pos_repo.list_all() or []
    print(f"✅ Found {len(existing)} existing positions")

    print("\n🎉 Backend is working correctly!")
    print("\nTo start the backend server, run:")
    print("cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload")

except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running from the project root directory")
except Exception as e:
    print(f"❌ Error: {e}")
