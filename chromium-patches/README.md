# VirtualBrowser Chromium Patches

本项目包含用于构建开源指纹浏览器的 Chromium 补丁文件。

## 概述

这些补丁基于 [Ungoogled Chromium](https://github.com/ungoogled-software/ungoogled-chromium) 项目，添加了指纹修改功能。

## 支持的指纹修改

| 指纹类型 | 功能描述 |
|---------|---------|
| Canvas 指纹 | 精确修改Canvas 2D绑制结果，添加随机噪声 |
| WebGL 指纹 | 修改GPU厂商、渲染器型号、WebGL绘制结果 |
| AudioContext 指纹 | 修改音频上下文指纹 |
| Navigator 属性 | 修改userAgent、platform、hardwareConcurrency、deviceMemory等 |
| ClientRects 指纹 | 修改DOMRect返回值 |
| 字体指纹 | 控制字体检测响应 |
| WebRTC | 防止WebRTC泄露真实IP |
| 时区/语言 | 全局覆盖时区和语言设置 |
| 屏幕分辨率 | 模拟不同的屏幕尺寸和色深 |

## 命令行参数

| 参数 | 描述 | 示例 |
|-----|------|------|
| `--fingerprint` | 指纹种子值，启用指纹功能 | 32位整数 |
| `--fingerprint-platform` | 操作系统类型 | `windows`, `linux`, `macos` |
| `--fingerprint-platform-version` | 操作系统版本 | 使用默认版本 |
| `--fingerprint-brand` | 浏览器品牌 | `Chrome`, `Edge`, `Opera` |
| `--fingerprint-gpu-vendor` | GPU厂商 | `Intel Inc.`, `NVIDIA Corporation` |
| `--fingerprint-gpu-renderer` | GPU型号 | `NVIDIA GeForce GTX 1060` |
| `--fingerprint-hardware-concurrency` | CPU核心数 | 整数 |
| `--fingerprint-device-memory` | 设备内存(GB) | 2, 4, 8, 16 |
| `--timezone` | 时区 | `Asia/Shanghai` |
| `--lang` | 浏览器语言 | `zh-CN` |

## 构建方法

### 前提条件

1. **Windows**: Visual Studio 2022, Windows 10/11 SDK
2. **Linux**: Ubuntu 20.04+, GCC 10+
3. **macOS**: Xcode 14+

### 构建步骤

```bash
# 1. 安装 depot_tools
git clone https://chromium.googlesource.com/chromium/tools/depot_tools.git
export PATH="$PATH:/path/to/depot_tools"

# 2. 下载 Chromium 源码
mkdir chromium && cd chromium
fetch chromium

# 3. 切换到目标版本
cd src
git checkout tags/139.0.7258.154

# 4. 应用 Ungoogled Chromium 补丁
# 参考: https://github.com/ungoogled-software/ungoogled-chromium

# 5. 应用本项目补丁
for patch in /path/to/chromium-patches/patches/*.patch; do
  git apply "$patch"
done

# 6. 生成构建配置
gn gen out/Default --args='is_debug=false is_component_build=false'

# 7. 构建
autoninja -C out/Default chrome
```

### Docker 构建 (推荐)

```bash
docker build -t virtualbrowser-builder -f Dockerfile .
docker run -v $(pwd)/out:/out virtualbrowser-builder
```

## 使用示例

### Playwright 自动化

```javascript
const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launchPersistentContext('./profile', {
    executablePath: '/path/to/virtualbrowser',
    args: [
      '--fingerprint=1001',
      '--fingerprint-platform=windows',
      '--fingerprint-gpu-vendor=Intel Inc.',
      '--fingerprint-gpu-renderer=Intel Iris OpenGL Engine',
      '--timezone=America/New_York',
      '--lang=en-US'
    ]
  });

  const page = await browser.newPage();
  await page.goto('https://browserleaks.com');
})();
```

### Puppeteer 自动化

```javascript
const puppeteer = require('puppeteer');

const browser = await puppeteer.launch({
  executablePath: '/path/to/virtualbrowser',
  args: [
    '--fingerprint=2001',
    '--fingerprint-platform=macos',
    '--timezone=Asia/Tokyo'
  ]
});
```

## 测试

推荐使用以下网站测试指纹修改效果：

- [CreepJS](https://abrahamjuliot.github.io/creepjs/)
- [BrowserLeaks](https://browserleaks.com/)
- [BrowserScan](https://www.browserscan.net/)
- [FingerprintJS](https://fingerprintjs.github.io/fingerprintjs/)

## 许可证

BSD-3-Clause

## 致谢

- [Ungoogled Chromium](https://github.com/ungoogled-software/ungoogled-chromium)
- [fingerprint-chromium](https://github.com/adryfish/fingerprint-chromium)
- [undetectable-fingerprint-browser](https://github.com/itbrowser-net/undetectable-fingerprint-browser)
