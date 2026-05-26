$ErrorActionPreference = "Stop"

Set-Location $PSScriptRoot

Write-Host "Preparing local environment..."

if (-not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment at .venv"
    python -m venv .venv
}

$python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"

Write-Host "Installing Python dependencies from requirements.txt"
& $python -m pip install -r requirements.txt

function Get-AguServerProcesses {
    Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {
        $_.Name -eq "python.exe" -and
        $_.CommandLine -like "*$PSScriptRoot*" -and
        $_.CommandLine -like "*uvicorn app.main:app*"
    }
}

function Stop-AguServerProcesses {
    $processes = @(Get-AguServerProcesses)
    if (-not $processes.Count) {
        return
    }

    Write-Host "Stopping existing Agu uvicorn processes..."

    foreach ($process in $processes) {
        try {
            Stop-Process -Id $process.ProcessId -Force -ErrorAction Stop
        } catch {
            Write-Host "Skipping process that could not be stopped: PID=$($process.ProcessId)"
        }
    }

    Start-Sleep -Seconds 1
}

function Test-PortListening([int]$Port) {
    try {
        $listener = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction Stop | Select-Object -First 1
        return $null -ne $listener
    } catch {
        return $false
    }
}

function Get-PreferredPort {
    foreach ($port in @(8000, 8001, 8002, 8010)) {
        if (-not (Test-PortListening -Port $port)) {
            return $port
        }
    }

    throw "Ports 8000, 8001, 8002, and 8010 are all in use. Stop the old service and try again."
}

Stop-AguServerProcesses

$port = Get-PreferredPort
Write-Host "Starting Agu local app: http://127.0.0.1:$port"
& $python -m uvicorn app.main:app --host 127.0.0.1 --port $port
