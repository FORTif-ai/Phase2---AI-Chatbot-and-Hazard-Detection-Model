# PowerShell script to start all services in one terminal using background jobs
# Run: .\start-all-in-one.ps1

Write-Host "🚀 Starting Fortif.ai Voice Command System (All in One Terminal)..." -ForegroundColor Green
Write-Host ""

# Get the script directory (project root)
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectRoot

# Function to check if a port is in use
function Test-Port {
    param([int]$Port)
    $connection = Test-NetConnection -ComputerName localhost -Port $Port -InformationLevel Quiet -WarningAction SilentlyContinue
    return $connection
}

# Check if ports are already in use
$ports = @{8000 = "RAG API"; 8081 = "Python FastAPI"; 3001 = "Node.js"; 3000 = "React Dashboard"}
foreach ($port in $ports.Keys) {
    if (Test-Port -Port $port) {
        Write-Host "⚠️  Port $port ($($ports[$port])) is already in use" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "Starting services..." -ForegroundColor Cyan
Write-Host ""

# Start RAG API Server (port 8000)
Write-Host "[RAG] Starting RAG API Server on port 8000..." -ForegroundColor Cyan
$ragJob = Start-Job -ScriptBlock {
    Set-Location $using:projectRoot
    Set-Location rag
    python main.py
} | Out-Null

# Start Python FastAPI Server (port 8080)
Write-Host "[PYTHON] Starting Python FastAPI Server on port 8080..." -ForegroundColor Yellow
$pythonJob = Start-Job -ScriptBlock {
    Set-Location $using:projectRoot
    python web_ui.py
} | Out-Null

# Start Node.js Server (port 3001)
Write-Host "[NODE] Starting Node.js Server on port 3001..." -ForegroundColor Green
$nodeJob = Start-Job -ScriptBlock {
    Set-Location $using:projectRoot
    Set-Location server
    if (-not (Test-Path 'node_modules')) {
        Write-Host "[NODE] Installing dependencies..." -ForegroundColor Yellow
        npm install
    }
    npm start
} | Out-Null

# Start React Dashboard (port 3000)
Write-Host "[REACT] Starting React Dashboard on port 3000..." -ForegroundColor Blue
$reactJob = Start-Job -ScriptBlock {
    Set-Location $using:projectRoot
    Set-Location dashboard
    if (-not (Test-Path 'node_modules')) {
        Write-Host "[REACT] Installing dependencies..." -ForegroundColor Yellow
        npm install
    }
    npm run dev
} | Out-Null

# Wait a bit for services to start
Start-Sleep -Seconds 3

Write-Host ""
Write-Host "✅ All services started in background!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Services:" -ForegroundColor Cyan
Write-Host "   • RAG API Server: http://localhost:8000" -ForegroundColor White
Write-Host "   • Python FastAPI: http://localhost:8081" -ForegroundColor White
Write-Host "   • Node.js Server: http://localhost:3001" -ForegroundColor White
Write-Host "   • React Dashboard: http://localhost:3000" -ForegroundColor White
Write-Host ""
Write-Host "🌐 Open your browser: http://localhost:3000" -ForegroundColor Green
Write-Host ""
Write-Host "📊 View logs: Get-Job | Receive-Job" -ForegroundColor Yellow
Write-Host "🛑 Stop all: Get-Job | Stop-Job; Get-Job | Remove-Job" -ForegroundColor Yellow
Write-Host ""
Write-Host "Press Ctrl+C to stop all services and exit..." -ForegroundColor Yellow

# Function to cleanup jobs on exit
function Cleanup {
    Write-Host ""
    Write-Host "Stopping all services..." -ForegroundColor Yellow
    Get-Job | Stop-Job
    Get-Job | Remove-Job
    Write-Host "✅ All services stopped" -ForegroundColor Green
}

# Register cleanup on exit
Register-EngineEvent PowerShell.Exiting -Action { Cleanup } | Out-Null

# Monitor jobs and display output
try {
    while ($true) {
        $jobs = Get-Job
        foreach ($job in $jobs) {
            if ($job.State -eq "Running") {
                $output = Receive-Job -Job $job -ErrorAction SilentlyContinue
                if ($output) {
                    $prefix = switch ($job.Name) {
                        { $_ -like "*rag*" } { "[RAG] " }
                        { $_ -like "*python*" } { "[PYTHON] " }
                        { $_ -like "*node*" } { "[NODE] " }
                        { $_ -like "*react*" } { "[REACT] " }
                        default { "[JOB] " }
                    }
                    Write-Host "$prefix$output" -NoNewline
                }
            }
        }
        Start-Sleep -Milliseconds 500
    }
} catch {
    Cleanup
}
