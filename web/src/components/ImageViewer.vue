<template>
  <div class="image-viewer-wrapper">
    <!-- 主要内容区域 -->
    <div class="image-viewer-container">
      <!-- 左侧图片展示区域 50% -->
      <div class="image-section">
        <div v-if="loading" class="image-loading">
          <div class="loading-spinner"></div>
          <p>Loading image...</p>
        </div>
        
        <div v-else-if="error" class="image-error">
          <p>{{ error }}</p>
          <Button @click="loadFullImage" label="Retry" severity="secondary" />
        </div>
        
        <div v-else-if="fullImageUrl" class="image-container">
          <img 
            ref="fullImageRef"
            :src="fullImageUrl" 
            :alt="`Page ${currentPage}`"
            class="full-image"
            crossorigin="anonymous"
            @error="handleImageError"
            @load="handleImageLoad"
          />
          
          <!-- 截图选择覆盖层 -->
          <div 
            v-if="isScreenshotMode"
            class="screenshot-overlay-container"
            @mousedown.prevent.stop="startSelection"
            @mousemove.prevent="updateSelection"
            @mouseup.prevent.stop="endSelection"
            @mouseleave="cancelSelection"
            @contextmenu.prevent
          >
            <!-- 选择框 -->
            <div 
              v-if="screenshotState.selection.visible"
              class="selection-box"
              :style="{
                left: screenshotState.selection.x + 'px',
                top: screenshotState.selection.y + 'px',
                width: screenshotState.selection.width + 'px',
                height: screenshotState.selection.height + 'px'
              }"
            >
              <div class="selection-border"></div>
              <div class="selection-info">
                {{ Math.round(screenshotState.selection.width) }} × {{ Math.round(screenshotState.selection.height) }}
              </div>
            </div>
            
            <!-- 确认按钮 -->
            <div 
              v-if="screenshotState.selection.visible && screenshotState.selection.width > 5 && screenshotState.selection.height > 5"
              class="screenshot-actions"
              :style="{
                left: (screenshotState.selection.x + screenshotState.selection.width + 10) + 'px',
                top: screenshotState.selection.y + 'px'
              }"
            >
              <Button 
                @mousedown.prevent.stop
                @click.prevent.stop="confirmScreenshot"
                size="small"
                severity="success"
                class="confirm-btn"
              >
                ✓ Capture
              </Button>
              <Button 
                @mousedown.prevent.stop
                @click.prevent.stop="cancelScreenshot"
                size="small"
                severity="secondary"
                class="cancel-btn"
              >
                ✕ Cancel
              </Button>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧翻译功能区域 50% -->
      <div class="form-section">
        <div class="translation-container">

          <!-- 截图功能区 -->
          <div class="screenshot-section">
            <h4>
              <span class="section-icon">📷</span>
              Screenshot & OCR
            </h4>
            
            <!-- 截图按钮 -->
            <div class="screenshot-controls">
              <Button 
                @click="toggleScreenshotMode"
                :disabled="screenshotLoading"
                :loading="screenshotLoading"
                class="screenshot-btn"
                :severity="isScreenshotMode ? 'danger' : 'success'"
              >
                <span class="btn-icon">{{ isScreenshotMode ? '✕' : '✂️' }}</span>
                <span class="btn-text">
                  {{ screenshotLoading ? 'Processing...' : (isScreenshotMode ? 'Cancel Screenshot' : 'Take Screenshot') }}
                </span>
              </Button>
              
              <Button 
                @click="clearScreenshot"
                :disabled="!screenshotData"
                class="clear-btn"
                severity="secondary"
                outlined
              >
                <span class="btn-icon">🗑️</span>
                <span class="btn-text">Clear</span>
              </Button>
            </div>

            <!-- 截图预览框 -->
            <div class="screenshot-preview">
              <div v-if="screenshotData" class="screenshot-image-container">
                <img :src="screenshotData" alt="Screenshot" class="screenshot-image" />
                <div class="screenshot-overlay">
                  <span class="screenshot-info">{{ screenshotWidth }}x{{ screenshotHeight }}</span>
                </div>
              </div>
              <div v-else class="screenshot-placeholder">
                <div class="placeholder-content">
                  <span class="placeholder-icon">🖼️</span>
                  <span class="placeholder-text">No screenshot taken</span>
                  <span class="placeholder-hint">Click "Take Screenshot" to capture image area</span>
                </div>
              </div>
            </div>
          </div>


          <!-- OCR结果区 -->
          <div class="ocr-section">
            <h4>
              <span class="section-icon">👁️</span>
              OCR Recognition
            </h4>
            
            <div class="ocr-controls">
              <Button 
                @click="performOCR"
                :disabled="!screenshotData || ocrLoading"
                :loading="ocrLoading"
                class="ocr-btn"
                severity="info"
              >
                <span class="btn-icon">🔍</span>
                <span class="btn-text">{{ ocrLoading ? 'Recognizing...' : 'Run OCR' }}</span>
              </Button>
            </div>

            <!-- OCR结果文本框（可编辑） -->
            <div class="text-result">
              <label class="result-label">Japanese Text:</label>
              <Textarea 
                v-model="ocrResult" 
                placeholder="OCR result will appear here..."
                rows="4"
                class="ocr-textarea"
                :disabled="ocrLoading"
              />
            </div>
          </div>


          <!-- AI翻译结果区 -->
          <div class="translation-section">
            <h4>
              <span class="section-icon">🌐</span>
              AI Translation
            </h4>
            
            <div class="translation-controls">
              <Button 
                @click="performTranslation"
                :disabled="!ocrResult.trim() || translationLoading"
                :loading="translationLoading"
                class="translate-btn"
                severity="warning"
              >
                <span class="btn-icon">⚡</span>
                <span class="btn-text">{{ translationLoading ? 'Translating...' : 'Translate to Chinese' }}</span>
              </Button>
            </div>

            <!-- AI翻译结果框（只读） -->
            <div class="text-result">
              <label class="result-label">Chinese Translation:</label>
              <Textarea 
                v-model="translationResult" 
                placeholder="Translation result will appear here..."
                rows="4"
                class="translation-textarea"
                readonly
              />
            </div>
          </div>

          <!-- 操作按钮 -->
          <div class="action-section">
            <Button 
              @click="copyTranslation"
              :disabled="!translationResult.trim()"
              class="copy-btn"
              severity="success"
              outlined
            >
              <span class="btn-icon">📋</span>
              <span class="btn-text">Copy Translation</span>
            </Button>
            
            <Button 
              @click="saveTranslation"
              :disabled="!translationResult.trim()"
              class="save-btn"
            >
              <span class="btn-icon">💾</span>
              <span class="btn-text">Save</span>
            </Button>
          </div>
        </div>
      </div>
    </div>

    <!-- 底部分页控制 -->
    <div class="pagination-controls">
      <!-- 第一页按钮 -->
      <Button 
        @click="goToFirstPage"
        :disabled="currentPage <= 1"
        v-tooltip="'First Page'"
        class="page-btn nav-btn"
      >
        <span class="nav-icon">&laquo;</span>
      </Button>
      
      <!-- 上一页按钮 -->
      <Button 
        @click="previousPage"
        :disabled="currentPage <= 1"
        v-tooltip="'Previous Page'"
        class="page-btn nav-btn"
      >
        <span class="nav-icon">&lsaquo;</span>
      </Button>
      
      <!-- 页码数字 -->
      <div class="page-numbers">
        <Button
          v-for="pageNum in visiblePages"
          :key="pageNum"
          @click="navigateToPage(pageNum)"
          :class="['page-btn', 'number-btn', { 'active': pageNum === currentPage }]"
          :disabled="pageNum === '...'"
        >
          {{ pageNum }}
        </Button>
      </div>
      
      <!-- 下一页按钮 -->
      <Button 
        @click="nextPage"
        :disabled="currentPage >= totalPages"
        v-tooltip="'Next Page'"
        class="page-btn nav-btn"
      >
        <span class="nav-icon">&rsaquo;</span>
      </Button>
      
      <!-- 最后一页按钮 -->
      <Button 
        @click="goToLastPage"
        :disabled="currentPage >= totalPages"
        v-tooltip="'Last Page'"
        class="page-btn nav-btn"
      >
        <span class="nav-icon">&raquo;</span>
      </Button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'
