# VirtualBrowser Launcher

这个模块将 VirtualBrowser 前端与 [fingerprint-chromium](https://github.com/adryfish/fingerprint-chromium) 开源指纹浏览器集成。

## 架构说明

```
┌─────────────────────────────────────────────────────────────┐
│                    VirtualBrowser 前端                       │
│                   (Vue.js 管理界面)                          │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ HTTP API (localhost:9528)
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Launcher 服务                             │
│              (Python Flask API 服务)                         │
│                                                              │
│  - 配置转换：VirtualBrowser格式 → fingerprint-chromium参数  │
│  - 进程管理：启动/停止浏览器实例                              │
│  - 状态监控：实时跟踪运行中的浏览器                           │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ subprocess
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                fingerprint-chromium                          │
│              (开源指纹浏览器内核)                             │
│                                                              │
│  启动参数:                                                   │
│  --fingerprint=1001                                         │
│  --fingerprint-platform=windows                             │
│  --fingerprint-gpu-vendor="Intel Inc."                      │
│  --timezone=Asia/Shanghai                                   │
│  ...                                                         │
└─────────────────────────────────────────────────────────────┘
```

## 快速开始

### 1. 下载 fingerprint-chromium

从 GitHub Releases 下载：
```
https://github.com/adryfish/fingerprint-chromium/releases
```

解压到 `launcher/fingerprint-chromium/` 目录。

### 2. 安装 Python 依赖

```bash
pip install flask flask-cors
```

### 3. 启动 Launcher

**Windows:**
```batch
双击 start.bat
```

**Linux/Mac:**
```bash
python launcher.py
```

### 4. 启动前端

```bash
cd ../server
npm run dev
```

## 配置映射

| VirtualBrowser 配置 | fingerprint-chromium 参数 |
|---------------------|---------------------------|
| `proxy` | `--proxy-server` |
| `time-zone.utc` | `--timezone` |
| `ua-language.language` | `--lang` |
| `os` | `--fingerprint-platform` |
| `webgl.vendor` | `--fingerprint-gpu-vendor` |
| `webgl.render` | `--fingerprint-gpu-renderer` |
| `cpu.value` | `--fingerprint-hardware-concurrency` |
| `webrtc.mode` | `--disable-webrtc` / `--disable-non-proxied-udp` |

## API 接口

### 启动浏览器
```
POST /api/launch
Content-Type: application/json

{
  "id": 1,
  "name": "Test Browser",
  "proxy": { "mode": 2, "host": "127.0.0.1", "port": "7890" },
  "time-zone": { "utc": "Asia/Shanghai" },
  ...
}
```

### 停止浏览器
```
POST /api/stop/{browser_id}
```

### 获取运行状态
```
GET /api/running
```

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `CHROMIUM_PATH` | `./fingerprint-chromium/chrome.exe` | 浏览器路径 |
| `DATA_DIR` | `~/.virtualbrowser/profiles` | 配置文件目录 |
| `PORT` | `9528` | API服务端口 |

## 注意事项

1. **指纹种子生成**：使用配置ID的hash值作为确定性种子，同一配置始终产生相同指纹
2. **端口冲突**：每个浏览器实例会分配不同的调试端口 (9222-10222)
3. **代理认证**：fingerprint-chromium 的 `--proxy-server` 参数不支持用户名密码认证，如需认证请使用代理软件

## 与原生 VirtualBrowser 的区别

| 功能 | 原生 VirtualBrowser | fingerprint-chromium 方案 |
|------|---------------------|---------------------------|
| 浏览器内核 | 闭源修改版Chromium | 开源fingerprint-chromium |
| 配置存储 | chromium内核存储 | localStorage + 文件系统 |
| 进程管理 | chromium内部管理 | Python外部管理 |
| 指纹修改深度 | 更深度（内核级） | 命令行参数级 |
| 自动化支持 | ✅ | ✅ |
| 开源程度 | 部分开源 | 完全开源 |
