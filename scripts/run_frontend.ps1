# ==============================================================================
# NexusRAG Next.js Frontend Runner
# ==============================================================================

$ErrorActionPreference = "Stop"
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Starting NexusRAG Next.js Frontend Development Server" -ForegroundColor Cyan
Write-Host "URL: http://localhost:3000" -ForegroundColor Green
Write-Host "Connecting to API on: http://localhost:8000/api" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan

Set-Location -Path "$PSScriptRoot\..\frontend"

if (-not (Test-Path "node_modules")) {
    Write-Host "Installing frontend dependencies..." -ForegroundColor Yellow
    npm install
}

npm run dev
