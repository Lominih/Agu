$ErrorActionPreference = "Stop"

Set-Location $PSScriptRoot

if (-not (Test-Path ".venv")) {
    python -m venv .venv
}

$python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"

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

    foreach ($process in $processes) {
        try {
            Stop-Process -Id $process.ProcessId -Force -ErrorAction Stop
        } catch {
            Write-Host "跳过无法停止的旧进程 PID=$($process.ProcessId)"
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

    throw "8000-8010 常用端口都被占用，请先关闭旧服务后重试。"
}

Stop-AguServerProcesses

$port = Get-PreferredPort
Write-Host "启动 A 股本地工作台: http://127.0.0.1:$port"
& $python -m uvicorn app.main:app --host 127.0.0.1 --port $port
