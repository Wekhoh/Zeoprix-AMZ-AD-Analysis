@echo off
title AMZ Ad Tracker
echo ====================================================
echo   AMZ Ad Tracker
echo   Starting... Browser will open automatically
echo   DO NOT close this window!
echo ====================================================
echo.
cd /d "C:\Users\jackl\amz-ad-tracker"

REM Kill any existing server on port 8000
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do taskkill /F /PID %%a >nul 2>&1

REM Launch browser AFTER server boots (4s delay, runs in background)
start "" /b powershell -NoProfile -WindowStyle Hidden -Command "Start-Sleep -Seconds 4; Start-Process 'http://127.0.0.1:8000'"

echo Starting server (this window stays open — DO NOT close)...
py -3.14 -m uvicorn backend.main:app --host 127.0.0.1 --port 8000

echo.
echo Server stopped.
pause