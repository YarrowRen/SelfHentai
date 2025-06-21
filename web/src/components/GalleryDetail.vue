<template>
  <div v-if="galleryData">
    <div class="container">
      <!-- 左侧封面 -->
      <div class="cover">
        <img :src="galleryData.thumb" alt="Cover Image" />
        <div class="category">
          <span>{{ galleryData.category }}</span>
        </div>
      </div>

      <!-- 右侧信息栏 -->
      <div class="details">
        <h3 class="title">
          {{ galleryData.title }}
          <br>
          <small v-if="galleryData.title_jpn">{{ galleryData.title_jpn }}</small>
        </h3>
        <div class="info-tags">
          <ul class="info-list">
            <li><strong>Uploader:</strong> {{ galleryData.uploader }}</li>
            <li><strong>Posted:</strong> {{ formatDate(galleryData.posted) }}</li>
            <li><strong>File Size:</strong> {{ formatFileSize(galleryData.filesize) }}</li>
            <li><strong>Length:</strong> {{ galleryData.filecount }} pages</li>
            <li>
              <span style="display: inline-flex; align-items: center;">
                <strong>Rating:</strong>
                <Rating style="margin-left: 5px; margin-right: 10px;" v-model="galleryData.rating" readonly /> {{
                  galleryData.rating }}
              </span>
            </li>
            <li>
              <strong>Link:</strong>
              <a :href="`https://exhentai.org/g/${gid}/${galleryData.token}`" target="_blank" rel="noopener noreferrer">
                https://exhentai.org/g/{{ gid }}/{{ galleryData.token }}
              </a>
            </li>
          </ul>
          <Divider layout="vertical" class="!hidden md:!flex"></Divider>
          <div class="tags">
            <!-- 切换语言按钮 -->
            <ToggleSwitch v-model="isChinese" :onLabel="'中文'" :offLabel="'英文'" class="language-toggle" />

            <template v-for="(tags, group) in groupedTags" :key="group">
              <div class="tag-group">
                <strong>{{ group }}</strong>:
                <Tag class="tag" v-for="(tag, index) in tags" :key="index"
                  :value="isChinese ? (tag.tag_cn || tag.value) : tag.value" severity="secondary" />
              </div>
            </template>
          </div>
        </div>
      </div>
    </div>
    <!-- 推荐内容 -->
    <!-- <div class="related-galleries">
      <h3>Related Galleries</h3>
      <ul class="gallery-list">
        <li v-for="(gallery, index) in relatedGalleries" :key="gallery.gid" class="gallery-item">
          <img :src="gallery.thumb" alt="Gallery Thumbnail" class="gallery-thumb" />
          <div class="gallery-info">
            <h4>{{ gallery.title }}</h4>
            <p><strong>Category:</strong> {{ gallery.category }}</p>
            <p><strong>Uploader:</strong> {{ gallery.uploader }}</p>
            <p><strong>Posted:</strong> {{ formatDate(gallery.posted) }}</p>
            <p><strong>Rating:</strong> {{ gallery.rating }}</p>
            <p>
              <Tag v-for="(tag, index) in gallery.tags" :key="index" :value="tag.tag_cn ? tag.tag_cn : tag.tag"
                :class="['tag', isMatchingTag(tag) ? 'highlighted-tag' : '']"
                :severity="isMatchingTag(tag) ? 'danger' : 'secondary'" />
            </p>
          </div>
        </li>
      </ul>
      <p v-if="relatedGalleries.length === 0">No related galleries found.</p>
    </div> -->
  </div>
  <div v-else class="loading">Loading...</div>
</template>


<script>
import axios from "axios";
import Divider from 'primevue/divider';
import Tag from "primevue/tag";
import Rating from 'primevue/rating';
import ToggleSwitch from 'primevue/toggleswitch';  // 引入 PrimeVue 的 ToggleSwitch 组件

