"""
VirtualBrowser Launcher - fingerprint-chromium 适配器

这个模块负责：
1. 提供HTTP API服务，替代原生chrome.send通信
2. 将VirtualBrowser配置转换为fingerprint-chromium命令行参数
3. 管理浏览器进程生命周期
"""

import os
import json
import subprocess
import asyncio
import uuid
import signal
import platform
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from flask import Flask, request, jsonify
from flask_cors import CORS
import threading

app = Flask(__name__)
CORS(app)

# 配置
CONFIG = {
    'chromium_path': os.environ.get('CHROMIUM_PATH', 'C:\\fingerprint-chromium\\chrome.exe'),
    'data_dir': os.environ.get('DATA_DIR', os.path.expanduser('~/.virtualbrowser/profiles')),
    'port': int(os.environ.get('PORT', 9528)),
}

# 运行中的浏览器进程
running_browsers: Dict[str, 'BrowserProcess'] = {}

@dataclass
class BrowserConfig:
    """浏览器配置"""
    id: str
    name: str
    group: str = '默认分组'
    os: str = 'Win 11'
    chrome_version: str = '139'
    
    # 代理配置
    proxy_mode: int = 0  # 0=默认, 1=不使用, 2=自定义
    proxy_protocol: str = 'HTTP'
    proxy_host: str = ''
    proxy_port: str = ''
    proxy_user: str = ''
    proxy_pass: str = ''
    
    # User-Agent
    ua_mode: int = 0
    ua_value: str = ''
    
    # 语言和时区
    language: str = 'zh-CN'
    timezone: str = 'Asia/Shanghai'
    
    # 地理位置
    location_mode: int = 0
    latitude: float = 0.0
    longitude: float = 0.0
    
    # 屏幕分辨率
    screen_mode: int = 0
    screen_width: int = 1920
    screen_height: int = 1080
    
    # Canvas/WebGL
    canvas_mode: int = 1
    webgl_mode: int = 0
    webgl_vendor: str = ''
    webgl_renderer: str = ''
    
    # 音频
    audio_mode: int = 1
    
    # 硬件
    cpu_cores: int = 8
    memory: int = 8
    
    # WebRTC
    webrtc_mode: int = 0  # 0=替换, 1=允许, 2=阻断
    
    # 其他
    device_name: str = ''
    mac_address: str = ''
    homepage: str = ''
    
    # 指纹种子
    fingerprint_seed: int = 0


