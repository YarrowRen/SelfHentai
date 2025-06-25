<template>
  <div v-if="galleryData" class="container">
    <!-- 左侧封面 -->
    <div class="cover">
      <img :src="galleryData.thumb" alt="Cover" />
      <div class="category"><span>{{ galleryData.category }}</span></div>
    </div>

    <!-- 右侧信息 -->
    <div class="details">
      <h3 class="title">
        {{ galleryData.title }}
        <br />
        <small v-if="galleryData.title_jpn">{{ galleryData.title_jpn }}</small>
      </h3>

      <div class="info-tags">
        <ul class="info-list">
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
            <a :href="`https://exhentai.org/g/${gid}/${galleryData.token}`" target="_blank">
              https://exhentai.org/g/{{ gid }}/{{ galleryData.token }}
            </a>
          </li>
        </ul>

        <Divider layout="vertical" class="!hidden md:!flex" />

        <div class="tags">
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
  <section v-if="galleryData.torrents?.length" class="torrents">
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
  <div v-else class="loading">Loading...</div>
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
      gid: null,
      galleryData: null,
      isChinese: true,
    };
  },
  created() {
    this.gid = this.$route.params.gid || this.$route.query.gid;
    if (this.gid) this.fetchGalleryData();
  },
  methods: {
    async fetchGalleryData() {
      try {
        const { data } = await axios.get(`${API}/api/gallery/item/${this.gid}`);
        this.galleryData = data;
      } catch (error) {
        console.error("Error fetching gallery data:", error);
      }
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
  },
  computed: {
    groupedTags() {
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
      (this.galleryData?.tags || []).forEach(tag => {
        const ns = tag.namespace.toLowerCase();
        (groups[ns] ?? groups.other_tags).push(tag);
      });
      return Object.fromEntries(Object.entries(groups).filter(([, v]) => v.length > 0));
    },
  },
};
</script>

<style scoped>
.container {
  display: flex;
  max-width: 1300px;
  margin: 0 auto;
  padding: 20px;
  background: #50535a;
  border-radius: 8px;
  color: white;
  font-family: Arial, sans-serif;
}

.cover {
  flex: 0 0 20%;
  padding-right: 20px;
}

.cover img {
  width: 100%;
  border-radius: 8px;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
}

.category span {
  background: #3498db;
  color: white;
  padding: 4px 8px;
  border-radius: 4px;
  display: inline-block;
  margin-top: 10px;
}

.details {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.title {
  font-weight: bold;
  margin-bottom: 10px;
}

.info-tags {
  display: flex;
  gap: 20px;
}

.info-list {
  list-style: none;
  padding: 0;
  flex: 1;
  text-align: left;
}

.info-list li {
  margin: 5px 0;
}

.tags {
  flex: 1;
  text-align: left;
}

.tag {
  display: inline-block;
  margin-right: 5px;
  white-space: nowrap;
  vertical-align: middle;
}

.loading {
  text-align: center;
  padding: 50px;
  font-size: 1.5em;
  color: #ccc;
}

.torrents {
  margin-top: 30px;
  max-width: 1300px;
  margin-left: auto;
  margin-right: auto;
  background: #3a3d45;
  padding: 20px;
  border-radius: 8px;
  color: white;
}

.torrents h4 {
  margin-bottom: 15px;
}

.torrent-table {
  width: 100%;
  border-collapse: collapse;
}

.torrent-table th,
.torrent-table td {
  padding: 10px;
  border: 1px solid #666;
  text-align: left;
  font-size: 14px;
}

.torrent-table th {
  background-color: #444;
}
</style>
