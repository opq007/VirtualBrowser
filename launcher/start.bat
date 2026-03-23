@echo off
echo ================================================================
echo     VirtualBrowser Launcher                                   
echo     for fingerprint-chromium (ungoogled-chromium)             
echo ================================================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [Error] Python not found, please install Python 3.8+
    pause
    exit /b 1
)

REM Check dependencies
echo [1/4] Checking dependencies...
pip show flask >nul 2>&1
if errorlevel 1 (
    echo Installing Flask...
    pip install flask flask-cors
    if errorlevel 1 (
        echo [Error] Failed to install dependencies
        pause
        exit /b 1
    )
)

REM Set environment variables
echo [2/4] Configuring environment...

REM Detect chromium path (by priority)
set "CHROMIUM_PATH="

REM 1. Check environment variable
if defined CHROMIUM_PATH (
    if exist "%CHROMIUM_PATH%" (
        echo Using environment variable CHROMIUM_PATH
        goto :found_chromium
    )
)

REM 2. Check launcher subdirectory
set "TEST_PATH=%~dp0fingerprint-chromium\chrome.exe"
if exist "%TEST_PATH%" (
    set "CHROMIUM_PATH=%TEST_PATH%"
    echo Found chromium: launcher/fingerprint-chromium/
    goto :found_chromium
)

REM 3. Check C drive
set "TEST_PATH=C:\fingerprint-chromium\chrome.exe"
if exist "%TEST_PATH%" (
    set "CHROMIUM_PATH=%TEST_PATH%"
    echo Found chromium: C:\fingerprint-chromium\
    goto :found_chromium
)

REM 4. Check D drive
set "TEST_PATH=D:\fingerprint-chromium\chrome.exe"
if exist "%TEST_PATH%" (
    set "CHROMIUM_PATH=%TEST_PATH%"
    echo Found chromium: D:\fingerprint-chromium\
    goto :found_chromium
)

:found_chromium

if not defined CHROMIUM_PATH (
    echo [Warning] fingerprint-chromium not found
    echo.
    echo Please download and extract to one of these locations:
    echo   - %~dp0fingerprint-chromium\  (Recommended)
    echo   - C:\fingerprint-chromium\
    echo   - D:\fingerprint-chromium\
    echo.
    echo Download: https://github.com/adryfish/fingerprint-chromium/releases
    echo.
    echo Or set environment variable:
    echo   set CHROMIUM_PATH=your_browser_path
    echo.
    set "CHROMIUM_PATH=%~dp0fingerprint-chromium\chrome.exe"
)

REM Set data directory and port
set "DATA_DIR=%~dp0profiles"
set "PORT=9528"

REM Create data directory
if not exist "%DATA_DIR%" (
    echo [3/4] Creating data directory...
    mkdir "%DATA_DIR%"
) else (
    echo [3/4] Data directory already exists
)

REM Display configuration
echo [4/4] Startup configuration:
echo   Browser path: %CHROMIUM_PATH%
echo   Data directory: %DATA_DIR%
echo   API port: %PORT%
echo.

REM Start service
cd /d %~dp0
echo Starting Launcher service...
echo Management UI: http://localhost:9527 (needs to be started separately)
echo API address:  http://localhost:%PORT%
echo.
echo Press Ctrl+C to stop service
echo.

python launcher.py

pause