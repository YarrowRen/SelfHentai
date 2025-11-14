<template>
  <div class="gallery-detail-wrapper">
    <div v-if="galleryData" class="gallery-detail-container">
    <!-- 数据源指示器 -->
    <div :class="['data-source-indicator', provider]">
      {{ provider.toUpperCase() }}
    </div>

    <!-- 左侧封面 -->
    <div class="cover">
      <img :src="galleryData.thumb || galleryData.image || '/placeholder.png'" alt="Cover" />
      <div class="category">
        <span>{{ getDisplayCategory() }}</span>
      </div>
    </div>

    <!-- 右侧信息 -->
    <div class="details">
      <h3 class="title">
        {{ getDisplayTitle() }}
        <br />
        <small v-if="galleryData.title_jpn">{{ galleryData.title_jpn }}</small>
      </h3>

      <div class="info-tags">
        <!-- EX 数据信息列表 -->
        <ul v-if="provider === 'ex'" class="info-list">
          <li><strong>Uploader:</strong> {{ galleryData.uploader }}</li>
          <li><strong>Posted:</strong> {{ formatDate(galleryData.posted) }}</li>
          <li><strong>File Size:</strong> {{ formatFileSize(galleryData.filesize) }}</li>
          <li><strong>Length:</strong> {{ galleryData.filecount }} pages</li>
          <li>
            <strong>Rating:</strong>
            <span style="display:inline-flex;align-items:center;">
              <Rating v-model="galleryData.rating" readonly style="margin: 0 10px;" />
              {{ galleryData.rating }}
            </span>
          </li>
          <li>
            <strong>Link:</strong>
            <a :href="`https://exhentai.org/g/${itemId}/${galleryData.token}`" target="_blank">
              https://exhentai.org/g/{{ itemId }}/{{ galleryData.token }}
            </a>
          </li>
          <li class="read-button-container">
            <button class="read-button" @click="startTranslation">
              开始翻译
            </button>
            <button class="auto-translate-button" @click="startAutoTranslation">
              自动翻译
            </button>
          </li>
        </ul>


        <Divider layout="vertical" class="!hidden md:!flex" />

        <!-- EX Tags -->
        <div v-if="provider === 'ex'" class="tags">
          <ToggleSwitch v-model="isChinese" :onLabel="'中文'" :offLabel="'英文'" class="language-toggle" />
          <div v-for="(tags, group) in groupedTags" :key="group" class="tag-group">
            <strong>{{ group }}</strong>:
            <Tag
              v-for="(tag, index) in tags"
              :key="index"
              :value="isChinese ? (tag.tag_cn || tag.value) : tag.value"
              class="tag"
              severity="secondary"
            />
          </div>
        </div>

      </div>
    </div>
    </div>

    <!-- EX Torrents Section -->
  <section v-if="provider === 'ex' && galleryData.torrents?.length" class="torrents">
    <h4>Torrent Downloads</h4>
    <table class="torrent-table">
      <thead>
        <tr>
          <th style="width: 40%;">Name</th>
          <th style="width: 15%;">Size</th>
          <th style="width: 15%;">Torrent Size</th>
          <th style="width: 15%;">Added</th>
          <th style="width: 15%;">Torrent Download</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(torrent, index) in galleryData.torrents" :key="index">
          <td>{{ torrent.name }}</td>
          <td>{{ formatFileSize(Number(torrent.fsize)) }}</td>
          <td>{{ formatFileSize(Number(torrent.tsize)) }}</td>
          <td>{{ formatDate(Number(torrent.added)) }}</td>
          <td>
            <a :href="`https://exhentai.org/torrent/${itemId}/${torrent.hash}.torrent`" target="_blank">Torrent</a>
          </td>
        </tr>
      </tbody>
    </table>
  </section>


  <!-- EX Thumbnail Gallery Section -->
  <section v-if="provider === 'ex'" class="thumbnail-gallery">
    <div class="thumbnail-header">
      <h4>Gallery Preview</h4>
      <div v-if="thumbnailData.pagination.page_info" class="thumbnail-info">
        Showing {{ thumbnailData.pagination.page_info.start }} - {{ thumbnailData.pagination.page_info.end }} 
        of {{ thumbnailData.pagination.page_info.total }} images
      </div>
    </div>

    <!-- Thumbnail Grid -->
    <div v-if="thumbnailData.thumbnails?.length" class="thumbnail-grid">
      <div 
        v-for="(thumb, index) in thumbnailData.thumbnails" 
        :key="index" 
        class="thumbnail-item"
