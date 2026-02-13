import { v4 as uuid_v4 } from 'uuid'

/* eslint-disable */
window.cr = {}
cr.__callbacks = {}
cr.webUIResponse = function (cb, status, data) {
  const callbackFn = cr.__callbacks[cb]
  callbackFn && callbackFn(data)
}

window.updateLaunchState = function () {
  updateRuningState()
}

// Launcher API 配置
const LAUNCHER_API = 'http://localhost:9528'

// 检测是否在原生 VirtualBrowser 环境中
const isNativeEnvironment = typeof chrome !== 'undefined' && typeof chrome.send === 'function'

console.log('[Native] Environment:', isNativeEnvironment ? 'Native VirtualBrowser' : 'Launcher Mode')

/**
 * Launcher API 请求封装
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
    console.error('[Launcher API Error]:', err)
    throw err
  }
}

/**
 * 获取浏览器配置列表 (从localStorage)
 */
function getStoredBrowserList() {
  try {
    const data = JSON.parse(localStorage.getItem('list'))
    return (data && data.users) || []
  } catch {
    return []
  }
}

/**
 * 保存浏览器配置列表 (到localStorage)
 */
function setStoredBrowserList(list) {
  const data = { users: list }
  localStorage.setItem('list', JSON.stringify(data))
}

/**
 * 根据ID获取浏览器配置
 */
function getBrowserConfigById(id) {
  const list = getStoredBrowserList()
  return list.find(item => String(item.id) === String(id))
}

export async function chromeSendTimeout(name, timeout = 2000, ...params) {
  // 如果是原生环境，使用 chrome.send
  if (isNativeEnvironment) {
    const pTimeOut = timeout => {
      return new Promise((resolve, reject) => {
        setTimeout(() => {
          reject('timeout')
        }, timeout)
      })
    }
    const pCall = new Promise(resolve => {
      const callbackName = 'callback_' + uuid_v4()
      cr.__callbacks[callbackName] = data => {
        resolve(data)
      }

      const args = [callbackName].concat(params)
      console.log(`chrome.send("${name}", `, args, `)`)
      chrome.send(name, args)
    })

    return Promise.race([pCall, pTimeOut(timeout)])
  }

  // 否则使用 Launcher API
  console.log(`[Launcher] ${name}`, params)

  switch (name) {
    case 'launchBrowser': {
      const browserId = params[0]
      const config = getBrowserConfigById(browserId)
      if (!config) {
        throw new Error('Browser config not found: ' + browserId)
      }
      
      const result = await launcherFetch('/api/launch', {
        method: 'POST',
        body: JSON.stringify(config)
      })
      
      return { data: result }
    }

    case 'getBrowserList': {
      const list = getStoredBrowserList()
      return { data: { users: list } }
    }

    case 'setBrowserList': {
      // 由其他函数处理
      return { data: 'ok' }
    }

    case 'getRuningBrowser': {
      const running = await launcherFetch('/api/running')
      return running || []
    }

    case 'deleteBrowser': {
      const browserId = params[0]
      try {
        await launcherFetch(`/api/stop/${browserId}`, { method: 'POST' })
      } catch (e) {
        // 忽略停止错误
      }
      return { data: 'ok' }
    }

    case 'getGlobalData': {
      const data = localStorage.getItem('GlobalData')
      return { data: data || '{}' }
    }

    case 'setGlobalData': {
      // 由 setGlobalData 函数处理
      return { data: 'ok' }
    }

    case 'getBrowserVersion': {
      return { data: '139.0.0.0' }
    }

    case 'checkProxy': {
      // 代理检测功能
      return { data: true }
    }

    case 'setIpGeo': {
      // IP地理位置设置 - fingerprint-chromium 不支持
      console.log('[Launcher] setIpGeo not supported in fingerprint-chromium')
      return { data: 'ok' }
    }

    default:
      console.warn(`[Launcher] Unknown command: ${name}`)
      return { data: null }
  }
}

