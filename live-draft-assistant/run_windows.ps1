$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Get-Command py -ErrorAction SilentlyContinue)) {
    Write-Host "Python is required. Install Python 3.11 or newer, then run this file again." -ForegroundColor Red
    Read-Host "Press Enter to close"
    exit 1
}

$needsInstall = -not (Test-Path ".venv")
if ($needsInstall) {
    py -3 -m venv .venv
}

if ($needsInstall -or -not (Test-Path ".venv\.draft-assistant-installed")) {
    & .\.venv\Scripts\python.exe -m pip install --upgrade pip
    & .\.venv\Scripts\python.exe -m pip install -e ".[dev]"
    New-Item -ItemType File -Path ".venv\.draft-assistant-installed" -Force | Out-Null
}

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Created .env. Manual mode works now; add Yahoo credentials for live syncing." -ForegroundColor Yellow
}

Start-Process powershell -ArgumentList '-NoProfile', '-Command', 'Start-Sleep -Seconds 2; Start-Process "http://127.0.0.1:8765"' -WindowStyle Hidden
& .\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8765
