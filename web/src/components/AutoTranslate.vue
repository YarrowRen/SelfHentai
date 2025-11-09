<template>
  <div class="auto-translate-container">
    <!-- 主要内容区域 -->
    <div class="main-content">
      <!-- 左侧图片区域 (40%) -->
      <div class="image-section">
        <div class="image-container" ref="imageContainer">
          <!-- 原图 -->
          <img 
            ref="mangaImage"
            :src="currentImageUrl" 
            alt="Manga page"
            class="manga-image"
            @load="onImageLoad"
            @error="onImageError"
          />
          
          <!-- OCR 检测框覆盖层 -->
          <div class="ocr-overlay" v-if="ocrResults.length > 0 && showTextBoxes">
            <div
              v-for="(result, index) in ocrResults"
              :key="index"
              class="text-box"
              :style="getTextBoxStyle(result.bbox)"
              @click="selectTextBox(index)"
              :class="{ active: selectedTextIndex === index }"
            >
            </div>
          </div>
          
          <!-- 加载状态 -->
          <div v-if="imageLoading" class="loading-overlay">
            <div class="spinner"></div>
            <p>加载中...</p>
          </div>
        </div>
      </div>

      <!-- 中间功能区域 (30%) -->
      <div class="function-section">
        <!-- 返回和页面控制 -->
        <div class="control-panel">
          
          <!-- 返回按钮 -->
          <button class="action-btn back-btn" @click="goBack">
            ← 返回
          </button>

          <!-- 页面控制 -->
          <div class="page-navigation">
            <div class="page-controls-row">
              <button 
                class="page-btn" 
                @click="previousPage" 
                :disabled="currentPage <= 0"
              >
                ← 上一页
              </button>
              <button 
                class="page-btn" 
                @click="nextPage" 
                :disabled="currentPage >= totalPages - 1"
              >
                下一页 →
              </button>
            </div>
            <div class="page-input-row">
              <input 
                type="number" 
                v-model.number="pageInput" 
                :min="1" 
                :max="totalPages"
                class="page-input"
                @keyup.enter="jumpToPage"
              />
              <span class="page-total">/ {{ totalPages }}</span>
              <button class="jump-btn" @click="jumpToPage">跳转</button>
            </div>
          </div>

          <!-- OCR和翻译控制 -->
          <div class="ocr-controls">
            <div class="ocr-button-row">
              <button 
                class="action-btn ocr-btn" 
                @click="performOCR"
                :disabled="ocrProcessing"
              >
                <span v-if="ocrProcessing">处理中...</span>
                <span v-else>开始识别</span>
              </button>
              
              <button 
                class="action-btn translate-btn" 
                @click="translateAllTexts"
                :disabled="!hasOcrResults || translating"
              >
                <span v-if="translating">翻译中...</span>
                <span v-else>翻译全部</span>
              </button>
            </div>

            <!-- 语言选择 -->
            <div class="language-selector">
              <select v-model="sourceLanguage" class="language-select">
                <option value="japan">日语</option>
                <option value="en">英语</option>
                <option value="ch">中文简体</option>
                <option value="chinese_cht">中文繁体</option>
              </select>
              <span class="arrow">→</span>
              <select v-model="targetLanguage" class="language-select">
                <option value="zh">中文</option>
                <option value="en">英语</option>
                <option value="ja">日语</option>
              </select>
            </div>

            <!-- 高级参数 -->
            <div class="advanced-params">
              <h5>高级参数</h5>
              <div class="param-row">
                <label>检测限制类型:</label>
                <select v-model="ocrParams.det_limit_type" class="param-select">
                  <option value="max">最大</option>
                  <option value="min">最小</option>
                </select>
              </div>
              <div class="param-row">
                <label>检测边长限制:</label>
                <input 
                  v-model.number="ocrParams.det_limit_side_len" 
                  type="number" 
                  min="320" 
                  max="2880" 
                  step="40"
                  class="param-input"
                />
              </div>
              <div class="param-row">
                <label>置信度阈值:</label>
                <input 
                  v-model.number="ocrParams.confidence_threshold" 
                  type="number" 
                  min="0.1" 
                  max="1.0" 
                  step="0.05"
                  class="param-input"
                />
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧结果区域 (30%) -->
      <div class="results-section-wrapper">

        <!-- OCR 结果显示 -->
        <div class="results-section">
          <div class="results-header">
            <h4>识别结果 ({{ ocrResults.length }})</h4>
            <div v-if="ocrResults.length > 0" class="toggle-switch-container">
              <label class="toggle-switch">
                <input type="checkbox" v-model="showTextBoxes">
                <span class="toggle-slider"></span>
              </label>
              <span class="toggle-label">显示框框</span>
            </div>
          </div>
          
          <div v-if="ocrResults.length === 0" class="no-results">
            点击"开始OCR识别"来识别图片中的文本
          </div>
          
          <div v-else class="results-list">
            <div 
              v-for="(result, index) in ocrResults"
              :key="index"
              class="result-item"
              :class="{ active: selectedTextIndex === index }"
              @click="selectTextBox(index)"
            >
              <div class="result-header">
                <span class="result-index">{{ index + 1 }}</span>
                <span class="confidence-score">置信度: {{ (result.confidence * 100).toFixed(1) }}%</span>
                <span v-if="result.is_merged" class="merged-badge">合并 ({{ result.original_count }})</span>
              </div>
              
              <div class="text-content">
                <div class="original-text">
                  <strong>原文:</strong>
                  <p>{{ result.text }}</p>
                  <div v-if="result.is_merged && result.original_texts.length > 1" class="merged-details">
                    <details>
                      <summary>查看原始文本 ({{ result.original_count }})</summary>
                      <ul class="original-text-list">
                        <li v-for="(text, i) in result.original_texts" :key="i">{{ text }}</li>
                      </ul>
                    </details>
                  </div>
                </div>
                
                <div v-if="result.translation" class="translated-text">
                  <strong>译文:</strong>
                  <p>{{ result.translation }}</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 处理状态 -->
        <div v-if="processingStatus" class="status-section">
          <h4>处理状态</h4>
          <div class="status-message" :class="statusType">
            {{ processingStatus }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

const API = import.meta.env.VITE_API_BASE;

export default {
  name: 'AutoTranslate',
  props: {
    gid: String,
    token: String,
    id: String // for JM provider
  },
  data() {
    return {
      // 基础信息
      provider: 'ex',
      galleryData: null,
      galleryTitle: '',
      
      // 分页相关
      currentPage: 0,
      totalPages: 0,
      imageList: [],
      pageInput: 1,
      
      // 图片相关
      currentImageUrl: '',
      originalImageUrl: '', // 用于OCR的原始URL
      imageLoading: false,
      imageError: false,
      
      // OCR 相关
      ocrResults: [],
      ocrProcessing: false,
      selectedTextIndex: -1,
      showTextBoxes: true, // 默认显示矩形框
      
      // 翻译相关
      translating: false,
      sourceLanguage: 'japan',
      targetLanguage: 'zh',
      
      // OCR 高级参数
      ocrParams: {
        det_limit_type: 'max',
        det_limit_side_len: 960,
        use_doc_orientation_classify: false,
        use_doc_unwarping: false,
        confidence_threshold: 0.75
      },
      
      // 状态信息
      processingStatus: '',
      statusType: 'info', // info, success, error
      
      // UI 相关
      imageScale: 1,
      imageOffset: { x: 0, y: 0 },
      
      // 响应式支持
      windowResizeTimer: null
    }
  },
  computed: {
    hasOcrResults() {
      return this.ocrResults.length > 0
    },
    
    currentImageData() {
      return this.imageList[this.currentPage] || null
    }
  },
  async mounted() {
    await this.initializeComponent()
    
    // 添加窗口大小变化监听器
    window.addEventListener('resize', this.handleWindowResize)
  },
  methods: {
    async initializeComponent() {
      try {
        // 判断提供商
        if (this.$route.path.includes('/jm/')) {
          this.provider = 'jm'
        }
        
        // 获取画廊信息
        await this.loadGalleryData()
        
        // 加载第一页图片
        await this.loadCurrentImage()
        
      } catch (error) {
        console.error('初始化失败:', error)
        this.setStatus('初始化失败: ' + error.message, 'error')
      }
    },
    
    async loadGalleryData() {
      try {
        let url
        
        if (this.provider === 'ex') {
          url = `${API}/api/gallery/item/${this.gid}`
        } else {
          url = `${API}/api/gallery/jm/item/${this.id}`
        }
        
        const { data } = await axios.get(url)
        this.galleryData = data
        this.galleryTitle = data.title || data.title_jpn || `Gallery ${this.gid || this.id}`
        
        // 根据页数设置总页数
        this.totalPages = data.filecount || data.episode_list?.length || 20
        
        this.setStatus('画廊信息加载完成', 'success')
      } catch (error) {
        throw new Error('无法加载画廊数据: ' + error.message)
      }
    },
    
    async loadCurrentImage() {
      if (this.currentPage < 0 || this.currentPage >= this.totalPages) {
        return
      }
      
      this.imageLoading = true
      this.imageError = false
      this.ocrResults = []
      
      try {
        this.setStatus(`正在加载第 ${this.currentPage + 1} 页...`, 'info')
        
        if (this.provider === 'ex') {
          // 使用现有的API获取完整图片信息
          const url = `${API}/api/gallery/ex/full-image/${this.gid}/${this.token}/${this.currentPage + 1}`
          const { data } = await axios.get(url)
          
          // 保存原始URL用于OCR，代理URL用于显示
          this.originalImageUrl = data.imageUrl
          const proxyImageUrl = `${API}/api/gallery/ex/proxy-image?url=${encodeURIComponent(data.imageUrl)}`
          this.currentImageUrl = proxyImageUrl
          
        } else {
          // JM的图片URL（需要根据实际JM API调整）
          this.currentImageUrl = `${API}/api/gallery/jm/${this.id}/image/${this.currentPage + 1}`
        }
        
      } catch (error) {
        this.imageError = true
        this.setStatus('图片加载失败: ' + error.message, 'error')
        console.error('图片加载失败:', error)
      }
    },
    
    onImageLoad() {
      this.imageLoading = false
      this.setStatus(`第 ${this.currentPage + 1} 页加载完成`, 'success')
      
      // 图片加载完成后重绘矩形框
      this.$nextTick(() => {
        this.redrawTextBoxes()
      })
    },
    
    onImageError() {
      this.imageLoading = false
      this.imageError = true
      this.setStatus('图片加载失败', 'error')
    },
    
    async performOCR() {
      if (!this.currentImageUrl) {
        this.setStatus('没有可用的图片进行OCR识别', 'error')
        return
      }
      
      this.ocrProcessing = true
      this.setStatus('正在进行OCR识别...', 'info')
      
      try {
        // 使用原始URL进行OCR识别，避免循环调用
        const imageUrlForOCR = this.originalImageUrl || this.currentImageUrl
        
        const response = await axios.post(`${API}/api/ocr/recognize`, {
          image_url: imageUrlForOCR,
          language: this.sourceLanguage,
          page_number: this.currentPage + 1,
          gallery_id: this.gid || this.id,
          provider: this.provider,
          // 添加高级参数
          det_limit_type: this.ocrParams.det_limit_type,
          det_limit_side_len: this.ocrParams.det_limit_side_len,
          use_doc_orientation_classify: this.ocrParams.use_doc_orientation_classify,
          use_doc_unwarping: this.ocrParams.use_doc_unwarping,
          confidence_threshold: this.ocrParams.confidence_threshold
        })
        
        if (response.data.success) {
          this.ocrResults = response.data.results.map((result, index) => ({
            id: index,
            text: result.text,
            confidence: result.confidence,
            bbox: result.bbox, // [x1, y1, x2, y2]
            translation: null,
            is_merged: result.is_merged || false,
            original_count: result.original_count || 1,
            original_texts: result.original_texts || [result.text]
          }))
          
          this.setStatus(`OCR识别完成，识别到 ${this.ocrResults.length} 个文本区域`, 'success')
          
          // OCR完成后确保矩形框正确绘制
          this.$nextTick(() => {
            this.redrawTextBoxes()
          })
        } else {
          this.setStatus('OCR识别失败: ' + response.data.error, 'error')
        }
      } catch (error) {
        console.error('OCR error:', error)
        this.setStatus('OCR识别出错: ' + error.message, 'error')
      } finally {
        this.ocrProcessing = false
      }
    },
    
    async translateAllTexts() {
      if (this.ocrResults.length === 0) {
        this.setStatus('没有可翻译的文本', 'error')
        return
      }
      
      this.translating = true
      this.setStatus(`正在翻译 ${this.ocrResults.length} 个文本...`, 'info')
      
      try {
        const textsToTranslate = this.ocrResults.map(result => result.text)
        
        const response = await axios.post(`${API}/api/ocr/translate/batch`, {
          texts: textsToTranslate,
          source_language: this.sourceLanguage,
          target_language: this.targetLanguage
        })
        
        if (response.data.success) {
          response.data.translations.forEach((translation, index) => {
            if (this.ocrResults[index]) {
              this.ocrResults[index].translation = translation
            }
          })
          
          this.setStatus('翻译完成', 'success')
        } else {
          this.setStatus('翻译失败: ' + response.data.error, 'error')
        }
      } catch (error) {
        console.error('Translation error:', error)
        this.setStatus('翻译出错: ' + error.message, 'error')
      } finally {
        this.translating = false
      }
    },
    
    selectTextBox(index) {
      this.selectedTextIndex = index
    },
    
    getTextBoxStyle(bbox) {
      if (!bbox || bbox.length !== 4) return { display: 'none' }
      
      // 获取图片元素
      const imgElement = this.$refs.mangaImage
      if (!imgElement) return { display: 'none' }
      
      // 确保图片已加载且有自然尺寸
      if (!imgElement.naturalWidth || !imgElement.naturalHeight) {
        return { display: 'none' }
      }
      
      const imgRect = imgElement.getBoundingClientRect()
      const containerRect = this.$refs.imageContainer.getBoundingClientRect()
      
      // 检查容器是否可见
      if (containerRect.width === 0 || containerRect.height === 0) {
        return { display: 'none' }
      }
      
      // 计算相对于容器的位置
      const relativeX = imgRect.left - containerRect.left
      const relativeY = imgRect.top - containerRect.top
      
      // 计算缩放比例
      const scaleX = imgElement.clientWidth / imgElement.naturalWidth
      const scaleY = imgElement.clientHeight / imgElement.naturalHeight
      
      const [x1, y1, x2, y2] = bbox
      
      // 计算矩形框的位置和大小
      const left = relativeX + x1 * scaleX
      const top = relativeY + y1 * scaleY
      const width = (x2 - x1) * scaleX
      const height = (y2 - y1) * scaleY
      
      return {
        position: 'absolute',
        left: Math.round(left) + 'px',
        top: Math.round(top) + 'px',
        width: Math.round(width) + 'px',
        height: Math.round(height) + 'px',
        display: 'block'
      }
    },
    
    previousPage() {
      if (this.currentPage > 0) {
        this.currentPage--
        this.pageInput = this.currentPage + 1
        this.loadCurrentImage()
      }
    },
    
    nextPage() {
      if (this.currentPage < this.totalPages - 1) {
        this.currentPage++
        this.pageInput = this.currentPage + 1
        this.loadCurrentImage()
      }
    },
    
    jumpToPage() {
      const targetPage = this.pageInput - 1
      if (targetPage >= 0 && targetPage < this.totalPages && targetPage !== this.currentPage) {
        this.currentPage = targetPage
        this.loadCurrentImage()
      }
    },
    
    goBack() {
      this.$router.go(-1)
    },
    
    handleWindowResize() {
      // 使用防抖处理，避免频繁重绘
      if (this.windowResizeTimer) {
        clearTimeout(this.windowResizeTimer)
      }
      
      this.windowResizeTimer = setTimeout(() => {
        this.redrawTextBoxes()
      }, 150)
    },
    
    redrawTextBoxes() {
      // 强制重新计算矩形框位置
      if (this.ocrResults.length > 0) {
        // 触发Vue的重新渲染
        this.$forceUpdate()
      }
    },
    
    setStatus(message, type = 'info') {
      this.processingStatus = message
      this.statusType = type
      
      // 3秒后清除状态（除了错误状态）
      if (type !== 'error') {
        setTimeout(() => {
          if (this.processingStatus === message) {
            this.processingStatus = ''
          }
        }, 3000)
      }
    }
  },
  
  beforeUnmount() {
    // 清理资源
    this.ocrResults = []
    
    // 移除窗口大小变化监听器
    window.removeEventListener('resize', this.handleWindowResize)
    
    // 清理定时器
    if (this.windowResizeTimer) {
      clearTimeout(this.windowResizeTimer)
    }
  }
}
</script>

<style src="@/assets/AutoTranslate.css" scoped></style>