export async function chromeSend(name, ...params) {
  return chromeSendTimeout(name, 2000, ...params)
}

export async function getGlobalData() {
  let GlobalData
  try {
    GlobalData = JSON.parse(localStorage.getItem('GlobalData'))
    if (Object.prototype.toString.call(GlobalData) === '[object Array]') {
      GlobalData = {}
    }
    
    if (isNativeEnvironment) {
      GlobalData = await chromeSend('getGlobalData')
      GlobalData = JSON.parse(GlobalData.data)
      if (Object.prototype.toString.call(GlobalData) === '[object Array]') {
        GlobalData = {}
      }
    }
  } catch {
    //
  }

  return GlobalData || {}
}

export async function setGlobalData(key, value) {
  const GlobalData = await getGlobalData()
  GlobalData[key] = value

  localStorage.setItem('GlobalData', JSON.stringify(GlobalData))
  
  if (isNativeEnvironment) {
    await chromeSend('setGlobalData', JSON.stringify(GlobalData)).catch(console.warn)
  }
}

export async function getBrowserList() {
  if (isNativeEnvironment) {
    let list
    try {
      list = JSON.parse(localStorage.getItem('list'))
      list = await chromeSend('getBrowserList')
      list = list.data
    } catch {
      //
    }
    return (list && list.users) || []
  }
  
  return getStoredBrowserList()
}

export async function addBrowser(item, defaultName) {
  const prefix = defaultName ? defaultName + ' ' : ''
  const list = await getBrowserList()
  const maxId = Math.max(0, Math.max(...list.map(item => item.id)))
  item.id = maxId + 1
  item.name = item.name || prefix + item.id

  list.push(item)

  const data = { users: list }
  localStorage.setItem('list', JSON.stringify(data))
  
  if (isNativeEnvironment) {
    await chromeSend('setBrowserList', data).catch(err => {
      console.warn(err)
    })
  }
}

export async function updateBrowser(item) {
  const list = await getBrowserList()
  const idx = list.findIndex(it => it.id === item.id)
  list[idx] = item

  const data = { users: list }
  localStorage.setItem('list', JSON.stringify(data))
  
  if (isNativeEnvironment) {
    await chromeSend('setBrowserList', data).catch(err => {
      console.warn(err)
    })
  }
}

export async function deleteBrowser(id) {
  await chromeSend('deleteBrowser', id).catch(() => {})

  const list = await getBrowserList()
  const idx = list.findIndex(it => it.id === id)

  list.splice(idx, 1)

  const data = { users: list }
  localStorage.setItem('list', JSON.stringify(data))
  
  if (isNativeEnvironment) {
    await chromeSend('setBrowserList', data).catch(err => {
      console.warn(err)
    })
  }
}

export async function updateRuningState() {
  const runingIds = await chromeSend('getRuningBrowser').catch(() => [])
  window._updateState && window._updateState(runingIds || [])
}

export async function getBrowserVersion() {
  if (isNativeEnvironment) {
    const ret = await chromeSend('getBrowserVersion')
    return ret
  }
  return '139.0.0.0'
}

export async function getGroupList() {
  let list
  try {
    list = JSON.parse(localStorage.getItem('group'))
  } catch {
    //
  }

  return list || []
}

export async function addGroup(item, defaultName) {
  const list = await getGroupList()
  const maxId = Math.max(0, Math.max(...list.map(item => item.id)))
  item.id = maxId + 1
  item.name = item.name || defaultName + ' ' + item.id

  list.push(item)

  localStorage.setItem('group', JSON.stringify(list))
}

export async function updateGroup(item) {
  const list = await getGroupList()
  const idx = list.findIndex(it => it.id === item.id)
  list[idx] = item

  localStorage.setItem('group', JSON.stringify(list))
}

export async function deleteGroup(id) {
  const list = await getGroupList()
  const idx = list.findIndex(it => it.id === id)

  list.splice(idx, 1)

  localStorage.setItem('group', JSON.stringify(list))
}