@echo off
REM Batch script to start all services using npm concurrently
REM This runs all services in a single terminal window

echo.
echo 🚀 Starting Fortif.ai Voice Command System (All in One Terminal)...
echo.

cd /d "%~dp0"

REM Check if node_modules exists, if not install dependencies
if not exist "node_modules" (
    echo Installing dependencies...
    call npm install
)

REM Start all services using concurrently
echo Starting all services...
echo.
call npm start

pause
