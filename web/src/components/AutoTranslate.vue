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
                :class="{ 'fitty-ready': fittyReadyStates[index] }"
                :ref="el => { if (el) setFittyRef(el, index) }"
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
import fitty from 'fitty'

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
      
      // 删除模式相关
      deleteMode: false,
      selectedForDelete: [], // 选中要删除的项目索引数组
      
      // 翻译相关
      translating: false,
      sourceLanguage: 'japan',
      targetLanguage: 'zh',
      
      // 文字替换模式相关
      textReplaceMode: false,
      fittyInstances: [], // 存储fitty实例
      fittyElements: {}, // 存储动态ref元素
      fittyReadyStates: {}, // 记录每个文字是否已经调整完成
      
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
    
    hasTranslations() {
      return this.ocrResults.some(result => result.translation && result.translation.trim())
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
    },

    // 设置动态ref
    setFittyRef(el, index) {
      this.fittyElements[index] = el
      console.log(`设置动态ref ${index}:`, el)
    },

    // 初始化Fitty文字适配
    initializeFitty() {
      console.log('开始初始化Fitty...')
      console.log('当前fittyElements:', this.fittyElements)
      
      // 只清理fitty实例，不清理元素引用
      this.fittyInstances.forEach(instance => {
        if (instance && typeof instance.unsubscribe === 'function') {
          instance.unsubscribe()
        }
      })
      this.fittyInstances = []
      
      this.$nextTick(() => {
        console.log('OCR结果数量:', this.ocrResults.length)
        
        // 为每个替换文字创建fitty实例
        this.ocrResults.forEach((result, index) => {
          if (result.translation) {
            console.log(`处理第${index}个翻译结果:`, result.translation)
            
            const element = this.fittyElements[index]
            console.log(`查找元素 ${index}:`, element)
            
            if (element) {
              console.log('找到DOM元素:', element)
              console.log('元素尺寸:', element.getBoundingClientRect())
              console.log('父容器尺寸:', element.parentElement?.getBoundingClientRect())
              
              // 添加事件监听器检测fitty是否工作
              element.addEventListener('fit', (e) => {
                console.log(`Fitty调整完成 - 索引${index}:`, e.detail)
                // 标记这个文字为准备就绪 - Vue 3 兼容写法
                this.fittyReadyStates[index] = true
              })
              
              const fittyInstance = fitty(element, {
                minSize: 8,
                maxSize: 48,
                multiLine: true, // 支持多行文字
                observeMutations: false // 我们手动控制更新
              })
              
              console.log('Fitty实例创建成功:', fittyInstance)
              this.fittyInstances.push(fittyInstance)
              
              // 强制触发一次fit
              setTimeout(() => {
                console.log('强制触发fit...')
                fittyInstance.fit({ sync: true })
              }, 200)
            } else {
              console.warn(`未找到索引${index}的DOM元素`)
            }
          } else {
            console.log(`第${index}个结果没有翻译`)
          }
        })
        
        console.log('Fitty实例总数:', this.fittyInstances.length)
      })
    },
    
    // 清理fitty实例
    clearFittyInstances() {
      console.log('清理Fitty实例...')
      this.fittyInstances.forEach(instance => {
        if (instance && typeof instance.unsubscribe === 'function') {
          instance.unsubscribe()
        }
      })
      this.fittyInstances = []
      this.fittyElements = {} // 清理元素引用
      this.fittyReadyStates = {} // 清理ready状态
    },

    // 文字替换模式相关方法
    toggleTextReplaceMode() {
      if (this.textReplaceMode) {
        // 退出文字替换模式
        this.textReplaceMode = false
        this.clearFittyInstances()
        this.setStatus('已退出文字替换模式', 'info')
      } else {
        // 进入文字替换模式
        if (!this.hasTranslations) {
          this.setStatus('请先完成翻译后再使用文字替换功能', 'error')
          return
        }
        this.textReplaceMode = true
        this.setStatus('已进入文字替换模式', 'success')
        
        // 延迟初始化Fitty，确保DOM完全渲染
        setTimeout(() => {
          this.initializeFitty()
        }, 50)
      }
    }
  },
  
  beforeUnmount() {
    // 清理资源
    this.ocrResults = []
    
    // 清理Fitty实例
    this.clearFittyInstances()
    
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