@echo off
REM Batch file wrapper for PowerShell script
REM This allows double-clicking to run the script

powershell.exe -ExecutionPolicy Bypass -File "%~dp0start_dev_environment.ps1" %*

