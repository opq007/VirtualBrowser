# VirtualBrowser 项目上下文

## 项目概述

VirtualBrowser 是一个基于 Chromium 的开源指纹浏览器项目，支持 Windows 10 及以上操作系统。该项目通过修改浏览器指纹（如 User-Agent、Canvas、WebGL、AudioContext 等）来创建多个独立的浏览器环境，用于隐私保护和反追踪。

**核心功能：**
- 支持在一台机器上创建和管理多个指纹浏览器环境
- 修改多种浏览器指纹（Canvas、WebGL、Audio、字体、时区、语言等）
- 支持代理配置（HTTP/HTTPS/SOCKS5）
- 支持自动化测试（Playwright/Puppeteer）

## 项目架构

项目采用模块化设计，包含以下主要组件：

```
VirtualBrowser/
├── server/          # 管理界面（Vue 2 + Element UI）
├── worker/          # 浏览器扩展/Worker（Vue 3 + TypeScript）
├── launcher/        # 启动器（Python Flask）
├── automation/      # 自动化示例（Node.js + Playwright）
├── chromium-patches/# Chromium 补丁文件
└── assets/          # 静态资源
```

### 1. Server - 管理界面
- **技术栈：** Vue 2.6 + Element UI 2.13 + Vuex + Vue Router
- **用途：** 浏览器环境的管理界面，用于创建、配置和启动指纹浏览器
- **开发命令：**
  ```bash
  cd server
  npm install
  npm run dev      # 开发模式
  npm run build    # 生产构建
  npm run lint     # 代码检查
  ```

### 2. Worker - 浏览器 Worker/扩展
- **技术栈：** Vue 3 + TypeScript + Element Plus
- **用途：** 浏览器扩展或 Worker 页面，显示指纹信息和 IP 地理位置
- **开发命令：**
  ```bash
  cd worker
  npm install
  npm run dev      # 开发模式
  npm run build    # 生产构建
  ```

### 3. Launcher - 启动器服务
- **技术栈：** Python 3 + Flask
- **用途：** 提供 HTTP API 服务，将 VirtualBrowser 配置转换为 fingerprint-chromium 命令行参数，管理浏览器进程生命周期
- **启动命令：**
  ```bash
  cd launcher
  pip install -r requirements.txt
  python launcher.py
  ```
- **默认端口：** 9528

### 4. Automation - 自动化示例
- **技术栈：** Node.js + Playwright
- **用途：** 提供自动化测试示例代码
- **运行命令：**
  ```bash
  cd automation
  npm install
  npm test         # 运行 index.js
  npm run test-api # 运行 test-api.js
  ```

### 5. Chromium Patches - 浏览器补丁
- **用途：** 基于 Ungoogled Chromium 的补丁文件，实现指纹修改功能
- **支持修改的指纹类型：**
  - Canvas 指纹
  - WebGL 指纹（GPU 厂商、渲染器）
  - AudioContext 指纹
  - Navigator 属性（User-Agent、CPU 核心数、内存等）
  - ClientRects 指纹
  - 字体指纹
  - WebRTC 防泄露
  - 时区/语言
  - 屏幕分辨率

## 关键技术栈

| 组件 | 技术 |
|------|------|
| 管理界面 | Vue 2, Element UI, Vuex, Vue Router |
| Worker | Vue 3, TypeScript, Element Plus |
| 启动器 | Python 3, Flask, Flask-CORS |
| 自动化 | Node.js, Playwright |
| 浏览器 | Chromium (带指纹补丁) |

## 开发环境要求

- **Node.js:** >= 8.9 (Server), >= 14 (Worker)
- **Python:** >= 3.8 (Launcher)
- **操作系统:** Windows 10/11 (当前主要支持)

## 快速启动

项目提供了一键启动脚本，方便快速启动所有依赖服务：

### Windows (推荐)

```bash
# 一键启动所有服务（Launcher + Server）
start-all.bat

# 停止所有服务
stop-all.bat
```

### Python 脚本 (跨平台)

```bash
# 一键启动所有服务
python start-all.py

# 跳过依赖检查快速启动
python start-all.py --no-check

# 仅启动 Launcher
python start-all.py --launcher-only

# 仅启动 Server
python start-all.py --server-only

# 查看帮助
python start-all.py --help
```

### 手动启动

如果需要手动启动各个服务：

```bash
# 1. 启动 Launcher 服务 (端口 9528)
cd launcher
python launcher.py

# 2. 启动管理界面 (端口 9527)
cd server
npm install  # 首次运行
npm run dev
```

启动完成后访问：
- 管理界面: http://localhost:9527
- Launcher API: http://localhost:9528

## 主要配置文件

- `server/package.json` - 管理界面依赖和脚本
- `worker/package.json` - Worker 依赖和脚本
- `launcher/requirements.txt` - Python 依赖
- `automation/package.json` - 自动化示例依赖

## 指纹修改功能清单

- ✅ 操作系统（User-Agent）
- ✅ 浏览器版本
- ✅ 代理设置
- ✅ 用户代理（User-Agent）
- ✅ 语言（navigator.language）
- ✅ 时区
- ✅ WebRTC
- ✅ 地理位置
- ✅ 屏幕分辨率
- ✅ 字体
- ✅ Canvas 2D
- ✅ WebGL 图像和元数据
- ✅ AudioContext
- ✅ ClientRects
- ✅ Speech Voices
- ✅ CPU 核心数
- ✅ 内存
- ✅ 设备名称
- ✅ MAC 地址
- ✅ Do Not Track

## 联系方式

- 邮箱: virtual.browser.2020@gmail.com
- 官网: http://virtualbrowser.cc
- QQ 群: 564142956
- GitHub: https://github.com/Virtual-Browser/VirtualBrowser

## 许可证

BSD 3-Clause License

## 致谢

- [Ungoogled Chromium](https://github.com/ungoogled-software/ungoogled-chromium)
- [fingerprintjs](https://fingerprintjs.github.io/fingerprintjs/)
- [browserleaks](https://browserleaks.com/)
- [vue-element-admin](https://github.com/PanJiaChen/vue-element-admin)
