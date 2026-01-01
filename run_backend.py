#!/usr/bin/env python3
"""
Proper backend startup script that handles the module path correctly
"""

import os
import sys
import subprocess

# Get the directory where this script is located (project root)
project_root = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.join(project_root, "backend")

# Change to backend directory
os.chdir(backend_dir)

# Add backend to Python path
sys.path.insert(0, backend_dir)

print(f"Starting backend from: {backend_dir}")
print(f"Python path: {sys.path[0]}")

# Start uvicorn
try:
    subprocess.run(
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
        ]
    )
except KeyboardInterrupt:
    print("\nBackend server stopped.")
except Exception as e:
    print(f"Error starting backend: {e}")
