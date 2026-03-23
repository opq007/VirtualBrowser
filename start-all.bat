@echo off
title VirtualBrowser Launcher
echo ================================================================
echo     VirtualBrowser One-Click Launcher
echo     Based on fingerprint-chromium
echo ================================================================
echo.

echo [Check] Checking dependencies...
python --version >nul 2>&1
if errorlevel 1 (
    echo [Error] Python not found
    pause
    exit /b 1
)
echo [OK] Python installed

node --version >nul 2>&1
if errorlevel 1 (
    echo [Error] Node.js not found
    pause
    exit /b 1
)
echo [OK] Node.js installed

pip show flask >nul 2>&1
if errorlevel 1 (
    echo [Install] Installing Flask...
    pip install flask flask-cors
    if errorlevel 1 (
        echo [Error] Flask installation failed
        pause
        exit /b 1
    )
)
echo [OK] Flask installed

echo.
echo [Check] Checking fingerprint-chromium...
set CHROMIUM_FOUND=0
set CHROMIUM_PATH=

if exist "%~dp0launcher\fingerprint-chromium\chrome.exe" (
    set CHROMIUM_PATH=%~dp0launcher\fingerprint-chromium\chrome.exe
    set CHROMIUM_FOUND=1
    echo [OK] Found chromium: launcher\fingerprint-chromium
)
if exist "C:\fingerprint-chromium\chrome.exe" (
    set CHROMIUM_PATH=C:\fingerprint-chromium\chrome.exe
    set CHROMIUM_FOUND=1
    echo [OK] Found chromium: C:\fingerprint-chromium
)
if exist "D:\fingerprint-chromium\chrome.exe" (
    set CHROMIUM_PATH=D:\fingerprint-chromium\chrome.exe
    set CHROMIUM_FOUND=1
    echo [OK] Found chromium: D:\fingerprint-chromium
)

if %CHROMIUM_FOUND%==0 (
    echo [Warning] fingerprint-chromium not found
    echo Please download from: https://github.com/adryfish/fingerprint-chromium/releases
    echo.
    pause
)

echo.
echo ================================================================
echo     Starting Services:
echo     1. Launcher Service  - http://localhost:9528
echo     2. Management UI     - http://localhost:9527
echo ================================================================
echo.
pause

if not exist "%~dp0logs" mkdir "%~dp0logs"

echo [1/2] Starting Launcher service...
cd /d "%~dp0launcher"
start "VirtualBrowser Launcher" cmd /c "python launcher.py > ..\logs\launcher.log 2>&1"
timeout /t 3 /nobreak >nul

echo [2/2] Starting management UI...
cd /d "%~dp0server"
start "VirtualBrowser Server" cmd /c "npm run dev > ..\logs\server.log 2>&1"
timeout /t 10 /nobreak >nul

echo.
echo ================================================================
echo     Services started!
echo     Launcher: http://localhost:9528
echo     Management UI: http://localhost:9527 (compiling...)
echo ================================================================
echo.
echo Options:
echo   [1] Open management UI
echo   [2] View Launcher log
echo   [3] View Server log
echo   [4] Stop all services
echo   [Q] Quit
echo.

:menu
set /p choice="Select (1-4, Q): "

if "%choice%"=="1" (
    start http://localhost:9527
    goto menu
)

if "%choice%"=="2" (
    if exist "%~dp0logs\launcher.log" type "%~dp0logs\launcher.log"
    if not exist "%~dp0logs\launcher.log" echo Log file not found
    pause
    goto menu
)

if "%choice%"=="3" (
    if exist "%~dp0logs\server.log" type "%~dp0logs\server.log"
    if not exist "%~dp0logs\server.log" echo Log file not found
    pause
    goto menu
)

if "%choice%"=="4" (
    echo Stopping services...
    taskkill /FI "WINDOWTITLE eq VirtualBrowser Launcher*" /F >nul 2>&1
    taskkill /FI "WINDOWTITLE eq VirtualBrowser Server*" /F >nul 2>&1
    taskkill /FI "WINDOWTITLE eq VirtualBrowser Launcher*" /F >nul 2>&1
    echo [OK] All services stopped
    pause
    exit /b 0
)

if /i "%choice%"=="Q" (
    echo Services still running. Use option 4 to stop.
    exit /b 0
)

goto menu
