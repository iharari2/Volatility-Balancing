#!/bin/bash
# Script to start the backend server

cd "$(dirname "$0")/backend"
source ../.venv/bin/activate
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000



