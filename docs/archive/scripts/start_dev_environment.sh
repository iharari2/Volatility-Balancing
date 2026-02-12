#!/bin/bash
# Launches development environment for Volatility Balancing
# Starts Backend, Frontend, and Regression testing

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Default values
WATCH_TESTS=true
USE_TMUX=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --no-watch)
            WATCH_TESTS=false
            shift
            ;;
        --tmux)
            USE_TMUX=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --no-watch    Run regression tests once instead of watch mode"
            echo "  --tmux        Use tmux to run all services in separate panes"
            echo "  -h, --help    Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                    # Start all services with watch mode"
            echo "  $0 --no-watch         # Run tests once"
            echo "  $0 --tmux              # Use tmux for all services"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use -h or --help for usage information"
            exit 1
            ;;
    esac
done

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
FRONTEND_DIR="$SCRIPT_DIR/frontend"

# Function to activate virtual environment
activate_venv() {
    local dir=$1
    if [ -d "$dir/.venv" ]; then
        source "$dir/.venv/bin/activate"
        echo -e "${GREEN}✅ Virtual environment activated${NC}"
        return 0
    elif [ -d "$SCRIPT_DIR/.venv" ]; then
        source "$SCRIPT_DIR/.venv/bin/activate"
        echo -e "${GREEN}✅ Virtual environment activated (from parent directory)${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠️  No virtual environment found, using system Python${NC}"
        return 1
    fi
}

# Function to start backend
start_backend() {
    local dir=$1
    cd "$dir"
    activate_venv "$dir" || true
    echo ""
    echo -e "${YELLOW}🔧 Starting Backend Server on http://0.0.0.0:8000${NC}"
    echo -e "${CYAN}   API Docs: http://localhost:8000/docs${NC}"
    echo ""
    python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
}

# Function to start frontend
start_frontend() {
    local dir=$1
    cd "$dir"
    echo -e "${MAGENTA}🎨 Starting Frontend Server on http://localhost:3000${NC}"
    echo ""
    npm run dev
}

# Function to start regression tests
start_regression_tests() {
    local dir=$1
    cd "$dir"
    activate_venv "$dir" || true
    echo ""
    
    if [ "$WATCH_TESTS" = true ]; then
        echo -e "${CYAN}🧪 Running Regression Tests (watch mode - auto-reruns every 10s)${NC}"
        echo -e "${CYAN}   Press Ctrl+C to stop watching${NC}"
        echo ""
        while true; do
            python -m pytest tests/ -v --tb=short
            echo ""
            echo -e "${YELLOW}⏳ Waiting 10 seconds before next run... (Press Ctrl+C to exit)${NC}"
            sleep 10
        done
    else
        echo -e "${CYAN}🧪 Running Regression Tests (one-time run)${NC}"
        echo ""
        python -m pytest tests/ -v --tb=short
        echo ""
        echo -e "${GREEN}✅ Tests completed.${NC}"
    fi
}

# Check if tmux is available and requested
if [ "$USE_TMUX" = true ]; then
    if ! command -v tmux &> /dev/null; then
        echo -e "${RED}❌ tmux is not installed. Install it with: sudo apt-get install tmux${NC}"
        echo -e "${YELLOW}   Falling back to background processes...${NC}"
        USE_TMUX=false
    fi
fi

echo -e "${GREEN}🚀 Starting Volatility Balancing Development Environment${NC}"
echo ""

