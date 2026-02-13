@echo off
chcp 65001 >nul
echo ╔═══════════════════════════════════════════════════════════════╗
echo ║     VirtualBrowser + fingerprint-chromium 启动器             ║
echo ╚═══════════════════════════════════════════════════════════════╝
echo.

:: 检查Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到Python，请先安装Python 3.8+
    pause
    exit /b 1
)

:: 检查依赖
echo [1/3] 检查依赖...
pip show flask >nul 2>&1
if errorlevel 1 (
    echo 正在安装依赖...
    pip install flask flask-cors
)

:: 设置环境变量
echo [2/3] 配置环境...
set CHROMIUM_PATH=%~dp0fingerprint-chromium\chrome.exe
if not exist "%CHROMIUM_PATH%" (
    echo [警告] fingerprint-chromium 未找到
    echo 请将 fingerprint-chromium 解压到: %~dp0fingerprint-chromium\
    echo 或设置 CHROMIUM_PATH 环境变量
    echo.
    echo 下载地址: https://github.com/adryfish/fingerprint-chromium/releases
    echo.
)

set DATA_DIR=%~dp0profiles
set PORT=9528

:: 启动服务
echo [3/3] 启动 Launcher 服务...
echo.
echo 浏览器路径: %CHROMIUM_PATH%
echo 数据目录:   %DATA_DIR%
echo API端口:    %PORT%
echo.

cd /d %~dp0
python launcher.py

pause
