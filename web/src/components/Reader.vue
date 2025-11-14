<template>
  <div class="reader-container">
    <!-- 功能栏 -->
    <div class="toolbar">
      <div class="toolbar-left">
        <button class="tool-btn" @click="goBack">
          返回
        </button>
        <span class="reader-title">{{ galleryTitle }}</span>
      </div>
      
      <div class="toolbar-center">
        <!-- 阅读方向切换 -->
        <div class="tool-group">
          <label>阅读方向：</label>
          <select v-model="readingDirection" class="tool-select">
            <option value="ltr">从左到右</option>
            <option value="rtl">从右到左</option>
          </select>
        </div>
        
        
        <!-- 阅读模式 -->
        <div class="tool-group">
          <label>阅读模式：</label>
          <select v-model="viewMode" class="tool-select">
            <option value="single">单栏</option>
            <option value="double">双栏</option>
          </select>
        </div>
      </div>
      
      <div class="toolbar-right">
        <button class="tool-btn" @click="showPagination = !showPagination" :title="showPagination ? '隐藏分页器' : '显示分页器'">
          {{ showPagination ? '隐藏分页' : '显示分页' }}
        </button>
        <span class="page-info">{{ currentPage }} / {{ totalPages }}</span>
      </div>
    </div>
    
    <!-- 阅读区域 -->
    <div 
      class="reader-content" 
      :class="{ 
        'rtl-mode': readingDirection === 'rtl',
        'double-mode': viewMode === 'double',
        'fullscreen': !showPagination
      }"
      ref="readerContent"
      @keydown="handleKeydown"
      tabindex="0"
    >
      <div v-if="loading" class="loading-message">
        <div class="spinner"></div>
        <p>正在加载图片...</p>
      </div>
      
      <div v-else-if="error" class="error-message">
        {{ error }}
      </div>
      
      <div v-else class="images-container" :class="{ 'fullscreen-images': true }">
        <!-- 点击区域覆盖层 -->
        <div class="click-overlay">
          <div class="click-zone left-zone" @click="handleLeftClick"></div>
          <div class="click-zone right-zone" @click="handleRightClick"></div>
        </div>
        
        <!-- 单栏模式 -->
        <div v-if="viewMode === 'single'" class="single-column">
          <div
            v-for="page in visiblePages"
            :key="page.number"
            class="page-container"
            :class="{ 'current': page.number === currentPage }"
          >
            <!-- 正常图片 -->
            <img
              v-if="page.url && !page.error"
              :src="page.url"
              :alt="`Page ${page.number}`"
              class="page-image"
              @load="onImageLoad(page.number)"
              @error="onImageError(page.number)"
              ref="pageImages"
            />
            
            <!-- 加载中状态 -->
            <div v-else-if="page.loading || page.lazy" class="page-loading">
              <div class="spinner"></div>
              <p>Loading page {{ page.number }}...</p>
            </div>
            
            <!-- 错误状态 -->
            <div v-else-if="page.error" class="page-error">
              <p>Failed to load page {{ page.number }}</p>
              <button @click="retryLoadPage(page.number)" class="retry-btn">Retry</button>
            </div>
          </div>
        </div>
        
        <!-- 双栏模式 -->
        <div v-else class="double-column">
          <div 
            v-for="(pair, index) in pairedPages" 
            :key="index"
            class="page-pair"
            :class="{ 'current-pair': isPairCurrent(pair) }"
          >
            <!-- 左侧页面 -->
            <div v-if="pair.left" class="page-container left-page">
              <img
                v-if="pair.left.url && !pair.left.error"
                :src="pair.left.url"
                :alt="`Page ${pair.left.number}`"
                class="page-image"
                :class="{ 'current': pair.left.number === currentPage }"
                @load="onImageLoad(pair.left.number)"
                @error="onImageError(pair.left.number)"
                />
              <div v-else-if="pair.left.loading || pair.left.lazy" class="page-loading">
                <div class="spinner"></div>
                <p>Loading page {{ pair.left.number }}...</p>
              </div>
              <div v-else-if="pair.left.error" class="page-error">
                <p>Failed to load page {{ pair.left.number }}</p>
                <button @click="retryLoadPage(pair.left.number)" class="retry-btn">Retry</button>
              </div>
            </div>
            
            <!-- 右侧页面 -->
            <div v-if="pair.right" class="page-container right-page">
              <img
                v-if="pair.right.url && !pair.right.error"
                :src="pair.right.url"
                :alt="`Page ${pair.right.number}`"
                class="page-image"
                :class="{ 'current': pair.right.number === currentPage }"
                @load="onImageLoad(pair.right.number)"
                @error="onImageError(pair.right.number)"
                />
              <div v-else-if="pair.right.loading || pair.right.lazy" class="page-loading">
                <div class="spinner"></div>
                <p>Loading page {{ pair.right.number }}...</p>
              </div>
              <div v-else-if="pair.right.error" class="page-error">
                <p>Failed to load page {{ pair.right.number }}</p>
                <button @click="retryLoadPage(pair.right.number)" class="retry-btn">Retry</button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 分页器 -->
    <div class="pagination-container" v-show="showPagination">
      <div class="pagination">
        <button 
          class="page-btn"
          :disabled="currentPage <= 1"
          @click="goToPage(1)"
        >
          <span class="nav-icon">«</span>
        </button>
        
        <button 
          class="page-btn"
          :disabled="currentPage <= 1"
          @click="previousPage"
        >
          <span class="nav-icon">‹</span>
        </button>
        
        <div class="page-input-group">
          <input 
            type="number" 
            v-model.number="pageInput" 
            :min="1" 
            :max="totalPages"
            class="page-input"
            @keyup.enter="goToInputPage"
          />
          <span class="page-separator">/</span>
          <span class="total-pages">{{ totalPages }}</span>
        </div>
        
        <button 
          class="page-btn"
          :disabled="currentPage >= totalPages"
          @click="nextPage"
        >
          <span class="nav-icon">›</span>
        </button>
        
        <button 
          class="page-btn"
          :disabled="currentPage >= totalPages"
          @click="goToPage(totalPages)"
        >
          <span class="nav-icon">»</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import axios from "axios";

