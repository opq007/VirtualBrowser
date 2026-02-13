<template>
  <section class="container">
    <header>
      <img src="./assets/96.png" />
      <h1>Virtual Browser</h1>
    </header>
    <main>
      <div class="geo" v-show="geo.ip">
        <h3>{{ geo.ip }}</h3>
        <p>
          <span class="item country">
            <span>(For reference only)</span>
            <span v-if="geo.country_flag">
              <img :src="geo.country_flag" />
              {{ geo.country_name }}({{ geo.country_code2 }})
            </span>
            {{ geo.city ? '/' : '' }}
            <span>{{ geo.city }}</span>
          </span>
        </p>
        <p v-if="geo.time_zone">
          <span class="item">
            <span>
              <b>Time Zone:</b>
              {{ geo.time_zone.name }}
            </span>
            <span v-if="geo.longitude && geo.latitude">
              <b>Coordinates:</b>
              {{ geo.longitude }}/{{ geo.latitude }}
            </span>
          </span>
        </p>
        <p>
          <span class="item">
            <span>
              <b>Fingerprint Hash:</b>
              {{ visitorId }}
            </span>
          </span>
        </p>
        <p>
          <img src="./assets/VirtualBrowser-qq-group.png" />
          <br />
          QQ Group:
          <code>564142956</code>
        </p>
      </div>
      <div v-if="!apiLinkIsValid && !ipGeoData" class="api-link-info">
        <h2>本地模式运行中</h2>
        <p>IP地理位置查询功能未启用。</p>
        <p>如需启用，请在浏览器管理界面设置API链接。</p>
        <p>
          支持免费API如:
          <a href="https://ip-api.com" target="_blank">ip-api.com</a>
        </p>
      </div>
      <div class="network-error" v-if="networkErr">
        <h1>网络连接错误</h1>
        <p>请检查您的网络或代理设置</p>
      </div>
      <div v-if="showLimitError" class="LimitError">
        <h2>IP查询Key超出限制</h2>
        <p>请检查您的API Key</p>
      </div>
      <el-timeline v-if="false" class="timeline">
        <el-timeline-item
          v-for="(value, key, index) in fingerprint"
          :key="index"
          :timestamp="key"
          placement="top"
        >
          <el-card class="card">
            <pre v-html="formatResult(value.value)"></pre>
          </el-card>
        </el-timeline-item>
      </el-timeline>
    </main>
  </section>
</template>

<script lang="ts" setup>
import FingerprintJS from '@fingerprintjs/fingerprintjs'
import { onMounted, ref, computed } from 'vue'
import formatHighlight from 'json-format-highlight'
import { chromeSend, getGlobalData } from '@/utils/native.js'
import random from 'random'

const geo = ref({
  ip: '',
  country_flag: '',
  country_name: '',
  country_code2: '',
  city: '',
  time_zone: { name: '' },
  longitude: '',
  latitude: ''
})
const fingerprint = ref()
const visitorId = ref('')
const networkErr = ref(false)
let apiLink = ref('')
const showLimitError = ref(false)
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const ipGeoData = ref<any>(null)

const apiLinkIsValid = computed(() => apiLink.value !== '')

onMounted(async () => {
  // 获取指纹信息
  try {
    const fp = await FingerprintJS.load()
    const result = await fp.get()
    visitorId.value = result.visitorId
    fingerprint.value = result.components
  } catch (err) {
    console.warn('FingerprintJS error:', err)
  }

  // 尝试获取全局数据和API配置
  try {
    const store = await getGlobalData()
    const storedApiLink = store.apiLink
    if (storedApiLink) {
      apiLink.value = storedApiLink
    }
  } catch (err) {
    console.warn('getGlobalData error:', err)
  }

  // 如果配置了API链接，则尝试获取IP地理位置
  if (apiLink.value) {
    try {
      let req = await fetch(apiLink.value)
      if (req) {
        const res = await req.json()
        const apiResponse = res
        if (
          apiResponse.code === -13 ||
          (apiResponse.msg && apiResponse.msg.includes('limit')) ||
          (apiResponse.message && apiResponse.message.includes('limit'))
        ) {
          showLimitError.value = true
          return
        }
        geo.value = res
        ipGeoData.value = res

        const ipGeo = {
          'time-zone': {
            zone: getZone(res.time_zone.offset_with_dst || res.time_zone?.offset || 0),
            locale: res.languages?.split(',')[0] || '',
            utc: res.time_zone.name
          },
          location: {
            longitude: parseFloat(res.longitude),
            latitude: parseFloat(res.latitude),
            precision: random.int(10, 5000)
          },
          'ua-language': {
            value: res.languages?.split(',')[0] || ''
          }
        }

        await chromeSend('setIpGeo', ipGeo).catch((err: Error) => {
          console.warn('setIpGeo error:', err)
        })
      }
    } catch (err) {
      console.log('API fetch error:', err)
      networkErr.value = true
    }
  }
})

const getZone = (offset: number) => {
  const sign = offset > 0 ? '+' : '-'
  const hours = Math.floor(Math.abs(offset))
  const decimal = Math.abs(offset) - hours
  const minutes = Math.round(decimal * 60)
  const paddedMinutes = minutes < 10 ? '0' + minutes : minutes.toString()
  return `UTC${sign}${hours}:${paddedMinutes}`
}

const formatResult = (json: JSON) => {
  let colorJson = formatHighlight(json)
  colorJson = colorJson.replace(/"data:image\/.+?"/g, ($0: string) => {
    return `<img src=${$0} style="vertical-align: text-top;" />`
  })

  return colorJson
}
</script>

<style lang="scss">
.container {
  width: 1000px;
  margin: auto;

  header {
    display: flex;
    align-items: center;
    justify-content: center;

    & > * {
      margin: 10px 10px 15px;
    }
  }

  main {
    border: 1px solid #dcdfe6;
    border-radius: 4px;
    padding: 15px 30px 20px;

    .geo {
      text-align: center;

      h3 {
        font-size: 36px;
        margin: 5px;
      }
      code {
        padding: 0.2em 0.4em;
        margin: 0;
        font-family: ui-monospace, SFMono-Regular, SF Mono, Menlo, Consolas, Liberation Mono,
          monospace;
        font-size: 120%;
        white-space: break-spaces;
        background-color: rgba(175, 184, 193, 0.2);
        border-radius: 6px;
      }
      .item {
        border: 1px dashed rgba(128, 128, 128, 0.4);
        border-radius: 6px;
        line-height: 30px;
        padding: 5px 10px;

        span {
          margin: 0 5px;
        }

        &.country {
          color: #2c9100;
          font-weight: bold;

          img {
            height: 31px;
            vertical-align: top;
          }
        }
      }
    }

    .api-link-info {
      text-align: center;
      padding: 20px;
      background-color: #f5f7fa;
      border-radius: 8px;
      margin-bottom: 20px;

      h2 {
        color: #409eff;
        margin-bottom: 10px;
      }

      p {
        color: #606266;
        margin: 8px 0;
      }

      a {
        color: #409eff;
        text-decoration: none;
        &:hover {
          text-decoration: underline;
        }
      }
    }

    .card {
      --el-card-padding: 10px;
      pre {
        margin: 0;
      }
    }

    .network-error {
      max-width: 200px;
      margin: auto;

      h1 {
        color: rgb(32, 33, 36);
        font-weight: 500;
      }
      p {
        color: rgb(95, 99, 104);
      }
    }
  }

  .timeline {
    padding: 0;
  }
}
</style>