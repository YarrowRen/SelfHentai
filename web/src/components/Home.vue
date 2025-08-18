<template>
  <div class="container">
    <div class="control-panel">
      <!-- 类型筛选 -->
      <div class="button-group">
        <Button
          v-for="type in currentTypeList"
          :key="type.name"
          :label="type.name"
          :class="['btn', type.color, 'type-btn', { active: activeType === type.name }]"
          @click="toggleType(type.name)"
          aria-label="Filter by type"
        />
      </div>

      <!-- 搜索条 -->
      <div class="search-bar">
        <InputText
          v-model.trim="searchQuery"
          placeholder="Search Keywords"
          class="custom-input"
          @keyup.enter="performSearch"
          aria-label="Search keywords"
        />
        <Button
          label="Search"
          class="btn search-btn"
          @click="performSearch"
          severity="secondary"
          :loading="loading"
        />
        <Button
          label="Clear"
          class="btn clear-btn"
          @click="clearSearch"
          severity="secondary"
          :disabled="loading && !searchQuery && !activeType"
        />
        <!-- 数据源切换 -->
        <Button
          :label="provider.toUpperCase()"
          class="btn provider-toggle-btn"
          @click="toggleProvider"
          severity="secondary"
          v-tooltip="`当前数据源: ${provider.toUpperCase()}, 点击切换`"
        />
      </div>
    </div>

    <!-- 顶部分页器 -->
    <Paginator
      :template="'CurrentPageReport FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink JumpToPageInput'"
      :rows="perPage"
      :totalRecords="totalRecords"
      :first="firstIndex"
      @page="onPageChange"
    />

    <!-- 表格展示 -->
    <div class="results-table">
      <table :class="{ 'jm-table': provider === 'jm' }">
        <thead>
          <tr v-if="provider === 'ex'">
            <th>Type</th>
            <th>Title</th>
            <th style="width: 150px;">Published</th>
            <th>Uploader</th>
          </tr>
          <tr v-else-if="provider === 'jm'">
            <th>Type</th>
            <th>ID</th>
            <th>Title</th>
            <th>Author</th>
            <th>Category</th>
            <th style="width: 120px;">AddTime</th>
          </tr>
        </thead>

        <tbody v-if="!loading && paddedResults.length">
          <!-- EX 数据表格行 -->
          <tr
            v-if="provider === 'ex'"
            v-for="item in paddedResults"
            :key="item.gid ?? 'placeholder-' + item.__placeholderId"
            :class="{ 'is-placeholder': item.__placeholder }"
          >
            <td>
              <span v-if="!item.__placeholder" :class="'badge ' + item.typeClass">{{ item.type }}</span>
            </td>
            <td
              v-if="!item.__placeholder"
              class="title-cell"
              @click="navigateToGallery(item.id, item.gid)"
              @mouseenter="showPopover($event, item)"
              @mouseleave="hidePopover"
            >
              <div class="title-container">
                {{ item.title_jpn || item.title }}
              </div>
              <div class="tags-container" v-if="item.tags && item.tags.length">
                <Tag
                  v-for="(tag, tIdx) in item.tags"
                  :key="tIdx"
                  :value="tag.tag_cn || tag.tag"
                  class="tag"
                  severity="secondary"
                />
              </div>
            </td>
            <td v-else class="title-cell"></td>
            <td>
              <div class="cell-content" v-if="!item.__placeholder">
                <div>{{ item.published }}</div>
                <div v-if="item.rating != null">
                  <Rating :modelValue="item.rating" readonly />
                </div>
              </div>
            </td>
            <td v-if="!item.__placeholder">
              {{ item.uploader }}<br />
              {{ item.filecount }}
            </td>
            <td v-else></td>
          </tr>

          <!-- JM 数据表格行 -->
          <tr
            v-else-if="provider === 'jm'"
            v-for="item in paddedResults"
            :key="item.id ?? 'placeholder-' + item.__placeholderId"
            :class="{ 'is-placeholder': item.__placeholder }"
          >
            <td>
              <span v-if="!item.__placeholder" :class="'badge ' + item.typeClass">{{ item.type }}</span>
            </td>
            <td v-if="!item.__placeholder">{{ item.id }}</td>
            <td v-else></td>
            <td
              v-if="!item.__placeholder"
              class="title-cell"
              @click="navigateToGallery(item.id, item.gid)"
              @mouseenter="showPopover($event, item)"
              @mouseleave="hidePopover"
            >
              <div class="title-container">
                {{ item.title }}
              </div>
              <div class="tags-container" v-if="item.tags && item.tags.length > 0">
                <Tag
                  v-for="(tag, tIdx) in item.tags"
                  :key="tIdx"
                  :value="tag"
                  class="tag"
                  severity="secondary"
                />
              </div>
            </td>
            <td v-else class="title-cell"></td>
            <td v-if="!item.__placeholder">{{ item.author }}</td>
            <td v-else></td>
            <td v-if="!item.__placeholder">{{ item.category }}</td>
            <td v-else></td>
            <td v-if="!item.__placeholder">{{ item.addtime }}</td>
            <td v-else></td>
          </tr>
        </tbody>

        <tbody v-else-if="loading">
          <tr>
            <td :colspan="provider === 'ex' ? 4 : 6" class="empty-state">Loading…</td>
          </tr>
        </tbody>

        <tbody v-else>
          <tr>
            <td :colspan="provider === 'ex' ? 4 : 6" class="empty-state">No data</td>
          </tr>
        </tbody>
      </table>

      <Popover ref="popover" class="image-popover">
        <img v-if="popoverData?.thumb" :src="popoverData.thumb" alt="thumbnail" />
        <div v-else>No Image Available</div>
      </Popover>
    </div>

    <!-- 底部分页器 -->
    <Paginator
      :template="'CurrentPageReport FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink JumpToPageInput'"
      :rows="perPage"
      :totalRecords="totalRecords"
      :first="firstIndex"
      @page="onPageChange"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import axios from 'axios'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Paginator from 'primevue/paginator'
