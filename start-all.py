#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VirtualBrowser 一键启动脚本
支持 Windows、Linux、macOS
"""

import os
import sys
import time
import subprocess
import platform
import argparse
from pathlib import Path
from typing import List, Optional

# 配置
PROJECT_ROOT = Path(__file__).parent.absolute()
LAUNCHER_DIR = PROJECT_ROOT / "launcher"
SERVER_DIR = PROJECT_ROOT / "server"
LOGS_DIR = PROJECT_ROOT / "logs"

LAUNCHER_PORT = 9528
SERVER_PORT = 9527

# 颜色输出
class Colors:
    HEADER = '\033[95m' if sys.platform != 'win32' else ''
    OKBLUE = '\033[94m' if sys.platform != 'win32' else ''
    OKGREEN = '\033[92m' if sys.platform != 'win32' else ''
    WARNING = '\033[93m' if sys.platform != 'win32' else ''
    FAIL = '\033[91m' if sys.platform != 'win32' else ''
    ENDC = '\033[0m' if sys.platform != 'win32' else ''
    BOLD = '\033[1m' if sys.platform != 'win32' else ''

def print_header():
    """打印标题"""
    print(f"""
{Colors.HEADER}╔═══════════════════════════════════════════════════════════════╗{Colors.ENDC}
{Colors.HEADER}║                                                               ║{Colors.ENDC}
{Colors.HEADER}║              VirtualBrowser 一键启动器                        ║{Colors.ENDC}
{Colors.HEADER}║              基于 fingerprint-chromium                        ║{Colors.ENDC}
{Colors.HEADER}║                                                               ║{Colors.ENDC}
{Colors.HEADER}╚═══════════════════════════════════════════════════════════════╝{Colors.ENDC}
""")

def check_python() -> bool:
    """检查 Python 版本"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"{Colors.FAIL}[错误] 需要 Python 3.8+，当前版本: {version.major}.{version.minor}{Colors.ENDC}")
        return False
    print(f"{Colors.OKGREEN}[OK] Python {version.major}.{version.minor}.{version.micro}{Colors.ENDC}")
    return True

def check_nodejs() -> bool:
    """检查 Node.js"""
    try:
        result = subprocess.run(
            ["node", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            version = result.stdout.strip()
            print(f"{Colors.OKGREEN}[OK] Node.js {version}{Colors.ENDC}")
            return True
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    print(f"{Colors.FAIL}[错误] 未找到 Node.js，请先安装 Node.js 14+{Colors.ENDC}")
    return False

def check_flask() -> bool:
    """检查 Flask"""
    try:
        import flask
        print(f"{Colors.OKGREEN}[OK] Flask 已安装{Colors.ENDC}")
        return True
    except ImportError:
        print(f"{Colors.WARNING}[安装] 正在安装 Flask...{Colors.ENDC}")
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "flask", "flask-cors"],
                check=True,
                capture_output=True
            )
            print(f"{Colors.OKGREEN}[OK] Flask 安装完成{Colors.ENDC}")
            return True
        except subprocess.CalledProcessError:
            print(f"{Colors.FAIL}[错误] Flask 安装失败{Colors.ENDC}")
            return False

def find_chromium() -> Optional[Path]:
    """查找 fingerprint-chromium"""
    possible_paths = [
        LAUNCHER_DIR / "fingerprint-chromium" / "chrome.exe",
        LAUNCHER_DIR / "fingerprint-chromium" / "chrome",
        Path("C:/fingerprint-chromium/chrome.exe"),
        Path("D:/fingerprint-chromium/chrome.exe"),
        Path("/Applications/fingerprint-chromium.app/Contents/MacOS/Chromium"),
        Path("/usr/bin/fingerprint-chromium"),
        Path.home() / "Applications" / "fingerprint-chromium" / "chrome",
    ]

    for path in possible_paths:
        if path.exists():
            return path

    return None

