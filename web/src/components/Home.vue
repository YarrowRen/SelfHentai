<template>
  <div class="container">
    <div class="control-panel">
      <div class="button-group">
        <Button
          v-for="type in typeList"
          :key="type.name"
          :label="type.name"
          :class="['btn', type.color, 'type-btn', { active: activeType === type.name }]"
          @click="toggleType(type.name)"
        />
      </div>

      <div class="search-bar">
        <InputText v-model="searchQuery" placeholder="Search Keywords" class="custom-input" />
        <Button label="Search" class="btn search-btn" @click="performSearch" severity="secondary" />
        <Button label="Clear" class="btn clear-btn" @click="clearSearch" severity="secondary" />
      </div>
    </div>

    <!-- 分页器 -->
    <Paginator
      :template="{ default: 'CurrentPageReport FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink JumpToPageInput ' }"
      :rows="perPage"
      :totalRecords="totalRecords"
      :first="(currentPage - 1) * perPage"
      @page="onPageChange"
    />

    <!-- 表格展示 -->
    <div class="results-table">
      <table>
        <thead>
          <tr>
            <th>Type</th>
            <th>Title</th>
            <th style="width: 150px;">Published</th>
            <th>Uploader</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(item, index) in results" :key="index">
            <td>
              <span :class="'badge ' + item.typeClass">{{ item.type }}</span>
            </td>
            <td
              @click="navigateToGallery(item.gid, item.token)"
              style="cursor: pointer; position: relative;"
              @mouseenter="showPopover($event, item)"
              @mouseleave="hidePopover"
            >
              <div class="title-container">
                {{ item.title_jpn || item.title }}
              </div>
              <div class="tags-container">
                <Tag
                  v-for="(tag, index) in item.tags"
                  :key="index"
                  :value="tag.tag_cn || tag.tag"
                  class="tag"
                  severity="secondary"
                />
              </div>
            </td>
            <td>
              <div class="cell-content">
                <div>{{ item.published }}</div>
                <div v-if="item.rating">
                  <Rating v-model="item.rating" readonly />
                </div>
              </div>
            </td>
            <td>
              {{ item.uploader }}<br />
              {{ item.filecount }}
            </td>
          </tr>
        </tbody>
      </table>

      <Popover ref="popover" class="image-popover">
        <img v-if="popoverData?.thumb" :src="popoverData.thumb" />
        <div v-else>No Image Available</div>
      </Popover>
    </div>

    <!-- 分页器 -->
    <Paginator
      :template="{ default: 'CurrentPageReport FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink JumpToPageInput ' }"
      :rows="perPage"
      :totalRecords="totalRecords"
      :first="(currentPage - 1) * perPage"
      @page="onPageChange"
    />
  </div>
</template>

<script>
import { ref, computed } from "vue";
import axios from "axios";
import Button from "primevue/button";
import InputText from "primevue/inputtext";
import Paginator from "primevue/paginator";
import Tag from "primevue/tag";
import Rating from "primevue/rating";
import Popover from "primevue/popover";

export default {
  components: {
    Button,
    InputText,
    Paginator,
    Tag,
    Rating,
    Popover,
  },
  setup() {
    const searchQuery = ref("");
    const results = ref([]);
    const currentPage = ref(1);
    const perPage = ref(25);
    const totalRecords = ref(0);
    const activeType = ref(null);
    const popover = ref();
    const popoverData = ref(null);
    const API = import.meta.env.VITE_API_BASE;

    const typeList = ref([
      { name: "Doujinshi", color: "red" },
      { name: "Manga", color: "orange" },
      { name: "Artist CG", color: "yellow" },
      { name: "Game CG", color: "green" },
      { name: "Western", color: "gold" },
      { name: "Non-H", color: "lightblue" },
      { name: "Image Set", color: "blue" },
      { name: "Cosplay", color: "purple" },
      { name: "Asian Porn", color: "pink" },
      { name: "Misc", color: "gray" },
    ]);

    const typeClassMap = Object.fromEntries(typeList.value.map(type => [type.name, type.color]));

    const fetchData = async (page = 1, keyword = "", type = null) => {
      try {
        const { data } = await axios.get(`${API}/api/gallery`, {
          params: {
            page,
            per_page: perPage.value,
            keyword,
            type,
          },
        });

        const { results: resList, total } = data;

        results.value = resList.map(item => ({
          type: item.category,
          typeClass: typeClassMap[item.category] || "default",
          title: item.title,
          title_jpn: item.title_jpn,
          published: item.favTime?.replace("T", " ").slice(0, 16) || "",
          gid: item.gid,
          token: item.token,
          uploader: item.uploader,
          filecount: item.filecount ? `${item.filecount} pages` : "",
          tags: item.tags || [],
          rating: item.rating,
          thumb: item.thumb,
        }));

        const fillCount = perPage.value - results.value.length;
        for (let i = 0; i < fillCount; i++) {
          results.value.push({
            type: "",
            typeClass: "default",
            title: "",
            published: "",
            gid: null,
            token: null,
            uploader: "",
            filecount: "",
            tags: [],
          });
        }

        currentPage.value = page;
        totalRecords.value = total;
      } catch (err) {
        console.error("Error fetching data:", err);
      }
    };

    const performSearch = () => fetchData(1, searchQuery.value, activeType.value);

    const clearSearch = () => {
      searchQuery.value = "";
      activeType.value = null;
      fetchData(1);
    };

    const onPageChange = ({ first }) => {
      const page = Math.floor(first / perPage.value) + 1;
      fetchData(page, searchQuery.value, activeType.value);
    };

    const toggleType = (type) => {
      activeType.value = activeType.value === type ? null : type;
      fetchData(1, searchQuery.value, activeType.value);
    };

    const navigateToGallery = (gid, token) => {
      const url = `/gallery/${gid}/`;
      window.open(url, "_blank");
    };

    const showPopover = (event, item) => {
      if (!item?.title) return;
      popoverData.value = item;
      popover.value?.show(event);
    };

    const hidePopover = () => {
      popover.value?.hide();
    };

    fetchData();

    return {
      searchQuery,
      results,
      currentPage,
      perPage,
      totalRecords,
      typeList,
      activeType,
      popover,
      popoverData,
      performSearch,
      clearSearch,
      onPageChange,
      toggleType,
      navigateToGallery,
      showPopover,
      hidePopover,
    };
  },
};
</script>

<style src="../assets/HelloWorld.css"></style>
