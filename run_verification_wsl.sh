#!/bin/bash
# WSL Verification Runner - Step by Step
# Run this script to verify Phase 1 functionality

set -e  # Exit on error

echo "============================================================"
echo "Phase 1 Verification - WSL Setup"
echo "============================================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Step 1: Check Python
echo -e "${BLUE}Step 1: Checking Python...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 not found. Installing...${NC}"
    sudo apt update
    sudo apt install -y python3 python3-pip python3-venv
fi
PYTHON_VERSION=$(python3 --version)
echo -e "${GREEN}✅ Found: $PYTHON_VERSION${NC}"
echo ""

# Step 2: Check requests library
echo -e "${BLUE}Step 2: Checking requests library...${NC}"
if ! python3 -c "import requests" 2>/dev/null; then
    echo -e "${YELLOW}⚠️  requests not found. Installing...${NC}"
    pip3 install --user requests
fi
echo -e "${GREEN}✅ requests library available${NC}"
echo ""

# Step 3: Check if backend is running
echo -e "${BLUE}Step 3: Checking if backend is running...${NC}"
if curl -s http://localhost:8000/v1/healthz > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Backend is running!${NC}"
    BACKEND_RUNNING=true
else
    echo -e "${RED}❌ Backend is not running${NC}"
    echo -e "${YELLOW}Please start backend in another terminal:${NC}"
    echo "  cd backend"
    echo "  source .venv/bin/activate"
    echo "  python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
    echo ""
    read -p "Press Enter when backend is running, or Ctrl+C to exit..."
    BACKEND_RUNNING=false
fi
echo ""

# Step 4: Verify backend again
echo -e "${BLUE}Step 4: Verifying backend connection...${NC}"
if curl -s http://localhost:8000/v1/healthz > /dev/null 2>&1; then
    HEALTH=$(curl -s http://localhost:8000/v1/healthz)
    echo -e "${GREEN}✅ Backend health check: $HEALTH${NC}"
else
    echo -e "${RED}❌ Cannot connect to backend${NC}"
    echo -e "${YELLOW}Make sure:${NC}"
    echo "  1. Backend is running on port 8000"
    echo "  2. Backend is bound to 0.0.0.0 (not 127.0.0.1)"
    echo "  3. No firewall blocking port 8000"
    exit 1
fi
echo ""

# Step 5: Run verification script
echo -e "${BLUE}Step 5: Running verification tests...${NC}"
echo ""

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Run verification
python3 verify_phase1.py

EXIT_CODE=$?

echo ""
echo "============================================================"
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✅ Verification completed successfully!${NC}"
else
    echo -e "${RED}❌ Verification failed. Check errors above.${NC}"
fi
echo "============================================================"

exit $EXIT_CODE




