def check_chromium() -> bool:
    """检查 chromium"""
    chromium_path = find_chromium()
    if chromium_path:
        print(f"{Colors.OKGREEN}[OK] 找到 chromium: {chromium_path}{Colors.ENDC}")
        return True
    else:
        print(f"{Colors.WARNING}[警告] 未找到 fingerprint-chromium！{Colors.ENDC}")
        print("请下载并解压到以下位置之一：")
        print("  - launcher/fingerprint-chromium/")
        print("  - C:/fingerprint-chromium/ (Windows)")
        print("  - D:/fingerprint-chromium/ (Windows)")
        print("  - ~/Applications/fingerprint-chromium/ (Mac/Linux)")
        print()
        print("下载地址: https://github.com/adryfish/fingerprint-chromium/releases")
        print()
        return False

def check_server_deps() -> bool:
    """检查 Server 依赖"""
    node_modules = SERVER_DIR / "node_modules"
    if node_modules.exists():
        print(f"{Colors.OKGREEN}[OK] Server 依赖已安装{Colors.ENDC}")
        return True
    else:
        print(f"{Colors.WARNING}[安装] 正在安装 Server 依赖...{Colors.ENDC}")
        print("这可能需要几分钟时间...")
        try:
            subprocess.run(
                ["npm", "install"],
                cwd=SERVER_DIR,
                check=True
            )
            print(f"{Colors.OKGREEN}[OK] Server 依赖安装完成{Colors.ENDC}")
            return True
        except subprocess.CalledProcessError:
            print(f"{Colors.FAIL}[错误] Server 依赖安装失败{Colors.ENDC}")
            return False

def wait_for_service(port: int, timeout: int = 30) -> bool:
    """等待服务启动"""
    import socket
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('localhost', port))
            sock.close()
            if result == 0:
                return True
        except:
            pass
        time.sleep(1)
    return False

def start_launcher() -> Optional[subprocess.Popen]:
    """启动 Launcher 服务"""
    print(f"\n{Colors.BOLD}[1/2] 正在启动 Launcher 服务...{Colors.ENDC}")
    print(f"       端口: {LAUNCHER_PORT}")
    print(f"       日志: logs/launcher.log")

    LOGS_DIR.mkdir(exist_ok=True)
    log_file = open(LOGS_DIR / "launcher.log", "w")

    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"

    if sys.platform == "win32":
        process = subprocess.Popen(
            [sys.executable, "launcher.py"],
            cwd=LAUNCHER_DIR,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NEW_CONSOLE,
            env=env
        )
    else:
        process = subprocess.Popen(
            [sys.executable, "launcher.py"],
            cwd=LAUNCHER_DIR,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            env=env
        )

    # 等待服务启动
    if wait_for_service(LAUNCHER_PORT, timeout=10):
        print(f"{Colors.OKGREEN}[OK] Launcher 服务启动成功{Colors.ENDC}")
        return process
    else:
        print(f"{Colors.WARNING}[警告] Launcher 服务可能未正常启动{Colors.ENDC}")
        return process

def start_server() -> Optional[subprocess.Popen]:
    """启动 Server 管理界面"""
    print(f"\n{Colors.BOLD}[2/2] 正在启动管理界面...{Colors.ENDC}")
    print(f"       端口: {SERVER_PORT}")
    print(f"       日志: logs/server.log")

    log_file = open(LOGS_DIR / "server.log", "w")

    env = os.environ.copy()
    env["BROWSER"] = "none"  # 禁止自动打开浏览器

    if sys.platform == "win32":
        process = subprocess.Popen(
            ["npm", "run", "dev"],
            cwd=SERVER_DIR,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NEW_CONSOLE,
            env=env
        )
    else:
        process = subprocess.Popen(
            ["npm", "run", "dev"],
            cwd=SERVER_DIR,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            env=env
        )

    print(f"{Colors.OKGREEN}[OK] 管理界面启动中，请等待编译完成...{Colors.ENDC}")
    return process

