#!/usr/bin/env python3
"""
Simple test script to verify simulation export fix
"""

import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

try:
    from test_excel_export import test_simulation_export

    print("🚀 Testing simulation export fix...")
    test_simulation_export()
    print("✅ Test completed successfully!")

except Exception as e:
    print(f"❌ Test failed: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)
