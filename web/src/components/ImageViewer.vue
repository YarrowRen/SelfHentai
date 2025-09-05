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
            @mousedown="startSelection"
            @mousemove="updateSelection"
            @mouseup="endSelection"
            @mouseleave="cancelSelection"
          >
            <!-- 选择框 -->
            <div 
              v-if="selectionBox.visible"
              class="selection-box"
              :style="{
                left: selectionBox.x + 'px',
                top: selectionBox.y + 'px',
                width: selectionBox.width + 'px',
                height: selectionBox.height + 'px'
              }"
            >
              <div class="selection-border"></div>
              <div class="selection-info">
                {{ Math.round(selectionBox.width) }} × {{ Math.round(selectionBox.height) }}
              </div>
            </div>
            
            <!-- 确认按钮 -->
            <div 
              v-if="selectionBox.visible && selectionBox.width > 10 && selectionBox.height > 10"
              class="screenshot-actions"
              :style="{
                left: (selectionBox.x + selectionBox.width + 10) + 'px',
                top: selectionBox.y + 'px'
              }"
            >
              <Button 
                @click="confirmScreenshot"
                size="small"
                severity="success"
                class="confirm-btn"
              >
                ✓ Capture
              </Button>
              <Button 
                @click="cancelScreenshot"
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
                @click="startScreenshot"
                :disabled="screenshotLoading"
                :loading="screenshotLoading"
                class="screenshot-btn"
                severity="success"
              >
                <span class="btn-icon">✂️</span>
                <span class="btn-text">{{ screenshotLoading ? 'Processing...' : 'Take Screenshot' }}</span>
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
                <span class="btn-text">{{ translationLoading ? 'Translating...' : 'Translate' }}</span>
              </Button>
              
              <Dropdown 
                v-model="targetLanguage" 
                :options="languageOptions" 
                optionLabel="label" 
                optionValue="value"
                placeholder="Target Language"
                class="language-dropdown"
              />
            </div>

            <!-- AI翻译结果框（只读） -->
            <div class="text-result">
              <label class="result-label">{{ targetLanguageLabel }} Translation:</label>
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
import Dropdown from 'primevue/dropdown'
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

// 截图选择相关
const isScreenshotMode = ref(false)
const isSelecting = ref(false)
const selectionBox = ref({
  visible: false,
  x: 0,
  y: 0,
  width: 0,
  height: 0,
  startX: 0,
  startY: 0
})

const ocrResult = ref('')
const ocrLoading = ref(false)

const translationResult = ref('')
const translationLoading = ref(false)
const targetLanguage = ref('en')

// 语言选项
const languageOptions = ref([
  { label: 'English', value: 'en' },
  { label: '中文', value: 'zh' },
  { label: '한국어', value: 'ko' },
  { label: 'Français', value: 'fr' },
  { label: 'Deutsch', value: 'de' },
  { label: 'Español', value: 'es' },
  { label: 'Русский', value: 'ru' }
])

