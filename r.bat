@echo off
setlocal
cd /d "%~dp0"
python menu.py
if errorlevel 1 (
    echo.
    echo Execution failed with error level %errorlevel%
    pause
)
endlocal
