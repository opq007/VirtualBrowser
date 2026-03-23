const { chromium } = require('playwright')

/**
 * VirtualBrowser Automation - fingerprint-chromium 版本
 *
 * 使用方式：
 * 1. 先启动 launcher: cd launcher && python launcher.py
 * 2. 在管理界面创建并启动浏览器
 * 3. 获取调试端口 (debug_port)
 * 4. 运行此脚本连接到已启动的浏览器
 */

// 配置
const LAUNCHER_API = process.env.LAUNCHER_API || 'http://localhost:9528'
const CHROMIUM_PATH = process.env.CHROMIUM_PATH || 'C:\\fingerprint-chromium\\chrome.exe'

/**
 * 通过 Launcher API 启动浏览器
 */
async function launchBrowserViaAPI(config) {
  console.log('[Automation] 通过 Launcher API 启动浏览器...')

  const response = await fetch(`${LAUNCHER_API}/api/launch`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(config)
  })

  if (!response.ok) {
    throw new Error(`启动失败: ${response.status}`)
  }

  const result = await response.json()
  console.log('[Automation] 浏览器已启动:', result)
  return result
}

/**
 * 获取运行中的浏览器列表
 */
async function getRunningBrowsers() {
  const response = await fetch(`${LAUNCHER_API}/api/running`)
  return await response.json()
}

/**
 * 使用 Playwright 连接到已启动的浏览器
 */
async function connectToBrowser(debugPort) {
  console.log(`[Automation] 连接到浏览器调试端口: ${debugPort}`)

  const browser = await chromium.connectOverCDP(`http://localhost:${debugPort}`)
  console.log('[Automation] 已连接到浏览器')

  return browser
}

/**
 * 直接启动浏览器（不通过 Launcher）
 */
async function launchBrowserDirectly(config) {
  console.log('[Automation] 直接启动 fingerprint-chromium...')

  const profileDir = config.profileDir || `./profiles/${config.id || 'default'}`

  // 构建启动参数
  const args = [
    `--user-data-dir=${profileDir}`,
    `--fingerprint=${config.fingerprintSeed || Math.floor(Math.random() * 1000000)}`,
    `--fingerprint-platform=${config.platform || 'windows'}`,
    `--remote-debugging-port=${config.debugPort || 9222}`,
  ]

  if (config.timezone) {
    args.push(`--timezone=${config.timezone}`)
  }
  if (config.language) {
    args.push(`--lang=${config.language}`)
  }
  if (config.proxy) {
    args.push(`--proxy-server=${config.proxy}`)
  }

  const browser = await chromium.launchPersistentContext(profileDir, {
    executablePath: CHROMIUM_PATH,
    args: args,
    headless: false,
    defaultViewport: null,
  })

  console.log('[Automation] 浏览器已启动')
  return browser
}

/**
 * 主函数
 */
;(async () => {
  try {
    // 方式1: 通过 Launcher API 启动并连接
    console.log('=== 方式1: 通过 Launcher API ===')

    // 示例配置
    const browserConfig = {
      id: 1,
      name: 'Test Browser',
      os: 'Win 11',
      'time-zone': { utc: 'Asia/Shanghai' },
      'ua-language': { language: 'zh-CN' },
      proxy: { mode: 0 },
      cpu: { value: 8 },
      memory: { value: 8 },
      canvas: { mode: 1 },
      webgl: { mode: 0 },
      webrtc: { mode: 0 }
    }

    // 启动浏览器
    const launchResult = await launchBrowserViaAPI(browserConfig)
    const debugPort = launchResult.debug_port

    // 等待浏览器完全启动
    await new Promise(resolve => setTimeout(resolve, 2000))

    // 连接并操作
    const browser = await connectToBrowser(debugPort)
    const context = browser.contexts()[0] || await browser.newContext()
    const page = await context.newPage()

    await page.goto('https://browserleaks.com')
    console.log('[Automation] 已打开测试页面')

    // 等待用户查看
    await new Promise(resolve => setTimeout(resolve, 10000))

    await browser.close()
    console.log('[Automation] 浏览器已关闭')

    // 方式2: 直接启动（示例）
    // console.log('=== 方式2: 直接启动 ===')
    // const directBrowser = await launchBrowserDirectly({
    //   id: 'test',
    //   platform: 'windows',
    //   timezone: 'America/New_York',
    //   language: 'en-US',
    //   debugPort: 9223
    // })
    // const directPage = await directBrowser.newPage()
    // await directPage.goto('https://fingerprintjs.github.io/fingerprintjs/')

  } catch (err) {
    console.error('[Automation] 错误:', err.message)
    console.log('\n请确保:')
    console.log('1. Launcher 服务已启动 (cd launcher && python launcher.py)')
    console.log('2. fingerprint-chromium 已安装并配置正确路径')
    console.log('3. 环境变量 CHROMIUM_PATH 已设置（如有需要）')
  }
})()
