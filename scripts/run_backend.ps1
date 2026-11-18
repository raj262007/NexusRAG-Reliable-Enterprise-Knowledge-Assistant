# ==============================================================================
# NexusRAG Backend Server Runner
# ==============================================================================

$ErrorActionPreference = "Stop"
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Starting NexusRAG FastAPI Backend Server" -ForegroundColor Cyan
Write-Host "URL: http://127.0.0.1:8000" -ForegroundColor Green
Write-Host "Interactive UI: http://127.0.0.1:8000/" -ForegroundColor Green
Write-Host "Swagger Docs:   http://127.0.0.1:8000/docs" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan

# Set project root in PYTHONPATH
$projectRoot = Resolve-Path "$PSScriptRoot\.."
$env:PYTHONPATH = $projectRoot

# Ensure virtual environment Python is used
$pythonExe = "$projectRoot\venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonExe = "python"
}

& $pythonExe -m uvicorn app.api.main:app --host 127.0.0.1 --port 8000 --reload
