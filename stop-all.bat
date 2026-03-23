@echo off
title VirtualBrowser Service Stopper
echo.
echo ================================================================
echo              VirtualBrowser Service Stopper                    
echo ================================================================
echo.

echo Stopping all VirtualBrowser services...
echo.

REM Stop Launcher service
echo [1/2] Stopping Launcher service...
taskkill /FI "WINDOWTITLE eq VirtualBrowser Launcher*" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq *launcher.py*" /F >nul 2>&1
echo [OK] Launcher service stopped

REM Stop Server service
echo [2/2] Stopping management UI service...
taskkill /FI "WINDOWTITLE eq VirtualBrowser Server*" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq *npm run dev*" /F >nul 2>&1
echo [OK] Management UI service stopped

echo.
echo ================================================================
echo              All services stopped                              
echo ================================================================
echo.
pause