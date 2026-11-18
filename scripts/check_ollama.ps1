# ==============================================================================
# NexusRAG Ollama Runtime Diagnostic
# ==============================================================================

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Checking Local Ollama Runtime for NexusRAG" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

$ollamaCmd = Get-Command ollama -ErrorAction SilentlyContinue
if ($ollamaCmd) {
    Write-Host "[OK] Ollama CLI installed: $($ollamaCmd.Source)" -ForegroundColor Green
} else {
    Write-Host "[WARNING] Ollama is not installed or not in PATH." -ForegroundColor Yellow
    Write-Host "  To install on Windows:" -ForegroundColor White
    Write-Host "    winget install Ollama.Ollama" -ForegroundColor White
    Write-Host "  Or download installer from: https://ollama.com/download" -ForegroundColor White
}

# Check localhost API
try {
    $res = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -Method Get -TimeoutSec 3 -ErrorAction Stop
    Write-Host "[OK] Ollama server is running at http://localhost:11434" -ForegroundColor Green
    $models = $res.models | ForEach-Object { $_.name }
    if ($models) {
        Write-Host "  Installed Models: $($models -join ', ')" -ForegroundColor White
    } else {
        Write-Host "  No models downloaded yet. Run:" -ForegroundColor Yellow
        Write-Host "    ollama run qwen2.5:3b" -ForegroundColor White
    }
} catch {
    Write-Host "[NOTICE] Ollama server is currently offline." -ForegroundColor Yellow
    Write-Host "  Start the server with:" -ForegroundColor White
    Write-Host "    ollama serve" -ForegroundColor White
    Write-Host "  Recommended lightweight model for 16GB RAM / 4GB VRAM:" -ForegroundColor White
    Write-Host "    ollama run qwen2.5:3b" -ForegroundColor White
}

Write-Host "============================================================" -ForegroundColor Cyan
