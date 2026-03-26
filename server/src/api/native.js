import { v4 as uuid_v4 } from 'uuid'

/* eslint-disable */
window.cr = window.cr || {}
cr.__callbacks = cr.__callbacks || {}
cr.webUIResponse = function(cb, status, data) {
  const callbackFn = cr.__callbacks[cb]
  callbackFn && callbackFn(data)
}

window.updateLaunchState = function() {
  updateRuningState()
}

const LAUNCHER_API = 'http://localhost:9528'
const isNativeEnvironment = typeof chrome !== 'undefined' && typeof chrome.send === 'function'

let migrationPromise = null
const MIGRATION_MARKER = 'vb_storage_migrated_v2'

async function launcherFetch(endpoint, options = {}) {
  const url = `${LAUNCHER_API}${endpoint}`
  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers
    }
  })

  if (!response.ok) {
    const errorText = await response.text()
    throw new Error(`HTTP ${response.status}: ${errorText || response.statusText}`)
  }

  const data = await response.json()
  if (data && data.error) {
    throw new Error(data.error)
  }
  return data
}

function normalizeListPayload(payload) {
  if (payload && Array.isArray(payload.users)) {
    return payload.users
  }
  if (Array.isArray(payload)) {
    return payload
  }
  return []
}

function readLegacyLocalStorage() {
  let list = []
  let group = []
  let global = {}

  try {
    const raw = localStorage.getItem('list')
    const parsed = raw ? JSON.parse(raw) : null
    list = normalizeListPayload(parsed)
  } catch (error) {
    console.warn('[migration] read list failed:', error)
  }

  try {
    const raw = localStorage.getItem('group')
    const parsed = raw ? JSON.parse(raw) : []
    group = Array.isArray(parsed) ? parsed : []
  } catch (error) {
    console.warn('[migration] read group failed:', error)
  }

  try {
    const raw = localStorage.getItem('GlobalData')
    const parsed = raw ? JSON.parse(raw) : {}
    global = parsed && Object.prototype.toString.call(parsed) === '[object Object]' ? parsed : {}
  } catch (error) {
    console.warn('[migration] read global failed:', error)
  }

  return { list, group, global }
}

async function migrateLegacyLocalStorageIfNeeded() {
  if (isNativeEnvironment) {
    return { migrated: false, reason: 'native-environment' }
  }

  if (migrationPromise) {
    return migrationPromise
  }

  migrationPromise = (async() => {
    try {
      const marker = localStorage.getItem(MIGRATION_MARKER)
      if (marker === '1') {
        localStorage.setItem(MIGRATION_MARKER, '1')
        return { migrated: false, reason: 'already-migrated' }
      }

      const legacy = readLegacyLocalStorage()
      if (legacy.list.length === 0 && legacy.group.length === 0 && Object.keys(legacy.global).length === 0) {
        localStorage.setItem(MIGRATION_MARKER, '1')
        return { migrated: false, reason: 'no-legacy-data' }
      }

      const result = await launcherFetch('/api/migrate/local-storage', {
        method: 'POST',
        body: JSON.stringify(legacy)
      })

      localStorage.setItem(MIGRATION_MARKER, '1')
      return { migrated: true, result }
    } catch (error) {
      console.warn('[migration] failed:', error)
      return { migrated: false, reason: 'failed', error: error.message }
    }
  })()

  return migrationPromise
}

export async function ensureLegacyMigration() {
  return migrateLegacyLocalStorageIfNeeded()
}

async function fetchServerBrowserList() {
  await migrateLegacyLocalStorageIfNeeded()
  const payload = await launcherFetch('/api/browsers')
  return normalizeListPayload(payload)
}

async function fetchServerGroupList() {
  await migrateLegacyLocalStorageIfNeeded()
  const payload = await launcherFetch('/api/groups')
  return Array.isArray(payload) ? payload : []
}

async function fetchServerGlobalData() {
  await migrateLegacyLocalStorageIfNeeded()
  const payload = await launcherFetch('/api/global')
  return payload && Object.prototype.toString.call(payload) === '[object Object]' ? payload : {}
}

export async function chromeSendTimeout(name, timeout = 2000, ...params) {
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
      chrome.send(name, args)
    })

    return Promise.race([pCall, pTimeOut(timeout)])
  }

  switch (name) {
    case 'launchBrowser': {
      const browserId = params[0]
      const list = await fetchServerBrowserList()
      const config = list.find(item => String(item.id) === String(browserId))
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
      const list = await fetchServerBrowserList()
      return { data: { users: list } }
    }

    case 'setBrowserList': {
      const payload = params[0]
      const users = normalizeListPayload(payload)
      for (let i = 0; i < users.length; i++) {
        await launcherFetch('/api/browsers', {
          method: 'POST',
          body: JSON.stringify(users[i])
        })
      }
      return { data: 'ok' }
    }

    case 'getRuningBrowser': {
      const running = await launcherFetch('/api/running')
      return running || []
    }

    case 'deleteBrowser': {
      const browserId = params[0]
      await launcherFetch(`/api/browsers/${browserId}`, { method: 'DELETE' })
      return { data: 'ok' }
    }

    case 'stopBrowser': {
      const browserId = params[0]
      const result = await launcherFetch(`/api/stop/${browserId}`, { method: 'POST' })
      return { data: result }
    }

    case 'getGlobalData': {
      const data = await fetchServerGlobalData()
      return { data: JSON.stringify(data || {}) }
    }

    case 'setGlobalData': {
      const payload = params[0]
      const parsed = typeof payload === 'string' ? JSON.parse(payload) : payload
      await launcherFetch('/api/global', { method: 'POST', body: JSON.stringify(parsed || {}) })
      return { data: 'ok' }
    }

    case 'getBrowserVersion': {
      return { data: '139.0.0.0' }
    }

    case 'checkProxy': {
      return { data: true }
    }

    case 'setIpGeo': {
      return { data: 'ok' }
    }

    default:
      return { data: null }
  }
}

