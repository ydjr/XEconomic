@echo off
:: ============================================
:: XEconomic — Schedule Monthly Pipeline
:: ============================================
:: Creates a Windows Task Scheduler task that
:: runs run_monthly.bat on the 5th of each month
:: ============================================

echo.
echo  ╔═══════════════════════════════════════════╗
echo  ║     XEconomic Scheduler Setup             ║
echo  ╚═══════════════════════════════════════════╝
echo.

set TASK_NAME=XEconomic_Monthly_Pipeline
set SCRIPT_PATH=%~dp0run_monthly.bat
set WORK_DIR=%~dp0

:: Delete existing task if present
schtasks /delete /tn "%TASK_NAME%" /f >nul 2>&1

:: Create scheduled task: runs on 5th of every month at 02:00 AM
schtasks /create ^
    /tn "%TASK_NAME%" ^
    /tr "\"%SCRIPT_PATH%\"" ^
    /sc monthly /d 5 ^
    /st 02:00 ^
    /rl HIGHEST ^
    /f

if %errorlevel% equ 0 (
    echo.
    echo  ✓ Scheduled task created successfully!
    echo.
    echo    Task Name:  %TASK_NAME%
    echo    Schedule:   Monthly, 5th at 02:00 AM
    echo    Script:     %SCRIPT_PATH%
    echo.
    echo  You can view/edit the task in Task Scheduler.
    echo  Run "schtasks /query /tn %TASK_NAME%" to verify.
) else (
    echo.
    echo  ✗ Failed to create scheduled task.
    echo    Try running this script as Administrator.
)

echo.
pause
