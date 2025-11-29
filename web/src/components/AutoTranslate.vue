<template>
  <div class="auto-translate-container" :class="{ 'delete-mode': deleteMode }">
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
              @click="handleTextBoxClick(index)"
              :class="{ 
                active: selectedTextIndex === index,
                'selected-for-delete': deleteMode && selectedForDelete.includes(index),
                'text-replace-mode': textReplaceMode && result.translation
              }"
            >
              <!-- 文字替换模式下显示翻译文字 -->
              <div 
                v-if="textReplaceMode && result.translation" 
                class="replacement-text"
                :class="{ 'text-fit-ready': textFitReadyStates[index] }"
                :ref="el => { if (el) setTextFitRef(el, index) }"
                :data-index="index"
              >
                {{ result.translation }}
              </div>
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
              
              <button 
                class="action-btn text-replace-btn" 
                @click="toggleTextReplaceMode"
                :disabled="!hasTranslations"
                :class="{ active: textReplaceMode }"
              >
                <span v-if="textReplaceMode">退出替换</span>
                <span v-else>文字替换</span>
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
            
            <!-- 独立的删除按钮区域 -->
            <div class="delete-control-section">
              <button 
                class="action-btn delete-btn" 
                @click="toggleDeleteMode"
                :disabled="!hasOcrResults"
                :class="{ active: deleteMode }"
              >
                <span v-if="deleteMode && selectedForDelete.length > 0">
                  删除选中 ({{ selectedForDelete.length }})
                </span>
                <span v-else-if="deleteMode">
                  取消删除
                </span>
                <span v-else>
                  删除
                </span>
              </button>
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
              :class="{ 
                active: selectedTextIndex === index,
                'selected-for-delete': deleteMode && selectedForDelete.includes(index)
              }"
              @click="handleResultItemClick(index)"
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
      
      // 删除模式相关
      deleteMode: false,
      selectedForDelete: [], // 选中要删除的项目索引数组
      
      // 翻译相关
      translating: false,
      sourceLanguage: 'japan',
      targetLanguage: 'zh',
      
      // 文字替换模式相关
      textReplaceMode: false,
      textFitElements: {}, // 存储文字元素引用
      textFitReadyStates: {}, // 记录每个文字是否已经调整完成
      
      // OCR 高级参数
      ocrParams: {
        det_limit_type: 'max',
        det_limit_side_len: 960,
        use_doc_orientation_classify: false,
        use_doc_unwarping: false,
        confidence_threshold: 0.5
      },
      
      // 状态信息
      processingStatus: '',
      statusType: 'info', // info, success, error
      
      // 响应式支持
      windowResizeTimer: null
    }
  },
  computed: {
    hasOcrResults() {
      return this.ocrResults.length > 0
    },
    
    hasTranslations() {
      return this.ocrResults.some(result => result.translation && result.translation.trim())
    }
  },
  async mounted() {
    await this.initializeComponent()
    
    // 监听窗口和全屏状态变化
    window.addEventListener('resize', this.handleWindowResize)
    document.addEventListener('fullscreenchange', this.handleWindowResize)
    document.addEventListener('webkitfullscreenchange', this.handleWindowResize)
    document.addEventListener('mozfullscreenchange', this.handleWindowResize)
    document.addEventListener('MSFullscreenChange', this.handleWindowResize)
  },
  methods: {
    async initializeComponent() {
      try {
        
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
        const url = `${API}/api/gallery/item/${this.gid}`
        
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
      this.textReplaceMode = false // 切换页面时退出文字替换模式
      
      try {
        this.setStatus(`正在加载第 ${this.currentPage + 1} 页...`, 'info')
        
        // 使用ExHentai API获取完整图片信息
        const url = `${API}/api/gallery/ex/full-image/${this.gid}/${this.token}/${this.currentPage + 1}`
        const { data } = await axios.get(url)
        
        // 保存原始URL用于OCR，代理URL用于显示
        this.originalImageUrl = data.imageUrl
        const proxyImageUrl = `${API}/api/gallery/ex/proxy-image?url=${encodeURIComponent(data.imageUrl)}`
        this.currentImageUrl = proxyImageUrl
        
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
          
          // 根据翻译方法显示不同的成功消息
          const translationMethod = response.data.translation_method
          let successMessage = '翻译完成'
          
          if (translationMethod === 'japanese_manga_prompt') {
            successMessage = '日译中翻译完成（使用漫画专用模型）'
          } else if (translationMethod === 'passthrough') {
            successMessage = '暂不支持该语言组合，显示原文'
          }
          
          this.setStatus(successMessage, 'success')
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
      // 如果点击的是已选中的项目，则取消选中
      if (this.selectedTextIndex === index) {
        this.selectedTextIndex = -1
      } else {
        this.selectedTextIndex = index
      }
    },
    
    // 处理文本框点击事件
    handleTextBoxClick(index) {
      if (this.deleteMode) {
        this.toggleSelectionForDelete(index)
      } else {
        this.selectTextBox(index)
      }
    },
    
    // 处理结果项点击事件
    handleResultItemClick(index) {
      if (this.deleteMode) {
        this.toggleSelectionForDelete(index)
      } else {
        this.selectTextBox(index)
      }
    },
    
    // 切换选择状态（用于删除）
    toggleSelectionForDelete(index) {
      const currentIndex = this.selectedForDelete.indexOf(index)
      if (currentIndex > -1) {
        // 如果已经选中，则取消选中
        this.selectedForDelete.splice(currentIndex, 1)
      } else {
        // 如果未选中，则添加到选中列表
        this.selectedForDelete.push(index)
      }
    },
    
    // 切换删除模式
    toggleDeleteMode() {
      if (this.deleteMode) {
        // 退出删除模式
        if (this.selectedForDelete.length > 0) {
          // 如果有选中的项目，执行删除
          this.deleteSelectedResults()
        } else {
          // 如果没有选中项目，直接退出删除模式
          this.exitDeleteMode()
        }
      } else {
        // 进入删除模式
        this.enterDeleteMode()
      }
    },
    
    // 进入删除模式
    enterDeleteMode() {
      this.deleteMode = true
      this.selectedForDelete = []
      this.selectedTextIndex = -1
      this.setStatus('进入删除模式，点击选择要删除的文本', 'info')
    },
    
    // 退出删除模式
    exitDeleteMode() {
      this.deleteMode = false
      this.selectedForDelete = []
      this.setStatus('已退出删除模式', 'info')
    },
    
    // 删除选中的结果
    deleteSelectedResults() {
      if (this.selectedForDelete.length === 0) {
        this.setStatus('没有选中要删除的项目', 'warning')
        return
      }
      
      const deleteCount = this.selectedForDelete.length
      
      // 按索引从大到小排序，确保删除时不会影响后续索引
      const sortedIndices = [...this.selectedForDelete].sort((a, b) => b - a)
      
      // 执行删除
      sortedIndices.forEach(index => {
        this.ocrResults.splice(index, 1)
      })
      
      // 重新分配ID，确保连续性
      this.ocrResults.forEach((result, newIndex) => {
        result.id = newIndex
      })
      
      // 退出删除模式
      this.exitDeleteMode()
      
      // 更新状态提示
      if (this.ocrResults.length === 0) {
        this.setStatus('所有识别结果已清空', 'info')
      } else {
        this.setStatus(`删除成功，删除了 ${deleteCount} 个识别结果，剩余 ${this.ocrResults.length} 个`, 'success')
      }
      
      // 强制重新渲染
      this.$forceUpdate()
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
        
        // 文字替换模式下重新适配文字大小
        if (this.textReplaceMode && this.hasTranslations) {
          // 等待DOM重新渲染完成后再进行文字适配
          setTimeout(() => {
            this.initializeSmartTextFit()
          }, 150)
        }
      }, 100)
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
    },

    // 设置文字元素引用
    setTextFitRef(el, index) {
      if (!this.textFitElements) {
        this.textFitElements = {}
      }
      this.textFitElements[index] = el
    },

    // 初始化智能文字适配
    initializeSmartTextFit() {
      if (!this.textFitElements) {
        this.textFitElements = {}
      }
      if (!this.textFitReadyStates) {
        this.textFitReadyStates = {}
      }
      
      this.clearTextFitStates()
      
      this.$nextTick(() => {
        setTimeout(() => {
          // 重新获取所有元素引用，确保引用有效
          this.refreshTextFitElements()
          
          this.ocrResults.forEach((result, index) => {
            if (result.translation) {
              const element = this.textFitElements[index]
              
              if (element) {
                this.fitTextToContainer(element, result.translation, index)
              }
            }
          })
        }, 50)
      })
    },

    // 刷新文字元素引用
    refreshTextFitElements() {
      this.ocrResults.forEach((result, index) => {
        if (result.translation) {
          const elementByRef = this.$refs.imageContainer?.querySelector(`[data-index="${index}"]`)
          if (elementByRef) {
            this.textFitElements[index] = elementByRef
          }
        }
      })
    },

    // 智能文字适配算法 - 横排模式
    fitTextToContainer(element, text, index) {
      try {
        const container = element.parentElement
        if (!container) return

        // 强制重新布局，确保获取到最新的尺寸
        container.offsetHeight
        
        // 获取容器尺寸（减去padding）
        const containerStyle = window.getComputedStyle(container)
        const containerWidth = container.clientWidth - 
          parseFloat(containerStyle.paddingLeft) - 
          parseFloat(containerStyle.paddingRight)
        const containerHeight = container.clientHeight - 
          parseFloat(containerStyle.paddingTop) - 
          parseFloat(containerStyle.paddingBottom)

        if (containerWidth <= 0 || containerHeight <= 0) {
          // 容器尺寸异常，延迟重试
          setTimeout(() => {
            this.fitTextToContainer(element, text, index)
          }, 100)
          return
        }

        // 设置文本内容和基础样式
        element.textContent = text
        element.style.overflow = 'hidden'
        element.style.width = '100%'
        element.style.height = '100%'
        element.style.display = 'flex'
        element.style.alignItems = 'center'
        element.style.justifyContent = 'center'
        element.style.textAlign = 'center'

        // 横排模式
        element.style.writingMode = 'horizontal-tb'
        element.style.whiteSpace = 'pre-wrap'
        element.style.wordBreak = 'break-word'

        // 使用二分查找找到最佳字体大小
        let minSize = 6
        let maxSize = 100
        let bestSize = minSize
        let attempts = 0
        const maxAttempts = 20

        while (minSize <= maxSize && attempts < maxAttempts) {
          attempts++
          const currentSize = Math.floor((minSize + maxSize) / 2)
          element.style.fontSize = currentSize + 'px'
          
          // 设置行间距
          element.style.lineHeight = '1.2'
          element.style.letterSpacing = 'normal'

          // 强制重排获取准确尺寸
          element.offsetHeight

          const textWidth = element.scrollWidth
          const textHeight = element.scrollHeight


          // 检查是否同时满足宽高约束
          if (textWidth <= containerWidth && textHeight <= containerHeight) {
            bestSize = currentSize
            minSize = currentSize + 1 // 尝试更大的字体
          } else {
            maxSize = currentSize - 1 // 字体太大，减小
          }
        }

        // 应用最佳字体大小
        element.style.fontSize = bestSize + 'px'

        // 优化文字布局
        this.optimizeTextLayout(element, containerWidth, containerHeight, bestSize)

        // 标记为准备就绪
        this.textFitReadyStates[index] = true
        element.style.opacity = '1'

      } catch (error) {
        console.error(`文字适配失败 ${index}:`, error)
      }
    },


    // 优化文字布局
    optimizeTextLayout(element, containerWidth, containerHeight, fontSize) {
      // 尝试不同的行间距以获得更好的布局
      const lineHeights = [1.0, 1.1, 1.2, 1.3, 1.4]
      let bestLineHeight = 1.2

      for (const lineHeight of lineHeights) {
        element.style.lineHeight = lineHeight.toString()
        element.offsetHeight // 强制重排

        if (element.scrollWidth <= containerWidth && 
            element.scrollHeight <= containerHeight) {
          bestLineHeight = lineHeight
        } else {
          break // 超出容器，停止尝试
        }
      }

      element.style.lineHeight = bestLineHeight.toString()

      // 如果文字仍然过长，尝试添加换行
      if (element.scrollWidth > containerWidth) {
        this.addSmartLineBreaks(element, containerWidth)
      }
    },

    // 智能添加换行
    addSmartLineBreaks(element, containerWidth) {
      const text = element.textContent
      const words = text.split(/(\s+|[、，。！？；：])/g)
      let lines = []
      let currentLine = ''

      for (const word of words) {
        const testLine = currentLine + word
        element.textContent = testLine
        element.offsetHeight // 强制重排

        if (element.scrollWidth > containerWidth && currentLine.length > 0) {
          lines.push(currentLine.trim())
          currentLine = word
        } else {
          currentLine = testLine
        }
      }

      if (currentLine.trim().length > 0) {
        lines.push(currentLine.trim())
      }

      element.textContent = lines.join('\n')
    },
    
    // 清理文字适配状态
    clearTextFitStates() {
      if (this.textFitElements) {
        Object.keys(this.textFitElements).forEach(index => {
          const element = this.textFitElements[index]
          if (element) {
            element.style.fontSize = ''
            element.style.lineHeight = ''
            element.style.opacity = '0'
          }
        })
      }
      
      this.textFitReadyStates = {}
    },

    // 完全清理文字适配状态（退出模式时使用）
    fullClearTextFitStates() {
      if (this.textFitElements) {
        Object.keys(this.textFitElements).forEach(index => {
          const element = this.textFitElements[index]
          if (element) {
            element.style.fontSize = ''
            element.style.lineHeight = ''
            element.style.opacity = '0'
          }
        })
      }
      
      this.textFitElements = {}
      this.textFitReadyStates = {}
    },

    // 切换文字替换模式
    toggleTextReplaceMode() {
      if (this.textReplaceMode) {
        this.textReplaceMode = false
        this.fullClearTextFitStates()
        this.setStatus('已退出文字替换模式', 'info')
      } else {
        if (!this.hasTranslations) {
          this.setStatus('请先完成翻译后再使用文字替换功能', 'error')
          return
        }
        this.textReplaceMode = true
        this.setStatus('已进入智能文字替换模式', 'success')
        
        // 延迟初始化确保DOM渲染完成
        setTimeout(() => {
          this.initializeSmartTextFit()
        }, 100)
      }
    },

  },
  
  beforeUnmount() {
    this.ocrResults = []
    this.fullClearTextFitStates()
    
    // 移除事件监听器
    window.removeEventListener('resize', this.handleWindowResize)
    document.removeEventListener('fullscreenchange', this.handleWindowResize)
    document.removeEventListener('webkitfullscreenchange', this.handleWindowResize)
    document.removeEventListener('mozfullscreenchange', this.handleWindowResize)
    document.removeEventListener('MSFullscreenChange', this.handleWindowResize)
    
    if (this.windowResizeTimer) {
      clearTimeout(this.windowResizeTimer)
    }
  }
}
</script>

<style src="@/assets/AutoTranslate.css" scoped></style>