import Button from 'primevue/button'
import InputNumber from 'primevue/inputnumber'
import Textarea from 'primevue/textarea'
import Divider from 'primevue/divider'

const route = useRoute()
const router = useRouter()
const API = import.meta.env.VITE_API_BASE

// 路由参数
const gid = computed(() => route.params.gid)
const token = computed(() => route.params.token)
const pageNumber = computed(() => parseInt(route.params.page) || 1)

// 状态管理
const loading = ref(false)
const error = ref(null)
const fullImageUrl = ref('')
const currentPage = ref(1)
const totalPages = ref(1)
const galleryTitle = ref('')
const imageName = ref('')
const imageSize = ref(null)

// 图片引用
const fullImageRef = ref(null)

// 翻译功能数据
const screenshotData = ref(null)
const screenshotWidth = ref(0)
const screenshotHeight = ref(0)
const screenshotLoading = ref(false)

// 截图功能状态管理
const isScreenshotMode = ref(false)
const screenshotState = ref({
  isSelecting: false,
  isDragging: false,
  selection: {
    visible: false,
    startX: 0,
    startY: 0,
    currentX: 0,
    currentY: 0,
    x: 0,
    y: 0,
    width: 0,
    height: 0
  }
})

const ocrResult = ref('')
const ocrLoading = ref(false)

