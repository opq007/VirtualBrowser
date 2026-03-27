<template>
  <div class="app-container">
    <div class="filter-container">
      <div>
        <el-button
          class="filter-item"
          type="primary"
          icon="el-icon-circle-plus"
          @click="handleCreate"
        >
          {{ $t('browser.add') }}
        </el-button>
        <el-dropdown class="filter-item">
          <el-button type="primary">
            {{ $t('browser.batchActions') }}
            <i class="el-icon-arrow-down el-icon--right" />
          </el-button>
          <el-dropdown-menu slot="dropdown">
            <el-dropdown-item @click.native="handleBatchStart">
              {{ $t('browser.batchStart') }}
            </el-dropdown-item>
            <el-dropdown-item @click.native="handleBatchStop">
              {{ $t('browser.batchStop') }}
            </el-dropdown-item>
            <el-dropdown-item @click.native="() => (dialogVisible = true)">
              {{ $t('browser.batchCreate') }}
            </el-dropdown-item>
            <el-dropdown-item @click.native="handleBatchDelete">
              {{ $t('browser.batchDelete') }}
            </el-dropdown-item>
            <el-dropdown-item @click.native="handleBatchSetGroup">
              {{ $t('browser.batchGroup') }}
            </el-dropdown-item>
          </el-dropdown-menu>
        </el-dropdown>
      </div>
      <div style="display: flex">
        <el-select
          v-model="listQuery.group"
          filterable
          clearable
          :placeholder="$t('group.filter')"
          style="width: 150px; margin-right: 10px"
          @change="handleFilter"
        >
          <el-option v-for="item in GroupList" :key="item.id" :value="item.name" />
        </el-select>
        <el-select
          v-model="listQuery.tags"
          multiple
          filterable
          clearable
          collapse-tags
          :placeholder="$t('browser.tagFilter')"
          style="width: 200px; margin-right: 10px"
          @change="handleFilter"
        >
          <el-option v-for="tag in allTags" :key="tag" :value="tag" />
        </el-select>
        <el-input
          v-model="listQuery.title"
          :placeholder="$t('browser.name')"
          style="width: 200px"
          class="filter-item"
          @keyup.enter.native="handleFilter"
        />
        <el-button v-waves class="filter-item" icon="el-icon-search" @click="handleFilter">
          {{ $t('browser.search') }}
        </el-button>
        <el-button @click="showSettingsDialog">IP查询API设置</el-button>
        <el-upload
          action=""
          accept=".json"
          :auto-upload="false"
          :show-file-list="false"
          :on-change="onImport"
        >
          <el-button style="margin-left: 10px">{{ $t('browser.import.import') }}</el-button>
        </el-upload>
        <el-button style="margin-left: 10px" @click="onExport">
          {{ $t('browser.import.export') }}
        </el-button>
      </div>
    </div>

    <el-table
      :key="tableKey"
      v-loading="listLoading"
      :data="list"
      border
      fit
      highlight-current-row
      style="width: 100%"
      @selection-change="handleSelectionChange"
    >
      <el-table-column type="selection" width="60" align="center" />
      <el-table-column :label="$t('browser.id')" prop="id" sortable align="center" width="80">
        <template slot-scope="{ row }">
          <span>{{ row.id }}</span>
        </template>
      </el-table-column>
      <el-table-column :label="$t('browser.name')" min-width="80px">
        <template slot-scope="{ row }">
          <span>{{ row.name }}</span>
        </template>
      </el-table-column>
      <el-table-column :label="$t('group.group')" min-width="50px">
        <template slot-scope="{ row }">
          <el-tooltip class="item" effect="dark" content="点击编辑分组" placement="top">
            <el-button type="text" @click="handleEditGroup(row)">
              {{ row.group }}
            </el-button>
          </el-tooltip>
        </template>
      </el-table-column>
      <el-table-column label="代理" width="300px">
        <template slot-scope="{ row }">
          <span>
            <template v-if="row.proxy.mode === 0">默认</template>
            <template v-else-if="row.proxy.mode === 1">不使用代理</template>
            <template v-else>
              {{ row.proxy.protocol }}
              {{
                row.proxy.host && row.proxy.port ? ' ' + row.proxy.host + ':' + row.proxy.port : ''
              }}
            </template>
          </span>
        </template>
      </el-table-column>
      <el-table-column :label="$t('browser.status')" width="100" align="center">
        <template slot-scope="{ row }">
          <el-tag v-if="row.isRunning" type="success" size="small" effect="dark">
            {{ $t('browser.running') }}
          </el-tag>
          <el-tag v-else type="info" size="small" effect="plain">
            {{ $t('browser.stopped') }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column :label="$t('browser.debug_port')" width="110" align="center">
        <template slot-scope="{ row }">
          <span v-if="row.isRunning && row.debug_port" style="color: #67c23a; font-weight: bold">
            {{ row.debug_port }}
          </span>
          <span v-else style="color: #909399">-</span>
        </template>
      </el-table-column>
      <el-table-column
        :label="$t('browser.date')"
        sortable
        prop="timestamp"
        width="150px"
        align="center"
      >
        <template slot-scope="{ row }">
          <span>{{ row.timestamp | parseTime('{y}-{m}-{d} {h}:{i}') }}</span>
        </template>
      </el-table-column>

      <el-table-column :label="$t('browser.launch')" class-name="status-col" width="150">
        <template slot-scope="{ row }">
          <el-button
            v-if="!row.isRunning"
            type="primary"
            icon="el-icon-video-play"
            :loading="row.runLoading"
            @click="handleLaunch(row)"
          >
            {{ $t(row.runLoading ? 'browser.launching' : 'browser.launch') }}
          </el-button>
          <el-button
            v-else
            type="danger"
            icon="el-icon-video-pause"
            :loading="row.stopLoading"
            @click="handleStop(row)"
          >
            {{ $t(row.stopLoading ? 'browser.stopping' : 'browser.stop') }}
          </el-button>
        </template>
      </el-table-column>
      <el-table-column :label="$t('browser.tags')" min-width="150px">
        <template slot-scope="{ row }">
          <div class="tags-cell">
            <el-tag
              v-for="tag in (row.tags || []).slice(0, 3)"
              :key="tag"
              size="mini"
              type="info"
              style="margin-right: 4px; margin-bottom: 2px"
            >
              {{ tag }}
            </el-tag>
            <el-tag
              v-if="(row.tags || []).length > 3"
              size="mini"
              type="info"
              style="margin-right: 4px"
            >
              +{{ row.tags.length - 3 }}
            </el-tag>
            <el-button
              type="text"
              size="mini"
              icon="el-icon-edit"
              style="margin-left: 4px"
              @click="handleEditTags(row)"
            />
          </div>
        </template>
      </el-table-column>
      <el-table-column
        :label="$t('browser.actions')"
        align="center"
        width="250"
        class-name="small-padding fixed-width"
      >
        <template slot-scope="{ row, $index }">
          <el-button type="primary" size="mini" @click="handleUpdate(row)">
            {{ $t('browser.edit') }}
          </el-button>
          <el-button type="success" size="mini" @click="handleCopy(row)">
            {{ $t('browser.copy') }}
          </el-button>
          <el-button
            v-if="row.status != 'deleted'"
            type="danger"
            size="mini"
            @click="handleDelete(row, $index)"
          >
            {{ $t('browser.delete') }}
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-drawer
      :title="$t(dialogStatus == 'create' ? 'browser.add' : 'browser.edit')"
      :visible.sync="dialogFormVisible"
      :close-on-click-modal="false"
      class="formDlg"
      size="800px"
    >
      <div class="drawer-content">
        <div class="form-wrap">
          <el-form
            ref="dataForm"
            :rules="rules"
            :model="form"
            label-position="left"
            label-width="100px"
          >
            <el-timeline>
              <el-timeline-item>
                <h3>{{ $t('browser.basic') }}</h3>
                <div>
                  <el-form-item :label="$t('browser.name')" prop="name">
                    <el-input v-model="form.name" :placeholder="$t('browser.name_placeholder')" />
                  </el-form-item>
                  <el-form-item :label="$t('browser.group')">
                    <el-select v-model="form.group" :placeholder="$t('browser.select')">
                      <el-option v-for="item in GroupList" :key="item.id" :value="item.name" />
                    </el-select>
                  </el-form-item>
                  <el-form-item :label="$t('browser.platform')">
                    <el-radio-group v-model="form.os">
                      <el-radio-button v-for="item in platforms" :key="item" :label="item" />
                    </el-radio-group>
                  </el-form-item>
                  <el-form-item :label="$t('browser.version')">
                    <el-select v-model="form.chrome_version" :placeholder="$t('browser.select')">
                      <el-option v-for="item in Versions" :key="item" :value="item" />
                    </el-select>
                  </el-form-item>
                  <el-form-item :label="$t('browser.proxy.setting')">
                    <el-radio-group v-model="form.proxy.mode">
                      <el-radio-button :label="0">{{ $t('browser.default') }}</el-radio-button>
                      <el-radio-button :label="1">{{ $t('browser.no_proxy') }}</el-radio-button>
                      <el-radio-button :label="2">{{ $t('browser.custom') }}</el-radio-button>
                    </el-radio-group>
                    <div v-if="form.proxy.mode == 2" style="margin-top: 10px">
                      <el-form-item :label="$t('browser.proxy.protocol')" label-width="70px">
                        <el-select v-model="form.proxy.protocol" style="width: 100px">
                          <el-option value="HTTP" />
                          <el-option value="HTTPS" />
                          <el-option value="SOCKS5" />
                        </el-select>
                      </el-form-item>
                      <el-form-item
                        :label="$t('browser.proxy.host')"
                        label-width="70px"
                        prop="proxy.host"
                      >
                        <el-input v-model="form.proxy.host" style="max-width: 250px" />
                        :
                        <el-input
                          v-model="form.proxy.port"
                          style="width: 70px"
                          :placeholder="$t('browser.proxy.port')"
                        />
                        <span style="font-size: 12px; margin-left: 10px; color: rgb(141, 133, 133)">
                          可按‘主机:端口:账号:密码’或‘主机:端口’格式粘贴自动识别
                        </span>
                      </el-form-item>
                      <el-form-item :label="$t('browser.proxy.user')" label-width="70px">
                        <el-input v-model="form.proxy.user" style="max-width: 250px" />
                      </el-form-item>
                      <el-form-item :label="$t('browser.proxy.pass')" label-width="70px">
                        <el-input v-model="form.proxy.pass" style="max-width: 250px" />
                        &nbsp;
                        <el-button
                          type="primary"
                          style="margin-left: 7px"
                          :disabled2="checkProxyState.checking"
                          :loading="checkProxyState.checking"
                          @click="checkProxy"
                        >
                          检测{{ checkProxyState.checking ? '中' : '' }}
                        </el-button>
                      </el-form-item>
                      <el-form-item :label="$t('browser.proxy.API')" label-width="70px">
                        <el-input v-model="form.proxy.API" style="max-width: 250px" />
                        &nbsp;
                        <el-button type="primary" style="margin-left: 7px" @click="checkAPIProxy">
                          提取代理
                        </el-button>
                      </el-form-item>
                    </div>
                  </el-form-item>
                  <el-form-item :label="$t('browser.cookie.jsonStr')" prop="cookie.jsonStr">
                    <el-switch v-model="form.cookie.mode" :active-value="1" :inactive-value="0" />
                    <div style="display: flex; align-items: flex-start">
                      <el-input
                        v-model="form.cookie.jsonStr"
                        type="textarea"
                        rows="6"
                        :placeholder="$t('browser.cookie.placeholder')"
                        :disabled="form.cookie.mode === 0"
                      />
                      <el-button
                        type="text"
                        style="margin: -5px 0 0 5px"
                        @click="dialogCookieFormatVisible = true"
                      >
                        {{ $t('browser.cookie.format') }}
                      </el-button>
                    </div>
                  </el-form-item>
                  <el-form-item :label="$t('browser.homepage')">
                    <el-radio-group v-model="form.homepage.mode">
                      <el-radio-button :label="0">{{ $t('browser.default') }}</el-radio-button>
                      <el-radio-button :label="1">{{ $t('browser.custom') }}</el-radio-button>
                    </el-radio-group>
                    <el-input
                      v-if="form.homepage.mode === 1"
                      v-model="form.homepage.value"
                      :placeholder="$t('browser.homepage_tips')"
                      style="width: 424px; margin-left: 10px"
                    />
                  </el-form-item>
                </div>
              </el-timeline-item>
              <el-timeline-item>
                <h3>{{ $t('browser.advanced') }}</h3>
                <div>
                  <el-form-item :label="$t('browser.ua')">
                    <el-radio-group v-model="form.ua.mode">
                      <el-radio-button :label="0">{{ $t('browser.default') }}</el-radio-button>
                      <el-radio-button :label="1">{{ $t('browser.custom') }}</el-radio-button>
                    </el-radio-group>
                    <div style="display: flex; align-items: flex-start; margin-top: 3px">
                      <div style="flex-grow: 1; margin-right: 10px">
                        <el-input
                          v-model="form.ua.value"
                          :disabled="form.ua.mode === 0"
                          type="textarea"
                          style="width: 100%"
                        />
                      </div>
                      <el-button
                        type="primary"
                        size="small"
                        icon="el-icon-refresh"
                        :disabled="form.ua.mode === 0"
                        @click="RandomFingerprint"
                      >
                        {{ $t('browser.random') }}
                      </el-button>
                    </div>
                  </el-form-item>
                  <el-form-item :label="$t('browser.sec_ua')">
                    <el-radio-group v-model="form['sec-ch-ua'].mode">
                      <el-radio-button :label="0">{{ $t('browser.default') }}</el-radio-button>
                      <el-radio-button :label="1">{{ $t('browser.custom') }}</el-radio-button>
                    </el-radio-group>
                    <div v-show="form['sec-ch-ua'].mode === 1" class="custom-sec-ua">
                      <div v-for="(item, i) in form['sec-ch-ua'].value" :key="i" class="item">
                        <el-form-item label="brand: " label-width="42px">
                          <el-input v-model="item.brand" />
                        </el-form-item>
                        <el-form-item label="version: " label-width="52px">
                          <el-input v-model="item.version" style="width: 60px" />
                        </el-form-item>
                        <el-button
                          type="danger"
                          icon="el-icon-minus"
                          circle
                          @click="onRemoveBrand(item.brand)"
                        />
                      </div>
                      <div class="item">
                        <el-form-item label="brand: " label-width="42px" style="visibility: hidden">
                          <el-input />
                        </el-form-item>
                        <el-form-item
                          label="version: "
                          label-width="52px"
                          style="visibility: hidden"
                        >
                          <el-input style="width: 60px" />
                        </el-form-item>
                        <el-button
                          type="success"
                          icon="el-icon-plus"
                          circle
                          @click="onAddBrand()"
                        />
                      </div>
                    </div>
                  </el-form-item>
                  <el-form-item :label="$t('browser.language')">
                    <el-switch
                      v-model="form['ua-language'].mode"
                      :active-value="2"
                      :inactive-value="1"
                    />
                    <span style="margin-left: 10px">{{ $t('browser.language_tips') }}</span>
                    <el-select
                      v-if="form['ua-language'].mode == 1"
                      v-model="form['ua-language'].language"
                      :placeholder="$t('browser.select')"
                      style="width: 100%"
                    >
                      <el-option
                        v-for="(item, i) in Languages"
                        :key="i"
                        :label="(language == 'zh' ? item.lang : item.en) + '    ' + item.code"
                        :value="item.code"
                      >
                        <span style="float: left">
                          {{ language == 'zh' ? item.lang : item.en }}
                        </span>
                        <span style="float: right; color: #8492a6; font-size: 13px">
                          {{ item.code }}
                        </span>
                      </el-option>
                    </el-select>
                  </el-form-item>
                  <el-form-item :label="$t('browser.timezone')">
                    <el-switch
                      v-model="form['time-zone'].mode"
                      :active-value="2"
                      :inactive-value="1"
                    />
                    <span style="margin-left: 10px">{{ $t('browser.timezone_tips') }}</span>
                    <el-select
                      v-if="form['time-zone'].mode == 1"
                      v-model="form['time-zone'].name"
                      :placeholder="$t('browser.select')"
                      style="width: 100%"
                      @change="
                        select => {
                          const selItem = TimeZones.find(item => item.text == select)
                          form['time-zone'].value = selItem.offset
                          form['time-zone'].zone = getZone(selItem.offset)
                          form['time-zone'].utc = selItem.utc[0]
                        }
                      "
                    >
                      <el-option v-for="(item, i) in TimeZones" :key="i" :value="item.text" />
                    </el-select>
                  </el-form-item>
                  <el-form-item :label="$t('browser.webrtc')">
                    <el-radio-group v-model="form.webrtc.mode">
                      <el-radio-button :label="0">{{ $t('browser.replace') }}</el-radio-button>
                      <el-radio-button :label="1">{{ $t('browser.allow') }}</el-radio-button>
                      <el-radio-button :label="2">{{ $t('browser.block') }}</el-radio-button>
                    </el-radio-group>
                  </el-form-item>
                  <el-form-item :label="$t('browser.location')">
                    <el-radio-group v-model="form.location.enable">
                      <el-radio-button label="0">{{ $t('browser.ask') }}</el-radio-button>
                      <el-radio-button label="1">{{ $t('browser.allow') }}</el-radio-button>
                      <el-radio-button label="2">{{ $t('browser.block') }}</el-radio-button>
                    </el-radio-group>
                    <div v-if="form.location.enable != 2">
                      <el-switch
                        v-model="form.location.mode"
                        :active-value="2"
                        :inactive-value="1"
                      />
                      <span style="margin-left: 10px">{{ $t('browser.location_tips') }}</span>
                      <div v-if="form.location.mode == 1">
                        <el-form-item :label="$t('browser.longitude')" label-width="80px">
                          <el-input v-model="form.location.longitude" style="width: 100px" />
                        </el-form-item>
                        <el-form-item :label="$t('browser.latitude')" label-width="80px">
                          <el-input v-model="form.location.latitude" style="width: 100px" />
                        </el-form-item>
                        <el-form-item :label="$t('browser.precision')" label-width="80px">
                          <el-input v-model="form.location.precision" style="width: 100px" />
                        </el-form-item>
                      </div>
                    </div>
                  </el-form-item>
                  <el-form-item :label="$t('browser.screen')">
                    <el-radio-group v-model="form.screen.mode">
                      <el-radio-button :label="0">{{ $t('browser.system_match') }}</el-radio-button>
                      <el-radio-button :label="1">{{ $t('browser.custom') }}</el-radio-button>
                    </el-radio-group>
                    <el-select
                      v-if="form.screen.mode === 1"
                      v-model="form.screen._value"
                      :placeholder="$t('browser.select')"
                      style="margin-left: 10px"
                    >
                      <el-option
                        v-for="(item, i) in resolutionList"
                        :key="i"
                        :value="item"
                        :label="item"
                      />
                    </el-select>
                  </el-form-item>
                  <el-form-item :label="$t('browser.fonts')">
                    <el-radio-group v-model="form.fonts.mode">
                      <el-radio-button :label="0">
                        {{ $t('browser.system_default') }}
                      </el-radio-button>
                      <el-radio-button :label="1">{{ $t('browser.random_match') }}</el-radio-button>
                    </el-radio-group>
                  </el-form-item>
                  <el-form-item :label="$t('browser.canvas')">
                    <el-radio-group v-model="form.canvas.mode">
                      <el-radio-button :label="0">{{ $t('browser.default') }}</el-radio-button>
                      <el-radio-button :label="1">{{ $t('browser.random') }}</el-radio-button>
                    </el-radio-group>
                  </el-form-item>
                  <el-form-item :label="$t('browser.webgl_img')">
                    <el-radio-group v-model="form['webgl-img'].mode">
                      <el-radio-button :label="0">{{ $t('browser.default') }}</el-radio-button>
                      <el-radio-button :label="1">{{ $t('browser.random') }}</el-radio-button>
                    </el-radio-group>
                  </el-form-item>
                  <el-form-item :label="$t('browser.webgl')">
                    <el-radio-group v-model="form.webgl.mode">
                      <el-radio-button :label="0">{{ $t('browser.default') }}</el-radio-button>
                      <el-radio-button :label="1">{{ $t('browser.custom') }}</el-radio-button>
                    </el-radio-group>
                  </el-form-item>
                  <template v-if="form.webgl.mode == 1">
                    <el-form-item :label="$t('browser.webgl_manu')">
                      <el-select v-model="form.webgl.vendor" :placeholder="$t('browser.select')">
                        <el-option v-for="(item, i) in WebGLVendors" :key="i" :value="item" />
                        <!-- <el-option value="Google Inc. (NVIDIA)" /> -->
                      </el-select>
                    </el-form-item>
                    <el-form-item :label="$t('browser.webgl_render')">
                      <el-select
                        v-model="form.webgl.render"
                        :placeholder="$t('browser.select')"
                        style="width: 100%"
                      >
                        <el-option v-for="(item, i) in WebGLRenders" :key="i" :value="item" />
                      </el-select>
                    </el-form-item>
                  </template>
                  <el-form-item :label="$t('browser.audio')">
                    <el-radio-group v-model="form['audio-context'].mode">
                      <el-radio-button :label="0">{{ $t('browser.default') }}</el-radio-button>
                      <el-radio-button :label="1">{{ $t('browser.random') }}</el-radio-button>
                    </el-radio-group>
                  </el-form-item>
                  <!-- <el-form-item :label="$t('browser.media')">
                <el-radio-group v-model="form.media.mode">
                  <el-radio-button :label="0">{{ $t('browser.default') }}</el-radio-button>
                  <el-radio-button :label="1">{{ $t('browser.random') }}</el-radio-button>
                </el-radio-group>
              </el-form-item> -->
                  <el-form-item :label="$t('browser.client_rects')">
                    <el-radio-group v-model="form['client-rects'].mode">
                      <el-radio-button :label="0">{{ $t('browser.default') }}</el-radio-button>
                      <el-radio-button :label="1">{{ $t('browser.random') }}</el-radio-button>
                    </el-radio-group>
                  </el-form-item>
                  <el-form-item :label="$t('browser.speech_voices')">
                    <el-radio-group v-model="form['speech_voices'].mode">
                      <el-radio-button :label="0">{{ $t('browser.default') }}</el-radio-button>
                      <el-radio-button :label="1">{{ $t('browser.random') }}</el-radio-button>
                    </el-radio-group>
                  </el-form-item>
                  <el-form-item :label="$t('browser.cpu')">
                    <el-select v-model="form.cpu.value" style="width: 60px">
                      <el-option :value="2" />
                      <el-option :value="4" />
                      <el-option :value="6" />
                      <el-option :value="8" />
                      <el-option :value="12" />
                    </el-select>
                    &nbsp;
                    <span>{{ $t('browser.cpu_unit') }}</span>
                  </el-form-item>
                  <el-form-item :label="$t('browser.memory')">
                    <el-select v-model="form.memory.value" style="width: 60px">
                      <el-option :value="2" />
                      <el-option :value="4" />
                      <el-option :value="8" />
                      <el-option :value="16" />
                      <el-option :value="32" />
                      <el-option :value="64" />
                    </el-select>
                    &nbsp;
                    <span>GB</span>
                  </el-form-item>
                  <el-form-item :label="$t('browser.device')" style="height: 36px">
                    <el-radio-group v-model="form['device-name'].mode">
                      <el-radio-button :label="0">{{ $t('browser.default') }}</el-radio-button>
                      <el-radio-button :label="1">{{ $t('browser.custom') }}</el-radio-button>
                    </el-radio-group>
                    <div v-if="form['device-name'].mode == 1" style="display: inline-block">
                      <el-input
                        v-model="form['device-name'].value"
                        style="width: 200px; margin-left: 10px"
                      />
                      <el-button type="text" @click="onReRandomComputerName">
                        {{ $t('browser.random_change') }}
                      </el-button>
                    </div>
                  </el-form-item>
                  <el-form-item :label="$t('browser.mac')" style="height: 36px">
                    <el-radio-group v-model="form.mac.mode">
                      <el-radio-button :label="0">{{ $t('browser.default') }}</el-radio-button>
                      <el-radio-button :label="1">{{ $t('browser.custom') }}</el-radio-button>
                    </el-radio-group>
                    <div v-if="form.mac.mode == 1" style="display: inline-block">
                      <el-input v-model="form.mac.value" style="width: 200px; margin-left: 10px" />
                      <el-button type="text" @click="onReRandomAddr">
                        {{ $t('browser.random_change') }}
                      </el-button>
                    </div>
                  </el-form-item>
                  <el-form-item :label="$t('browser.dnt')">
                    <el-switch v-model="form.dnt.value" :active-value="1" :inactive-value="0" />
                  </el-form-item>
                  <el-form-item :label="$t('browser.ssl')">
                    <el-radio-group v-model="form.ssl.mode">
                      <el-radio-button :label="1">{{ $t('browser.enable') }}</el-radio-button>
                      <el-radio-button :label="0">{{ $t('browser.disable') }}</el-radio-button>
                    </el-radio-group>
                  </el-form-item>
                  <el-form-item v-if="form.ssl.mode == 1" :label="$t('browser.ssl_disabled')">
                    <el-checkbox-group v-model="form.ssl.value">
                      <el-checkbox v-for="(val, key) in SSL" :key="key" :label="val">
                        {{ key }}
                      </el-checkbox>
                    </el-checkbox-group>
                  </el-form-item>
                  <el-form-item :label="$t('browser.port_scan')">
                    <el-radio-group v-model="form['port-scan'].mode">
                      <el-radio-button :label="1">{{ $t('browser.enable') }}</el-radio-button>
                      <el-radio-button :label="0">{{ $t('browser.disable') }}</el-radio-button>
                    </el-radio-group>
                  </el-form-item>
                  <el-form-item
                    v-if="form['port-scan'].mode == 1"
                    :label="$t('browser.enable_ports')"
                  >
                    <el-input
                      :value="form['port-scan'].value.join(',')"
                      :placeholder="$t('browser.enable_ports_tips')"
                      @input="value => (form['port-scan'].value = value.split(','))"
                      @change="
                        value =>
                          (form['port-scan'].value = value
                            .split(',')
                            .filter(item => /^\d+$/.test(item)))
                      "
                    />
                  </el-form-item>
                  <el-form-item :label="$t('browser.gpu')">
                    <el-switch v-model="form.gpu.value" :active-value="1" :inactive-value="0" />
                  </el-form-item>
                </div>
              </el-timeline-item>
              <el-timeline-item :hide-timestamp="true" />
            </el-timeline>
          </el-form>
        </div>
        <div class="dialog-footer">
          <el-button size="medium" @click="dialogFormVisible = false">
            {{ $t('browser.cancel') }}
          </el-button>
          <el-button
            type="primary"
            size="medium"
            @click="dialogStatus === 'create' ? onCreateData() : onUpdateData()"
          >
            {{ $t('browser.confirm') }}
          </el-button>
        </div>
      </div>
    </el-drawer>
    <el-dialog
      :visible.sync="dialogCookieFormatVisible"
      :title="$t('browser.cookie.format_title')"
      class="dialog-cookie"
    >
      <el-input v-model="cookieFormat" type="textarea" :rows="19" />
      <span slot="footer" class="dialog-footer">
        <el-tooltip
          v-model="copied"
          :manual="true"
          :hide-after="3000"
          :content="$t('browser.cookie.copied')"
          placement="top"
        >
          <el-button v-clipboard="() => cookieFormat" v-clipboard:success="onCopy" type="primary">
            {{ $t('browser.cookie.copy') }}
          </el-button>
        </el-tooltip>
        <el-button @click="dialogCookieFormatVisible = false">
          {{ $t('browser.cookie.close') }}
        </el-button>
      </span>
    </el-dialog>
    <el-dialog :visible.sync="dialogVisible" title="批量创建">
      <el-form :model="form" label-width="120px">
        <el-form-item label="环境数量">
          <el-input v-model.number="form.numberOfEnvironments" type="number" min="1" />
        </el-form-item>
        <el-form-item label="名称前缀">
          <el-input v-model="form.namePrefix" placeholder="例如：测试环境" style="width: 300px" />
          <span style="margin-left: 10px; color: #909399; font-size: 12px">
            最终名称格式：前缀 + 序号（例如：测试环境 1）
          </span>
        </el-form-item>
        <el-form-item label="备注前缀">
          <el-input
            v-model="form.remarkPrefix"
            placeholder="例如：用于自动化测试"
            style="width: 300px"
          />
        </el-form-item>
        <el-form-item label="起始序号">
          <el-input-number v-model="form.startNumber" :min="1" />
        </el-form-item>
        <el-form-item label="代理类型">
          <el-select v-model="form.proxyType" placeholder="请选择">
            <el-option label="默认" value="默认" />
            <el-option label="不使用代理" value="不使用代理" />
            <el-option label="HTTP" value="HTTP" />
            <el-option label="HTTPS" value="HTTPS" />
            <el-option label="SOCKS5" value="SOCKS5" />
          </el-select>
        </el-form-item>
        <el-form-item label="代理API链接">
          <el-input v-model="form.proxyAPI" placeholder="自动从API提取不同代理" />
        </el-form-item>
      </el-form>
      <div slot="footer" class="dialog-footer">
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleBatchCreate">确认</el-button>
      </div>
    </el-dialog>

    <el-dialog v-model="showSetDialog" title="IP查询API设置" :visible.sync="showSetDialog">
      <el-form :model="form">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="查询渠道">
              <el-select v-model="Channel" placeholder="请选择" @change="onChannelChange">
                <el-option label="ip-api.com (免费)" value="ip-api" />
                <el-option label="ipinfo.io" value="ipinfo" />
                <el-option label="ipapi.co" value="ipapi" />
                <el-option label="ipgeolocation" value="ipgeolocation" />
                <el-option label="VirtualBrowser" value="virtualbrowser" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <div v-if="Channel === 'ip-api'" style="color: #67c23a; font-size: 12px">
              免费，无需密钥，每分钟45次请求限制
            </div>
            <div v-else-if="Channel === 'ipinfo'" style="font-size: 12px">
              点击
              <a href="https://ipinfo.io" target="_blank" style="color: #42b983">官网</a>
              获取免费 Token
            </div>
            <div v-else-if="Channel === 'ipapi'" style="font-size: 12px">
              点击
              <a href="https://ipapi.co" target="_blank" style="color: #42b983">官网</a>
              获取 API Key
            </div>
            <div v-else-if="Channel === 'ipgeolocation'" style="font-size: 12px">
              点击
              <a href="https://ipgeolocation.io" target="_blank" style="color: #42b983">官网</a>
              获取 API Key
            </div>
            <div v-else-if="Channel === 'virtualbrowser'" style="font-size: 12px">
              点击
              <a href="https://virtualbrowser.cc" target="_blank" style="color: #42b983">官网</a>
              获取 API Key
            </div>
          </el-col>
        </el-row>
        <el-input
          v-model="apiLink"
          placeholder="API链接将根据渠道自动填充，也可手动修改"
          style="margin-top: 10px"
        />
        <div style="font-size: 12px; color: #909399; margin-top: 8px">
          <div v-if="Channel === 'ip-api'">默认链接: http://ip-api.com/json</div>
          <div v-else-if="Channel === 'ipinfo'">格式: https://ipinfo.io/json?token=YOUR_TOKEN</div>
          <div v-else-if="Channel === 'ipapi'">格式: https://ipapi.co/YOUR_KEY/json/</div>
          <div v-else-if="Channel === 'ipgeolocation'">
            格式: https://api.ipgeolocation.io/ipgeo?apiKey=YOUR_KEY
          </div>
          <div v-else-if="Channel === 'virtualbrowser'">
            格式: https://api.virtualbrowser.cc/ipgeo?key=YOUR_KEY
          </div>
        </div>
      </el-form>
      <span slot="footer" class="dialog-footer">
        <el-button @click="showSetDialog = false">取消</el-button>
        <el-button type="primary" @click="saveSettings">保存</el-button>
      </span>
    </el-dialog>

    <el-dialog :title="'编辑分组'" :visible.sync="dialogBatchSetGroupVisible" width="30%">
      <el-form>
        <el-form-item :label="$t('browser.group')">
          <el-select v-model="selectedGroup" :placeholder="$t('browser.select')">
            <el-option v-for="item in GroupList" :key="item.id" :value="item.name" />
          </el-select>
        </el-form-item>
      </el-form>
      <span slot="footer" class="dialog-footer">
        <el-button @click="dialogBatchSetGroupVisible = false">取消</el-button>
        <el-button type="primary" @click="applyBatchSetGroup">保存</el-button>
      </span>
    </el-dialog>

    <el-dialog
      :title="currentTagRow ? $t('browser.editTags') : $t('browser.batchTags')"
      :visible.sync="dialogTagsVisible"
      width="40%"
    >
      <el-form>
        <el-form-item :label="$t('browser.tags')">
          <el-select
            v-model="tagForm.tags"
            multiple
            filterable
            allow-create
            default-first-option
            :placeholder="$t('browser.tagPlaceholder')"
            style="width: 100%"
          >
            <el-option v-for="tag in allTags" :key="tag" :label="tag" :value="tag" />
          </el-select>
        </el-form-item>
      </el-form>
      <span slot="footer" class="dialog-footer">
        <el-button @click="dialogTagsVisible = false">{{ $t('browser.cancel') }}</el-button>
        <el-button type="primary" @click="currentTagRow ? saveTags() : applyBatchSetTags()">
          {{ $t('browser.confirm') }}
        </el-button>
      </span>
    </el-dialog>
  </div>
</template>

<script>
import {
  getBrowserList,
  getGlobalData,
  setGlobalData,
  addBrowser,
  updateBrowser,
  deleteBrowser,
  chromeSend,
  chromeSendTimeout,
  updateRuningState,
  getGroupList
} from '@/api/native'
import { saveAs } from 'file-saver'
import waves from '@/directive/waves' // waves directive
import random from 'random'
import {
  // parseTime,
  genRandomMacAddr,
  genRandomComputerName,
  genRandomSpeechVoices,
  getRandomCpuCore,
  getRandomMemorySize,
  genUserAgent,
  getUaFullVersion,
  loadScript
} from '@/utils'
// import Pagination from '@/components/Pagination' // secondary package based on el-pagination
import TimeZones from '@/utils/timezones.json'
import Languages from '@/utils/languages.json'
import SSL from '@/utils/ssl.json'
import Versions from '@/utils/versions.json'
import uaFullVersions from '@/utils/ua-full-versions.json'
import WebGLRenders from '@/utils/webgl.json'
import { getFontList } from '@/utils/fonts'
import { compareVersions } from 'compare-versions'
import { fetchIpGeoData, generateBrowserConfig } from '@/utils/ipApiAdapter'

let IPGeo = {}
let fontList = []
let osVer = '10.0'
let chromeVer = ''
// const sslList = ['0xc02c', '0xa02c', '0xb02c', '0xd02c', '0xe02c', '0xf02c']
let tooltipTimer
const chromiumCoreVer =
  Number(navigator.userAgentData.brands.find(item => item.brand === 'Chromium')?.version) || 117
const coreVersions = Array.from(new Set(Versions.map(item => Number(item.split('.')[0]))))
for (let i = Math.max(...coreVersions) + 1; i <= chromiumCoreVer; i++) {
  coreVersions.unshift(i)
  Versions.unshift(`${i}.0.0.0`)
}

export default {
  name: 'ComplexTable',
  components: {
    // Pagination
  },
  directives: { waves },
  filters: {
    statusFilter(status) {
      const statusMap = {
        published: 'success',
        draft: 'info',
        deleted: 'danger'
      }
      return statusMap[status]
    }
  },
  data() {
    const validateCookie = (rule, value, callback) => {
      if (this.form.cookie.mode === 0) {
        this.form.cookie.value = ''
        callback()
        return
      }

      let json
      try {
        // eslint-disable-next-line no-eval
        json = eval(`(${value})`)
      } catch {
        callback(new Error(this.$t('browser.cookie.format_error')))
        return
      }

      if (Object.prototype.toString.call(json) !== '[object Array]') {
        callback(new Error(this.$t('browser.cookie.format_error')))
        return
      }

      const setDefaultValue = (obj, key, value) => {
        if (obj[key] === undefined) {
          obj[key] = value
        }
      }

      json = json.map(item => {
        const cookie = {}
        Object.keys(item).forEach(key => {
          let newKey = key.substring(0, 1).toLowerCase() + key.substring(1)
          if (newKey === 'samesite') {
            newKey = 'sameSite'
          }
          cookie[newKey] = item[key]
        })

        setDefaultValue(cookie, 'sameSite', '')
        setDefaultValue(cookie, 'session', false)
        setDefaultValue(cookie, 'secure', false)
        setDefaultValue(cookie, 'httpOnly', false)

        return cookie
      })

      const checkNameValue = json.every(item => {
        return item.name && item.value && item.domain
      })

      if (!checkNameValue) {
        callback(new Error(this.$t('browser.cookie.format_error')))
        return
      }

      // this.form.cookie.mode = 1
      this.form.cookie.value = json
      callback()
    }
    return {
      currentEditingRow: null,
      showSetDialog: false,
      showSetApiDialog: false,
      dialogBatchSetGroupVisible: false,
      dialogTagsVisible: false,
      selectedGroup: '默认分组',
      apiLink: 'http://ip-api.com/json',
      Channel: 'ip-api',
      saveApi: false,
      selectedRows: [],
      chromeVer: '',
      tableKey: 0,
      sourceList: [],
      list: null,
      listLoading: true,
      listQuery: {
        page: 1,
        limit: 5,
        title: undefined,
        group: '',
        tags: []
      },
      dialogFormVisible: false,
      dialogVisible: false,
      dialogStatus: '',
      dialogCookieFormatVisible: false,
      textMap: {
        update: this.$t('browser.edit'),
        create: this.$t('browser.add')
      },
      tagForm: {
        tags: []
      },
      currentTagRow: null,
      form: {
        numberOfEnvironments: 1,
        namePrefix: '',
        remarkPrefix: '',
        startNumber: 1,
        proxyType: '默认',
        proxyAPI: '',
        proxy: {},
        cookie: {},
        homepage: {},
        ua: {},
        'ua-full-version': {},
        'sec-ch-ua': {},
        'ua-language': {},
        'time-zone': {},
        location: {},
        screen: {},
        fonts: {},
        canvas: {},
        'webgl-img': {},
        webgl: {},
        'audio-context': {},
        media: {},
        'client-rects': {},
        speech_voices: {},
        ssl: {},
        cpu: {},
        memory: {},
        'device-name': {},
        mac: {},
        dnt: {},
        'port-scan': {},
        gpu: {},
        webrtc: {}
      },
      rules: {
        // name: [{ required: true, message: this.$t('browser.required'), trigger: 'change' }],
        'proxy.value': [
          {
            required: true,
            message: this.$t('browser.required'),
            trigger: 'change'
          }
        ],
        'proxy.host': [
          {
            required: true,
            message: this.$t('browser.required'),
            trigger: 'change'
          }
        ],
        'cookie.jsonStr': [{ validator: validateCookie, trigger: 'blur' }]
      },
      downloadLoading: false,
      platforms: ['Win 7', 'Win 8', 'Win 10', 'Win 11'],
      WebGLVendors: Array.from(
        new Set(
          WebGLRenders.map(item => {
            const match = item.match(/\((.+?),/)
            if (match && match[1]) {
              return `Google Inc. (${match[1]})`
            }
          })
        )
      ),
      WebGLRenders: WebGLRenders,
      resolutionList: [
        '800 x 600',
        '1024 x 768',
        '1280 x 720',
        '1280 x 800',
        '1280 x 960',
        '1280 x 1024',
        '1360 x 768',
        '1400 x 900',
        '1400 x 1050',
        '1600 x 900',
        '1600 x 1200',
        '1920 x 1080',
        '1920 x 1200',
        '2048 x 1152',
        '2304 x 1440',
        '2560 x 1440',
        '2560 x 1600',
        '2880 x 1800',
        '5120 x 2880'
      ],
      TimeZones,
      Languages,
      SSL,
      Versions: coreVersions,
      cookieFormat: `[{
        "name": "cookie1",
        "value": "1",
        "domain": ".xxx.com",
        "path": "/",
        "session": false,
        "httpOnly": false,
        "secure": false,
        "sameSite": "None"
      }, {
        "name": "cookie2",
        "value": "2",
        "domain": ".xxx.com",
        "path": "/",
        "session": false,
        "httpOnly": false,
        "secure": false,
        "sameSite": "None"
      }]`,
      copied: false,
      checkProxyState: {
        checking: false
      },
      GroupList: []
    }
  },
  computed: {
    language() {
      return this.$store.getters.language
    },
    allTags() {
      const tags = new Set()
      ;(this.sourceList || []).forEach(item => {
        if (item.tags && Array.isArray(item.tags)) {
          item.tags.forEach(tag => tags.add(tag))
        }
      })
      return Array.from(tags)
    }
  },
  watch: {
    'form.proxy.host': function (newVal, oldVal) {
      const parts = newVal.split(':')
      if (parts.length === 4) {
        this.form.proxy.host = parts[0]
        this.form.proxy.port = parts[1]
        this.form.proxy.user = parts[2]
        this.form.proxy.pass = parts[3]
      } else if (parts.length === 2) {
        this.form.proxy.host = parts[0]
        this.form.proxy.port = parts[1]
        this.form.proxy.user = ''
        this.form.proxy.pass = ''
      }
    },
    'form.screen._value'(val) {
      const wh = val.split('x')
      this.form.screen.width = parseInt(wh[0])
      this.form.screen.height = parseInt(wh[1])
    },
    'form.chrome_version'(val) {
      if (val === '默认') {
        val = chromiumCoreVer
        this.form.ua.mode = 0
      } else {
        this.form.ua.mode = 1
      }
      this.form['sec-ch-ua'].value.forEach(item => {
        if (item.brand === 'Chromium') {
          item.version = val
        }
      })

      const curVers = Versions.filter(item => Number(item.split('.')[0]) === val)
      chromeVer = curVers[random.int(0, curVers.length - 1)]
      this.form.ua.value = genUserAgent(osVer, chromeVer)
      this.form['ua-full-version'].value = getUaFullVersion(uaFullVersions, chromeVer)
    },
    'form.os'(val) {
      switch (val) {
        case 'Win 7':
          osVer = '6.1'
          break
        case 'Win 8':
          osVer = '6.2'
          break
        case 'Win 10':
        case 'Win 11':
          osVer = '10.0'
          break
      }

      this.form.ua.value = genUserAgent(osVer, chromeVer)

      let vers = Array.from(new Set(Versions.map(item => Number(item.split('.')[0]))))
      if (val === 'Win 7' || val === 'Win 8') {
        vers = vers.filter(item => item <= 109)
      }
      vers.unshift('默认')
      this.Versions = vers
      if (!vers.includes(this.form.chrome_version)) {
        this.form.chrome_version = vers[0]
      }
    },
    'form.webgl.vendor': {
      handler(val) {
        if (!val) return
        const vendor = val.match(/\((.+?)\)/)[1]
        this.WebGLRenders = WebGLRenders.filter(item => item.match(/\((.+?),/)[1] === vendor)
        if (!this.WebGLRenders.includes(this.form.webgl.render)) {
          this.form.webgl.render =
            this.WebGLRenders.length > 0
              ? this.WebGLRenders[random.int(0, this.WebGLRenders.length - 1)]
              : ''
        }
      },
      immediate: true,
      deep: true
    }
  },
  beforeCreate() {
    window._updateState = runingIds => {
      const runningIdSet = new Set((runingIds || []).map(id => String(id)))

      const applyRunningState = list => {
        return (list || []).map(item => {
          const wasRunning = item.isRunning
          item.isRunning = runningIdSet.has(String(item.id))

          // 如果状态从加载中变为运行或停止，重置加载状态
          if (item.runLoading && (item.isRunning || wasRunning !== item.isRunning)) {
            item.runLoading = false
          }

          return item
        })
      }

      this.sourceList = applyRunningState(this.sourceList)
      this.list = applyRunningState(this.list)
    }
  },
  async created() {
    await this.getList()

    this.$watch(
      () => this.form['ua-language'].language,
      val => {
        this.form['ua-language'].value = [val, val.split('-')[0]].join(',')
        this.form['time-zone'].locale = val
      }
    )
    const store = await getGlobalData()
    const storedApiLink = store.apiLink
    if (storedApiLink) {
      this.apiLink = storedApiLink
      this.Channel = store.Channel || 'ip-api'
    } else {
      // 使用默认值
      this.apiLink = 'http://ip-api.com/json'
      this.Channel = 'ip-api'
    }

    // 使用适配器获取 IP 地理位置数据
    if (this.apiLink) {
      try {
        const isIpGeoApi =
          this.apiLink.includes('ip-api.com') ||
          this.apiLink.includes('ipinfo.io') ||
          this.apiLink.includes('ipapi.co') ||
          this.apiLink.includes('ipgeolocation')

        if (isIpGeoApi) {
          // 使用适配器获取标准化的地理位置数据
          const geoData = await fetchIpGeoData(this.apiLink)
          IPGeo = generateBrowserConfig(geoData)
          console.log('IP 地理位置数据已加载:', geoData)
        } else {
          // 原有的自定义 API 处理
          const res = await fetch(this.apiLink)
            .then(req => req.json())
            .catch(console.warn)
          if (res) {
            IPGeo = res
          }
        }
      } catch (error) {
        console.warn('获取 IP 地理位置失败:', error)
        // 使用默认空数据
        IPGeo = {}
      }
    }

    fontList = getFontList()

    const ver = await chromeSend('getBrowserVersion').catch(err => {
      console.warn(err)
      return '1.116.0.0'
    })

    window._callback = data => {
      if (sessionStorage.getItem('check_update_showed') === '1') {
        return
      }
      if (compareVersions(ver, data.ver) >= 0) {
        return
      }

      sessionStorage.setItem('check_update_showed', 1)
      const update = data.update.map(item => `<li>${item}</li>`).join('')
      this.$alert(
        `<div>版本：<b>${data.ver}</b></div>
         <div class="update">更新：<ol>${update}</ol></div>`,
        '发现新版本',
        {
          dangerouslyUseHTMLString: true,
          showCancelButton: true,
          confirmButtonText: '更新'
        }
      )
        .then(() => {
          window.open(data.url)
        })
        .catch(() => {})
    }
    loadScript(
      `http://api.virtualbrowser.cc/update/check_update.js?c=${
        (this.list || []).length
      }&v=${ver}&t=${Date.now()}`
    )
  },
  async mounted() {
    this.checkApiLinkSet()
    this.GroupList = await getGroupList()
    this.GroupList.unshift({
      id: 0,
      name: this.$t('group.default')
    })
  },
  methods: {
    async getList() {
      this.listLoading = true
      this.sourceList = await getBrowserList()
      this.list = [...this.sourceList]
      this.GlobalData = await getGlobalData()
      this.apiLink = this.GlobalData.apiLink || ''
      this.Channel = this.GlobalData.Channel || ''
      await this.processUpdateData()
      await updateRuningState()
      this.searchList()
      this.listLoading = false
    },
    searchList() {
      const source = this.sourceList || []
      const filteredList = source.filter(item => {
        // 名称过滤
        if (this.listQuery.title) {
          const keyword = this.listQuery.title.toLowerCase()
          const itemName = String(item.name || '').toLowerCase()
          const itemId = String(item.id || '').toLowerCase()
          if (!itemName.includes(keyword) && !itemId.includes(keyword)) {
            return false
          }
        }
        // 分组过滤
        if (this.listQuery.group && item.group !== this.listQuery.group) {
          return false
        }
        // 标签过滤（OR逻辑：只要包含任一选中标签即可）
        if (this.listQuery.tags && this.listQuery.tags.length > 0) {
          if (!item.tags || !Array.isArray(item.tags)) {
            return false
          }
          const hasAnyTag = this.listQuery.tags.some(tag => item.tags.includes(tag))
          if (!hasAnyTag) {
            return false
          }
        }
        return true
      })
      this.list = filteredList
    },
    handleFilter() {
      this.listQuery.page = 1
      this.searchList()
    },
    handleSelectionChange(selection) {
      this.selectedRows = selection
    },
    handleBatchStart() {
      if (this.selectedRows.length === 0) {
        this.$notify({
          title: '错误提示',
          message: '至少需要勾选一个环境',
          type: 'warning',
          duration: 2000
        })
        return
      }
      for (let i = 0; i < this.selectedRows.length; i++) {
        const row = this.selectedRows[i]
        this.launchEnvironment(row, i * 2000)
      }
    },
    handleBatchStop() {
      if (this.selectedRows.length === 0) {
        this.$notify({
          title: '错误提示',
          message: '至少需要勾选一个环境',
          type: 'warning',
          duration: 2000
        })
        return
      }
      // 只停止运行中的浏览器
      const runningBrowsers = this.selectedRows.filter(row => row.isRunning)
      if (runningBrowsers.length === 0) {
        this.$notify({
          title: '提示',
          message: '没有运行中的浏览器需要停止',
          type: 'info',
          duration: 2000
        })
        return
      }
      runningBrowsers.forEach(row => {
        this.handleStop(row)
      })
    },
    launchEnvironment(row, delay) {
      setTimeout(() => {
        this.handleLaunch(row)
      }, delay)
    },
    getDefaultForm() {
      const currentZone = this.getCurrentTimeZone()
      // const defaultLanguage = IPGeo.languages?.split(',')[0] || ''
      const cpuCore = getRandomCpuCore()
      const memorySize = getRandomMemorySize(cpuCore)

      return {
        id: undefined,
        name: '',
        group: this.$t('group.default'),
        os: 'Win 11',
        chrome_version: '默认',
        proxy: {
          mode: 0,
          value: '',
          protocol: 'HTTP',
          host: '',
          port: '',
          user: '',
          pass: '',
          API: ''
        },
        cookie: {
          mode: 0,
          value: ''
        },
        homepage: {
          mode: 0,
          value: ''
        },
        ua: {
          mode: 1,
          value: genUserAgent(osVer, chromeVer)
        },
        'ua-full-version': {
          mode: 1,
          value: getUaFullVersion(uaFullVersions, chromeVer)
        },
        'sec-ch-ua': {
          mode: 0,
          value: [
            { brand: 'Chromium', version: chromiumCoreVer },
            { brand: 'Not=A?Brand', version: '99' }
          ]
        },
        'ua-language': {
          mode: 2,
          language: IPGeo['ua-language']?.value || IPGeo.languages?.split(',')[0] || '',
          value: IPGeo['ua-language']?.value || IPGeo.languages || ''
        },
        'time-zone': {
          mode: 2,
          zone: IPGeo['time-zone']?.zone || this.getZone(currentZone?.offset || 0),
          utc: IPGeo['time-zone']?.utc || currentZone?.utc[0] || '',
          locale: IPGeo['time-zone']?.locale || IPGeo.languages?.split(',')[0] || '',
          name: IPGeo['time-zone']?.name || currentZone?.text || '',
          value: IPGeo['time-zone']?.zone
            ? parseFloat(IPGeo['time-zone'].zone.replace('UTC', '').replace(':', '.'))
            : currentZone?.offset || 0
        },
        webrtc: {
          mode: 0
        },
        location: {
          mode: 2,
          enable: 1,
          longitude: IPGeo.location?.longitude || IPGeo.longitude,
          latitude: IPGeo.location?.latitude || IPGeo.latitude,
          precision: IPGeo.location?.precision || random.int(10, 5000)
        },
        screen: {
          mode: 0,
          width: screen.width,
          height: screen.height,
          _value: `${screen.width} x ${screen.height}`
        },
        fonts: {
          mode: 1,
          value: fontList.sort(() => Math.random() - 0.5).slice(0, random.int(1, 10))
        },
        canvas: {
          mode: 1,
          r: random.int(-10, 10),
          g: random.int(-10, 10),
          b: random.int(-10, 10),
          a: random.int(-10, 10)
        },
        'webgl-img': {
          mode: 1,
          r: random.int(-10, 10),
          g: random.int(-10, 10),
          b: random.int(-10, 10),
          a: random.int(-10, 10)
        },
        webgl: {
          mode: 1,
          vendor: this.WebGLVendors[random.int(0, this.WebGLVendors.length - 1)]
          // render: this.WebGLRenders[random.int(0, this.WebGLRenders.length - 1)],
        },
        'audio-context': {
          mode: 1,
          channel: random.float(0, 0.0000001),
          analyer: random.float(0, 0.1)
        },
        media: { mode: 1 },
        'client-rects': {
          mode: 1,
          width: random.float(-1, 1),
          height: random.float(-1, 1)
        },
        speech_voices: {
          mode: 1,
          value: genRandomSpeechVoices()
        },
        ssl: {
          mode: 0,
          value: []
        },
        cpu: { mode: 1, value: cpuCore },
        memory: { mode: 1, value: memorySize },
        'device-name': { mode: 1, value: genRandomComputerName() },
        mac: { mode: 1, value: genRandomMacAddr() },
        dnt: { mode: 1, value: 0 },
        'port-scan': { mode: 1, value: [] },
        gpu: { mode: 1, value: 1 },
        window_title: {
          mode: 0,
          value: ''
        },
        remark: '',
        debug_port: null
      }
    },
    getCurrentTimeZone() {
      if (!this.cachedTimeZone) {
        const timezoneOffset = new Date().getTimezoneOffset() / -60
        this.cachedTimeZone = TimeZones.find(item => item.offset === timezoneOffset)
      }
      return this.cachedTimeZone
    },
    resetForm() {
      this.$nextTick(() => {
        this.form = this.getDefaultForm()
      })
    },
    RandomFingerprint() {
      const { id, name, timestamp, proxy } = this.form
      this.$nextTick(() => {
        this.form = {
          ...this.getDefaultForm(),
          id,
          name,
          timestamp,
          proxy: { ...proxy }
        }
      })
    },
    handleCreate() {
      this.resetForm()
      this.dialogStatus = 'create'
      this.dialogFormVisible = true
      this.$nextTick(() => {
        this.$refs['dataForm'].clearValidate()
      })
    },
    onCreateData() {
      this.$refs['dataForm'].validate(async (valid, result) => {
        if (valid) {
          this.form.timestamp = Date.now()
          this.preProcessData(this.form)
          await addBrowser(this.form, this.$t('browser.browser'))

          this.getList()
          this.dialogFormVisible = false
          this.$notify({
            title: this.$t('browser.success'),
            message: this.$t('browser.create') + this.$t('browser.success'),
            type: 'success',
            duration: 2000
          })
        } else {
          const arr = Object.values(result)
            .map(item => this.$t('browser.' + item[0].field) + item[0].message)
            .slice(0, 1)

          this.$message({
            type: 'error',
            dangerouslyUseHTMLString: true,
            message: '<p>' + arr.join('</p><p>') + '</p>'
          })
        }
      })
    },
    async processUpdateData() {
      for (let i = 0; i < this.sourceList.length; i++) {
        const item = this.sourceList[i]
        if (this.processData(item)) {
          await updateBrowser(item)
        }
      }
    },
    processData(data) {
      let changed = false

      const { proxy, ua, chrome_version } = data
      if (proxy.mode === 2) {
        let oldProxy = proxy.value
        if (oldProxy && !proxy.host) {
          oldProxy = oldProxy.replace(/#.*/, '')
          let protocol
          if (oldProxy.includes('@socks')) {
            protocol = 'SOCKS5'
            oldProxy = 'http://' + oldProxy.replace('@socks', '')
          } else if (!oldProxy.includes('://')) {
            oldProxy = 'http://' + oldProxy
          }
          try {
            const proxyURL = new URL(oldProxy)
            proxy.protocol = protocol || proxyURL.protocol.replace(':', '').toUpperCase()
            proxy.host = proxyURL.hostname
            proxy.port = proxyURL.port
            proxy.user = proxyURL.username
            proxy.pass = proxyURL.password

            changed = true
          } catch (ex) {
            console.warn('Parse Proxy Error: ', ex)
          }

          // proxy.value = ''
        }
      }
      if (ua.mode === 1) {
        if (ua.value.includes("'")) {
          ua.value = ua.value.replace(/^'|'$/g, '')
          changed = true
        }
      }
      if (typeof data['sec-ch-ua'].value === 'string') {
        data['sec-ch-ua'].value = [
          { brand: 'Chromium', version: chromiumCoreVer },
          { brand: 'Not=A?Brand', version: '99' }
        ]
        changed = true
      }
      if (data['ua-full-version'] === undefined) {
        const chrome_version_num = chrome_version === '默认' ? chromiumCoreVer : chrome_version
        const chromeVer = Versions.find(item => Number(item.split('.')[0]) === chrome_version_num)
        data['ua-full-version'] = {
          mode: 1,
          value: getUaFullVersion(uaFullVersions, chromeVer)
        }
        changed = true
      }

      return changed
    },
    preProcessData(data) {
      const { proxy } = data
      if (proxy.mode === 2) {
        let url = proxy.protocol.toLowerCase() + '://'
        if (proxy.user) {
          url += proxy.user + ':' + proxy.pass + '@'
        }
        url += proxy.host
        if (proxy.port) {
          url += ':' + proxy.port
        }

        proxy.url = url
      }

      data['sec-ch-ua'].value = data['sec-ch-ua'].value.filter(item => {
        return item.brand && item.version
      })
    },
    handleUpdate(row) {
      this.resetForm()
      this.dialogStatus = 'update'
      this.dialogFormVisible = true
      this.$nextTick(() => {
        this.form = Object.assign(this.form, row) // copy obj
        const cookie = this.form.cookie.value
        if (cookie && typeof cookie === 'object') {
          this.form.cookie.value = JSON.stringify(this.form.cookie.value)
        }
        this.form.timestamp = new Date(this.form.timestamp)
        this.$refs['dataForm'].clearValidate()
      })
    },
    onUpdateData() {
      this.$refs['dataForm'].validate(async (valid, result) => {
        if (valid) {
          const tempData = Object.assign({}, this.form)
          console.log('submit', tempData)
          tempData.timestamp = +new Date(tempData.timestamp) // change Thu Nov 30 2017 16:41:05 GMT+0800 (CST) to 1512031311464
          this.preProcessData(tempData)
          await updateBrowser(tempData)
          this.getList()
          this.dialogFormVisible = false
          this.$notify({
            title: this.$t('browser.success'),
            message: this.$t('browser.update') + this.$t('browser.success'),
            type: 'success',
            duration: 2000
          })
        } else {
          const arr = Object.values(result)
            .map(item => this.$t('browser.' + item[0].field) + item[0].message)
            .slice(0, 1)

          this.$message({
            type: 'error',
            dangerouslyUseHTMLString: true,
            message: '<p>' + arr.join('</p><p>') + '</p>'
          })
        }
      })
    },
    handleDelete(row, index) {
      this.$confirm(this.$t('browser.delete_confirm').replace('${name}', row.name))
        .then(async () => {
          await deleteBrowser(row.id)
          this.getList()
          this.$notify({
            title: this.$t('browser.success'),
            message: this.$t('browser.delete') + this.$t('browser.success'),
            type: 'success',
            duration: 2000
          })
        })
        .catch(() => {})
    },
    async handleLaunch(row) {
      row.runLoading = true
      try {
        // 如果配置了代理API，先获取代理
        if (row.proxy && row.proxy.API) {
          await this.GetAPIProxy(row)
        }

        // 调用 Launcher API 启动浏览器
        const result = await chromeSend('launchBrowser', row.id.toString())
        console.log('浏览器启动成功:', result)

        // 保存调试端口
        if (result && result.data && result.data.debug_port) {
          row.debug_port = result.data.debug_port
        }

        // 同步最新运行状态
        await updateRuningState()

        this.$notify({
          title: '启动成功',
          message: `浏览器 "${row.name}" 已启动 (端口: ${row.debug_port || '未知'})`,
          type: 'success',
          duration: 2000
        })
      } catch (error) {
        console.error('启动浏览器失败:', error)
        this.$notify({
          title: '启动失败',
          message: error.message || '启动浏览器时发生错误',
          type: 'error',
          duration: 3000
        })
      } finally {
        // 无论成功失败，都要关闭加载状态
        row.runLoading = false
      }
    },
    async handleStop(row) {
      row.stopLoading = true
      try {
        // 调用 Launcher API 停止浏览器
        const result = await chromeSend('stopBrowser', row.id.toString())
        console.log('浏览器停止成功:', result)

        // 同步最新运行状态
        await updateRuningState()

        this.$notify({
          title: '停止成功',
          message: `浏览器 "${row.name}" 已停止`,
          type: 'success',
          duration: 2000
        })
      } catch (error) {
        console.error('停止浏览器失败:', error)
        this.$notify({
          title: '停止失败',
          message: error.message || '停止浏览器时发生错误',
          type: 'error',
          duration: 3000
        })
      } finally {
        row.stopLoading = false
      }
    },
    onReRandomComputerName() {
      this.form['device-name'].value = genRandomComputerName()
    },
    onReRandomAddr() {
      this.form.mac.value = genRandomMacAddr()
    },
    getZone(offset) {
      const sign = offset > 0 ? '+' : '-'
      const hours = Math.floor(Math.abs(offset))
      const decimal = Math.abs(offset) - hours
      const minutes = Math.round(decimal * 60)
      const paddedMinutes = minutes < 10 ? '0' + minutes : minutes.toString()
      return `UTC${sign}${hours}:${paddedMinutes}`
    },
    onCopy() {
      this.copied = true
      clearTimeout(tooltipTimer)
      tooltipTimer = setTimeout(() => {
        this.copied = false
      }, 3000)
    },
    onImport({ raw: file }) {
      const reader = new FileReader()
      reader.onload = async e => {
        const jsonStr = e.target.result

        let json
        try {
          json = JSON.parse(jsonStr)
          for (let i = 0; i < json.length; i++) {
            await addBrowser(json[i])
          }

          this.getList()
          this.$notify({
            title: this.$t('browser.success'),
            message: `导入${json.length}条数据`,
            type: 'success',
            duration: 3000
          })
        } catch (ex) {
          this.$notify({
            title: '导入失败',
            message: `${ex.message}`,
            type: 'error',
            duration: 3000
          })
        }
      }
      reader.readAsText(file)
    },
    onExport() {
      if (this.selectedRows.length === 0) {
        this.$notify({
          title: '错误提示',
          message: '至少需要勾选一个环境',
          type: 'warning',
          duration: 2000
        })
        return
      }
      var currentDate = new Date().toISOString().replace(/[-:]/g, '')
      var fileName = 'Virtual-Browser_' + currentDate + '.json'
      var blob = new Blob([JSON.stringify(this.selectedRows, null, 2)], {
        type: 'application/json;charset=utf-8'
      })
      saveAs(blob, fileName)
    },
    async checkProxy() {
      this.checkProxyState.checking = true
      this.preProcessData(this.form)
      let timeout = false
      const ret = await chromeSendTimeout('checkProxy', 10 * 1000, this.form.proxy.url).catch(
        err => {
          timeout = err === 'timeout'
        }
      )
      this.$alert(
        `<p>代理：${this.form.proxy.url}</p>
        <p style="color:${ret ? '#67C23A' : '#F56C6C'}">检测${
          ret ? '成功' : timeout ? '超时' : '失败'
        }</p>`,
        '代理检测',
        {
          type: ret ? 'success' : 'error',
          dangerouslyUseHTMLString: true
        }
      )
      this.checkProxyState.checking = false
    },
    setAPI(data) {
      this.$set(this.form.proxy, 'API', data)
    },
    async fetchAndParseAPI(apiData) {
      // 判断是否为 IP 地理位置 API（如 ip-api.com、ipinfo.io 等）
      const isIpGeoApi =
        apiData.includes('ip-api.com') ||
        apiData.includes('ipinfo.io') ||
        apiData.includes('ipapi.co') ||
        apiData.includes('ipgeolocation')

      if (isIpGeoApi) {
        // 使用适配器获取 IP 地理位置数据
        try {
          const geoData = await fetchIpGeoData(apiData)

          // 检查 API 限制错误
          if (geoData._raw) {
            const raw = geoData._raw
            if (raw.status === 'fail' || raw.message?.includes('limit')) {
              this.$notify({
                title: '错误提示',
                message: raw.message || 'API 请求受限，请检查 API Key 或使用其他服务',
                type: 'warning',
                duration: 3000
              })
              throw new Error('API 限制: ' + (raw.message || '未知错误'))
            }
          }

          // 存储地理位置数据供后续使用
          IPGeo = generateBrowserConfig(geoData)

          // 返回包含 IP 的数据（代理 API 格式兼容）
          return {
            ip: geoData.ip,
            country: geoData.country_name,
            country_code: geoData.country_code2,
            city: geoData.city,
            timezone: geoData.time_zone?.name,
            // 标记为 IP 地理位置 API 数据
            _isIpGeoData: true,
            _geoData: geoData
          }
        } catch (error) {
          console.error('IP Geo API Error:', error)
          this.$notify({
            title: '错误提示',
            message: 'IP 地理位置 API 请求失败: ' + error.message,
            type: 'warning',
            duration: 3000
          })
          throw error
        }
      }

      // 原有的代理 API 处理逻辑
      const response = await fetch(apiData)
      if (!response.ok) {
        this.$notify({
          title: '错误提示',
          message: '响应错误，请检查API接口有效性',
          type: 'warning',
          duration: 2000
        })
        throw new Error(`网络响应不是 ok，状态码为：${response.status}`)
      }

      let data
      const clonedResponse = response.clone()
      try {
        data = await response.json()
        // 处理 JSON 格式的代理数据，支持多种字段名
        if (data.ip || data.host) {
          data.ip = data.ip || data.host
          data.port = data.port || data.port_number || ''
          data.user = data.user || data.username || ''
          data.pass = data.pass || data.password || ''
        }
      } catch (jsonError) {
        const text = await clonedResponse.text()
        const parts = text.split(':')
        switch (parts.length) {
          case 4:
            data = { user: parts[0] || '', pass: parts[1] || '', ip: parts[2], port: parts[3] }
            break
          case 2:
            data = { ip: parts[0], port: parts[1], user: '', pass: '' }
            break
          default:
            this.$notify({
              title: '错误提示',
              message:
                '响应格式既不是有效的JSON格式也不是有效的[ip:端口]或[用户名:密码:IP:端口]格式',
              type: 'warning',
              duration: 2000
            })
            throw new Error(
              '响应格式既不是有效的 JSON 也不是有效的 ip:port 或 用户名:密码:IP:端口 格式'
            )
        }
      }

      if (!data || !data.ip || !data.port) {
        this.$notify({
          title: '错误提示',
          message: '响应不包含ip或端口',
          type: 'warning',
          duration: 2000
        })
        throw new Error('API 响应不包含 ip 或 port')
      }

      // 确保端口号是字符串类型（避免数字类型问题）
      data.port = String(data.port)

      console.log('[DEBUG] 代理API返回数据:', data)
      return data
    },

    updateProxyData(proxyData, data) {
      // 如果是 IP 地理位置 API 数据，不更新代理设置，而是更新地理位置设置
      if (data._isIpGeoData) {
        // 地理位置数据已通过 IPGeo 变量存储
        console.log('IP 地理位置数据已获取:', data._geoData)
        return
      }

      // 原有的代理 API 数据处理
      proxyData.host = data.ip
      proxyData.port = data.port
      proxyData.user = data.user || ''
      proxyData.pass = data.pass || ''
    },

    async checkAPIProxy() {
      try {
        const data = await this.fetchAndParseAPI(this.form.proxy.API)
        this.updateProxyData(this.form.proxy, data)
        this.onUpdateData()
      } catch (error) {
        console.error('请求代理 API 失败:', error)
        return
      }
      this.checkProxy()
    },
    async GetAPIProxy(row) {
      try {
        const data = await this.fetchAndParseAPI(row.proxy.API)
        this.updateProxyData(row.proxy, data)
        this.onUpdateRowData(row)
        this.getList()
      } catch (error) {
        console.error('请求代理 API 失败:', error)
        return
      }
      this.checkProxy(row)
    },
    onUpdateRowData(row) {
      if (!row || typeof row !== 'object') {
        console.error('The provided row is undefined or not an object.')
        return
      }

      row.timestamp = +new Date()
      this.preProcessData(row)
      updateBrowser(row)
      this.getList()
      this.dialogFormVisible = false
      this.$notify({
        title: this.$t('browser.success'),
        message: this.$t('browser.update') + this.$t('browser.success'),
        type: 'success',
        duration: 2000
      })
    },
    onAddBrand() {
      this.form['sec-ch-ua'].value.push({ brand: '', version: '' })
    },
    onRemoveBrand(brand) {
      this.form['sec-ch-ua'].value = this.form['sec-ch-ua'].value.filter(item => {
        return item.brand !== brand
      })
    },
    async handleBatchCreate() {
      if (!this.form.numberOfEnvironments || this.form.numberOfEnvironments < 1) {
        this.$message.error('无效的环境数量')
        return
      }

      const startNumber = this.form.startNumber || 1

      for (let i = 0; i < this.form.numberOfEnvironments; i++) {
        const newEnvironmentData = this.getDefaultForm()
        const sequenceNumber = startNumber + i

        // 设置名称
        if (this.form.namePrefix) {
          newEnvironmentData.name = `${this.form.namePrefix} ${sequenceNumber}`
        } else {
          newEnvironmentData.name = `浏览器 ${sequenceNumber}`
        }

        // 设置备注
        if (this.form.remarkPrefix) {
          newEnvironmentData.remark = `${this.form.remarkPrefix} #${sequenceNumber}`
        }

        newEnvironmentData.timestamp = Date.now()
        const uaData = this.updateChromeVer(newEnvironmentData.chrome_version)
        newEnvironmentData.ua.value = uaData.ua
        newEnvironmentData['ua-full-version'].value = uaData.uaFullVersion

        if (this.form.proxyAPI) {
          newEnvironmentData.proxy.API = this.form.proxyAPI
          newEnvironmentData.proxy.protocol = this.form.proxyType
          newEnvironmentData.proxy.mode = 2
        }
        if (this.form.proxyType === '默认') {
          newEnvironmentData.proxy.mode = 0
        }
        if (this.form.proxyType === '不使用代理') {
          newEnvironmentData.proxy.mode = 1
        }
        this.preProcessData(newEnvironmentData)
        try {
          await addBrowser(newEnvironmentData)
          this.$notify({
            title: this.$t('browser.success'),
            message: `已创建 "${newEnvironmentData.name}"`,
            type: 'success',
            duration: 2000
          })
        } catch (error) {
          this.$message.error('创建环境失败: ' + error.message)
          break
        }
      }

      this.form.numberOfEnvironments = 1
      this.form.namePrefix = ''
      this.form.remarkPrefix = ''
      this.form.startNumber = 1
      this.form.proxyType = '默认'
      this.form.proxyAPI = ''

      this.getList()
      this.dialogVisible = false
    },
    updateChromeVer(val) {
      if (val === '默认') {
        val = chromiumCoreVer
      }
      const curVers = Versions.filter(item => Number(item.split('.')[0]) === val)
      this.chromeVer = curVers[random.int(0, curVers.length - 1)]
      const UaValue = genUserAgent(osVer, this.chromeVer)
      const UaFullVersion = getUaFullVersion(uaFullVersions, this.chromeVer)
      return {
        ua: UaValue,
        uaFullVersion: UaFullVersion
      }
    },
    async handleBatchDelete() {
      if (this.selectedRows.length === 0) {
        this.$notify({
          title: '错误提示',
          message: '至少需要勾选一个环境',
          type: 'warning',
          duration: 2000
        })
        return
      }

      this.$confirm(
        this.$t('browser.delete_confirm').replace(
          '${name}',
          this.selectedRows.map(row => row.name).join(', ')
        )
      )
        .then(async () => {
          try {
            for (const row of this.selectedRows) {
              await deleteBrowser(row.id)
            }

            this.getList()
            this.$notify({
              title: this.$t('browser.success'),
              message:
                `${this.selectedRows.length} ` +
                this.$t('browser.delete') +
                this.$t('browser.success'),
              type: 'success',
              duration: 2000
            })
          } catch (error) {
            console.error('Error during batch delete:', error)
          }
        })
        .catch(() => {})
    },
    async handleCopy(row) {
      const newRow = JSON.parse(JSON.stringify(row))
      newRow.id = undefined
      newRow.name = row.name + ' (副本)'
      newRow.timestamp = Date.now()

      // 重新生成随机指纹参数
      const defaultForm = this.getDefaultForm()
      newRow.ua = { ...defaultForm.ua, mode: row.ua.mode }
      newRow['ua-full-version'] = {
        ...defaultForm['ua-full-version'],
        mode: row['ua-full-version'].mode
      }
      newRow['sec-ch-ua'] = { ...defaultForm['sec-ch-ua'], mode: row['sec-ch-ua'].mode }
      newRow['ua-language'] = { ...defaultForm['ua-language'], mode: row['ua-language'].mode }
      newRow['time-zone'] = { ...defaultForm['time-zone'], mode: row['time-zone'].mode }
      newRow.location = {
        ...defaultForm.location,
        mode: row.location.mode,
        enable: row.location.enable
      }
      newRow.screen = { ...defaultForm.screen, mode: row.screen.mode }
      newRow.fonts = { ...defaultForm.fonts, mode: row.fonts.mode }
      newRow.canvas = { ...defaultForm.canvas, mode: row.canvas.mode }
      newRow['webgl-img'] = { ...defaultForm['webgl-img'], mode: row['webgl-img'].mode }
      newRow.webgl = { ...defaultForm.webgl, mode: row.webgl.mode }
      newRow['audio-context'] = { ...defaultForm['audio-context'], mode: row['audio-context'].mode }
      newRow['client-rects'] = { ...defaultForm['client-rects'], mode: row['client-rects'].mode }
      newRow.speech_voices = { ...defaultForm.speech_voices, mode: row.speech_voices.mode }
      newRow.cpu = { ...defaultForm.cpu }
      newRow.memory = { ...defaultForm.memory }
      newRow['device-name'] = { ...defaultForm['device-name'], mode: row['device-name'].mode }
      newRow.mac = { ...defaultForm.mac, mode: row.mac.mode }
      newRow.dnt = { ...defaultForm.dnt }
      newRow.ssl = { ...defaultForm.ssl }
      newRow['port-scan'] = { ...defaultForm['port-scan'] }
      newRow.gpu = { ...defaultForm.gpu }

      // 保留代理设置
      newRow.proxy = { ...row.proxy }

      // 保留标签
      newRow.tags = row.tags || []

      this.preProcessData(newRow)
      await addBrowser(newRow)
      this.getList()
      this.$notify({
        title: this.$t('browser.success'),
        message: `已复制 "${row.name}" 为 "${newRow.name}"`,
        type: 'success',
        duration: 2000
      })
    },
    async handleBatchCopy() {
      if (this.selectedRows.length === 0) {
        this.$notify({
          title: '错误提示',
          message: '至少需要勾选一个环境',
          type: 'warning',
          duration: 2000
        })
        return
      }

      for (const row of this.selectedRows) {
        await this.handleCopy(row)
      }
    },
    handleEditTags(row) {
      this.currentTagRow = row
      this.tagForm.tags = row.tags || []
      this.dialogTagsVisible = true
    },
    async saveTags() {
      if (!this.currentTagRow) return

      this.currentTagRow.tags = [...this.tagForm.tags]
      await updateBrowser(this.currentTagRow)
      this.getList()
      this.dialogTagsVisible = false
      this.$notify({
        title: this.$t('browser.success'),
        message: '标签已更新',
        type: 'success',
        duration: 2000
      })
    },
    async handleBatchSetTags() {
      if (this.selectedRows.length === 0) {
        this.$notify({
          title: '错误提示',
          message: '至少需要勾选一个环境',
          type: 'warning',
          duration: 2000
        })
        return
      }

      this.currentTagRow = null
      this.tagForm.tags = []
      this.dialogTagsVisible = true
    },
    async applyBatchSetTags() {
      if (this.selectedRows.length === 0) return

      for (const row of this.selectedRows) {
        row.tags = [...this.tagForm.tags]
        await updateBrowser(row)
      }

      this.getList()
      this.dialogTagsVisible = false
      this.$notify({
        title: this.$t('browser.success'),
        message: `已更新 ${this.selectedRows.length} 个环境的标签`,
        type: 'success',
        duration: 2000
      })
    },
    async showSettingsDialog() {
      const store = await getGlobalData()
      this.apiLink = store.apiLink || 'http://ip-api.com/json'
      this.Channel = store.Channel || 'ip-api'
      this.showSetDialog = true
    },
    onChannelChange(channel) {
      // 根据渠道自动填充默认 API Link
      const defaultLinks = {
        'ip-api': 'http://ip-api.com/json',
        ipinfo: 'https://ipinfo.io/json?token=YOUR_TOKEN',
        ipapi: 'https://ipapi.co/json/',
        ipgeolocation: 'https://api.ipgeolocation.io/ipgeo?apiKey=YOUR_KEY',
        virtualbrowser: 'https://api.virtualbrowser.cc/ipgeo?key=YOUR_KEY'
      }
      this.apiLink = defaultLinks[channel] || ''
    },
    async saveSettings() {
      const GlobalData = await getGlobalData()

      // 验证 API 链接格式
      if (this.apiLink) {
        // 支持的 IP 查询 API 列表
        const supportedApis = [
          'ip-api.com',
          'ipinfo.io',
          'ipapi.co',
          'ipgeolocation.io',
          'virtualbrowser'
        ]

        const isSupported = supportedApis.some(api => this.apiLink.includes(api))

        if (!isSupported) {
          this.$notify({
            title: '警告',
            message: '未知的 API 格式，请确保是有效的 IP 查询服务',
            type: 'warning',
            duration: 3000
          })
          // 继续保存，但给出警告
        }
      }

      // 保存 API 链接
      if (this.apiLink !== GlobalData.apiLink) {
        await setGlobalData('apiLink', this.apiLink)
        console.log('API链接已保存:', this.apiLink)
      }

      // 保存渠道选择
      if (this.Channel && this.Channel !== GlobalData.Channel) {
        await setGlobalData('Channel', this.Channel)
      }

      this.$notify({
        title: '保存成功',
        message: 'IP 查询 API 设置已保存',
        type: 'success',
        duration: 2000
      })
      this.showSetDialog = false

      // 重新加载 IP 地理位置数据
      if (this.apiLink) {
        this.reloadIpGeoData()
      }
    },
    async checkApiLinkSet() {
      const store = await getGlobalData()
      const storedApiLink = store.apiLink
      if (storedApiLink) {
        this.apiLink = storedApiLink
        this.Channel = store.Channel || 'ip-api'
      } else {
        // 使用默认值
        this.apiLink = 'http://ip-api.com/json'
        this.Channel = 'ip-api'
      }
    },
    async reloadIpGeoData() {
      // 重新加载 IP 地理位置数据
      if (!this.apiLink) return

      try {
        const isIpGeoApi =
          this.apiLink.includes('ip-api.com') ||
          this.apiLink.includes('ipinfo.io') ||
          this.apiLink.includes('ipapi.co') ||
          this.apiLink.includes('ipgeolocation')

        if (isIpGeoApi) {
          const geoData = await fetchIpGeoData(this.apiLink)
          console.log('IP 地理位置数据已重新加载:', geoData)

          // 更新 IPGeo 变量
          IPGeo = generateBrowserConfig(geoData)

          this.$notify({
            title: '数据已更新',
            message: `IP: ${geoData.ip}, 位置: ${geoData.country_name} ${geoData.city}`,
            type: 'success',
            duration: 3000
          })
        }
      } catch (error) {
        console.error('重新加载 IP 地理位置失败:', error)
        this.$notify({
          title: '数据加载失败',
          message: error.message || '无法获取 IP 地理位置数据',
          type: 'warning',
          duration: 3000
        })
      }
    },
    handleBatchSetGroup() {
      if (this.selectedRows.length === 0) {
        this.$notify({
          title: '错误提示',
          message: '至少需要勾选一个环境',
          type: 'warning',
          duration: 2000
        })
        return
      }
      this.selectedGroup = this.$t('group.default')
      this.currentEditingRow = null
      this.dialogBatchSetGroupVisible = true
    },
    async applyBatchSetGroup() {
      if (!this.selectedGroup) {
        this.$notify({
          title: '操作失败',
          message: '请先选择一个分组',
          type: 'warning',
          duration: 2000
        })
        return
      }

      if (this.currentEditingRow) {
        this.currentEditingRow.group = this.selectedGroup
        await updateBrowser(this.currentEditingRow)
      } else {
        for (let i = 0; i < this.selectedRows.length; i++) {
          const row = this.selectedRows[i]
          row.group = this.selectedGroup
          await updateBrowser(row)
        }
      }

      this.$notify({
        title: '操作成功',
        message: '分组更新成功',
        type: 'success',
        duration: 2000
      })
      this.dialogBatchSetGroupVisible = false
      this.getList()
    },
    async handleEditGroup(row) {
      this.selectedGroup = row.group || this.$t('group.default')
      this.currentEditingRow = row
      this.dialogBatchSetGroupVisible = true
    }
  }
}
</script>

<style lang="scss" scoped>
@import '@/styles/element-variables.scss';

.filter-container {
  display: flex;
  justify-content: space-between;

  .filter-item:not(:last-child) {
    margin-right: 10px;
  }
}

.flex {
  display: flex;
  align-items: center;
}

.formDlg {
  ::v-deep {
    .el-dialog {
      min-width: 400px;
    }
    .tips {
      font-size: 12px;
      color: #999;
      line-height: 1.5;
      margin-top: 5px;
    }
    .el-dialog__body {
      padding-top: 5px;
      padding-bottom: 0;
    }
    .el-timeline {
      padding: 0;

      .el-timeline-item {
        padding-bottom: 5px;
      }
      .el-timeline-item__tail {
        border-color: $--color-primary;
      }
      .el-timeline-item__node {
        background-color: $--color-primary;
      }

      .el-timeline-item__content {
        h3 {
          color: $--color-primary;
          margin: 0;
          font-size: 1em;
        }
      }
    }
    .el-form-item {
      margin-bottom: 15px;
      margin-right: 5px;
    }
    .el-form-item__label {
      font-size: 12px;
      word-break: keep-all;
    }
    .custom-sec-ua {
      margin-top: 5px;

      .item {
        display: flex;
        align-items: flex-start;
      }
    }
  }

  .drawer-content {
    height: calc(100vh - 80px);
    display: flex;
    flex-direction: column;

    .form-wrap {
      overflow-y: auto;
      padding: 10px 20px;
    }
    .dialog-footer {
      padding: 20px;
      text-align: center;

      ::v-deep {
        .el-button {
          width: 150px;
        }
      }
    }
  }
}

.dialog-cookie {
  ::v-deep {
    .el-dialog__body {
      padding: 10px 20px;
    }
  }
}

.qq-group {
  margin-left: -15px;
  p {
    margin-top: -5px;
    margin-left: 18px;
    font-size: 13px;
  }
  code {
    padding: 0.2em 0.4em;
    margin: 0;
    font-family: ui-monospace, SFMono-Regular, SF Mono, Menlo, Consolas, Liberation Mono, monospace;
    font-size: 120%;
    white-space: break-spaces;
    background-color: rgba(175, 184, 193, 0.2);
    border-radius: 6px;
  }
}
</style>