@click="openReader(thumb)"
      >
        <div 
          class="thumbnail-image"
          :style="{
            width: thumb.size?.width + 'px',
            height: thumb.size?.height + 'px',
            backgroundImage: `url(${thumb.background_url})`,
            backgroundPosition: `${thumb.bg_position?.x || 0}px ${thumb.bg_position?.y || 0}px`,
            backgroundRepeat: 'no-repeat'
          }"
          :title="thumb.title"
        ></div>
      </div>
    </div>

    <!-- Pagination Controls -->
    <div v-if="thumbnailData.pagination.page_links?.length" class="thumbnail-pagination">
      <button 
        class="page-btn"
        :disabled="thumbnailCurrentPage === 0"
        @click="loadThumbnails(thumbnailCurrentPage - 1)"
      >
        &lt;
      </button>
      
      <button
        v-for="link in visiblePageLinks"
        :key="link.page"
        class="page-btn"
        :class="{ active: link.page === thumbnailCurrentPage }"
        @click="loadThumbnails(link.page)"
      >
        {{ link.display }}
      </button>

      <button 
        v-if="hasMorePages"
        class="page-btn ellipsis"
        @click="showPageJump = true"
      >
        ...
      </button>

      <button 
        class="page-btn"
        :disabled="thumbnailCurrentPage >= thumbnailData.pagination.total_pages - 1"
        @click="loadThumbnails(thumbnailCurrentPage + 1)"
      >
        &gt;
      </button>
    </div>

    <!-- Page Jump Dialog -->
    <div v-if="showPageJump" class="page-jump-overlay" @click="showPageJump = false">
      <div class="page-jump-dialog" @click.stop>
        <p>Jump to page: (1-{{ thumbnailData.pagination.total_pages }})</p>
        <input 
          ref="pageJumpInput"
          type="number" 
          v-model="jumpToPage" 
          :min="1" 
          :max="thumbnailData.pagination.total_pages"
          @keyup.enter="handlePageJump"
        />
        <div class="page-jump-buttons">
          <button @click="handlePageJump">Go</button>
          <button @click="showPageJump = false">Cancel</button>
        </div>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="thumbnailLoading" class="thumbnail-loading">
      Loading thumbnails...
    </div>

    <!-- Error State -->
    <div v-if="thumbnailError" class="thumbnail-error">
      {{ thumbnailError }}
    </div>
  </section>
    <div v-else-if="loading" class="loading">Loading...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
  </div>
</template>

<script>
import axios from "axios";
import Divider from "primevue/divider";
import Tag from "primevue/tag";
import Rating from "primevue/rating";
import ToggleSwitch from "primevue/toggleswitch";

const API = import.meta.env.VITE_API_BASE;

