"""
VirtualBrowser Launcher - fingerprint-chromium 适配器

这个模块负责：
1. 提供HTTP API服务，替代原生chrome.send通信
2. 将VirtualBrowser配置转换为fingerprint-chromium命令行参数
3. 管理浏览器进程生命周期
4. 支持需要认证的代理（通过本地代理转发）
"""

import os
import sys
import json
import sqlite3
import time
import subprocess
import asyncio
import uuid
import signal
import platform
import socket
import select
import struct
import threading
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from flask import Flask, request, jsonify
from flask_cors import CORS

# 设置控制台输出编码为 UTF-8，避免 UnicodeEncodeError
if platform.system() == 'Windows':
    try:
        stdout_reconfigure = getattr(sys.stdout, 'reconfigure', None)
        stderr_reconfigure = getattr(sys.stderr, 'reconfigure', None)
        if callable(stdout_reconfigure):
            stdout_reconfigure(encoding='utf-8')
        if callable(stderr_reconfigure):
            stderr_reconfigure(encoding='utf-8')
    except:
        # 如果 reconfigure 不可用，尝试使用 setlocale
        import locale
        try:
            locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
        except:
            pass

app = Flask(__name__)
CORS(app)

# 配置
def find_chromium_path():
    """自动检测 chromium 路径"""
    possible_paths = [
        os.environ.get('CHROMIUM_PATH'),  # 环境变量优先
        os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fingerprint-chromium', 'chrome.exe'),
        'C:\\fingerprint-chromium\\chrome.exe',
        'D:\\fingerprint-chromium\\chrome.exe',
        os.path.expanduser('~/fingerprint-chromium/chrome.exe'),
        # Mac/Linux 路径
        '/Applications/fingerprint-chromium.app/Contents/MacOS/Chromium',
        '/usr/bin/fingerprint-chromium',
        os.path.expanduser('~/Applications/fingerprint-chromium/chrome'),
    ]

    for path in possible_paths:
        if path and os.path.exists(path):
            return path

    # 默认返回第一个路径（即使不存在，后续会报错提示）
    return possible_paths[1] if possible_paths[1] else 'C:\\fingerprint-chromium\\chrome.exe'


CONFIG = {
    'chromium_path': find_chromium_path(),
    'data_dir': os.environ.get('DATA_DIR', os.path.expanduser('~/.virtualbrowser/profiles')),
    'port': int(os.environ.get('PORT', 9528)),
}

DB_PATH = os.path.join(CONFIG['data_dir'], 'virtualbrowser.db')
db_lock = threading.Lock()

# 运行中的浏览器进程
running_browsers: Dict[str, 'BrowserProcess'] = {}

# 本地代理转发服务
local_proxies: Dict[str, 'LocalProxyForwarder'] = {}


def _now_ms() -> int:
    return int(time.time() * 1000)


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_storage():
    os.makedirs(CONFIG['data_dir'], exist_ok=True)
    with db_lock:
        conn = get_db_connection()
        try:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS browsers (
                    id TEXT PRIMARY KEY,
                    data TEXT NOT NULL,
                    name TEXT,
                    group_name TEXT,
                    updated_at INTEGER NOT NULL
                )
            ''')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS groups_storage (
                    id TEXT PRIMARY KEY,
                    data TEXT NOT NULL,
                    name TEXT,
                    updated_at INTEGER NOT NULL
                )
            ''')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS global_storage (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    data TEXT NOT NULL,
                    updated_at INTEGER NOT NULL
                )
            ''')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS migrations (
                    key TEXT PRIMARY KEY,
                    updated_at INTEGER NOT NULL
                )
            ''')
            conn.commit()
        finally:
            conn.close()


def _next_numeric_browser_id(conn) -> str:
    rows = conn.execute('SELECT id FROM browsers').fetchall()
    max_id = 0
    for row in rows:
        value = str(row['id'])
        if value.isdigit():
            max_id = max(max_id, int(value))
    return str(max_id + 1)


def load_browsers() -> List[dict]:
    with db_lock:
        conn = get_db_connection()
        try:
            rows = conn.execute('''
                SELECT data FROM browsers
                ORDER BY CASE WHEN id GLOB '[0-9]*' THEN 0 ELSE 1 END,
                         CAST(id AS INTEGER),
                         id
            ''').fetchall()
            result = []
            for row in rows:
                try:
                    result.append(json.loads(row['data']))
                except Exception:
                    continue
            return result
        finally:
            conn.close()


