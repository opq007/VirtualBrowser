/**
 * IP 地理位置 API 适配器
 * 支持多种流行的 IP 查询服务
 */

/**
 * 支持的 IP API 类型
 */
export const IP_API_TYPES = {
  IP_API_COM: 'ip-api.com',      // ip-api.com (免费，无需密钥)
  IPINFO_IO: 'ipinfo.io',        // ipinfo.io
  IPAPI_CO: 'ipapi.co',          // ipapi.co
  IP_GEOLOCATION: 'ipgeolocation', // ipgeolocation.io
  CUSTOM: 'custom'               // 自定义格式
}

/**
 * 字段映射配置
 * 将不同 API 的字段名映射到统一格式
 */
const FIELD_MAPPINGS = {
  // ip-api.com 格式
  [IP_API_TYPES.IP_API_COM]: {
    ip: 'query',
    country_name: 'country',
    country_code2: 'countryCode',
    city: 'city',
    region: 'regionName',
    latitude: 'lat',
    longitude: 'lon',
    time_zone: (data) => ({
      name: data.timezone,
      offset: data.offset / 3600 // 转换为小时
    }),
    languages: (data) => {
      // ip-api.com 不直接返回语言，根据国家代码推断
      const langMap = {
        'CN': 'zh-CN',
        'US': 'en-US',
        'GB': 'en-GB',
        'JP': 'ja-JP',
        'KR': 'ko-KR',
        'DE': 'de-DE',
        'FR': 'fr-FR',
        'RU': 'ru-RU',
        'BR': 'pt-BR',
        'IN': 'hi-IN',
        'TW': 'zh-TW',
        'HK': 'zh-HK'
      }
      return langMap[data.countryCode] || 'en-US'
    },
    country_flag: (data) => data.countryCode ? `https://flagcdn.com/w80/${data.countryCode.toLowerCase()}.png` : ''
  },

  // ipinfo.io 格式
  [IP_API_TYPES.IPINFO_IO]: {
    ip: 'ip',
    country_name: (data) => {
      const countryNames = {
        'CN': 'China',
        'US': 'United States',
        'GB': 'United Kingdom',
        'JP': 'Japan',
        'KR': 'South Korea',
        'DE': 'Germany',
        'FR': 'France',
        'RU': 'Russia',
        'BR': 'Brazil',
        'IN': 'India',
        'TW': 'Taiwan',
        'HK': 'Hong Kong'
      }
      return countryNames[data.country] || data.country
    },
    country_code2: 'country',
    city: 'city',
    region: 'region',
    latitude: (data) => {
      if (data.loc) {
        return parseFloat(data.loc.split(',')[0])
      }
      return 0
    },
    longitude: (data) => {
      if (data.loc) {
        return parseFloat(data.loc.split(',')[1])
      }
      return 0
    },
    time_zone: (data) => ({
      name: data.timezone || 'UTC',
      offset: 0
    }),
    languages: (data) => {
      const langMap = {
        'CN': 'zh-CN',
        'US': 'en-US',
        'GB': 'en-GB',
        'JP': 'ja-JP',
        'KR': 'ko-KR',
        'DE': 'de-DE',
        'FR': 'fr-FR',
        'RU': 'ru-RU',
        'BR': 'pt-BR',
        'IN': 'hi-IN',
        'TW': 'zh-TW',
        'HK': 'zh-HK'
      }
      return langMap[data.country] || 'en-US'
    },
    country_flag: (data) => data.country ? `https://flagcdn.com/w80/${data.country.toLowerCase()}.png` : ''
  },

  // ipapi.co 格式
  [IP_API_TYPES.IPAPI_CO]: {
    ip: 'ip',
    country_name: 'country_name',
    country_code2: 'country_code',
    city: 'city',
    region: 'region',
    latitude: 'latitude',
    longitude: 'longitude',
    time_zone: (data) => ({
      name: data.timezone?.id || data.timezone || 'UTC',
      offset: data.utc_offset ? parseFloat(data.utc_offset) : 0
    }),
    languages: (data) => data.languages?.split(',')[0] || 'en-US',
    country_flag: (data) => data.country_flag || (data.country_code ? `https://flagcdn.com/w80/${data.country_code.toLowerCase()}.png` : '')
  },

  // ipgeolocation.io 格式
  [IP_API_TYPES.IP_GEOLOCATION]: {
    ip: 'ip',
    country_name: 'country_name',
    country_code2: 'country_code2',
    city: 'city',
    region: 'state_prov',
    latitude: 'latitude',
    longitude: 'longitude',
    time_zone: (data) => ({
      name: data.time_zone?.name || 'UTC',
      offset: data.time_zone?.offset || 0
    }),
    languages: (data) => data.languages?.split(',')[0] || 'en-US',
    country_flag: (data) => data.country_flag || (data.country_code2 ? `https://flagcdn.com/w80/${data.country_code2.toLowerCase()}.png` : '')
  },

  // 自定义格式（与原始 VirtualBrowser 兼容）
  [IP_API_TYPES.CUSTOM]: {
    ip: 'ip',
    country_name: 'country_name',
    country_code2: 'country_code2',
    city: 'city',
    region: 'region',
    latitude: 'latitude',
    longitude: 'longitude',
    time_zone: 'time_zone',
    languages: 'languages',
    country_flag: 'country_flag'
  }
}

