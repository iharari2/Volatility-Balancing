#!/usr/bin/env python3
"""
Simple script to start the backend server for testing
"""

import subprocess
import sys
import os


def start_backend():
    """Start the backend server"""
    backend_dir = os.path.join(os.path.dirname(__file__), "backend")

    try:
        print("🚀 Starting backend server...")
        print(f"   Working directory: {backend_dir}")

        # Change to backend directory and start the server
        process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "app.main:app",
                "--host",
                "0.0.0.0",
                "--port",
                "8001",
                "--reload",
            ],
            cwd=backend_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
        )

        print("✅ Backend server started!")
        print("   Server running on: http://localhost:8001")
        print("   API docs available at: http://localhost:8001/docs")
        print(
            "   Comprehensive export test URL: http://localhost:8001/v1/excel/positions/pos_test123/comprehensive-export"
        )
        print("\n   Press Ctrl+C to stop the server...")

        # Stream output
        try:
            for line in process.stdout:
                print(f"   {line.strip()}")
        except KeyboardInterrupt:
            print("\n🛑 Stopping backend server...")
            process.terminate()
            process.wait()
            print("✅ Backend server stopped.")

    except Exception as e:
        print(f"❌ Failed to start backend server: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(start_backend())