def upsert_browser(raw_item: dict) -> dict:
    item = json.loads(json.dumps(raw_item or {}))
    with db_lock:
        conn = get_db_connection()
        try:
            browser_id = item.get('id')
            if browser_id is None or str(browser_id).strip() == '':
                browser_id = _next_numeric_browser_id(conn)
            browser_id = str(browser_id)
            item['id'] = int(browser_id) if browser_id.isdigit() else browser_id
            now = _now_ms()
            conn.execute(
                '''
                INSERT INTO browsers (id, data, name, group_name, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                  data=excluded.data,
                  name=excluded.name,
                  group_name=excluded.group_name,
                  updated_at=excluded.updated_at
                ''',
                (
                    browser_id,
                    json.dumps(item, ensure_ascii=False),
                    str(item.get('name', '')),
                    str(item.get('group', '')),
                    now,
                ),
            )
            conn.commit()
            return item
        finally:
            conn.close()


def delete_browser_storage(browser_id: str):
    with db_lock:
        conn = get_db_connection()
        try:
            conn.execute('DELETE FROM browsers WHERE id = ?', (str(browser_id),))
            conn.commit()
        finally:
            conn.close()


def load_groups() -> List[dict]:
    with db_lock:
        conn = get_db_connection()
        try:
            rows = conn.execute('SELECT data FROM groups_storage ORDER BY updated_at ASC, id ASC').fetchall()
            result = []
            for row in rows:
                try:
                    result.append(json.loads(row['data']))
                except Exception:
                    continue
            return result
        finally:
            conn.close()


def upsert_group(raw_item: dict) -> dict:
    item = json.loads(json.dumps(raw_item or {}))
    with db_lock:
        conn = get_db_connection()
        try:
            group_id = item.get('id')
            if group_id is None or str(group_id).strip() == '':
                rows = conn.execute('SELECT id FROM groups_storage').fetchall()
                max_id = 0
                for row in rows:
                    value = str(row['id'])
                    if value.isdigit():
                        max_id = max(max_id, int(value))
                group_id = str(max_id + 1)
            group_id = str(group_id)
            item['id'] = int(group_id) if group_id.isdigit() else group_id
            now = _now_ms()
            conn.execute(
                '''
                INSERT INTO groups_storage (id, data, name, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                  data=excluded.data,
                  name=excluded.name,
                  updated_at=excluded.updated_at
                ''',
                (group_id, json.dumps(item, ensure_ascii=False), str(item.get('name', '')), now),
            )
            conn.commit()
            return item
        finally:
            conn.close()


def delete_group_storage(group_id: str):
    with db_lock:
        conn = get_db_connection()
        try:
            conn.execute('DELETE FROM groups_storage WHERE id = ?', (str(group_id),))
            conn.commit()
        finally:
            conn.close()


def load_global_data() -> dict:
    with db_lock:
        conn = get_db_connection()
        try:
            row = conn.execute('SELECT data FROM global_storage WHERE id = 1').fetchone()
            if not row:
                return {}
            try:
                return json.loads(row['data'])
            except Exception:
                return {}
        finally:
            conn.close()


def save_global_data(data: dict):
    payload = data or {}
    with db_lock:
        conn = get_db_connection()
        try:
            conn.execute(
                '''
                INSERT INTO global_storage (id, data, updated_at)
                VALUES (1, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                  data=excluded.data,
                  updated_at=excluded.updated_at
                ''',
                (json.dumps(payload, ensure_ascii=False), _now_ms()),
            )
            conn.commit()
        finally:
            conn.close()


init_storage()