def show_status():
    """显示服务状态"""
    print(f"\n{Colors.HEADER}╔═══════════════════════════════════════════════════════════════╗{Colors.ENDC}")
    print(f"{Colors.HEADER}║  服务状态：                                                   ║{Colors.ENDC}")
    print(f"{Colors.HEADER}║                                                               ║{Colors.ENDC}")

    launcher_ok = wait_for_service(LAUNCHER_PORT, timeout=2)
    if launcher_ok:
        print(f"{Colors.HEADER}║  {Colors.OKGREEN}[OK]{Colors.ENDC}{Colors.HEADER} Launcher 服务    - http://localhost:{LAUNCHER_PORT}              ║{Colors.ENDC}")
    else:
        print(f"{Colors.HEADER}║  {Colors.FAIL}[X]{Colors.ENDC}{Colors.HEADER}  Launcher 服务    - 未启动                             ║{Colors.ENDC}")

    print(f"{Colors.HEADER}║                                                               ║{Colors.ENDC}")
    print(f"{Colors.HEADER}║  管理界面编译完成后访问: http://localhost:{SERVER_PORT}              ║{Colors.ENDC}")
    print(f"{Colors.HEADER}║                                                               ║{Colors.ENDC}")
    print(f"{Colors.HEADER}╚═══════════════════════════════════════════════════════════════╝{Colors.ENDC}")

def interactive_menu(processes: List[subprocess.Popen]):
    """交互式菜单"""
    while True:
        print(f"\n{Colors.BOLD}操作选项：{Colors.ENDC}")
        print("  [1] 打开管理界面")
        print("  [2] 查看 Launcher 日志")
        print("  [3] 查看 Server 日志")
        print("  [4] 停止所有服务")
        print("  [Q] 退出")
        print()

        choice = input("请选择操作 (1-4, Q): ").strip().lower()

        if choice == "1":
            import webbrowser
            webbrowser.open(f"http://localhost:{SERVER_PORT}")

        elif choice == "2":
            log_file = LOGS_DIR / "launcher.log"
            if log_file.exists():
                with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
                    print(f.read())
            else:
                print("日志文件不存在")
            input("\n按回车键继续...")

        elif choice == "3":
            log_file = LOGS_DIR / "server.log"
            if log_file.exists():
                with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
                    # 只显示最后 50 行
                    lines = f.readlines()
                    print("".join(lines[-50:]))
            else:
                print("日志文件不存在")
            input("\n按回车键继续...")

        elif choice == "4":
            print("\n正在停止所有服务...")
            for p in processes:
                try:
                    p.terminate()
                    p.wait(timeout=5)
                except:
                    try:
                        p.kill()
                    except:
                        pass
            print(f"{Colors.OKGREEN}[OK] 所有服务已停止{Colors.ENDC}")
            input("\n按回车键退出...")
            break

        elif choice == "q":
            print("\n提示：服务仍在后台运行")
            print("如需停止服务，请重新运行此脚本并选择选项 4")
            break

def main():
    parser = argparse.ArgumentParser(description="VirtualBrowser 一键启动器")
    parser.add_argument("--no-check", action="store_true", help="跳过依赖检查")
    parser.add_argument("--launcher-only", action="store_true", help="仅启动 Launcher")
    parser.add_argument("--server-only", action="store_true", help="仅启动 Server")
    args = parser.parse_args()

    print_header()

    processes = []

    # 依赖检查
    if not args.no_check:
        print(f"{Colors.BOLD}[检查] 检查必要依赖...{Colors.ENDC}\n")

        if not check_python():
            sys.exit(1)

        if not args.launcher_only:
            if not check_nodejs():
                sys.exit(1)

        if not check_flask():
            sys.exit(1)

        check_chromium()

        if not args.launcher_only:
            if not check_server_deps():
                sys.exit(1)

        print("\n" + "="*60)
        input("按回车键开始启动服务...")

    # 启动服务
    try:
        if args.server_only:
            processes.append(start_server())
        elif args.launcher_only:
            processes.append(start_launcher())
        else:
            processes.append(start_launcher())
            time.sleep(2)
            processes.append(start_server())

        # 显示状态
        time.sleep(3)
        show_status()

        # 交互式菜单
        interactive_menu(processes)

    except KeyboardInterrupt:
        print("\n\n正在停止所有服务...")
        for p in processes:
            try:
                p.terminate()
                p.wait(timeout=5)
            except:
                pass
        print(f"{Colors.OKGREEN}[OK] 服务已停止{Colors.ENDC}")

if __name__ == "__main__":
    main()
