# Voicebox GPU Launcher (Intel Arc / OpenVINO) - idempotent production launcher
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File start-voicebox-gpu.ps1           # start only if not healthy
#   powershell -ExecutionPolicy Bypass -File start-voicebox-gpu.ps1 -Force    # always kill + restart
#   powershell -ExecutionPolicy Bypass -File start-voicebox-gpu.ps1 -WarmUp   # after ready, run a tiny
#                                                                             # generation so OpenVINO kernel
#                                                                             # compilation happens now, not at
#                                                                             # first real use (5-8 min saved)
#
# NOTE: production mode, NO --reload. The project lives inside OneDrive; uvicorn's
# reload watcher restarts workers whenever OneDrive touches a file, killing
# generations mid-flight. Never add --reload back.
param(
    [switch]$Force,
    [switch]$WarmUp
)
$ErrorActionPreference = "Stop"
$VoiceboxPath = "C:\Users\Allen\OneDrive\Desktop\Voicebox\voicebox"
$GpuVenv      = "C:\Users\Allen\AppData\Local\voicebox-venv312"
$Port         = 17493
$DataDir      = "C:\Users\Allen\AppData\Roaming\sh.voicebox.app"
$LogDir       = Join-Path $DataDir "logs"
$BaseUrl      = "http://127.0.0.1:$Port"
$ConfigPath   = "C:\Users\Allen\OneDrive\Desktop\Voicebox\config\profiles.json"

function Get-Health {
    try { return Invoke-RestMethod -Uri "$BaseUrl/health" -TimeoutSec 3 } catch { return $null }
}

$health = Get-Health
if ($health -and -not $Force) {
    $gpu = $health.gpu_type; if (-not $gpu) { $gpu = "unknown" }
    Write-Host "[OK] Backend already running (gpu_type=$gpu). Use -Force to restart." -ForegroundColor Green
} else {
    # --- 1. Kill stale processes: uvicorn matches AND anything still holding the port
    #        (multiprocessing children can survive their parent and keep the port)
    $killed = @()
    Get-CimInstance Win32_Process -Filter "Name = 'python.exe'" |
        Where-Object { $_.CommandLine -match "uvicorn backend\.(app|main):app" } |
        ForEach-Object {
            Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
            $killed += $_.ProcessId
        }
    $portPids = netstat -ano | Select-String ":$Port\s" |
        ForEach-Object { ($_.Line.Trim() -split '\s+')[-1] } | Sort-Object -Unique
    foreach ($p in $portPids) {
        if ($p -match '^\d+$' -and [int]$p -gt 4) {
            Stop-Process -Id ([int]$p) -Force -ErrorAction SilentlyContinue
            $killed += $p
        }
    }
    if ($killed.Count -gt 0) {
        Write-Host "[1/4] Killed stale PIDs: $(($killed | Sort-Object -Unique) -join ', ')"
        Start-Sleep -Seconds 2
    } else {
        Write-Host "[1/4] No stale processes."
    }

    # --- 2. Verify GPU venv (wrong venv = stuck at loading_model forever)
    $PythonExe = Join-Path $GpuVenv "Scripts\python.exe"
    if (-not (Test-Path $PythonExe)) {
        Write-Host "[ERROR] GPU venv missing: $GpuVenv" -ForegroundColor Red
        exit 1
    }
    Write-Host "[2/4] GPU venv OK: $GpuVenv"

    # --- 3. Launch backend (hidden window, logs to AppData)
    New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
    $stamp  = Get-Date -Format "yyyyMMdd-HHmmss"
    $outLog = Join-Path $LogDir "backend-$stamp.out.log"
    $errLog = Join-Path $LogDir "backend-$stamp.err.log"
    $env:OPENVINO_DEVICE          = "GPU"
    $env:VOICEBOX_BACKEND         = "openvino"
    $env:VOICEBOX_BACKEND_VARIANT = "gpu"
    $env:VOICEBOX_DATA_DIR        = $DataDir
    $env:PYTHONIOENCODING         = "utf-8"
    $env:PYTHONUTF8               = "1"
    Start-Process -FilePath $PythonExe `
        -ArgumentList "-m","uvicorn","backend.app:app","--port","$Port","--host","127.0.0.1" `
        -WorkingDirectory $VoiceboxPath -WindowStyle Hidden `
        -RedirectStandardOutput $outLog -RedirectStandardError $errLog
    Write-Host "[3/4] Backend starting... (logs: $LogDir)"

    # --- 4. Wait for /health (up to 90 s)
    $ready = $false
    for ($i = 1; $i -le 90; $i++) {
        Start-Sleep -Seconds 1
        $health = Get-Health
        if ($health) { $ready = $true; break }
    }
    if (-not $ready) {
        Write-Host "[ERROR] Backend not healthy after 90 s. Check $errLog" -ForegroundColor Red
        exit 1
    }
    $gpu = $health.gpu_type; if (-not $gpu) { $gpu = "unknown" }
    Write-Host "[4/4] Backend ready in ${i}s (gpu_type=$gpu)." -ForegroundColor Green
}

if ($WarmUp) {
    # Tiny generation so kernel compilation happens now. Non-fatal on any error.
    try {
        $cfg = Get-Content $ConfigPath -Encoding UTF8 -Raw | ConvertFrom-Json
        $defKey = $cfg.social_defaults.zh
        $prof = $cfg.profiles.$defKey
        # "warm-up test" in Chinese, built from code points to keep this file pure ASCII
        $warmText = -join [char[]]@(0x6696, 0x6A5F, 0x6E2C, 0x8A66)
        $payload = @{
            profile_id = $prof.id
            text       = $warmText
            language   = $prof.language
            engine     = $prof.engine
            model_size = $prof.model_size
            normalize  = $true
        } | ConvertTo-Json
        $bytes = [System.Text.Encoding]::UTF8.GetBytes($payload)
        $resp = Invoke-RestMethod -Uri "$BaseUrl/generate" -Method Post -Body $bytes `
            -ContentType "application/json; charset=utf-8" -TimeoutSec 60
        $genId = $resp.id
        Write-Host "[WarmUp] Submitted $genId. First GPU run compiles kernels (can take 5-8 min)..."
        $done = $false
        for ($i = 1; $i -le 60; $i++) {
            Start-Sleep -Seconds 10
            try { $st = Invoke-RestMethod -Uri "$BaseUrl/history/$genId" -TimeoutSec 10 } catch { continue }
            if ($st.status -eq "completed" -and $st.duration -gt 0) {
                Write-Host "[WarmUp] Done in $($i * 10)s. Kernels compiled; next generations are fast." -ForegroundColor Green
                $done = $true; break
            }
            if ($st.status -eq "failed") {
                Write-Host "[WarmUp] Generation failed (non-fatal); backend itself is up." -ForegroundColor Yellow
                $done = $true; break
            }
        }
        if (-not $done) {
            Write-Host "[WarmUp] Still running after 10 min; leaving it in background (non-fatal)." -ForegroundColor Yellow
        }
    } catch {
        Write-Host "[WarmUp] Skipped (non-fatal): $($_.Exception.Message)" -ForegroundColor Yellow
    }
}
exit 0
