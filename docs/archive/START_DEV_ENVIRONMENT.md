# Development Environment Startup Script

This script launches three WSL terminal windows for the Volatility Balancing development environment.

## Quick Start

### Option 1: Double-click (Windows)
- Double-click `start_dev_environment.bat` to run the script

### Option 2: PowerShell
```powershell
.\start_dev_environment.ps1
```

### Option 3: PowerShell with options
```powershell
# Run regression tests once (not in watch mode)
.\start_dev_environment.ps1 -WatchTests:$false
```

## What It Does

The script opens three separate WSL terminal windows:

1. **Backend Server** (Yellow)
   - Activates Python virtual environment (if found)
   - Starts FastAPI server with uvicorn on port 8000
   - Auto-reloads on code changes
   - API available at: http://localhost:8000
   - API docs at: http://localhost:8000/docs

2. **Frontend Server** (Magenta)
   - Starts Vite development server on port 3000
   - Auto-reloads on code changes
   - Available at: http://localhost:3000

3. **Regression Tests** (Cyan)
   - Activates Python virtual environment (if found)
   - Runs pytest regression tests
   - By default: Watch mode (auto-reruns every 10 seconds)
   - With `-WatchTests:$false`: Runs once

## Requirements

- Windows 10/11 with WSL 2 installed
- Ubuntu (or another WSL distribution) with the project set up
- Python virtual environment in `backend/.venv` (optional, will use system Python if not found)
- Node.js and npm installed for frontend

## Configuration

If your WSL path is different, edit the script and modify:

```powershell
$WslPath = "/home/iharari/Volatility-Balancing"
```

If your WSL distribution name is different, the script will auto-detect it, but you can also modify:

```powershell
$WslDistro = "Ubuntu"  # Change to your distribution name
```

## Troubleshooting

### Windows Terminal not opening
- The script will fall back to the default terminal if Windows Terminal is not available
- Install Windows Terminal from Microsoft Store for a better experience

### Virtual environment not found
- The script will use system Python if no `.venv` is found
- Create a virtual environment: `cd backend && python -m venv .venv`

### Ports already in use
- Backend uses port 8000, Frontend uses port 3000
- Stop any existing services on these ports before running the script

### WSL distribution not found
- Make sure WSL is installed and at least one distribution is set up
- Run `wsl -l` to see available distributions

## Stopping Services

Simply close the terminal windows to stop the services. The script doesn't manage process lifecycle - each window runs independently.





