# Use tmux if requested
if [ "$USE_TMUX" = true ]; then
    # Check if session already exists
    if tmux has-session -t volatility-balancing 2>/dev/null; then
        echo -e "${YELLOW}⚠️  tmux session 'volatility-balancing' already exists${NC}"
        echo -e "${CYAN}   Attaching to existing session...${NC}"
        echo -e "${CYAN}   Use 'tmux kill-session -t volatility-balancing' to kill it first${NC}"
        tmux attach-session -t volatility-balancing
        exit 0
    fi
    
    # Create new tmux session
    tmux new-session -d -s volatility-balancing -n backend
    tmux send-keys -t volatility-balancing:backend "cd '$BACKEND_DIR' && $(declare -f activate_venv start_backend); start_backend '$BACKEND_DIR'" C-m
    
    tmux new-window -t volatility-balancing -n frontend
    tmux send-keys -t volatility-balancing:frontend "cd '$FRONTEND_DIR' && $(declare -f start_frontend); start_frontend '$FRONTEND_DIR'" C-m
    
    tmux new-window -t volatility-balancing -n tests
    if [ "$WATCH_TESTS" = true ]; then
        tmux send-keys -t volatility-balancing:tests "cd '$BACKEND_DIR' && $(declare -f activate_venv start_regression_tests); start_regression_tests '$BACKEND_DIR'" C-m
    else
        tmux send-keys -t volatility-balancing:tests "cd '$BACKEND_DIR' && $(declare -f activate_venv start_regression_tests); start_regression_tests '$BACKEND_DIR'; read -n 1" C-m
    fi
    
    # Select first window and attach
    tmux select-window -t volatility-balancing:backend
    tmux attach-session -t volatility-balancing
    
    echo ""
    echo -e "${GREEN}✅ All services started in tmux session 'volatility-balancing'${NC}"
    echo -e "${CYAN}   Use Ctrl+B then number to switch windows:${NC}"
    echo -e "${CYAN}   0 = Backend, 1 = Frontend, 2 = Tests${NC}"
    echo -e "${CYAN}   Use 'tmux detach' to detach from session${NC}"
    
else
    # Run in background processes
    echo -e "${YELLOW}📦 Backend Server${NC}"
    (start_backend "$BACKEND_DIR" > /tmp/volatility-backend.log 2>&1) &
    BACKEND_PID=$!
    echo -e "   ${GREEN}Started (PID: $BACKEND_PID)${NC}"
    sleep 2
    
    echo -e "${MAGENTA}🎨 Frontend Server${NC}"
    (start_frontend "$FRONTEND_DIR" > /tmp/volatility-frontend.log 2>&1) &
    FRONTEND_PID=$!
    echo -e "   ${GREEN}Started (PID: $FRONTEND_PID)${NC}"
    sleep 2
    
    echo -e "${CYAN}🧪 Regression Tests${NC}"
    if [ "$WATCH_TESTS" = true ]; then
        (start_regression_tests "$BACKEND_DIR" > /tmp/volatility-tests.log 2>&1) &
        TESTS_PID=$!
        echo -e "   ${GREEN}Started in watch mode (PID: $TESTS_PID)${NC}"
    else
        start_regression_tests "$BACKEND_DIR"
        TESTS_PID=""
    fi
    
    echo ""
    echo -e "${GREEN}✅ All development services started!${NC}"
    echo ""
    echo -e "${CYAN}📍 Services:${NC}"
    echo -e "   ${CYAN}Backend:    http://localhost:8000${NC}"
    echo -e "   ${CYAN}API Docs:   http://localhost:8000/docs${NC}"
    echo -e "   ${CYAN}Frontend:   http://localhost:3000${NC}"
    if [ "$WATCH_TESTS" = true ]; then
        echo -e "   ${CYAN}Regression: Running in watch mode (auto-reruns every 10s)${NC}"
    else
        echo -e "   ${CYAN}Regression: Completed${NC}"
    fi
    echo ""
    echo -e "${YELLOW}💡 Tips:${NC}"
    echo -e "   ${YELLOW}- Logs are in /tmp/volatility-*.log${NC}"
    echo -e "   ${YELLOW}- Backend auto-reloads on code changes${NC}"
    echo -e "   ${YELLOW}- Frontend auto-reloads on code changes${NC}"
    if [ "$WATCH_TESTS" = true ]; then
        echo -e "   ${YELLOW}- Regression tests auto-rerun every 10 seconds${NC}"
    fi
    echo ""
    echo -e "${YELLOW}To stop services, run:${NC}"
    echo -e "   ${CYAN}kill $BACKEND_PID $FRONTEND_PID${NC}"
    if [ -n "$TESTS_PID" ]; then
        echo -e "   ${CYAN}kill $TESTS_PID${NC}"
    fi
    echo ""
    
    # Wait for user interrupt
    trap "echo ''; echo -e '${YELLOW}Stopping services...${NC}'; kill $BACKEND_PID $FRONTEND_PID $TESTS_PID 2>/dev/null; exit 0" INT TERM
    wait
fi