class BrowserProcess:
    """浏览器进程管理"""
    def __init__(self, config: BrowserConfig):
        self.config = config
        self.process: Optional[subprocess.Popen] = None
        self.debug_port: int = 0
        
    def build_args(self) -> List[str]:
        """构建fingerprint-chromium命令行参数"""
        args = []
        
        # 基础参数
        profile_dir = os.path.join(CONFIG['data_dir'], str(self.config.id))
        args.extend([f'--user-data-dir={profile_dir}'])
        
        # 指纹种子（从配置ID生成或使用指定值）
        if self.config.fingerprint_seed:
            seed = self.config.fingerprint_seed
        else:
            # 从ID生成确定性种子
            seed = abs(hash(str(self.config.id))) % (2**32)
        args.append(f'--fingerprint={seed}')
        
        # 平台
        platform_map = {
            'Win 7': 'windows',
            'Win 8': 'windows', 
            'Win 10': 'windows',
            'Win 11': 'windows',
            'Mac': 'macos',
            'Linux': 'linux'
        }
        args.append(f'--fingerprint-platform={platform_map.get(self.config.os, "windows")}')
        
        # GPU配置
        if self.config.webgl_vendor:
            args.append(f'--fingerprint-gpu-vendor={self.config.webgl_vendor}')
        if self.config.webgl_renderer:
            args.append(f'--fingerprint-gpu-renderer={self.config.webgl_renderer}')
        
        # CPU核心数
        if self.config.cpu_cores:
            args.append(f'--fingerprint-hardware-concurrency={self.config.cpu_cores}')
        
        # 时区
        if self.config.timezone:
            args.append(f'--timezone={self.config.timezone}')
        
        # 语言
        if self.config.language:
            args.append(f'--lang={self.config.language}')
            args.append(f'--accept-lang={self.config.language}')
        
        # 代理
        if self.config.proxy_mode == 2:  # 自定义代理
            proxy_url = f'{self.config.proxy_protocol.lower()}://'
            if self.config.proxy_user and self.config.proxy_pass:
                proxy_url += f'{self.config.proxy_user}:{self.config.proxy_pass}@'
            proxy_url += f'{self.config.proxy_host}:{self.config.proxy_port}'
            args.append(f'--proxy-server={proxy_url}')
        elif self.config.proxy_mode == 1:  # 不使用代理
            args.append('--proxy-server=direct://')
        
        # WebRTC
        if self.config.webrtc_mode == 2:  # 阻断
            args.append('--disable-webrtc')
        elif self.config.webrtc_mode == 0:  # 替换(防止泄露)
            args.append('--disable-non-proxied-udp')
        
        # 调试端口
        self.debug_port = 9222 + (hash(str(self.config.id)) % 1000)
        args.append(f'--remote-debugging-port={self.debug_port}')
        
        # 主页
        if self.config.homepage:
            args.append(self.config.homepage)
        else:
            args.append('about:blank')
        
        return args
    
    def start(self):
        """启动浏览器"""
        args = self.build_args()
        cmd = [CONFIG['chromium_path']] + args
        
        print(f'启动浏览器: {" ".join(cmd)}')
        
        self.process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if platform.system() == 'Windows' else 0
        )
        
    def stop(self):
        """停止浏览器"""
        if self.process:
            if platform.system() == 'Windows':
                self.process.terminate()
            else:
                self.process.send_signal(signal.SIGTERM)
            self.process.wait(timeout=10)
            self.process = None
    
    def is_running(self) -> bool:
        """检查是否运行中"""
        if self.process:
            return self.process.poll() is None
        return False


def convert_config(vb_config: dict) -> BrowserConfig:
    """将VirtualBrowser配置转换为适配器配置"""
    config = BrowserConfig(
        id=str(vb_config.get('id', uuid.uuid4().hex[:8])),
        name=vb_config.get('name', 'New Browser'),
        group=vb_config.get('group', '默认分组'),
        os=vb_config.get('os', 'Win 11'),
    )
    
    # 代理
    proxy = vb_config.get('proxy', {})
    config.proxy_mode = proxy.get('mode', 0)
    config.proxy_protocol = proxy.get('protocol', 'HTTP')
    config.proxy_host = proxy.get('host', '')
    config.proxy_port = proxy.get('port', '')
    config.proxy_user = proxy.get('user', '')
    config.proxy_pass = proxy.get('pass', '')
    
    # User-Agent
    ua = vb_config.get('ua', {})
    config.ua_mode = ua.get('mode', 0)
    config.ua_value = ua.get('value', '')
    
    # 语言
    lang_config = vb_config.get('ua-language', {})
    config.language = lang_config.get('language', 'zh-CN')
    
    # 时区
    tz_config = vb_config.get('time-zone', {})
    config.timezone = tz_config.get('utc', 'Asia/Shanghai')
    
    # 地理位置
    loc = vb_config.get('location', {})
    config.location_mode = loc.get('mode', 0)
    config.latitude = float(loc.get('latitude', 0) or 0)
    config.longitude = float(loc.get('longitude', 0) or 0)
    
    # 屏幕
    screen = vb_config.get('screen', {})
    config.screen_mode = screen.get('mode', 0)
    config.screen_width = screen.get('width', 1920)
    config.screen_height = screen.get('height', 1080)
    
    # WebGL
    webgl = vb_config.get('webgl', {})
    config.webgl_mode = webgl.get('mode', 0)
    config.webgl_vendor = webgl.get('vendor', '')
    config.webgl_renderer = webgl.get('render', '')
    
    # Canvas
    canvas = vb_config.get('canvas', {})
    config.canvas_mode = canvas.get('mode', 1)
    
    # 音频
    audio = vb_config.get('audio-context', {})
    config.audio_mode = audio.get('mode', 1)
    
    # 硬件
    config.cpu_cores = vb_config.get('cpu', {}).get('value', 8)
    config.memory = vb_config.get('memory', {}).get('value', 8)
    
    # WebRTC
    config.webrtc_mode = vb_config.get('webrtc', {}).get('mode', 0)
    
    # 设备名称
    device = vb_config.get('device-name', {})
    config.device_name = device.get('value', '') if device.get('mode') == 1 else ''
    
    # MAC地址
    mac = vb_config.get('mac', {})
    config.mac_address = mac.get('value', '') if mac.get('mode') == 1 else ''
    
    # 主页
    homepage = vb_config.get('homepage', {})
    config.homepage = homepage.get('value', '') if homepage.get('mode') == 1 else ''
    
    return config


