# PowerShell script to start all services
# Run this script to launch all three services in separate windows

Write-Host "🚀 Starting Fortif.ai Voice Command System..." -ForegroundColor Green
Write-Host ""

# Get the script directory (project root)
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

# Start Python FastAPI Server
Write-Host "📡 Starting Python FastAPI Server (Port 8081)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$projectRoot'; Write-Host 'Python FastAPI Server' -ForegroundColor Cyan; python web_ui.py"

Start-Sleep -Seconds 2

# Start Node.js Server
Write-Host "🟢 Starting Node.js Server (Port 3001)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$projectRoot\server'; Write-Host 'Node.js Server' -ForegroundColor Cyan; if (-not (Test-Path 'node_modules')) { Write-Host 'Installing dependencies...' -ForegroundColor Yellow; npm install }; npm start"

Start-Sleep -Seconds 2

# Start React Dashboard
Write-Host "⚛️  Starting React Dashboard (Port 3000)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$projectRoot\dashboard'; Write-Host 'React Dashboard' -ForegroundColor Cyan; if (-not (Test-Path 'node_modules')) { Write-Host 'Installing dependencies...' -ForegroundColor Yellow; npm install }; npm run dev"

Start-Sleep -Seconds 3

Write-Host ""
Write-Host "✅ All services are starting!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Services:" -ForegroundColor Cyan
Write-Host "   • Python FastAPI: http://localhost:8081" -ForegroundColor White
Write-Host "   • Node.js Server: http://localhost:3001" -ForegroundColor White
Write-Host "   • React Dashboard: http://localhost:3000" -ForegroundColor White
Write-Host ""
Write-Host "🌐 Open your browser and navigate to: http://localhost:3000/voice" -ForegroundColor Green
Write-Host ""
Write-Host "Press any key to exit this window (services will continue running)..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
