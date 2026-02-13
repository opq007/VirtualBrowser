/**
 * VirtualBrowser Launcher 适配器
 * 用于连接 fingerprint-chromium 浏览器
 */

const LAUNCHER_API = 'http://localhost:9528'

/**
 * 发送请求到 Launcher API
 */
async function launcherFetch(endpoint, options = {}) {
  const url = `${LAUNCHER_API}${endpoint}`
  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      }
    })
    return await response.json()
  } catch (err) {
    console.error('Launcher API error:', err)
    throw err
  }
}

/**
 * 启动浏览器
 * @param {Object} config - 浏览器配置
 */
export async function launchBrowser(config) {
  return launcherFetch('/api/launch', {
    method: 'POST',
    body: JSON.stringify(config)
  })
}

/**
 * 停止浏览器
 * @param {string} browserId - 浏览器ID
 */
export async function stopBrowser(browserId) {
  return launcherFetch(`/api/stop/${browserId}`, {
    method: 'POST'
  })
}

/**
 * 获取运行中的浏览器列表
 */
export async function getRunningBrowsers() {
  return launcherFetch('/api/running')
}

/**
 * 获取所有浏览器状态
 */
export async function getBrowserStatus() {
  return launcherFetch('/api/status')
}

/**
 * 获取/设置全局配置
 */
export async function getConfig() {
  return launcherFetch('/api/config')
}

export async function setConfig(config) {
  return launcherFetch('/api/config', {
    method: 'POST',
    body: JSON.stringify(config)
  })
}

/**
 * 参数映射：将VirtualBrowser配置转换为fingerprint-chromium参数
 */
export function buildFingerprintArgs(config) {
  const args = []

  // 指纹种子
  const seed = config.fingerprint_seed || Math.abs(hashCode(String(config.id)))
  args.push(`--fingerprint=${seed}`)

  // 平台
  const platformMap = {
    'Win 7': 'windows',
    'Win 8': 'windows',
    'Win 10': 'windows',
    'Win 11': 'windows',
    Mac: 'macos',
    Linux: 'linux'
  }
  args.push(`--fingerprint-platform=${platformMap[config.os] || 'windows'}`)

  // GPU
  if (config.webgl?.vendor) {
    args.push(`--fingerprint-gpu-vendor=${config.webgl.vendor}`)
  }
  if (config.webgl?.render) {
    args.push(`--fingerprint-gpu-renderer=${config.webgl.render}`)
  }

  // CPU核心
  if (config.cpu?.value) {
    args.push(`--fingerprint-hardware-concurrency=${config.cpu.value}`)
  }

  // 时区
  if (config['time-zone']?.utc) {
    args.push(`--timezone=${config['time-zone'].utc}`)
  }

  // 语言
  if (config['ua-language']?.language) {
    args.push(`--lang=${config['ua-language'].language}`)
  }

  // 代理
  if (config.proxy?.mode === 2 && config.proxy.host) {
    const protocol = config.proxy.protocol?.toLowerCase() || 'http'
    let proxyUrl = `${protocol}://`
    if (config.proxy.user && config.proxy.pass) {
      proxyUrl += `${config.proxy.user}:${config.proxy.pass}@`
    }
    proxyUrl += `${config.proxy.host}:${config.proxy.port}`
    args.push(`--proxy-server=${proxyUrl}`)
  } else if (config.proxy?.mode === 1) {
    args.push('--proxy-server=direct://')
  }

  // WebRTC
  if (config.webrtc?.mode === 2) {
    args.push('--disable-webrtc')
  } else if (config.webrtc?.mode === 0) {
    args.push('--disable-non-proxied-udp')
  }

  return args
}

function hashCode(str) {
  let hash = 0
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i)
    hash = (hash << 5) - hash + char
    hash = hash & hash
  }
  return Math.abs(hash)
}

// 兼容原有 native.js API
export const launcherApi = {
  launchBrowser,
  stopBrowser,
  getRunningBrowsers,
  getBrowserStatus,
  buildFingerprintArgs
}

export default launcherApi