// 初始化
onMounted(() => {
  currentPage.value = pageNumber.value
  loadFullImage()
  checkOCRStatus()
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
  console.log('Image loaded successfully')
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

// 计算目标语言标签
const targetLanguageLabel = computed(() => {
  const option = languageOptions.value.find(opt => opt.value === targetLanguage.value)
  return option ? option.label : 'Translation'
})

// 翻译功能方法
function startScreenshot() {
  if (!fullImageRef.value) return
  
  isScreenshotMode.value = true
  // 重置选择框
  selectionBox.value = {
    visible: false,
    x: 0,
    y: 0,
    width: 0,
    height: 0,
    startX: 0,
    startY: 0
  }
}

function clearScreenshot() {
  screenshotData.value = null
  screenshotWidth.value = 0
  screenshotHeight.value = 0
  ocrResult.value = ''
  translationResult.value = ''
  isScreenshotMode.value = false
  selectionBox.value.visible = false
}

// 获取图片在容器中的实际位置和尺寸
function getImageBounds() {
  if (!fullImageRef.value) return null
  
  const img = fullImageRef.value
  const container = img.parentElement
  
  const imgRect = img.getBoundingClientRect()
  const containerRect = container.getBoundingClientRect()
  
  return {
    left: imgRect.left - containerRect.left,
    top: imgRect.top - containerRect.top,
    width: imgRect.width,
    height: imgRect.height,
    naturalWidth: img.naturalWidth,
    naturalHeight: img.naturalHeight
  }
}

// 开始选择
function startSelection(event) {
  const imageBounds = getImageBounds()
  if (!imageBounds) return
  
  const rect = event.currentTarget.getBoundingClientRect()
  const x = event.clientX - rect.left
  const y = event.clientY - rect.top
  
  // 检查是否在图片范围内
  if (x < imageBounds.left || x > imageBounds.left + imageBounds.width ||
      y < imageBounds.top || y > imageBounds.top + imageBounds.height) {
    return
  }
  
  isSelecting.value = true
  selectionBox.value.startX = x
  selectionBox.value.startY = y
  selectionBox.value.x = x
  selectionBox.value.y = y
  selectionBox.value.width = 0
  selectionBox.value.height = 0
  selectionBox.value.visible = true
  
  event.preventDefault()
}

// 更新选择
function updateSelection(event) {
  if (!isSelecting.value) return
  
  const imageBounds = getImageBounds()
  if (!imageBounds) return
  
  const rect = event.currentTarget.getBoundingClientRect()
  const currentX = event.clientX - rect.left
  const currentY = event.clientY - rect.top
  
  // 限制在图片范围内
  const constrainedX = Math.max(imageBounds.left, Math.min(currentX, imageBounds.left + imageBounds.width))
  const constrainedY = Math.max(imageBounds.top, Math.min(currentY, imageBounds.top + imageBounds.height))
  
  const startX = Math.max(imageBounds.left, Math.min(selectionBox.value.startX, imageBounds.left + imageBounds.width))
  const startY = Math.max(imageBounds.top, Math.min(selectionBox.value.startY, imageBounds.top + imageBounds.height))
  
  selectionBox.value.x = Math.min(startX, constrainedX)
  selectionBox.value.y = Math.min(startY, constrainedY)
  selectionBox.value.width = Math.abs(constrainedX - startX)
  selectionBox.value.height = Math.abs(constrainedY - startY)
}

// 结束选择
function endSelection() {
  isSelecting.value = false
}

// 取消选择
function cancelSelection() {
  if (isSelecting.value) {
    isSelecting.value = false
    selectionBox.value.visible = false
  }
}

// 确认截图
function confirmScreenshot() {
  const imageBounds = getImageBounds()
  if (!imageBounds || !selectionBox.value.visible) return
  
  screenshotLoading.value = true
  
  try {
    // 创建canvas进行截图
    const canvas = document.createElement('canvas')
    const ctx = canvas.getContext('2d')
    
    // 计算选择区域在原始图片上的位置
    const scaleX = imageBounds.naturalWidth / imageBounds.width
    const scaleY = imageBounds.naturalHeight / imageBounds.height
    
    const sourceX = (selectionBox.value.x - imageBounds.left) * scaleX
    const sourceY = (selectionBox.value.y - imageBounds.top) * scaleY
    const sourceWidth = selectionBox.value.width * scaleX
    const sourceHeight = selectionBox.value.height * scaleY
    
    canvas.width = sourceWidth
    canvas.height = sourceHeight
    
    // 绘制裁剪后的图片
    ctx.drawImage(
      fullImageRef.value,
      sourceX, sourceY, sourceWidth, sourceHeight,
      0, 0, sourceWidth, sourceHeight
    )
    
    // 转换为数据URL
    const dataUrl = canvas.toDataURL('image/png')
    
    screenshotData.value = dataUrl
    screenshotWidth.value = sourceWidth
    screenshotHeight.value = sourceHeight
    
    // 退出截图模式
    isScreenshotMode.value = false
    selectionBox.value.visible = false
    
  } catch (error) {
    console.error('Screenshot failed:', error)
  } finally {
    screenshotLoading.value = false
  }
}

// 取消截图
function cancelScreenshot() {
  isScreenshotMode.value = false
  selectionBox.value.visible = false
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

function performTranslation() {
  if (!ocrResult.value.trim()) return
  
  translationLoading.value = true
  // TODO: 实现AI翻译功能
  setTimeout(() => {
    translationLoading.value = false
    // 模拟翻译结果
    translationResult.value = 'This is a test translation result'
    console.log('Translation functionality will be implemented')
  }, 1500)
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