# ==================== API 路由 ====================

@app.route('/api/launch', methods=['POST'])
def launch_browser():
    """启动浏览器"""
    data = request.json
    config = convert_config(data)
    
    if config.id in running_browsers:
        return jsonify({'error': 'Browser already running', 'id': config.id}), 400
    
    process = BrowserProcess(config)
    process.start()
    running_browsers[config.id] = process
    
    return jsonify({
        'success': True,
        'id': config.id,
        'debug_port': process.debug_port
    })


@app.route('/api/stop/<browser_id>', methods=['POST'])
def stop_browser(browser_id):
    """停止浏览器"""
    if browser_id not in running_browsers:
        return jsonify({'error': 'Browser not found'}), 404
    
    process = running_browsers[browser_id]
    process.stop()
    del running_browsers[browser_id]
    
    return jsonify({'success': True})


@app.route('/api/status', methods=['GET'])
def get_status():
    """获取所有浏览器状态"""
    status = {}
    for bid, process in running_browsers.items():
        status[bid] = {
            'running': process.is_running(),
            'debug_port': process.debug_port,
            'config': asdict(process.config)
        }
    return jsonify(status)


@app.route('/api/running', methods=['GET'])
def get_running():
    """获取运行中的浏览器ID列表"""
    running = [bid for bid, proc in running_browsers.items() if proc.is_running()]
    return jsonify(running)


@app.route('/api/config', methods=['GET', 'POST'])
def handle_config():
    """获取/设置全局配置"""
    if request.method == 'POST':
        global CONFIG
        CONFIG.update(request.json)
        return jsonify({'success': True})
    return jsonify(CONFIG)


# ==================== 模拟原生 chrome.send API ====================

@app.route('/chrome/send/launchBrowser', methods=['POST'])
def chrome_launch_browser():
    """模拟chrome.send('launchBrowser')"""
    browser_id = request.json.get('id')
    # 从存储中获取配置
    # 这里需要与前端localStorage同步
    return launch_browser()


@app.route('/chrome/send/getBrowserList', methods=['GET'])
def chrome_get_browser_list():
    """模拟chrome.send('getBrowserList')"""
    return jsonify({'users': []})  # 由前端localStorage管理


@app.route('/chrome/send/getRuningBrowser', methods=['GET'])
def chrome_get_running():
    """模拟chrome.send('getRuningBrowser')"""
    running = [bid for bid, proc in running_browsers.items() if proc.is_running()]
    return jsonify(running)


@app.route('/chrome/send/deleteBrowser', methods=['POST'])
def chrome_delete_browser():
    """模拟chrome.send('deleteBrowser')"""
    browser_id = request.json.get('id')
    if browser_id in running_browsers:
        running_browsers[browser_id].stop()
        del running_browsers[browser_id]
    return jsonify({'success': True})


if __name__ == '__main__':
    print(f'''
╔═══════════════════════════════════════════════════════════════╗
║           VirtualBrowser Launcher for fingerprint-chromium    ║
╠═══════════════════════════════════════════════════════════════╣
║  Chromium Path: {CONFIG['chromium_path']:<46} ║
║  Data Dir:      {CONFIG['data_dir']:<46} ║
║  Port:          {CONFIG['port']:<46} ║
╚═══════════════════════════════════════════════════════════════╝
    ''')
    app.run(host='0.0.0.0', port=CONFIG['port'], debug=True)
