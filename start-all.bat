@echo off
REM Batch script to start all services
REM Run this script to launch all three services in separate windows

echo.
echo 🚀 Starting Fortif.ai Voice Command System...
echo.

REM Get the script directory (project root)
set "PROJECT_ROOT=%~dp0"

REM Start Python FastAPI Server
echo 📡 Starting Python FastAPI Server (Port 8081)...
start "Python FastAPI Server" cmd /k "cd /d "%PROJECT_ROOT%" && python web_ui.py"

timeout /t 2 /nobreak >nul

REM Start Node.js Server
echo 🟢 Starting Node.js Server (Port 3001)...
start "Node.js Server" cmd /k "cd /d "%PROJECT_ROOT%server" && if not exist node_modules (echo Installing dependencies... && npm install) && npm start"

timeout /t 2 /nobreak >nul

REM Start React Dashboard
echo ⚛️  Starting React Dashboard (Port 3000)...
start "React Dashboard" cmd /k "cd /d "%PROJECT_ROOT%dashboard" && if not exist node_modules (echo Installing dependencies... && npm install) && npm run dev"

timeout /t 3 /nobreak >nul

echo.
echo ✅ All services are starting!
echo.
echo 📋 Services:
echo    • Python FastAPI: http://localhost:8081
echo    • Node.js Server: http://localhost:3001
echo    • React Dashboard: http://localhost:3000
echo.
echo 🌐 Open your browser and navigate to: http://localhost:3000/voice
echo.
pause