class LocalProxyForwarder:
    """
    本地代理转发服务
    用于处理需要认证的代理（HTTP/HTTPS/SOCKS5）
    浏览器连接本地代理（无需认证），本地代理转发到实际的需要认证的上游代理
    """
    
    def __init__(self, browser_id: str, upstream_host: str, upstream_port: int,
                 upstream_user: str = '', upstream_pass: str = '', proxy_type: str = 'http'):
        self.browser_id = browser_id
        self.upstream_host = upstream_host
        self.upstream_port = upstream_port
        self.upstream_user = upstream_user
        self.upstream_pass = upstream_pass
        self.proxy_type = proxy_type.lower()  # http, https, socks5
        
        # 本地监听端口 (使用 browser_id 的 hash 确定端口)
        self.local_port = 10000 + (hash(browser_id) % 50000)
        self.server_socket = None
        self.running = False
        self.thread = None
        
    def start(self):
        """启动本地代理服务"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(('127.0.0.1', self.local_port))
            self.server_socket.listen(100)
            self.server_socket.settimeout(1)
            self.running = True
            
            self.thread = threading.Thread(target=self._accept_loop, daemon=True)
            self.thread.start()
            
            print(f'[PROXY] 本地代理转发服务已启动: 127.0.0.1:{self.local_port} -> {self.proxy_type}://{self.upstream_host}:{self.upstream_port}')
            return True
        except Exception as e:
            print(f'[PROXY] 启动本地代理服务失败: {e}')
            return False
    
    def stop(self):
        """停止本地代理服务"""
        self.running = False
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        print(f'[PROXY] 本地代理转发服务已停止: {self.local_port}')
    
    def _accept_loop(self):
        """接受客户端连接"""
        while self.running:
            try:
                if self.server_socket is None:
                    return
                client_socket, _ = self.server_socket.accept()
                threading.Thread(target=self._handle_client, args=(client_socket,), daemon=True).start()
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    print(f'[PROXY] Accept error: {e}')
    
    def _handle_client(self, client_socket):
        """处理客户端连接"""
        # 本地代理始终作为 HTTP 代理接收请求
        # 然后根据上游代理类型选择转发方式
        try:
            self._handle_http_request(client_socket)
        except Exception as e:
            print(f'[PROXY] Handle client error: {e}')
            import traceback
            traceback.print_exc()
        finally:
            try:
                client_socket.close()
            except:
                pass
    
    def _connect_upstream(self):
        """连接上游代理服务器"""
        upstream_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        upstream_socket.settimeout(30)
        upstream_socket.connect((self.upstream_host, self.upstream_port))
        return upstream_socket

    def _recv_exact(self, sock: socket.socket, size: int) -> bytes:
        """精确读取指定字节数，避免 SOCKS 握手被分包导致解析失败"""
        data = b''
        while len(data) < size:
            chunk = sock.recv(size - len(data))
            if not chunk:
                break
            data += chunk
        return data
    
    def _handle_http_request(self, client_socket):
        """处理 HTTP 代理请求（浏览器始终使用 HTTP 协议）"""
        upstream_socket = None
        try:
            # 接收客户端请求
            request = b''
            while b'\r\n\r\n' not in request and len(request) < 8192:
                chunk = client_socket.recv(4096)
                if not chunk:
                    return
                request += chunk
            
            # 解析请求行
            request_line = request.split(b'\r\n')[0].decode('utf-8', errors='ignore')
            parts = request_line.split(' ')
            if len(parts) < 2:
                return
            
            method = parts[0]
            url = parts[1]
            
            # 如果是 CONNECT 方法（HTTPS），需要建立隧道
            if method == 'CONNECT':
                # 解析目标主机和端口
                host_port = url.split(':')
                if len(host_port) != 2:
                    return
                target_host = host_port[0]
                target_port = int(host_port[1])
                
                # 根据上游代理类型选择连接方式
                if self.proxy_type == 'socks5':
                    # 上游是 SOCKS5 代理
                    upstream_socket = self._connect_via_socks5(target_host, target_port)
                else:
                    # 上游是 HTTP 代理
                    upstream_socket = self._connect_via_http_proxy(target_host, target_port, request)
                
                if upstream_socket:
                    # 告诉客户端连接成功
                    client_socket.sendall(b'HTTP/1.1 200 Connection Established\r\n\r\n')
                    
                    # 开始双向转发
                    self._tunnel(client_socket, upstream_socket)
            else:
                # HTTP 请求
                if self.proxy_type == 'socks5':
                    # SOCKS5 不支持直接转发 HTTP 请求，需要先解析 URL
                    from urllib.parse import urlparse
                    parsed = urlparse(url)
                    target_host = parsed.hostname
                    target_port = parsed.port or 80

                    # 某些客户端可能发送 origin-form（只包含 path），从 Host 头回退解析
                    if not target_host:
                        header_text = request.decode('utf-8', errors='ignore')
                        host_line = next((line for line in header_text.split('\r\n') if line.lower().startswith('host:')), '')
                        host_value = host_line.split(':', 1)[1].strip() if ':' in host_line else ''
                        if host_value:
                            if ':' in host_value:
                                host_part, port_part = host_value.rsplit(':', 1)
                                target_host = host_part.strip('[]')
                                if port_part.isdigit():
                                    target_port = int(port_part)
                            else:
                                target_host = host_value
                    if not target_host:
                        print('[PROXY] SOCKS5 HTTP 请求无法解析目标主机')
                        return
                    
                    # 通过 SOCKS5 连接
                    upstream_socket = self._connect_via_socks5(target_host, target_port)
                    
                    if upstream_socket:
                        # 修改请求的 URL 为绝对路径
                        path = parsed.path or '/'
                        if parsed.query:
                            path += '?' + parsed.query
                        request = request.replace(url.encode(), path.encode(), 1)
                        upstream_socket.sendall(request)
                        
                        # 接收响应并转发
                        response = upstream_socket.recv(8192)
                        client_socket.sendall(response)
                        
                        # 继续双向转发
                        self._tunnel(client_socket, upstream_socket)
                else:
                    # HTTP 代理，直接转发
                    upstream_socket = self._connect_upstream()
                    
                    if self.upstream_user and self.upstream_pass:
                        # 添加代理认证头
                        import base64
                        auth = base64.b64encode(f'{self.upstream_user}:{self.upstream_pass}'.encode()).decode()
                        
                        request_str = request.decode('utf-8', errors='ignore')
                        if '\r\n' in request_str:
                            parts = request_str.split('\r\n', 1)
                            request_str = parts[0] + f'\r\nProxy-Authorization: Basic {auth}\r\n' + parts[1]
                            request = request_str.encode('utf-8')
                    
                    upstream_socket.sendall(request)
                    
                    # 接收响应并转发
                    response = upstream_socket.recv(8192)
                    client_socket.sendall(response)
                    
                    # 继续双向转发
                    self._tunnel(client_socket, upstream_socket)
            
        except Exception as e:
            print(f'[PROXY] HTTP handle error: {e}')
            import traceback
            traceback.print_exc()
        finally:
            if upstream_socket:
                try:
                    upstream_socket.close()
                except:
                    pass
    
    def _connect_via_socks5(self, target_host, target_port):
        """通过 SOCKS5 代理连接目标主机"""
        try:
            # 连接上游 SOCKS5 代理
            upstream_socket = self._connect_upstream()
            
            # SOCKS5 握手
            if self.upstream_user and self.upstream_pass:
                # 支持无认证和用户名密码认证
                upstream_socket.sendall(b'\x05\x02\x00\x02')
            else:
                upstream_socket.sendall(b'\x05\x01\x00')
            
            # 接收握手响应
            greeting_response = self._recv_exact(upstream_socket, 2)
            if len(greeting_response) != 2 or greeting_response[0] != 5:
                print(f'[PROXY] SOCKS5 握手失败')
                upstream_socket.close()
                return None
            
            auth_method = greeting_response[1]
            
            # 如果需要认证
            if auth_method == 0x02:
                user_bytes = self.upstream_user.encode('utf-8')
                pass_bytes = self.upstream_pass.encode('utf-8')
                auth_request = bytes([1, len(user_bytes)]) + user_bytes + bytes([len(pass_bytes)]) + pass_bytes
                upstream_socket.sendall(auth_request)
                
                auth_response = self._recv_exact(upstream_socket, 2)
                if len(auth_response) != 2 or auth_response[1] != 0:
                    print(f'[PROXY] SOCKS5 认证失败')
                    upstream_socket.close()
                    return None
            elif auth_method != 0x00:
                print(f'[PROXY] SOCKS5 不支持的认证方法: {auth_method}')
                upstream_socket.close()
                return None
            
            # 发送 CONNECT 请求
            # 构造 SOCKS5 CONNECT 请求
            # ATYP=1 (IPv4) 或 ATYP=3 (域名)
            host_bytes = target_host.encode('utf-8')
            if len(host_bytes) <= 255:
                # 使用域名类型
                connect_request = bytes([5, 1, 0, 3, len(host_bytes)]) + host_bytes + struct.pack('!H', target_port)
            else:
                # 使用 IPv4
                import ipaddress
                try:
                    ip_bytes = ipaddress.IPv4Address(target_host).packed
                    connect_request = bytes([5, 1, 0, 1]) + ip_bytes + struct.pack('!H', target_port)
                except:
                    print(f'[PROXY] 无法解析主机地址: {target_host}')
                    upstream_socket.close()
                    return None
            
            upstream_socket.sendall(connect_request)
            
            # 接收 CONNECT 响应
            connect_head = self._recv_exact(upstream_socket, 4)
            if len(connect_head) < 4 or connect_head[0] != 5 or connect_head[1] != 0:
                code = connect_head[1] if len(connect_head) > 1 else 'unknown'
                print(f'[PROXY] SOCKS5 CONNECT 失败: {code}')
                upstream_socket.close()
                return None

            atyp = connect_head[3]
            if atyp == 1:  # IPv4
                _ = self._recv_exact(upstream_socket, 4 + 2)
            elif atyp == 3:  # DOMAIN
                domain_len_bytes = self._recv_exact(upstream_socket, 1)
                if len(domain_len_bytes) != 1:
                    print('[PROXY] SOCKS5 CONNECT 响应域名长度读取失败')
                    upstream_socket.close()
                    return None
                domain_len = domain_len_bytes[0]
                _ = self._recv_exact(upstream_socket, domain_len + 2)
            elif atyp == 4:  # IPv6
                _ = self._recv_exact(upstream_socket, 16 + 2)
            else:
                print(f'[PROXY] SOCKS5 CONNECT 返回未知地址类型: {atyp}')
                upstream_socket.close()
                return None
            
            print(f'[PROXY] SOCKS5 隧道建立成功: {target_host}:{target_port}')
            return upstream_socket
            
        except Exception as e:
            print(f'[PROXY] SOCKS5 连接错误: {e}')
            return None
    
    def _connect_via_http_proxy(self, target_host, target_port, original_request):
        """通过 HTTP 代理连接目标主机（用于 CONNECT）"""
        try:
            upstream_socket = self._connect_upstream()
            
            # 构造 CONNECT 请求
            connect_request = f'CONNECT {target_host}:{target_port} HTTP/1.1\r\nHost: {target_host}:{target_port}\r\n'.encode()
            
            # 添加代理认证
            if self.upstream_user and self.upstream_pass:
                import base64
                auth = base64.b64encode(f'{self.upstream_user}:{self.upstream_pass}'.encode()).decode()
                connect_request += f'Proxy-Authorization: Basic {auth}\r\n'.encode()
            
            connect_request += b'\r\n'
            
            upstream_socket.sendall(connect_request)
            
            # 接收响应
            response = upstream_socket.recv(8192)
            if not response.startswith(b'HTTP/1.1 200') and not response.startswith(b'HTTP/1.0 200'):
                print(f'[PROXY] HTTP CONNECT 失败: {response.decode(errors="ignore")[:100]}')
                upstream_socket.close()
                return None
            
            print(f'[PROXY] HTTP 隧道建立成功: {target_host}:{target_port}')
            return upstream_socket
            
        except Exception as e:
            print(f'[PROXY] HTTP 连接错误: {e}')
            return None
    
    def _tunnel(self, client_socket, upstream_socket):
        """双向数据转发"""
        client_socket.setblocking(False)
        upstream_socket.setblocking(False)
        
        sockets = [client_socket, upstream_socket]
        
        while self.running:
            try:
                readable, _, _ = select.select(sockets, [], [], 1)
            except:
                break
            
            for sock in readable:
                try:
                    data = sock.recv(65536)
                    if not data:
                        return
                    
                    if sock is client_socket:
                        upstream_socket.sendall(data)
                    else:
                        client_socket.sendall(data)
                except:
                    return


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
        
        # 代理配置
        print(f'[DEBUG] 代理配置: mode={self.config.proxy_mode}, host={self.config.proxy_host}, port={self.config.proxy_port}')
        if self.config.proxy_mode == 2:  # 自定义代理
            from urllib.parse import quote
            
            # 验证必要的代理参数
            if not self.config.proxy_host or not self.config.proxy_port:
                print(f'[WARNING] 代理配置不完整: host={self.config.proxy_host}, port={self.config.proxy_port}')
            else:
                # 确保端口号有效
                try:
                    port = int(self.config.proxy_port)
                except (ValueError, TypeError):
                    print(f'[ERROR] 无效的端口号: {self.config.proxy_port}')
                    port = 0
                
                if port > 0:
                    # 协议转小写
                    protocol = (self.config.proxy_protocol or 'HTTP').lower()
                    
                    # 如果需要认证，使用本地代理转发服务
                    if self.config.proxy_user and self.config.proxy_pass:
                        print(f'[PROXY] 检测到代理认证，启动本地代理转发服务')
                        
                        # 创建并启动本地代理转发服务
                        forwarder = LocalProxyForwarder(
                            browser_id=str(self.config.id),
                            upstream_host=self.config.proxy_host,
                            upstream_port=port,
                            upstream_user=self.config.proxy_user,
                            upstream_pass=self.config.proxy_pass,
                            proxy_type=protocol
                        )
                        
                        if forwarder.start():
                            # 保存转发器引用
                            local_proxies[str(self.config.id)] = forwarder
                            
                            # 浏览器连接本地代理（无需认证）
                            proxy_url = f'http://127.0.0.1:{forwarder.local_port}'
                            print(f'[PROXY] 浏览器将连接本地代理: {proxy_url}')
                            args.append(f'--proxy-server={proxy_url}')
                        else:
                            # 转发服务启动失败，直接使用原始代理（可能无法认证）
                            proxy_url = f'{protocol}://{self.config.proxy_host}:{port}'
                            print(f'[PROXY] 本地代理启动失败，直接使用上游代理: {proxy_url}')
                            args.append(f'--proxy-server={proxy_url}')
                    else:
                        # 无需认证，直接使用原始代理
                        proxy_url = f'{protocol}://{self.config.proxy_host}:{port}'
                        print(f'[PROXY] 代理URL（无认证）: {proxy_url}')
                        args.append(f'--proxy-server={proxy_url}')
                    
        elif self.config.proxy_mode == 1:  # 不使用代理
            args.append('--proxy-server=direct://')
            print('[PROXY] 不使用代理')
        
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
        # 停止本地代理转发服务
        browser_id = str(self.config.id)
        if browser_id in local_proxies:
            local_proxies[browser_id].stop()
            del local_proxies[browser_id]
        
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

    def normalize_proxy_protocol(raw_protocol: str) -> str:
        protocol = str(raw_protocol or 'HTTP').strip().upper()
        if protocol in ('SOCKS5', 'SOCKS', 'SOCKS5H'):
            return 'SOCKS5'
        if protocol in ('HTTP', 'HTTPS'):
            return protocol
        return 'HTTP'

    config.proxy_mode = proxy.get('mode', 0)
    config.proxy_protocol = normalize_proxy_protocol(proxy.get('protocol', 'HTTP'))
    config.proxy_host = proxy.get('host', '')
    config.proxy_port = proxy.get('port', '')
    config.proxy_user = proxy.get('user', '')
    config.proxy_pass = proxy.get('pass', '')

    # 处理可能的 URL 编码凭据（例如 %40, %3A）
    try:
        from urllib.parse import unquote
        if config.proxy_user:
            config.proxy_user = unquote(str(config.proxy_user))
        if config.proxy_pass:
            config.proxy_pass = unquote(str(config.proxy_pass))
    except Exception:
        pass

    # 兼容历史代理格式：当 user/pass/host/port 缺失时，尝试从 url 或 value 中恢复
    # 支持：
    # - socks5://user:pass@host:port
    # - user:pass@host:port@socks
    # - host:port
    proxy_url = str(proxy.get('url', '') or proxy.get('value', '') or '').strip()
    if proxy_url and (not config.proxy_host or not config.proxy_port or not config.proxy_user):
        try:
            normalized = proxy_url
            if '@socks' in normalized and '://' not in normalized:
                normalized = 'socks5://' + normalized.replace('@socks', '')
            elif '://' not in normalized:
                normalized = 'http://' + normalized

            from urllib.parse import urlparse, unquote
            parsed = urlparse(normalized)
            if parsed.scheme:
                config.proxy_protocol = normalize_proxy_protocol(parsed.scheme)
            if parsed.hostname and not config.proxy_host:
                config.proxy_host = parsed.hostname
            if parsed.port and not config.proxy_port:
                config.proxy_port = str(parsed.port)
            if parsed.username and not config.proxy_user:
                config.proxy_user = unquote(parsed.username)
            if parsed.password and not config.proxy_pass:
                config.proxy_pass = unquote(parsed.password)
        except Exception:
            pass
    
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

@app.route('/api/browsers', methods=['GET'])
def api_get_browsers():
    """获取浏览器配置列表（持久化）"""
    return jsonify({'users': load_browsers()})


@app.route('/api/browsers', methods=['POST'])
def api_add_browser():
    """新增浏览器配置（持久化）"""
    data = request.json or {}
    saved = upsert_browser(data)
    return jsonify({'success': True, 'item': saved})


@app.route('/api/browsers/<browser_id>', methods=['PUT'])
def api_update_browser(browser_id):
    """更新浏览器配置（持久化）"""
    data = request.json or {}
    data['id'] = browser_id
    saved = upsert_browser(data)
    return jsonify({'success': True, 'item': saved})


@app.route('/api/browsers/<browser_id>', methods=['DELETE'])
def api_delete_browser(browser_id):
    """删除浏览器配置（持久化）"""
    if browser_id in running_browsers:
        running_browsers[browser_id].stop()
        del running_browsers[browser_id]
    delete_browser_storage(browser_id)
    return jsonify({'success': True})


@app.route('/api/groups', methods=['GET'])
def api_get_groups():
    return jsonify(load_groups())


@app.route('/api/groups', methods=['POST'])
def api_add_group():
    data = request.json or {}
    saved = upsert_group(data)
    return jsonify({'success': True, 'item': saved})


@app.route('/api/groups/<group_id>', methods=['PUT'])
def api_update_group(group_id):
    data = request.json or {}
    data['id'] = group_id
    saved = upsert_group(data)
    return jsonify({'success': True, 'item': saved})


@app.route('/api/groups/<group_id>', methods=['DELETE'])
def api_delete_group(group_id):
    delete_group_storage(group_id)
    return jsonify({'success': True})


@app.route('/api/global', methods=['GET'])
def api_get_global_data():
    return jsonify(load_global_data())


@app.route('/api/global', methods=['POST'])
def api_set_global_data():
    payload = request.json or {}
    if not isinstance(payload, dict):
        return jsonify({'error': 'global payload must be object'}), 400
    save_global_data(payload)
    return jsonify({'success': True})


@app.route('/api/migrate/local-storage', methods=['POST'])
def api_migrate_local_storage():
    """导入本地 localStorage 数据到服务端持久化存储"""
    payload = request.json or {}
    browsers_payload = payload.get('list', [])
    groups_payload = payload.get('group', [])
    global_payload = payload.get('global', {})

    if isinstance(browsers_payload, dict):
        browsers_payload = browsers_payload.get('users', [])

    if not isinstance(browsers_payload, list):
        return jsonify({'error': 'list must be array or {users: []}'}), 400
    if not isinstance(groups_payload, list):
        return jsonify({'error': 'group must be array'}), 400
    if not isinstance(global_payload, dict):
        return jsonify({'error': 'global must be object'}), 400

    imported = {
        'browsers': 0,
        'groups': 0,
        'global_updated': False,
    }

    for item in browsers_payload:
        if isinstance(item, dict):
            upsert_browser(item)
            imported['browsers'] += 1

    for item in groups_payload:
        if isinstance(item, dict):
            upsert_group(item)
            imported['groups'] += 1

    if global_payload:
        current = load_global_data()
        current.update(global_payload)
        save_global_data(current)
        imported['global_updated'] = True

    with db_lock:
        conn = get_db_connection()
        try:
            conn.execute(
                '''
                INSERT INTO migrations (key, updated_at)
                VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET updated_at=excluded.updated_at
                ''',
                ('local_storage_imported', _now_ms()),
            )
            conn.commit()
        finally:
            conn.close()

    return jsonify({'success': True, 'imported': imported})


@app.route('/api/migrate/status', methods=['GET'])
def api_migrate_status():
    with db_lock:
        conn = get_db_connection()
        try:
            row = conn.execute('SELECT updated_at FROM migrations WHERE key = ?', ('local_storage_imported',)).fetchone()
        finally:
            conn.close()
    return jsonify({'local_storage_imported': row is not None, 'updated_at': row['updated_at'] if row else None})

@app.route('/api/launch', methods=['POST'])
def launch_browser():
    """启动浏览器"""
    try:
        data = request.json
        print(f'[DEBUG] 接收到的配置数据: {json.dumps(data, indent=2, ensure_ascii=True)}')
        
        config = convert_config(data)
        print(f'[DEBUG] 转换后的代理配置: mode={config.proxy_mode}, protocol={config.proxy_protocol}, host={config.proxy_host}, port={config.proxy_port}, user={config.proxy_user}, pass={"***" if config.proxy_pass else ""}')

        # 检查是否已存在相同ID的进程记录
        if config.id in running_browsers:
            existing_process = running_browsers[config.id]
            # 检查进程是否真正运行中
            if existing_process.is_running():
                return jsonify({'error': 'Browser already running', 'id': config.id}), 400
            else:
                # 进程已退出（可能被用户手动关闭），清除旧记录
                print(f'浏览器 {config.id} 进程已退出，清除旧记录并重新启动')
                del running_browsers[config.id]

        # 检查 chromium 是否存在
        if not os.path.exists(CONFIG['chromium_path']):
            return jsonify({
                'error': f'Chromium not found: {CONFIG["chromium_path"]}',
                'details': 'Please download fingerprint-chromium from https://github.com/adryfish/fingerprint-chromium/releases'
            }), 500

        process = BrowserProcess(config)
        process.start()
        running_browsers[config.id] = process

        return jsonify({
            'success': True,
            'id': config.id,
            'debug_port': process.debug_port
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': str(e),
            'details': 'Failed to launch browser'
        }), 500


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
    return jsonify({'users': load_browsers()})


@app.route('/chrome/send/getRuningBrowser', methods=['GET'])
def chrome_get_running():
    """模拟chrome.send('getRuningBrowser')"""
    running = [bid for bid, proc in running_browsers.items() if proc.is_running()]
    return jsonify(running)


@app.route('/chrome/send/deleteBrowser', methods=['POST'])
def chrome_delete_browser():
    """模拟chrome.send('deleteBrowser')"""
    browser_id = request.json.get('id')
    browser_id = str(browser_id)
    if browser_id in running_browsers:
        running_browsers[browser_id].stop()
        del running_browsers[browser_id]
    delete_browser_storage(browser_id)
    return jsonify({'success': True})


if __name__ == '__main__':
    # 检查 chromium 路径
    chromium_exists = os.path.exists(CONFIG['chromium_path'])

    print('''
╔═══════════════════════════════════════════════════════════════╗
║           VirtualBrowser Launcher                             ║
║           for fingerprint-chromium (ungoogled-chromium)       ║
╠═══════════════════════════════════════════════════════════════╣''')

    if chromium_exists:
        print(f"║  Chromium Path: {CONFIG['chromium_path']:<46} ║")
    else:
        print(f"║  Chromium Path: {CONFIG['chromium_path']:<46} ║")
        print("║  Status:        [NOT FOUND]                                  ║")

    print(f"║  Data Dir:      {CONFIG['data_dir']:<46} ║")
    print(f"║  Port:          {CONFIG['port']:<46} ║")
    print('''╚═══════════════════════════════════════════════════════════════╝
    ''')

    if not chromium_exists:
        print('''
[警告] 未找到 fingerprint-chromium 浏览器！

请执行以下步骤之一：
1. 下载 fingerprint-chromium:
   https://github.com/adryfish/fingerprint-chromium/releases

2. 解压到以下位置之一：
    - launcher/fingerprint-chromium/chrome.exe (推荐)
    - C:\\fingerprint-chromium\\chrome.exe
    - D:\\fingerprint-chromium\\chrome.exe

3. 或设置环境变量:
   set CHROMIUM_PATH=你的浏览器路径

4. 构建自己的指纹浏览器:
   参考 chromium-patches/ 目录下的补丁文件和构建说明
        ''')

    # 确保数据目录存在
    os.makedirs(CONFIG['data_dir'], exist_ok=True)
    init_storage()

    print(f'启动服务: http://localhost:{CONFIG["port"]}')
    print('按 Ctrl+C 停止服务\n')

    app.run(host='0.0.0.0', port=CONFIG['port'], debug=True)