/**
 * 自动检测 API 类型
 * @param {string} url - API URL
 * @param {Object} data - API 返回的数据
 * @returns {string} - 检测到的 API 类型
 */
export function detectApiType(url, data) {
  if (url.includes('ip-api.com')) {
    return IP_API_TYPES.IP_API_COM
  }
  if (url.includes('ipinfo.io')) {
    return IP_API_TYPES.IPINFO_IO
  }
  if (url.includes('ipapi.co')) {
    return IP_API_TYPES.IPAPI_CO
  }
  if (url.includes('ipgeolocation')) {
    return IP_API_TYPES.IP_GEOLOCATION
  }

  // 根据数据结构推断
  if (data.query && data.countryCode) {
    return IP_API_TYPES.IP_API_COM
  }
  if (data.loc && data.org) {
    return IP_API_TYPES.IPINFO_IO
  }
  if (data.country_code && data.utc_offset !== undefined) {
    return IP_API_TYPES.IPAPI_CO
  }

  return IP_API_TYPES.CUSTOM
}

/**
 * 获取字段值
 * @param {Object} data - 原始数据
 * @param {string|Function} mapping - 字段映射
 * @returns {any} - 字段值
 */
function getFieldValue(data, mapping) {
  if (typeof mapping === 'function') {
    return mapping(data)
  }
  if (typeof mapping === 'string') {
    return data[mapping]
  }
  return mapping
}

/**
 * 转换 API 响应为统一格式
 * @param {Object} rawData - 原始 API 响应数据
 * @param {string} apiType - API 类型
 * @returns {Object} - 统一格式的数据
 */
export function normalizeIpGeoData(rawData, apiType = IP_API_TYPES.CUSTOM) {
  const mapping = FIELD_MAPPINGS[apiType] || FIELD_MAPPINGS[IP_API_TYPES.CUSTOM]

  const normalized = {
    ip: getFieldValue(rawData, mapping.ip) || '',
    country_name: getFieldValue(rawData, mapping.country_name) || '',
    country_code2: getFieldValue(rawData, mapping.country_code2) || '',
    city: getFieldValue(rawData, mapping.city) || '',
    region: getFieldValue(rawData, mapping.region) || '',
    latitude: getFieldValue(rawData, mapping.latitude) || 0,
    longitude: getFieldValue(rawData, mapping.longitude) || 0,
    time_zone: getFieldValue(rawData, mapping.time_zone) || { name: 'UTC', offset: 0 },
    languages: getFieldValue(rawData, mapping.languages) || 'en-US',
    country_flag: getFieldValue(rawData, mapping.country_flag) || ''
  }

  return normalized
}

/**
 * 获取 IP 地理位置信息
 * @param {string} apiUrl - API URL
 * @returns {Promise<Object>} - 统一格式的地理位置数据
 */
export async function fetchIpGeoData(apiUrl) {
  const response = await fetch(apiUrl)

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`)
  }

  const rawData = await response.json()

  // 检测 API 类型
  const apiType = detectApiType(apiUrl, rawData)

  // 转换为统一格式
  const normalizedData = normalizeIpGeoData(rawData, apiType)

  return {
    ...normalizedData,
    _raw: rawData,
    _apiType: apiType
  }
}

/**
 * 生成时区字符串
 * @param {number} offset - 时区偏移量（小时）
 * @returns {string} - UTC 时区字符串，如 "UTC+8:00"
 */
export function formatTimezone(offset) {
  const sign = offset >= 0 ? '+' : '-'
  const hours = Math.floor(Math.abs(offset))
  const minutes = Math.round((Math.abs(offset) - hours) * 60)
  const paddedMinutes = minutes < 10 ? '0' + minutes : minutes.toString()
  return `UTC${sign}${hours}:${paddedMinutes}`
}

/**
 * 生成浏览器配置用的 IP 地理位置对象
 * @param {Object} geoData - 标准化的地理位置数据
 * @returns {Object} - 浏览器配置对象
 */
export function generateBrowserConfig(geoData) {
  return {
    'time-zone': {
      zone: formatTimezone(geoData.time_zone?.offset || 0),
      locale: geoData.languages?.split(',')[0] || 'en-US',
      utc: geoData.time_zone?.name || 'UTC'
    },
    location: {
      longitude: parseFloat(geoData.longitude) || 0,
      latitude: parseFloat(geoData.latitude) || 0,
      precision: Math.floor(Math.random() * 5000) + 10
    },
    'ua-language': {
      value: geoData.languages?.split(',')[0] || 'en-US'
    }
  }
}

export default {
  IP_API_TYPES,
  detectApiType,
  normalizeIpGeoData,
  fetchIpGeoData,
  formatTimezone,
  generateBrowserConfig
}
