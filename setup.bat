@echo off
:: ============================================
:: XEconomic — Environment Setup
:: ============================================
:: Sets up Python venv, installs dependencies,
:: and validates the environment.
:: ============================================

echo.
echo  ╔═══════════════════════════════════════════╗
echo  ║     XEconomic Environment Setup           ║
echo  ╚═══════════════════════════════════════════╝
echo.

cd /d "%~dp0"

:: ─── Step 1: Python venv ───
echo [1/4] Setting up Python virtual environment...
if not exist ".venv" (
    python -m venv .venv
    echo       Created .venv
) else (
    echo       .venv already exists
)

call .venv\Scripts\activate
echo       Activated .venv

:: ─── Step 2: Python dependencies ───
echo.
echo [2/4] Installing Python dependencies...
pip install -r requirements.txt --quiet
echo       Done

:: ─── Step 3: Node.js dependencies ───
echo.
echo [3/4] Installing Node.js dependencies for dashboard...
cd dashboard
if exist "package.json" (
    call npm install --silent
    echo       Done
) else (
    echo       [!] dashboard/package.json not found
)
cd ..

:: ─── Step 4: Validate ───
echo.
echo [4/4] Validating environment...
python run_pipeline.py --check

echo.
echo  ╔═══════════════════════════════════════════╗
echo  ║     Setup Complete!                       ║
echo  ╠═══════════════════════════════════════════╣
echo  ║                                           ║
echo  ║  Quick Start:                             ║
echo  ║    start.bat          → Launch dashboard  ║
echo  ║    run_pipeline.py    → Run pipeline      ║
echo  ║    schedule_setup.bat → Monthly scheduler ║
echo  ║                                           ║
echo  ╚═══════════════════════════════════════════╝
echo.
pause
