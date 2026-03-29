# Voicebox GPU Launcher (Intel Arc / DirectML)
# This script stops the current Voicebox backend and restarts it with GPU acceleration.

$ErrorActionPreference = "Stop"
$VoiceboxPath = "C:\Users\Allen\OneDrive\Desktop\Voicebox\voicebox"
$GpuVenv = "C:\Users\Allen\AppData\Local\voicebox-venv312"
$Port = 17493

Write-Host "--- Voicebox GPU Switcher ---" -ForegroundColor Cyan

# 1. Kill existing backend process
Write-Host "[1/3] Terminating existing Voicebox backend on port $Port..."
$process = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -First 1
if ($process) {
    Stop-Process -Id $process -Force
    Write-Host "      Process $process terminated." -ForegroundColor Green
} else {
    Write-Host "      No active process found on port $Port." -ForegroundColor Yellow
}

# 2. Verify GPU Venv
Write-Host "[2/3] Verifying GPU Environment..."
$PythonExe = "$GpuVenv\Scripts\python.exe"
if (-not (Test-Path $PythonExe)) {
    Write-Host "ERROR: GPU Virtual Environment not found at $GpuVenv" -ForegroundColor Red
    Write-Host "Please ensure Python 3.12 is installed and run the setup command in Voicebox."
    exit 1
}
Write-Host "      GPU Venv verified: $GpuVenv" -ForegroundColor Green

# 3. Launch Backend with GPU
Write-Host "[3/3] Starting Backend with Intel Arc GPU (DirectML + OpenVINO)..." -ForegroundColor Cyan
$env:OPENVINO_DEVICE = "GPU"
$env:VOICEBOX_BACKEND = "openvino"
$env:VOICEBOX_BACKEND_VARIANT = "gpu"

Set-Location $VoiceboxPath
Start-Process -FilePath $PythonExe -ArgumentList "-m", "uvicorn", "backend.app:app", "--reload", "--port", "$Port" -NoNewWindow

Write-Host "`nSUCCESS: Voicebox is now starting in GPU mode." -ForegroundColor Green
Write-Host "Wait about 5-10 seconds for the server to initialize, then let me know!"
