@echo off
:: ============================================
:: XEconomic — Monthly Pipeline Scheduler
:: ============================================
:: Runs the full pipeline (skip LLM by default)
:: Logs output to logs/pipeline_YYYY-MM.log
:: ============================================

cd /d "%~dp0"

echo.
echo  ╔═══════════════════════════════════════════╗
echo  ║     XEconomic Monthly Pipeline Run        ║
echo  ╚═══════════════════════════════════════════╝
echo.

:: Activate venv
call .venv\Scripts\activate

:: Run full pipeline
echo [*] Running pipeline...
python run_pipeline.py --all --force

echo.
echo [*] Pipeline complete. Check logs/ for details.
