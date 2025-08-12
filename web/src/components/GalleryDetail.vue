<template>
  <div v-if="galleryData" class="gallery-detail-container">
    <!-- 数据源指示器 -->
    <div :class="['data-source-indicator', provider]">
      {{ provider.toUpperCase() }}
    </div>

    <!-- 左侧封面 -->
    <div class="cover">
      <img :src="galleryData.thumb || galleryData.image || '/placeholder.png'" alt="Cover" />
      <div :class="['category', { 'jm-category': provider === 'jm' }]">
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
        </ul>

        <!-- JM 数据信息列表 -->
        <ul v-else-if="provider === 'jm'" class="info-list">
          <li><strong>ID:</strong> {{ galleryData.id }}</li>
          <li><strong>Author:</strong> {{ galleryData.author || '未知作者' }}</li>
          <li><strong>Category:</strong> {{ galleryData.category?.title || '未知分类' }}</li>
          <li><strong>Subcategory:</strong> {{ galleryData.category_sub?.title || '无' }}</li>
          <li><strong>Added:</strong> {{ formatJMDate(galleryData.addtime) }}</li>
          <li v-if="galleryData.latest_ep"><strong>Latest Episode:</strong> {{ galleryData.latest_ep }}</li>
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

        <!-- JM Tags -->
        <div v-else-if="provider === 'jm'" class="jm-tags">
          <strong>Tags:</strong>
          <div v-if="galleryData.tags && galleryData.tags.length">
            <span
              v-for="(tag, index) in galleryData.tags"
              :key="index"
              class="jm-tag"
            >
              {{ tag }}
            </span>
          </div>
          <div v-else style="color: #bdc3c7; font-style: italic;">
            No tags available
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
          <th style="width: 15%;">Magnet Link</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(torrent, index) in galleryData.torrents" :key="index">
          <td>{{ torrent.name }}</td>
          <td>{{ formatFileSize(Number(torrent.fsize)) }}</td>
          <td>{{ formatFileSize(Number(torrent.tsize)) }}</td>
          <td>{{ formatDate(Number(torrent.added)) }}</td>
          <td>
            <a :href="`magnet:?xt=urn:btih:${torrent.hash}`" target="_blank">Magnet</a>
          </td>
        </tr>
      </tbody>
    </table>
  </section>

  <!-- JM Stats Section -->
  <section v-if="provider === 'jm'" class="jm-stats">
    <h4>Statistics</h4>
    <div class="stats-grid">
      <div class="stat-item">
        <div class="stat-value">{{ formatNumber(galleryData.total_views) }}</div>
        <div class="stat-label">Total Views</div>
      </div>
      <div class="stat-item">
        <div class="stat-value">{{ formatNumber(galleryData.likes) }}</div>
        <div class="stat-label">Likes</div>
      </div>
      <div class="stat-item">
        <div class="stat-value">{{ formatNumber(galleryData.comment_total) }}</div>
        <div class="stat-label">Comments</div>
      </div>
    </div>
    
    <!-- Description Section for JM -->
    <div v-if="galleryData.description" style="margin-top: 20px;">
      <h4>Description</h4>
      <div style="background: rgba(52, 73, 94, 0.3); padding: 15px; border-radius: 8px; line-height: 1.6;">
        {{ galleryData.description }}
      </div>
    </div>
  </section>
  <div v-else-if="loading" class="loading">Loading...</div>
  <div v-else-if="error" class="error">{{ error }}</div>
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
      provider: 'ex', // 默认为 EX
      galleryData: null,
      isChinese: true,
      loading: true,
      error: null,
    };
  },
  created() {
    this.initializeFromRoute();
    if (this.itemId) this.fetchGalleryData();
  },
  watch: {
    '$route'() {
      this.initializeFromRoute();
      if (this.itemId) this.fetchGalleryData();
    }
  },
  methods: {
    initializeFromRoute() {
      // 支持多种路由格式：
      // /gallery/:gid (EX)
      // /jm/:id (JM)
      // 或者通过查询参数 ?provider=jm&id=xxx
      const path = this.$route.path;
      const params = this.$route.params;
      const query = this.$route.query;

      if (path.startsWith('/jm/') || query.provider === 'jm') {
        this.provider = 'jm';
        this.itemId = params.id || query.id;
      } else {
        this.provider = 'ex';
        this.itemId = params.gid || query.gid;
      }
    },

    async fetchGalleryData() {
      this.loading = true;
      this.error = null;
      
      try {
        let url;
        if (this.provider === 'ex') {
          url = `${API}/api/gallery/item/${this.itemId}`;
        } else if (this.provider === 'jm') {
          url = `${API}/api/gallery/jm/item/${this.itemId}`;
        }

        const { data } = await axios.get(url);
        this.galleryData = data;
      } catch (error) {
        console.error("Error fetching gallery data:", error);
        this.error = `Failed to load ${this.provider.toUpperCase()} data: ${error.message}`;
      } finally {
        this.loading = false;
      }
    },

    getDisplayTitle() {
      if (this.provider === 'ex') {
        return this.galleryData.title;
      } else if (this.provider === 'jm') {
        return this.galleryData.name || this.galleryData.title;
      }
      return 'Unknown Title';
    },

    getDisplayCategory() {
      if (this.provider === 'ex') {
        return this.galleryData.category;
      } else if (this.provider === 'jm') {
        return this.galleryData.category?.title || 'Unknown Category';
      }
      return 'Unknown';
    },

    formatDate(timestamp) {
      const date = new Date(timestamp * 1000);
      return date.toISOString().replace("T", " ").split(".")[0];
    },

    formatJMDate(timestamp) {
      if (!timestamp) return 'Unknown';
      const date = new Date(parseInt(timestamp) * 1000);
      return date.toLocaleDateString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit'
      }).replace(/\//g, '-');
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
  },
};
</script>

<style src="../assets/GalleryDetail.css"></style>