export default {
  components: { Tag, Divider, Rating, ToggleSwitch },
  name: "GalleryDetail",
  data() {
    return {
      gid: null,
      galleryData: null,
      relatedGalleries: [], // 用于存储推荐的 Galleries
      isChinese: true,
    };
  },
  created() {
    this.gid = this.$route.params.gid || this.$route.query.gid;
    if (this.gid) {
      this.fetchGalleryData();
    }
  },
  methods: {
    async fetchGalleryData() {
      try {
        const response = await axios.get(`http://localhost:5001/api/gallery/item/${this.gid}`);
        this.galleryData = response.data;

        // 获取相关的 Galleries
        // this.fetchRelatedGalleries();
      } catch (error) {
        console.error("Error fetching gallery data:", error);
      }
    },
    // async fetchRelatedGalleries() {
    //   if (!this.galleryData || !this.galleryData.tags || !this.galleryData.gid) return;

    //   const tags = this.galleryData.tags.map(tag => `${tag.tag}`);
    //   const currentGid = this.galleryData.gid; // 当前 Gallery 的 ID

    //   try {
    //     const response = await axios.post("http://localhost:5001/api/get_top_galleries", {
    //       tags_list: tags, // 当前 Gallery 的所有 Tags
    //       n: 6,
    //     });

    //     // 手动筛选掉与当前 Gallery 的 gid 一样的结果
    //     this.relatedGalleries = (response.data.galleries || []).filter(gallery => gallery.gid !== currentGid);
    //   } catch (error) {
    //     console.error("Error fetching related galleries:", error);
    //   }
    // },
    formatDate(timestamp) {
      const date = new Date(timestamp * 1000);
      return date.toISOString().replace('T', ' ').split('.')[0];
    },
    formatFileSize(bytes) {
      if (bytes === 0) return "0 B";
      const sizes = ["B", "KB", "MB", "GB", "TB"];
      const i = Math.floor(Math.log(bytes) / Math.log(1024));
      return (bytes / Math.pow(1024, i)).toFixed(2) + " " + sizes[i];
    },
    isMatchingTag(galleryTag) {
      // 检查当前 gallery 的 tag 是否与主 gallery 的 tags 匹配
      if (!this.galleryData || !this.galleryData.tags) return false;

      return this.galleryData.tags.some(
        mainTag => mainTag.tag === galleryTag.tag && mainTag.namespace === galleryTag.namespace
      );
    }
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

      this.galleryData.tags.forEach(tag => {
        const namespace = tag.namespace.toLowerCase();
        if (groups[namespace] !== undefined) {
          groups[namespace].push(tag);
        } else {
          groups.other_tags.push(tag);
        }
      });

      return Object.fromEntries(Object.entries(groups).filter(([, tags]) => tags.length > 0));
    },
  },
};

</script>

<style scoped>
.container {
  display: flex;
  width: 100%;
  max-width: 1300px;
  background-color: #50535a;
  padding: 20px;
  margin: 0 auto;
  border-radius: 8px;
  color: white;
  font-family: Arial, sans-serif;
  box-sizing: border-box;
}


.cover {
  flex: 0 0 25%;
  align-items: center;
  justify-content: center;
  padding-right: 20px;
}

.cover img {
  max-width: 100%;
  border-radius: 8px;
  box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.3);
}

.details {
  flex: 0 0 75%;
  display: flex;
  flex-direction: column;
}

.title {
  font-weight: bold;
  margin-bottom: 10px;
}

.category span {
  display: inline-block;
  background: #3498db;
  color: white;
  padding: 4px 8px;
  border-radius: 4px;
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
  /* 标签单独显示 */
  margin-right: 5px;
  /* 标签之间的水平间距 */
  white-space: nowrap;
  /* 禁止换行 */
  vertical-align: middle;
  /* 垂直对齐 */
}

.loading {
  text-align: center;
  padding: 50px;
  font-size: 1.5em;
  color: #ccc;
}

.related-galleries {
  border-radius: 8px;
  width: 100%;
  max-width: 1300px;
  background-color: #50535a;
  padding: 20px;
  margin: 0 auto;
  margin-top: 20px;
  color: white;
  font-family: Arial, sans-serif;
  box-sizing: border-box;
}

.related-galleries .gallery-list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.gallery-item {

  display: flex;
  width: 100%;
  align-items: center;
  margin-bottom: 15px;
  border: 1px solid #ccc;
  padding: 10px;
  border-radius: 5px;
}

.gallery-thumb {
  width: 160px;
  height: auto;
  object-fit: cover;
  margin-right: 15px;
  border-radius: 8px;
}

.gallery-info {

  width: 100%;
}


.gallery-info h4 {
  margin: 0 0 5px;
}

.gallery-info p {
  margin: 0;
  font-size: 14px;
}
</style>
