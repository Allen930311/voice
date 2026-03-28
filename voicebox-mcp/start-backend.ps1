# Voicebox Backend 啟動腳本
# 用法: powershell -File start-backend.ps1

$projectDir = "c:\Users\Allen\OneDrive\Desktop\Voicebox\voicebox"
$venvPython = "$projectDir\backend\venv\Scripts\python.exe"
$port = 17493

# 檢查是否已在運行
try {
    $null = Invoke-WebRequest -Uri "http://127.0.0.1:$port/health" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
    Write-Host "Voicebox backend already running on port $port"
    exit 0
} catch {
    Write-Host "Starting Voicebox backend on port $port..."
}

# 檢查 venv
if (-not (Test-Path $venvPython)) {
    Write-Host "ERROR: Python venv not found at $venvPython"
    Write-Host "Please run 'just setup-python' in $projectDir first."
    exit 1
}

# 啟動
Set-Location $projectDir
& $venvPython -m uvicorn backend.main:app --port $port --host 127.0.0.1
