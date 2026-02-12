#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Launches three WSL windows for Frontend, Backend, and Regression testing.

.DESCRIPTION
    This script opens three separate WSL terminal windows:
    1. Frontend - Runs the Vite development server
    2. Backend - Runs the FastAPI server with uvicorn
    3. Regression - Runs pytest regression tests (watch mode or once)

.PARAMETER WatchTests
    If specified, regression tests will run in watch mode (auto-reruns every 10s).
    Otherwise, tests run once and the window stays open.

.EXAMPLE
    .\start_dev_environment.ps1
    Launches all three windows with regression tests in watch mode.

.EXAMPLE
    .\start_dev_environment.ps1 -WatchTests:$false
    Launches all three windows, runs regression tests once.
#>

param(
    [switch]$WatchTests = $true
)

$ErrorActionPreference = "Stop"

# Detect WSL distribution (defaults to Ubuntu)
$WslDistro = "Ubuntu"
try {
    $wslOutput = wsl.exe -l -q 2>&1 | Out-String
    if ($wslOutput) {
        $distros = $wslOutput -split "`n" | Where-Object { $_.Trim() -and $_ -notmatch "Windows" -and $_ -notmatch "NAME" } | ForEach-Object { $_.Trim() }
        if ($distros) {
            # Try to find Ubuntu or use first available distro
            $ubuntuDistro = $distros | Where-Object { $_ -like "*Ubuntu*" } | Select-Object -First 1
            if ($ubuntuDistro) {
                $WslDistro = $ubuntuDistro
            } else {
                $WslDistro = $distros | Select-Object -First 1
            }
        }
    }
} catch {
    Write-Host "⚠️  Could not detect WSL distribution, using default: $WslDistro" -ForegroundColor Yellow
}

# Get the WSL path (modify this if your path is different)
$WslPath = "/home/iharari/Volatility-Balancing"
$BackendPath = "$WslPath/backend"
$FrontendPath = "$WslPath/frontend"

Write-Host "Using WSL Distribution: $WslDistro" -ForegroundColor Gray
Write-Host "Project Path: $WslPath" -ForegroundColor Gray
Write-Host ""

Write-Host "🚀 Starting Volatility Balancing Development Environment" -ForegroundColor Green
Write-Host ""

# Function to launch a WSL window with a command
function Start-WslWindow {
    param(
        [string]$Title,
        [string]$WorkingDir,
        [string]$Command,
        [string]$Color = "Cyan"
    )
    
    Write-Host "  Starting $Title..." -ForegroundColor $Color
    
    # Build the full bash command
    # Use bash -c with proper quoting to handle multi-line commands
    $bashCommand = "cd '$WorkingDir' && $Command"
    
    # Try to use Windows Terminal (wt.exe) if available
    if (Get-Command wt.exe -ErrorAction SilentlyContinue) {
        # Use Windows Terminal with new tab
        Start-Process wt.exe -ArgumentList "new-tab", "--title", $Title, "wsl", "-d", $WslDistro, "-e", "bash", "-c", $bashCommand
    } else {
        # Fallback: Use wsl.exe directly (opens in default terminal)
        Start-Process wsl.exe -ArgumentList "-d", $WslDistro, "-e", "bash", "-c", $bashCommand
    }
    
    Start-Sleep -Milliseconds 800
}

# 1. Start Backend Server
Write-Host "📦 Backend Server" -ForegroundColor Yellow
$backendCommand = "if [ -d '.venv' ]; then source .venv/bin/activate && echo '✅ Virtual environment activated'; elif [ -d '../.venv' ]; then source ../.venv/bin/activate && echo '✅ Virtual environment activated (from parent directory)'; else echo '⚠️  No virtual environment found, using system Python'; fi; echo ''; echo '🔧 Starting Backend Server on http://0.0.0.0:8000'; echo '   API Docs: http://localhost:8000/docs'; echo ''; python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
Start-WslWindow -Title "Backend Server" -WorkingDir $BackendPath -Command $backendCommand -Color "Yellow"

# 2. Start Frontend Server
Write-Host "🎨 Frontend Server" -ForegroundColor Magenta
$frontendCommand = "echo '🎨 Starting Frontend Server on http://localhost:3000'; echo ''; npm run dev"
Start-WslWindow -Title "Frontend Server" -WorkingDir $FrontendPath -Command $frontendCommand -Color "Magenta"

# 3. Start Regression Tests
Write-Host "🧪 Regression Tests" -ForegroundColor Cyan
if ($WatchTests) {
    $regressionCommand = "if [ -d '.venv' ]; then source .venv/bin/activate && echo '✅ Virtual environment activated'; elif [ -d '../.venv' ]; then source ../.venv/bin/activate && echo '✅ Virtual environment activated (from parent directory)'; else echo '⚠️  No virtual environment found, using system Python'; fi; echo ''; echo '🧪 Running Regression Tests (watch mode - auto-reruns every 10s)'; echo '   Press Ctrl+C to stop watching'; echo ''; while true; do python -m pytest tests/ -v --tb=short; echo ''; echo '⏳ Waiting 10 seconds before next run... (Press Ctrl+C to exit)'; sleep 10; done"
} else {
    $regressionCommand = "if [ -d '.venv' ]; then source .venv/bin/activate && echo '✅ Virtual environment activated'; elif [ -d '../.venv' ]; then source ../.venv/bin/activate && echo '✅ Virtual environment activated (from parent directory)'; else echo '⚠️  No virtual environment found, using system Python'; fi; echo ''; echo '🧪 Running Regression Tests (one-time run)'; echo ''; python -m pytest tests/ -v --tb=short; echo ''; echo '✅ Tests completed. Press any key to close...'; read -n 1"
}
Start-WslWindow -Title "Regression Tests" -WorkingDir $BackendPath -Command $regressionCommand -Color "Cyan"

Write-Host ""
Write-Host "✅ All development windows launched!" -ForegroundColor Green
Write-Host ""
Write-Host "📍 Services:" -ForegroundColor White
Write-Host "   Backend:    http://localhost:8000" -ForegroundColor Cyan
Write-Host "   API Docs:   http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "   Frontend:   http://localhost:3000" -ForegroundColor Cyan
if ($WatchTests) {
    Write-Host "   Regression: Running in watch mode (auto-reruns every 10s)" -ForegroundColor Cyan
} else {
    Write-Host "   Regression: Running once" -ForegroundColor Cyan
}
Write-Host ""
Write-Host "💡 Tips:" -ForegroundColor Gray
Write-Host "   - Close the terminal windows to stop the services" -ForegroundColor Gray
Write-Host "   - Backend auto-reloads on code changes" -ForegroundColor Gray
Write-Host "   - Frontend auto-reloads on code changes" -ForegroundColor Gray
if ($WatchTests) {
    Write-Host "   - Regression tests auto-rerun every 10 seconds" -ForegroundColor Gray
}
Write-Host ""