import Tag from 'primevue/tag'
import Rating from 'primevue/rating'
import Popover from 'primevue/popover'

/** ========= 常量与状态 ========= */
const API = import.meta.env?.VITE_API_BASE || ''
const searchQuery = ref('')
const results = ref([])
const currentPage = ref(1)
const perPage = ref(25)
const totalRecords = ref(0)
const activeType = ref(null)
const loading = ref(false)
const provider = ref('ex') // 默认使用 EX 数据源

const popover = ref()
const popoverData = ref(null)

// EX 类型配置
const exTypeList = [
  { name: 'Doujinshi',  color: 'red' },
  { name: 'Manga',      color: 'orange' },
  { name: 'Artist CG',  color: 'yellow' },
  { name: 'Game CG',    color: 'green' },
  { name: 'Western',    color: 'gold' },
  { name: 'Non-H',      color: 'lightblue' },
  { name: 'Image Set',  color: 'blue' },
  { name: 'Cosplay',    color: 'purple' },
  { name: 'Asian Porn', color: 'pink' },
  { name: 'Misc',       color: 'gray' }
]

// JM 类型配置
const jmTypeList = [
  { name: '同人', color: 'red' },
  { name: '单本', color: 'orange' },
  { name: '短篇', color: 'yellow' },
  { name: '韩漫', color: 'purple' },
  { name: '其他类', color: 'gray' }
]

// 预计算类型->颜色映射
const exTypeClassMap = Object.fromEntries(exTypeList.map(t => [t.name, t.color]))
const jmTypeClassMap = Object.fromEntries(jmTypeList.map(t => [t.name, t.color]))

// 当前类型列表（根据数据源切换）
const currentTypeList = computed(() => provider.value === 'ex' ? exTypeList : jmTypeList)
const currentTypeClassMap = computed(() => provider.value === 'ex' ? exTypeClassMap : jmTypeClassMap)

/** ========= 工具计算 ========= */
const firstIndex = computed(() => (currentPage.value - 1) * perPage.value)

// 时间戳转换为 年-月-日 格式
function formatTimestamp(timestamp) {
  if (!timestamp) return ''
  
  // 处理字符串或数字时间戳
  const ts = typeof timestamp === 'string' ? parseInt(timestamp) : timestamp
  if (isNaN(ts)) return ''
  
  // 如果时间戳看起来像是秒级时间戳（10位数），则乘以1000转为毫秒
  const date = ts.toString().length === 10 ? new Date(ts * 1000) : new Date(ts)
  
  if (isNaN(date.getTime())) return ''
  
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  }).replace(/\//g, '-')
}

