@echo off
title Supermarket Sales Dashboard
echo ============================================
echo   Supermarket Sales Dashboard - Launcher
echo ============================================
echo.

:: Install dependencies quietly (skips if already installed)
echo [1/2] Checking dependencies...
pip install -q -r "%~dp0requirements.txt"

echo [2/2] Starting Streamlit dashboard...
echo.
echo  Open your browser at: http://localhost:8501
echo  Press Ctrl+C in this window to stop the server.
echo.
streamlit run "%~dp0src\dashboard.py"

pause
