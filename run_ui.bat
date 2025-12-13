@echo off
echo Starting AMO Image Generator UI...
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not found in PATH!
    echo Please ensure Python is installed and added to PATH.
    pause
    exit /b 1
)

REM Try to run the application
python ui_app/main.py
if errorlevel 1 (
    echo.
    echo ========================================
    echo ERROR: Application failed to start!
    echo ========================================
    echo.
    echo If you see a PyQt6 DLL error, try:
    echo 1. Run: fix_pyqt6.bat
    echo 2. Or run: python check_pyqt6.py (for diagnostics)
    echo.
    pause
    exit /b 1
)
pause