export async function chromeSend(name, ...params) {
  return chromeSendTimeout(name, 2000, ...params)
}

export async function getGlobalData() {
  if (isNativeEnvironment) {
    try {
      const ret = await chromeSend('getGlobalData')
      const parsed = JSON.parse(ret.data)
      return parsed && Object.prototype.toString.call(parsed) === '[object Object]' ? parsed : {}
    } catch (error) {
      console.warn('getGlobalData(native) failed:', error)
      return {}
    }
  }

  return fetchServerGlobalData()
}

export async function setGlobalData(key, value) {
  const data = await getGlobalData()
  data[key] = value

  if (isNativeEnvironment) {
    await chromeSend('setGlobalData', JSON.stringify(data))
    return
  }

  await launcherFetch('/api/global', {
    method: 'POST',
    body: JSON.stringify(data)
  })
}

export async function getBrowserList() {
  if (isNativeEnvironment) {
    try {
      const ret = await chromeSend('getBrowserList')
      return (ret && ret.data && ret.data.users) || []
    } catch (error) {
      console.warn('getBrowserList(native) failed:', error)
      return []
    }
  }

  return fetchServerBrowserList()
}

export async function addBrowser(item, defaultName) {
  const payload = JSON.parse(JSON.stringify(item || {}))
  if (!payload.name && defaultName) {
    payload.name = defaultName
  }

  if (isNativeEnvironment) {
    const list = await getBrowserList()
    const maxId = Math.max(0, ...list.map(it => Number(it.id) || 0))
    payload.id = payload.id || maxId + 1
    payload.name = payload.name || `${defaultName || 'Browser'} ${payload.id}`
    list.push(payload)
    await chromeSend('setBrowserList', { users: list })
    return
  }

  await launcherFetch('/api/browsers', {
    method: 'POST',
    body: JSON.stringify(payload)
  })
}

export async function updateBrowser(item) {
  const payload = JSON.parse(JSON.stringify(item || {}))
  if (payload.id === undefined || payload.id === null) {
    throw new Error('updateBrowser requires id')
  }

  if (isNativeEnvironment) {
    const list = await getBrowserList()
    const index = list.findIndex(it => String(it.id) === String(payload.id))
    if (index < 0) {
      throw new Error('Browser not found: ' + payload.id)
    }
    list[index] = payload
    await chromeSend('setBrowserList', { users: list })
    return
  }

  await launcherFetch(`/api/browsers/${payload.id}`, {
    method: 'PUT',
    body: JSON.stringify(payload)
  })
}

export async function deleteBrowser(id) {
  if (isNativeEnvironment) {
    await chromeSend('deleteBrowser', id)
    return
  }

  await launcherFetch(`/api/browsers/${id}`, { method: 'DELETE' })
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
  if (isNativeEnvironment) {
    try {
      const raw = localStorage.getItem('group')
      const parsed = raw ? JSON.parse(raw) : []
      return Array.isArray(parsed) ? parsed : []
    } catch (error) {
      console.warn('getGroupList(native) failed:', error)
      return []
    }
  }
  return fetchServerGroupList()
}

export async function addGroup(item, defaultName) {
  const payload = JSON.parse(JSON.stringify(item || {}))
  if (!payload.name && defaultName) {
    payload.name = `${defaultName}`
  }

  if (isNativeEnvironment) {
    const list = await getGroupList()
    const maxId = Math.max(0, ...list.map(it => Number(it.id) || 0))
    payload.id = payload.id || maxId + 1
    payload.name = payload.name || `${defaultName || 'Group'} ${payload.id}`
    list.push(payload)
    localStorage.setItem('group', JSON.stringify(list))
    return
  }

  await launcherFetch('/api/groups', {
    method: 'POST',
    body: JSON.stringify(payload)
  })
}

export async function updateGroup(item) {
  const payload = JSON.parse(JSON.stringify(item || {}))
  if (payload.id === undefined || payload.id === null) {
    throw new Error('updateGroup requires id')
  }

  if (isNativeEnvironment) {
    const list = await getGroupList()
    const idx = list.findIndex(it => String(it.id) === String(payload.id))
    if (idx < 0) {
      throw new Error('Group not found: ' + payload.id)
    }
    list[idx] = payload
    localStorage.setItem('group', JSON.stringify(list))
    return
  }

  await launcherFetch(`/api/groups/${payload.id}`, {
    method: 'PUT',
    body: JSON.stringify(payload)
  })
}

export async function deleteGroup(id) {
  if (isNativeEnvironment) {
    const list = await getGroupList()
    const idx = list.findIndex(it => String(it.id) === String(id))
    if (idx >= 0) {
      list.splice(idx, 1)
      localStorage.setItem('group', JSON.stringify(list))
    }
    return
  }

  await launcherFetch(`/api/groups/${id}`, { method: 'DELETE' })
}