const translationResult = ref('')
const translationLoading = ref(false)
const targetLanguage = ref('zh')

// 初始化
onMounted(() => {
  currentPage.value = pageNumber.value
  loadFullImage()
  checkOCRStatus()
  checkTranslationStatus()
})

// 监听路由变化
watch(() => route.params, (newParams) => {
  currentPage.value = parseInt(newParams.page) || 1
  loadFullImage()
})

// 加载完整大图
async function loadFullImage() {
  if (!gid.value || !token.value) return
  
  loading.value = true
  error.value = null
  
  try {
    const url = `${API}/api/gallery/ex/full-image/${gid.value}/${token.value}/${currentPage.value}`
    const { data } = await axios.get(url)
    
    // 使用代理URL来解决CORS问题
    const originalImageUrl = data.imageUrl
    const proxyImageUrl = `${API}/api/gallery/ex/proxy-image?url=${encodeURIComponent(originalImageUrl)}`
    
    fullImageUrl.value = proxyImageUrl
    imageName.value = data.imageName
    galleryTitle.value = data.galleryTitle
    totalPages.value = data.totalPages || 1
    
    // 获取图片尺寸 (使用原始URL以避免重复请求)
    if (originalImageUrl) {
      getImageSize(proxyImageUrl)
    }
    
  } catch (err) {
    console.error('Error loading full image:', err)
    error.value = `Failed to load image: ${err.message}`
  } finally {
    loading.value = false
  }
}

// 获取图片尺寸
function getImageSize(url) {
  const img = new Image()
  img.onload = () => {
    imageSize.value = {
      width: img.naturalWidth,
      height: img.naturalHeight
    }
  }
  img.src = url
}

// 图片加载事件
function handleImageLoad() {
  console.log('图片加载完成')
  
  // 如果正在截图模式，重置状态
  if (isScreenshotMode.value) {
    console.log('图片重新加载，重置截图状态')
    resetScreenshotState()
  }
}

function handleImageError() {
  error.value = 'Failed to load image'
}

// 分页控制
function previousPage() {
  if (currentPage.value > 1) {
    navigateToPage(currentPage.value - 1)
  }
}

function nextPage() {
  if (currentPage.value < totalPages.value) {
    navigateToPage(currentPage.value + 1)
  }
}

function goToFirstPage() {
  navigateToPage(1)
}

function goToLastPage() {
  navigateToPage(totalPages.value)
}

function navigateToPage(page) {
  if (typeof page === 'number' && page >= 1 && page <= totalPages.value) {
    router.push(`/gallery/${gid.value}/${token.value}/page/${page}`)
  }
}

