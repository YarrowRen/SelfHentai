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
            :src="fullImageUrl" 
            :alt="`Page ${currentPage}`"
            class="full-image"
            @error="handleImageError"
            @load="handleImageLoad"
          />
        </div>
      </div>

      <!-- 右侧表单区域 50% -->
      <div class="form-section">
        <div class="form-container">
          <h3>Image Details</h3>
          
          <div class="form-group">
            <label>Gallery:</label>
            <span>{{ galleryTitle || 'Unknown Gallery' }}</span>
          </div>
          
          <div class="form-group">
            <label>Page:</label>
            <span>{{ currentPage }} / {{ totalPages }}</span>
          </div>
          
          <div class="form-group">
            <label>Image Name:</label>
            <span>{{ imageName || 'Unknown' }}</span>
          </div>
          
          <div class="form-group">
            <label>Size:</label>
            <span v-if="imageSize">{{ imageSize.width }} x {{ imageSize.height }}</span>
            <span v-else>Loading...</span>
          </div>

          <!-- Demo表单 -->
          <Divider />
          <h4>Actions (Demo)</h4>
          
          <div class="form-group">
            <label for="rating">Rating:</label>
            <Rating v-model="demoRating" id="rating" />
          </div>
          
          <div class="form-group">
            <label for="tags">Tags:</label>
            <InputText v-model="demoTags" id="tags" placeholder="Add tags..." />
          </div>
          
          <div class="form-group">
            <label for="notes">Notes:</label>
            <Textarea v-model="demoNotes" id="notes" rows="4" placeholder="Add notes..." />
          </div>
          
          <div class="form-actions">
            <Button label="Save" icon="pi pi-save" />
            <Button label="Download" icon="pi pi-download" severity="secondary" />
            <Button label="Share" icon="pi pi-share-alt" severity="info" />
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
import InputText from 'primevue/inputtext'
import InputNumber from 'primevue/inputnumber'
import Textarea from 'primevue/textarea'
import Rating from 'primevue/rating'
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

// Demo表单数据
const demoRating = ref(0)
const demoTags = ref('')
const demoNotes = ref('')

// 初始化
onMounted(() => {
  currentPage.value = pageNumber.value
  loadFullImage()
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
    
    fullImageUrl.value = data.imageUrl
    imageName.value = data.imageName
    galleryTitle.value = data.galleryTitle
    totalPages.value = data.totalPages || 1
    
    // 获取图片尺寸
    if (fullImageUrl.value) {
      getImageSize(fullImageUrl.value)
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
</script>

<style src="../assets/ImageViewer.css"></style>