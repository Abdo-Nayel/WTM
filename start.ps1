# WorkTaskMe — one-command local server (feels like production)
# Usage:  .\start.ps1
# Stop:   Ctrl+C

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Backend = Join-Path $Root "backend"
$Python = Join-Path $Backend ".venv\Scripts\python.exe"

Write-Host ""
Write-Host "=== WorkTaskMe Local Server ===" -ForegroundColor Cyan
Write-Host "Root: $Root"

if (-not (Test-Path $Python)) {
    Write-Host "Creating virtualenv..." -ForegroundColor Yellow
    & "C:\Users\Admin\AppData\Local\Programs\Python\Python313\python.exe" -m venv (Join-Path $Backend ".venv")
    if (-not (Test-Path $Python)) {
        python -m venv (Join-Path $Backend ".venv")
    }
    & $Python -m pip install -r (Join-Path $Backend "requirements.txt")
}

Set-Location $Backend

# Ensure .env exists
$EnvFile = Join-Path $Backend ".env"
if (-not (Test-Path $EnvFile)) {
    Copy-Item (Join-Path $Backend ".env.example") $EnvFile
    Write-Host "Created .env from .env.example" -ForegroundColor Yellow
}

Write-Host "Bootstrapping DB + demo data..." -ForegroundColor Yellow
& $Python manage.py bootstrap_local

Write-Host ""
Write-Host "Starting ASGI server (Daphne) on http://0.0.0.0:8000 ..." -ForegroundColor Green
Write-Host "Open:  http://127.0.0.1:8000/" -ForegroundColor Green
Write-Host "API:   http://127.0.0.1:8000/api/docs/" -ForegroundColor Green
Write-Host "Demo:  demo@worktaskme.com / Demo1234!" -ForegroundColor Green
Write-Host ""

& $Python -m daphne -b 0.0.0.0 -p 8000 config.asgi:application