// 计算可见页码列表
const visiblePages = computed(() => {
  const current = currentPage.value
  const total = totalPages.value
  const pages = []
  
  if (total <= 7) {
    // 总页数少于等于7，显示所有页码
    for (let i = 1; i <= total; i++) {
      pages.push(i)
    }
  } else {
    // 总页数大于7，使用智能分页（不显示首尾页码，因为有专门按钮）
    if (current <= 4) {
      // 当前页靠近开头：显示 2 3 4 5 6 ... 
      for (let i = 2; i <= Math.min(6, total - 1); i++) {
        pages.push(i)
      }
      if (total > 6) {
        pages.push('...')
      }
    } else if (current >= total - 3) {
      // 当前页靠近结尾：显示 ... n-4 n-3 n-2 n-1
      if (total > 6) {
        pages.push('...')
      }
      for (let i = Math.max(2, total - 4); i <= total - 1; i++) {
        pages.push(i)
      }
    } else {
      // 当前页在中间：显示 ... n-2 n-1 n n+1 n+2 ...
      pages.push('...')
      for (let i = current - 2; i <= current + 2; i++) {
        pages.push(i)
      }
      pages.push('...')
    }
  }
  
  return pages
})


// 截图功能主要方法
function toggleScreenshotMode() {
  if (!fullImageRef.value?.complete) {
    alert('图片未加载完成，请稍后再试')
    return
  }
  
  if (isScreenshotMode.value) {
    exitScreenshotMode()
  } else {
    enterScreenshotMode()
  }
}

function enterScreenshotMode() {
  console.log('进入截图模式')
  isScreenshotMode.value = true
  resetScreenshotState()
}

function exitScreenshotMode() {
  console.log('退出截图模式')
  isScreenshotMode.value = false
  resetScreenshotState()
}

function resetScreenshotState() {
  screenshotState.value = {
    isSelecting: false,
    isDragging: false,
    selection: {
      visible: false,
      startX: 0,
      startY: 0,
      currentX: 0,
      currentY: 0,
      x: 0,
      y: 0,
      width: 0,
      height: 0
    }
  }
}

function clearScreenshot() {
  screenshotData.value = null
  screenshotWidth.value = 0
  screenshotHeight.value = 0
  ocrResult.value = ''
  translationResult.value = ''
  exitScreenshotMode()
}

// 获取图片在容器中的实际位置和尺寸
function getImageBounds() {
  if (!fullImageRef.value) {
    console.error('getImageBounds: fullImageRef 不存在')
    return null
  }
  
  const img = fullImageRef.value
  
  if (!img.complete) {
    console.error('getImageBounds: 图片尚未加载完成')
    return null
  }
  
  if (img.naturalWidth === 0 || img.naturalHeight === 0) {
    console.error('getImageBounds: 图片自然尺寸为0')
    return null
  }
  
  const container = img.parentElement
  if (!container) {
    console.error('getImageBounds: 找不到图片容器')
    return null
  }
  
  const imgRect = img.getBoundingClientRect()
  const containerRect = container.getBoundingClientRect()
  
  const bounds = {
    left: imgRect.left - containerRect.left,
    top: imgRect.top - containerRect.top,
    width: imgRect.width,
    height: imgRect.height,
    naturalWidth: img.naturalWidth,
    naturalHeight: img.naturalHeight
  }
  
  // 只在首次调用或调试模式下输出详细信息
  // console.log('getImageBounds 返回:', bounds)
  return bounds
}

// 选择开始
function startSelection(event) {
  console.log('开始选择')
  
  if (!isScreenshotMode.value) return
  
  // 如果正在加载截图，忽略新的选择
  if (screenshotLoading.value) {
    console.log('截图正在处理中，忽略新选择')
    return
  }
  
  // 检查事件来源，避免按钮点击触发选择
  if (event.target.closest('.screenshot-actions')) {
    console.log('来自按钮区域的事件，忽略')
    return
  }
  
  const imageBounds = getImageBounds()
  if (!imageBounds) return
  
  const rect = event.currentTarget.getBoundingClientRect()
  const x = event.clientX - rect.left
  const y = event.clientY - rect.top
  
  // 检查是否在图片范围内
  if (!isPointInImageBounds(x, y, imageBounds)) {
    return
  }
  
  // 设置选择状态
  screenshotState.value.isSelecting = true
  screenshotState.value.isDragging = false
  screenshotState.value.selection = {
    visible: true,
    startX: x,
    startY: y,
    currentX: x,
    currentY: y,
    x: x,
    y: y,
    width: 0,
    height: 0
  }
  
  event.preventDefault()
}