const API = import.meta.env.VITE_API_BASE;

export default {
  name: "Reader",
  data() {
    return {
      // 基本信息
      gid: null,
      token: null,
      provider: 'ex',
      galleryTitle: '',
      
      // 阅读设置
      readingDirection: 'ltr', // ltr 或 rtl
      viewMode: 'single', // single 或 double
      
      // 页面状态
      currentPage: 1,
      totalPages: 0,
      pageInput: 1,
      
      // 图片数据
      currentPageUrl: null,  // 当前页面URL
      nextPageUrl: null,     // 下一页面URL (双栏模式用)
      pageLoading: false,    // 页面加载状态
      
      // 缓存机制
      imageCache: new Map(),  // 图片URL缓存 {pageNumber: {url, timestamp}}
      cacheTimeout: 10 * 60 * 1000, // 缓存10分钟
      
      // UI状态
      loading: true,
      error: null,
      showPagination: true, // 控制分页器显示/隐藏
    };
  },
  
  computed: {
    visiblePages() {
      // 单栏模式：只返回当前页
      if (this.viewMode === 'single') {
        if (this.pageLoading || !this.currentPageUrl) {
          // 如果正在加载或没有URL，显示加载状态
          return [{
            number: this.currentPage,
            url: null,
            loading: this.pageLoading,
            error: false
          }];
        }
        
        return [{
          number: this.currentPage,
          url: this.currentPageUrl,
          loading: false,
          error: false
        }];
      }
      
      // 双栏模式：返回当前页和下一页
      if (this.viewMode === 'double') {
        const pages = [];
        
        let firstPageNumber, secondPageNumber;
        
        // 无论LTR还是RTL，页面数字序列保持一致
        firstPageNumber = this.currentPage;
        secondPageNumber = this.currentPage + 1;
        
        // 第一页
        if (this.pageLoading || !this.currentPageUrl) {
          pages.push({
            number: firstPageNumber,
            url: null,
            loading: this.pageLoading,
            error: false
          });
        } else {
          pages.push({
            number: firstPageNumber,
            url: this.currentPageUrl,
            loading: false,
            error: false
          });
        }
        
        // 第二页
        if (secondPageNumber <= this.totalPages) {
          if (this.pageLoading || !this.nextPageUrl) {
            pages.push({
              number: secondPageNumber,
              url: null,
              loading: this.pageLoading,
              error: false
            });
          } else {
            pages.push({
              number: secondPageNumber,
              url: this.nextPageUrl,
              loading: false,
              error: false
            });
          }
        }
        
        return pages;
      }
      
      return [];
    },
    
    pairedPages() {
      if (this.viewMode !== 'double' || !this.visiblePages.length) return [];
      
      // 双栏模式下，visiblePages最多包含两页
      const page1 = this.visiblePages[0]; // 当前页 (较小页码)
      const page2 = this.visiblePages[1] || null; // 下一页 (较大页码)
      
      if (this.readingDirection === 'rtl') {
        // RTL：CSS会用row-reverse交换显示顺序，所以：
        // - pair.left 实际显示在右侧 → 应该是较小页码（先读）
        // - pair.right 实际显示在左侧 → 应该是较大页码（后读）
        return [{ left: page1, right: page2 }];
      } else {
        // LTR：正常显示顺序，所以：
        // - pair.left 显示在左侧 → 较小页码（先读）
        // - pair.right 显示在右侧 → 较大页码（后读）
        return [{ left: page1, right: page2 }];
      }
    }
  },
  
  created() {
    this.initializeFromRoute();
    this.loadGalleryData();
    
    // 从localStorage恢复设置
    this.loadSettings();
  },
  
  watch: {
    '$route'(newRoute, oldRoute) {
      // 检查是否只是页面参数变化
      const newPage = newRoute.query.page;
      const oldPage = oldRoute.query.page;
      
      if (newRoute.params.gid === oldRoute.params.gid && 
          newRoute.params.token === oldRoute.params.token &&
          newPage !== oldPage) {
        // 只是页面参数变化，直接跳转到新页面
        if (newPage && !isNaN(parseInt(newPage))) {
          const targetPage = Math.max(1, Math.min(this.totalPages, parseInt(newPage)));
          if (targetPage !== this.currentPage) {
            this.currentPage = targetPage;
            this.pageInput = targetPage;
            this.loadCurrentPages();
          }
        }
      } else {
        // 其他参数变化，重新初始化
        this.initializeFromRoute();
        this.loadGalleryData();
      }
    }
  },
  
  mounted() {
    // 添加body类以隐藏全局滚动条
    document.body.classList.add('reader-active');
    
    // 添加键盘监听
    this.$refs.readerContent?.focus();
    
    // 保存设置到localStorage
    this.$watch('readingDirection', this.saveSettings);
    this.$watch('viewMode', this.saveSettings);
    this.$watch('currentPage', (newPage) => {
      this.pageInput = newPage;
      // currentPage变化时只更新输入框，加载逻辑由翻页方法处理
    });
    
    // 暴露缓存方法到全局，方便调试
    window.readerCache = {
      stats: () => this.getCacheStats(),
      clear: () => this.clearImageCache(),
      size: () => this.imageCache.size
    };
    
    console.log('Reader cache system initialized. Use window.readerCache to debug.');
  },
  
  beforeUnmount() {
    // 移除body类，恢复全局滚动条
    document.body.classList.remove('reader-active');
    
    // 组件销毁时清理缓存
    this.imageCache.clear();
  },
  
  methods: {
    initializeFromRoute() {
      const { gid, token, id } = this.$route.params;
      const { page } = this.$route.query;
      const path = this.$route.path;
      
      // 只支持ExHentai阅读器
      this.provider = 'ex';
      this.gid = gid;
      this.token = token;
      
      // 设置起始页面
      if (page && !isNaN(parseInt(page))) {
        this.currentPage = Math.max(1, parseInt(page));
        this.pageInput = this.currentPage;
      }
    },
    
    async loadGalleryData() {
      this.loading = true;
      this.error = null;
      
      try {
        // 获取ExHentai画廊基本信息
        const galleryUrl = `${API}/api/gallery/item/${this.gid}`;
        
        const { data: galleryData } = await axios.get(galleryUrl);
        this.galleryTitle = galleryData.title || galleryData.name || 'Unknown Title';
        
        this.totalPages = galleryData.filecount || 0;
        
        // 如果URL没有指定页面，则默认为第1页
        if (!this.$route.query.page) {
          this.currentPage = 1;
          this.pageInput = 1;
        }
        
        // 确保页面号在有效范围内
        this.currentPage = Math.max(1, Math.min(this.totalPages, this.currentPage));
        this.pageInput = this.currentPage;
        
        // 立即加载当前页面
        await this.loadCurrentPages();
        
      } catch (error) {
        console.error("Error loading gallery data:", error);
        this.error = `加载失败: ${error.message}`;
      } finally {
        this.loading = false;
      }
    },
    
    async loadCurrentPages() {
      try {
        // 检查是否有缓存，如果全部缓存命中则不显示loading
        const currentCached = this.getCachedUrl(this.currentPage);
        const nextCached = this.viewMode === 'double' && this.currentPage < this.totalPages 
          ? this.getCachedUrl(this.currentPage + 1) 
          : true; // 单栏模式或最后一页时视为已缓存
        
        const allCached = currentCached && nextCached;
        
        if (!allCached) {
          // 有未缓存的图片，显示loading并清除旧图片
          this.pageLoading = true;
          this.currentPageUrl = null;
          this.nextPageUrl = null;
        }
        
        // 加载当前页
        await this.loadPageUrl(this.currentPage);
        
        // 双栏模式下加载下一页
        if (this.viewMode === 'double' && this.currentPage < this.totalPages) {
          await this.loadPageUrl(this.currentPage + 1, true);
        }
        
        // 加载完成
        this.pageLoading = false;
        
      } catch (error) {
        console.error("Error loading current pages:", error);
        this.error = `加载失败: ${error.message}`;
        this.pageLoading = false;
      }
    },

    // 检查缓存是否有效
    isCacheValid(pageNumber) {
      const cached = this.imageCache.get(pageNumber);
      if (!cached) return false;
      
      const now = Date.now();
      const isValid = (now - cached.timestamp) < this.cacheTimeout;
      
      if (!isValid) {
        // 缓存过期，删除
        this.imageCache.delete(pageNumber);
        return false;
      }
      
      return true;
    },

    // 从缓存获取图片URL
    getCachedUrl(pageNumber) {
      if (this.isCacheValid(pageNumber)) {
        return this.imageCache.get(pageNumber).url;
      }
      return null;
    },

    // 缓存图片URL
    setCachedUrl(pageNumber, url) {
      this.imageCache.set(pageNumber, {
        url: url,
        timestamp: Date.now()
      });
      
      // 限制缓存大小，最多缓存50张图片
      if (this.imageCache.size > 50) {
        // 删除最旧的缓存项
        const oldestKey = this.imageCache.keys().next().value;
        this.imageCache.delete(oldestKey);
      }
    },

    async loadPageUrl(pageNumber, isNextPage = false) {
      try {
        // 先检查缓存
        let imageUrl = this.getCachedUrl(pageNumber);
        
        if (imageUrl) {
          console.log(`Using cached image for page ${pageNumber}`);
          // 直接使用缓存的URL
          if (isNextPage) {
            this.nextPageUrl = imageUrl;
          } else {
            this.currentPageUrl = imageUrl;
          }
          return;
        }
        
        // 缓存中没有，发起网络请求
        const { data } = await axios.get(`${API}/api/gallery/ex/full-image/${this.gid}/${this.token}/${pageNumber}`);
        imageUrl = `${API}/api/gallery/ex/proxy-image?url=${encodeURIComponent(data.imageUrl)}`;
        
        // 缓存URL
        this.setCachedUrl(pageNumber, imageUrl);
        
        if (isNextPage) {
          this.nextPageUrl = imageUrl;
        } else {
          this.currentPageUrl = imageUrl;
        }
        
      } catch (error) {
        console.error(`Failed to load page ${pageNumber}:`, error);
        if (isNextPage) {
          this.nextPageUrl = null;
        } else {
          this.currentPageUrl = null;
        }
        throw error;
      }
    },
    
    goBack() {
      // 返回到ExHentai画廊详情页面
      this.$router.push(`/gallery/${this.gid}`);
    },
    
    previousPage() {
      if (this.currentPage > 1) {
        let newPage;
        if (this.viewMode === 'double') {
          // 双栏模式：跳转到上一对页面的第一页
          newPage = Math.max(1, this.currentPage - 2);
        } else {
          // 单栏模式：跳转到上一页
          newPage = this.currentPage - 1;
        }
        
        if (newPage !== this.currentPage) {
          this.currentPage = newPage;
          this.loadCurrentPages();
        }
        this.scrollToCurrentPage();
      }
    },
    
    nextPage() {
      let newPage = this.currentPage;
      
      if (this.viewMode === 'double') {
        // 双栏模式：跳转到下一对页面的第一页
        if (this.currentPage + 1 < this.totalPages) {
          newPage = this.currentPage + 2;
        } else if (this.currentPage < this.totalPages) {
          // 如果只剩最后一页，跳转到最后一页
          newPage = this.totalPages;
        }
      } else {
        // 单栏模式：跳转到下一页
        if (this.currentPage < this.totalPages) {
          newPage = this.currentPage + 1;
        }
      }
      
      if (newPage !== this.currentPage) {
        this.currentPage = newPage;
        this.loadCurrentPages();
      }
      this.scrollToCurrentPage();
    },
    
    goToPage(page) {
      const newPage = Math.max(1, Math.min(this.totalPages, page));
      if (newPage !== this.currentPage) {
        this.currentPage = newPage;
        this.loadCurrentPages();
      }
      this.scrollToCurrentPage();
    },
    
    goToInputPage() {
      this.goToPage(this.pageInput);
    },
    
    scrollToCurrentPage() {
      this.$nextTick(() => {
        const currentImage = document.querySelector('.page-image.current');
        if (currentImage) {
          currentImage.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
      });
    },
    
    handleKeydown(event) {
      switch (event.code) {
        case 'ArrowLeft':
          event.preventDefault();
          if (this.readingDirection === 'rtl') {
            this.nextPage();
          } else {
            this.previousPage();
          }
          break;
        case 'ArrowRight':
          event.preventDefault();
          if (this.readingDirection === 'rtl') {
            this.previousPage();
          } else {
            this.nextPage();
          }
          break;
        case 'ArrowUp':
          event.preventDefault();
          this.previousPage();
          break;
        case 'ArrowDown':
          event.preventDefault();
          this.nextPage();
          break;
        case 'Home':
          event.preventDefault();
          this.goToPage(1);
          break;
        case 'End':
          event.preventDefault();
          this.goToPage(this.totalPages);
          break;
        case 'KeyH':
          event.preventDefault();
          this.showPagination = !this.showPagination;
          break;
      }
    },
    
    handleLeftClick() {
      // 根据阅读方向决定左侧点击的行为
      if (this.readingDirection === 'ltr') {
        // 从左到右：左侧点击=上一页
        this.previousPage();
      } else {
        // 从右到左：左侧点击=下一页
        this.nextPage();
      }
    },

    handleRightClick() {
      // 根据阅读方向决定右侧点击的行为
      if (this.readingDirection === 'ltr') {
        // 从左到右：右侧点击=下一页
        this.nextPage();
      } else {
        // 从右到左：右侧点击=上一页
        this.previousPage();
      }
    },
    
    onImageLoad(pageNumber) {
      // 图片加载成功
    },
    
    onImageError(pageNumber) {
      console.error(`Failed to load image for page ${pageNumber}`);
    },

    retryLoadPage(pageNumber) {
      // 重新加载当前页面
      this.loadCurrentPages();
    },
    
    isPairCurrent(pair) {
      return (pair.left && pair.left.number === this.currentPage) || 
             (pair.right && pair.right.number === this.currentPage);
    },
    
    loadSettings() {
      const settings = localStorage.getItem('reader-settings');
      if (settings) {
        try {
          const parsed = JSON.parse(settings);
          this.readingDirection = parsed.readingDirection || 'ltr';
          this.viewMode = parsed.viewMode || 'single';
        } catch (e) {
          console.error('Error loading reader settings:', e);
        }
      }
    },
    
    saveSettings() {
      const settings = {
        readingDirection: this.readingDirection,
        viewMode: this.viewMode
      };
      localStorage.setItem('reader-settings', JSON.stringify(settings));
    },

    // 清除所有缓存
    clearImageCache() {
      this.imageCache.clear();
      console.log('Image cache cleared');
    },

    // 获取缓存统计信息
    getCacheStats() {
      const now = Date.now();
      let validCount = 0;
      let expiredCount = 0;
      
      for (const [pageNumber, cached] of this.imageCache.entries()) {
        if ((now - cached.timestamp) < this.cacheTimeout) {
          validCount++;
        } else {
          expiredCount++;
        }
      }
      
      return {
        total: this.imageCache.size,
        valid: validCount,
        expired: expiredCount,
        cacheTimeout: this.cacheTimeout / 1000 / 60 // 转换为分钟
      };
    }
  }
};
</script>

<style src="../assets/Reader.css"></style>