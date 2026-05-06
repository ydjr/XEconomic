@echo off
:: ============================================
:: XEconomic Dashboard — One-Click Start
:: ============================================
:: Starts FastAPI backend + Vite frontend
:: Dashboard: http://localhost:5173
:: ============================================

echo.
echo  ╔═══════════════════════════════════════════╗
echo  ║     XEconomic Dashboard Launcher          ║
echo  ╚═══════════════════════════════════════════╝
echo.

cd /d "%~dp0"

:: Check if .venv exists
if not exist ".venv\Scripts\activate.bat" (
    echo [!] Virtual environment not found.
    echo     Run setup.bat first.
    pause
    exit /b 1
)

:: Start FastAPI Backend
echo [1/2] Starting FastAPI backend on port 8000...
start "XEconomic-API" cmd /k "cd /d %~dp0 && .venv\Scripts\activate && uvicorn api.main:app --reload --host 0.0.0.0 --port 8000"

:: Wait for backend to start
timeout /t 3 /nobreak > nul

:: Start Vite Frontend
echo [2/2] Starting Vite frontend on port 5173...
start "XEconomic-Dashboard" cmd /k "cd /d %~dp0\dashboard && npm run dev"

echo.
echo  ✓ Dashboard starting...
echo.
echo    Frontend:  http://localhost:5173
echo    API:       http://localhost:8000
echo    Health:    http://localhost:8000/health
echo.
echo  Close this window or press Ctrl+C to continue.
echo  (Servers run in separate windows)
echo.
pause