// 选择更新
function updateSelection(event) {
  if (!isScreenshotMode.value || !screenshotState.value.isSelecting) {
    return
  }
  
  const imageBounds = getImageBounds()
  if (!imageBounds) return
  
  const rect = event.currentTarget.getBoundingClientRect()
  const currentX = event.clientX - rect.left
  const currentY = event.clientY - rect.top
  
  screenshotState.value.isDragging = true
  screenshotState.value.selection.currentX = currentX
  screenshotState.value.selection.currentY = currentY
  
  // 计算选择框位置和大小
  updateSelectionBounds(imageBounds)
}

// 选择结束
function endSelection(event) {
  if (!screenshotState.value.isSelecting) return
  
  screenshotState.value.isSelecting = false
  
  const selection = screenshotState.value.selection
  
  // 检查选择框是否有效
  if (selection.width < 5 || selection.height < 5) {
    console.log('选择区域太小，重置状态')
    resetScreenshotState()
  } else {
    console.log(`选择完成: ${Math.round(selection.width)} × ${Math.round(selection.height)}`)
  }
  
  if (event) {
    event.stopPropagation()
  }
}

// 取消选择
function cancelSelection() {
  if (screenshotState.value.isSelecting && !screenshotState.value.isDragging) {
    resetScreenshotState()
  }
}

// 辅助函数：检查点是否在图片范围内
function isPointInImageBounds(x, y, imageBounds) {
  return x >= imageBounds.left && x <= imageBounds.left + imageBounds.width &&
         y >= imageBounds.top && y <= imageBounds.top + imageBounds.height
}

// 辅助函数：更新选择框边界
function updateSelectionBounds(imageBounds) {
  const selection = screenshotState.value.selection
  
  // 限制坐标在图片范围内
  const constrainedStartX = Math.max(imageBounds.left, Math.min(selection.startX, imageBounds.left + imageBounds.width))
  const constrainedStartY = Math.max(imageBounds.top, Math.min(selection.startY, imageBounds.top + imageBounds.height))
  const constrainedCurrentX = Math.max(imageBounds.left, Math.min(selection.currentX, imageBounds.left + imageBounds.width))
  const constrainedCurrentY = Math.max(imageBounds.top, Math.min(selection.currentY, imageBounds.top + imageBounds.height))
  
  // 计算选择框的最终位置和大小
  selection.x = Math.min(constrainedStartX, constrainedCurrentX)
  selection.y = Math.min(constrainedStartY, constrainedCurrentY)
  selection.width = Math.abs(constrainedCurrentX - constrainedStartX)
  selection.height = Math.abs(constrainedCurrentY - constrainedStartY)
}

// 确认截图
function confirmScreenshot() {
  // 立即停止任何正在进行的选择操作
  screenshotState.value.isSelecting = false
  
  const imageBounds = getImageBounds()
  const selection = screenshotState.value.selection
  
  if (!imageBounds || !fullImageRef.value?.complete) {
    alert('截图失败：图片未准备好')
    return
  }
  
  if (!selection.visible || selection.width < 5 || selection.height < 5) {
    alert('截图失败：请选择一个有效的区域')
    return
  }
  
  screenshotLoading.value = true
  
  try {
    const canvas = document.createElement('canvas')
    const ctx = canvas.getContext('2d')
    
    // 计算缩放比例
    const scaleX = imageBounds.naturalWidth / imageBounds.width
    const scaleY = imageBounds.naturalHeight / imageBounds.height
    
    // 计算在原始图片上的坐标
    const sourceX = Math.max(0, (selection.x - imageBounds.left) * scaleX)
    const sourceY = Math.max(0, (selection.y - imageBounds.top) * scaleY)
    const sourceWidth = Math.min(imageBounds.naturalWidth - sourceX, selection.width * scaleX)
    const sourceHeight = Math.min(imageBounds.naturalHeight - sourceY, selection.height * scaleY)
    
    console.log('截图参数:', { sourceX, sourceY, sourceWidth, sourceHeight })
    
    canvas.width = sourceWidth
    canvas.height = sourceHeight
    
    // 绘制截图
    ctx.drawImage(
      fullImageRef.value,
      sourceX, sourceY, sourceWidth, sourceHeight,
      0, 0, sourceWidth, sourceHeight
    )
    
    const dataUrl = canvas.toDataURL('image/png')
    
    if (dataUrl && dataUrl !== 'data:,') {
      screenshotData.value = dataUrl
      screenshotWidth.value = Math.round(sourceWidth)
      screenshotHeight.value = Math.round(sourceHeight)
      console.log('截图成功')
      exitScreenshotMode()
    } else {
      throw new Error('无法生成截图数据')
    }
    
  } catch (error) {
    console.error('Screenshot failed:', error)
    alert(`截图失败: ${error.message}`)
  } finally {
    screenshotLoading.value = false
  }
}

