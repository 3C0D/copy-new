#!/usr/bin/env pwsh

Write-Host "===== Testing Console Mode Executable ====="
Write-Host ""

$exePath = "dist\dev\Writing Tools.exe"

if (-not (Test-Path $exePath)) {
    Write-Host "ERROR: Console build not found at $exePath"
    Write-Host ""
    Write-Host "Please run first:"
    Write-Host "  python scripts\dev_build.py --console"
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "Launching Writing Tools in console mode..."
Write-Host "You should see logs directly in this window."
Write-Host ""
Write-Host "Press Ctrl+C to stop the application."
Write-Host "=========================================="
Write-Host ""

# Run the executable directly in this console
& $exePath

Write-Host ""
Write-Host "=========================================="
Write-Host "Application has exited."
Read-Host "Press Enter to exit"