// 数据映射和填充逻辑
const paddedResults = computed(() => {
  const mapped = results.value.map(item => {
    if (provider.value === 'ex') {
      return {
        type: item.category,
        typeClass: currentTypeClassMap.value[item.category] || 'default',
        title: item.title,
        title_jpn: item.title_jpn,
        published: item.favTime ? item.favTime.replace('T', ' ').slice(0, 16) : '',
        gid: item.gid,
        id: null,
        uploader: item.uploader,
        filecount: item.filecount ? `${item.filecount} pages` : '',
        tags: Array.isArray(item.tags) ? item.tags : [],
        rating: item.rating,
        thumb: item.thumb,
        author: null,
        category_info: null,
        latest_ep: null
      }
    } else {
      // JM 数据映射
      return {
        type: item.category?.title || '未知',
        typeClass: currentTypeClassMap.value[item.category?.title] || 'default',
        title: item.name,
        title_jpn: null,
        published: null,
        gid: null,
        id: item.id,
        uploader: null,
        filecount: null,
        tags: Array.isArray(item.tags) ? item.tags.filter(tag => tag && tag.trim()) : [],
        rating: null,
        thumb: item.image,
        author: item.author || '未知作者',
        category: item.category?.title || '未知分类',
        addtime: item.addtime ? formatTimestamp(item.addtime) : '未知时间',
        latest_ep: item.latest_ep
      }
    }
  })

  const fillCount = Math.max(0, perPage.value - mapped.length)
  if (fillCount === 0) return mapped

  const placeholders = Array.from({ length: fillCount }, (_, i) => ({
    __placeholder: true,
    __placeholderId: i
  }))

  return [...mapped, ...placeholders]
})

/** ========= 网络请求与并发控制 ========= */
let abortController = null

async function fetchData (page = 1, keyword = '', type = null) {
  // 取消上一次未完成的请求，避免竞态覆盖
  if (abortController) abortController.abort()
  abortController = new AbortController()

  loading.value = true
  try {
    const params = {
      page,
      per_page: perPage.value,
      provider: provider.value,
      ...(keyword ? { keyword } : {})
    }

    // 根据数据源添加相应的筛选参数
    if (provider.value === 'ex' && type) {
      params.type = type
    } else if (provider.value === 'jm' && type) {
      params.category = type
    }

    const { data } = await axios.get(`${API}/api/gallery`, {
      params,
      signal: abortController.signal
    })

    const { results: resList = [], total = 0 } = data || {}

    results.value = resList
    totalRecords.value = Number.isFinite(total) ? total : 0
    currentPage.value = page
  } catch (err) {
    if (axios.isCancel?.(err) || err?.name === 'CanceledError' || err?.name === 'AbortError') {
      // 被主动取消，不提示
    } else {
      console.error('Error fetching data:', err)
    }
  } finally {
    loading.value = false
  }
}

function performSearch () {
  fetchData(1, searchQuery.value, activeType.value)
}

function clearSearch () {
  searchQuery.value = ''
  activeType.value = null
  fetchData(1)
}

function onPageChange (e) {
  // PrimeVue onPage: { page, first, rows, pageCount }
  const page = Math.floor(e.first / e.rows) + 1
  fetchData(page, searchQuery.value, activeType.value)
}

function toggleType (type) {
  activeType.value = activeType.value === type ? null : type
  fetchData(1, searchQuery.value, activeType.value)
}

function switchProvider (newProvider) {
  if (provider.value === newProvider) return
  provider.value = newProvider
  activeType.value = null // 重置类型筛选
  searchQuery.value = '' // 重置搜索
  fetchData(1)
}

function toggleProvider () {
  const newProvider = provider.value === 'ex' ? 'jm' : 'ex'
  switchProvider(newProvider)
}

function navigateToGallery (id, gid) {
  if (provider.value === 'ex' && gid) {
    const url = `/gallery/${gid}/`
    window.open(url, '_blank', 'noopener,noreferrer')
  } else if (provider.value === 'jm' && id) {
    const url = `/jm/${id}/`
    window.open(url, '_blank', 'noopener,noreferrer')
  }
}

function showPopover (event, item) {
  if (!item?.title) return
  popoverData.value = item
  popover.value?.show(event)
}
function hidePopover () {
  popover.value?.hide()
}

onMounted(() => {
  fetchData()
})
onBeforeUnmount(() => {
  if (abortController) abortController.abort()
})
</script>

<style src="../assets/Home.css"></style>