// 取消截图
function cancelScreenshot() {
  exitScreenshotMode()
}

// 检查OCR服务状态
async function checkOCRStatus() {
  try {
    const url = `${API}/api/gallery/ocr/status`
    const { data } = await axios.get(url)
    
    if (!data.is_loaded) {
      console.warn('OCR服务未加载:', data.error || '模型未启动')
    } else {
      console.log('OCR服务正常')
    }
    
  } catch (error) {
    console.error('检查OCR状态失败:', error)
  }
}

// 检查翻译服务状态
async function checkTranslationStatus() {
  try {
    const url = `${API}/api/gallery/translate/status`
    const { data } = await axios.get(url)
    
    if (!data.is_initialized) {
      console.warn('翻译服务未初始化:', data.error || '服务未启动')
    } else if (!data.api_key_available) {
      console.warn('翻译服务 API Key 未配置')
    } else {
      console.log('翻译服务正常，模型:', data.model_name)
    }
    
  } catch (error) {
    console.error('检查翻译状态失败:', error)
  }
}

async function performOCR() {
  if (!screenshotData.value) return
  
  ocrLoading.value = true
  
  try {
    const url = `${API}/api/gallery/ocr`
    const { data } = await axios.post(url, {
      image: screenshotData.value
    })
    
    if (data.success) {
      ocrResult.value = data.text || ''
      console.log('OCR识别完成，文本长度:', data.length || 0)
    } else {
      console.error('OCR识别失败:', data.error)
      ocrResult.value = ''
    }
    
  } catch (error) {
    console.error('OCR请求失败:', error)
    ocrResult.value = ''
    
    // 显示错误信息给用户
    if (error.response?.data?.detail) {
      alert(`OCR失败: ${error.response.data.detail}`)
    } else {
      alert('OCR识别失败，请检查网络连接和后端服务')
    }
  } finally {
    ocrLoading.value = false
  }
}

async function performTranslation() {
  if (!ocrResult.value.trim()) return
  
  translationLoading.value = true
  
  try {
    const url = `${API}/api/gallery/translate`
    const { data } = await axios.post(url, {
      text: ocrResult.value,
      target_language: targetLanguage.value
    })
    
    if (data.success) {
      translationResult.value = data.translation || ''
      console.log('翻译完成，目标语言:', data.target_language)
      console.log('翻译结果:', data.translation)
    } else {
      console.error('翻译失败:', data.error)
      translationResult.value = ''
    }
    
  } catch (error) {
    console.error('翻译请求失败:', error)
    translationResult.value = ''
    
    // 显示错误信息给用户
    if (error.response?.data?.detail) {
      alert(`翻译失败: ${error.response.data.detail}`)
    } else {
      alert('翻译失败，请检查网络连接和后端服务')
    }
  } finally {
    translationLoading.value = false
  }
}

function copyTranslation() {
  if (translationResult.value.trim()) {
    navigator.clipboard.writeText(translationResult.value)
    console.log('Translation copied to clipboard')
  }
}

function saveTranslation() {
  // TODO: 实现保存翻译功能
  console.log('Save translation functionality will be implemented')
  const data = {
    page: currentPage.value,
    screenshot: screenshotData.value,
    ocrResult: ocrResult.value,
    translation: translationResult.value,
    targetLanguage: targetLanguage.value
  }
  console.log('Translation data:', data)
}
</script>

<style src="../assets/ImageViewer.css"></style>