export default {
  name: "GalleryDetail",
  components: { Divider, Tag, Rating, ToggleSwitch },
  data() {
    return {
      itemId: null,
provider: 'ex', // 只支持ExHentai数据源
      galleryData: null,
      isChinese: true,
      loading: true,
      error: null,
      // Thumbnail related data
      thumbnailData: {
        thumbnails: [],
        pagination: {
          current_page: 0,
          total_pages: 0,
          page_info: {},
          page_links: []
        }
      },
      thumbnailCurrentPage: 0,
      thumbnailLoading: false,
      thumbnailError: null,
      showPageJump: false,
      jumpToPage: 1,
    };
  },
  created() {
    this.initializeFromRoute();
    if (this.itemId) {
      this.fetchGalleryData();
    }
  },
  watch: {
    '$route'() {
      this.initializeFromRoute();
      if (this.itemId) {
        this.fetchGalleryData();
      }
    }
  },
  methods: {
    initializeFromRoute() {
      // 只支持ExHentai路由格式：/gallery/:gid
      const params = this.$route.params;
      
      this.provider = 'ex';
      this.itemId = params.gid;
    },

    async fetchGalleryData() {
      this.loading = true;
      this.error = null;
      
      try {
        const url = `${API}/api/gallery/item/${this.itemId}`;

        const { data } = await axios.get(url);
        this.galleryData = data;
        
        // 如果是EX画廊，加载缩略图
        if (this.provider === 'ex' && this.galleryData) {
          this.loadThumbnails(0);
        }
      } catch (error) {
        console.error("Error fetching gallery data:", error);
        this.error = `Failed to load ${this.provider.toUpperCase()} data: ${error.message}`;
      } finally {
        this.loading = false;
      }
    },

    getDisplayTitle() {
      return this.galleryData.title || 'Unknown Title';
    },

    getDisplayCategory() {
      return this.galleryData.category || 'Unknown Category';
    },

    formatDate(timestamp) {
      const date = new Date(timestamp * 1000);
      return date.toISOString().replace("T", " ").split(".")[0];
    },


    formatFileSize(bytes) {
      if (bytes === 0) return "0 B";
      const sizes = ["B", "KB", "MB", "GB", "TB"];
      const i = Math.floor(Math.log(bytes) / Math.log(1024));
      return (bytes / Math.pow(1024, i)).toFixed(2) + " " + sizes[i];
    },

    formatNumber(num) {
      if (!num) return '0';
      return parseInt(num).toLocaleString();
    },

    async loadThumbnails(page) {
      console.log('loadThumbnails called:', { provider: this.provider, galleryData: !!this.galleryData, itemId: this.itemId });
      
      if (this.provider !== 'ex' || !this.galleryData) {
        console.log('Early return from loadThumbnails:', { provider: this.provider, hasGalleryData: !!this.galleryData });
        return;
      }
      
      this.thumbnailLoading = true;
      this.thumbnailError = null;
      
      try {
        const url = `${API}/api/gallery/ex/thumbnails/${this.itemId}/${this.galleryData.token}?page=${page}`;
        console.log('Fetching thumbnails from:', url);
        
        const { data } = await axios.get(url);
        console.log('Thumbnail data received:', data);
        
        this.thumbnailData = data;
        this.thumbnailCurrentPage = page;
        
      } catch (error) {
        console.error("Error loading thumbnails:", error);
        this.thumbnailError = `Failed to load thumbnails: ${error.message}`;
      } finally {
        this.thumbnailLoading = false;
      }
    },

    openReader(thumb) {
      // 跳转到阅读器界面的特定页面
      if (thumb.page_number && this.galleryData) {
        const route = `/reader/${this.itemId}/${this.galleryData.token}?page=${thumb.page_number}`;
        this.$router.push(route);
      }
    },

    handlePageJump() {
      const page = Math.min(
        Math.max(1, parseInt(this.jumpToPage) || 1), 
        this.thumbnailData.pagination.total_pages
      ) - 1; // 转换为0开始的页码
      
      this.loadThumbnails(page);
      this.showPageJump = false;
      this.jumpToPage = page + 1;
    },

    startTranslation() {
      // 跳转到第一页的翻译界面
      if (this.galleryData) {
        const route = `/gallery/${this.itemId}/${this.galleryData.token}/page/1`;
        this.$router.push(route);
      }
    },

    startAutoTranslation() {
      // 跳转到自动翻译界面
      if (this.galleryData) {
        const route = `/auto-translate/${this.itemId}/${this.galleryData.token}`;
        this.$router.push(route);
      }
    },
  },
  computed: {
    groupedTags() {
      if (this.provider !== 'ex' || !this.galleryData?.tags) {
        return {};
      }

      const groups = {
        language: [],
        artist: [],
        group: [],
        female: [],
        male: [],
        mixed: [],
        other: [],
        cosplayer: [],
        parody: [],
        character: [],
        other_tags: [],
      };
      
      this.galleryData.tags.forEach(tag => {
        const ns = tag.namespace?.toLowerCase() || 'other_tags';
        (groups[ns] ?? groups.other_tags).push(tag);
      });
      
      return Object.fromEntries(Object.entries(groups).filter(([, v]) => v.length > 0));
    },

    visiblePageLinks() {
      const links = this.thumbnailData.pagination.page_links || [];
      const current = this.thumbnailCurrentPage;
      
      // 显示当前页面周围的页码
      return links.filter(link => {
        const page = link.page;
        return page <= 6 || Math.abs(page - current) <= 2 || page >= links.length - 3;
      });
    },

    hasMorePages() {
      const links = this.thumbnailData.pagination.page_links || [];
      const visible = this.visiblePageLinks;
      return visible.length < links.length;
    },
  },
};
</script>

<style src="../assets/GalleryDetail.css"></style>
