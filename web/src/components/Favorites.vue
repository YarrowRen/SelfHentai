<template>
  <div class="container">
    <div class="control-panel">
      <div class="button-group">
        <Button v-for="type in favCategoryList" :key="type.name" :label="type.name"
          :class="['btn', type.color, 'type-btn', { active: activeFav === type.name }]"
          @click="toggleFav(type.name)" />
      </div>
    </div>

    <!-- 使用 PrimeVue Paginator -->
    <Paginator :template="{
      default: 'CurrentPageReport FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink JumpToPageInput '
    }" :rows="perPage" :totalRecords="totalRecords" :first="(currentPage - 1) * perPage" @page="onPageChange" />

    <!-- 动态生成表单 -->
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
            <td @click="navigateToGallery(item.gid, item.token)" style="cursor: pointer; position: relative;"
              @mouseenter="showPopover($event, item)" @mouseleave="hidePopover">
              <!-- 标题容器 -->
              <div class="title-container">

                {{ item.title_jpn || item.title }}
              </div>
              <!-- 标签容器 -->
              <div class="tags-container">
                <Tag v-for="(tag, index) in item.tags" :key="index" :value="tag.tag_cn ? tag.tag_cn : tag.tag"
                  class="tag" severity="secondary" />
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
            <td>{{ item.uploader }}<br>{{ item.filecount }}</td>
          </tr>
        </tbody>
      </table>
      <!-- 鼠标悬停显示 Popover -->
      <Popover ref="popover" class="image-popover">
        <img v-if="popoverData.thumb" :src="popoverData.thumb" />
        <div v-else>No Image Available</div>
      </Popover>
    </div>

    <!-- 使用 PrimeVue Paginator -->
    <Paginator :template="{
      default: 'CurrentPageReport FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink JumpToPageInput '
    }" :rows="perPage" :totalRecords="totalRecords" :first="(currentPage - 1) * perPage" @page="onPageChange" />
  </div>
</template>

<script>
import { ref, computed } from "vue";
import axios from "axios";
import Button from "primevue/button";
import InputText from "primevue/inputtext";
import Paginator from "primevue/paginator";
import Tag from "primevue/tag"; // 引入 Tag 组件
import Rating from 'primevue/rating';
import Image from 'primevue/image';
import Popover from "primevue/popover";

export default {
  components: {
    Popover,
    Image,
    Button,
    InputText,
    Paginator,
    Tag, // 注册 Tag 组件
    Rating,
  },
  setup() {
    const searchQuery = ref("");
    const results = ref([]);
    const currentPage = ref(1);
    const perPage = ref(25);
    const totalRecords = ref(0);
    const popover = ref();
    const popoverData = ref(null);


    const navigateToGallery = (gid, token) => {
      const url = `http://localhost:5173/gallery/${gid}/`;
      window.open(url, "_blank");
    };

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


    // favCategory 状态
    const activeFav = ref(null);
    const favCategoryList = ref([]);
    const colorPalette = [
      "red",
      "orange",
      "yellow",
      "green",
      "blue",
      "purple",
      "pink",
      "gray",
      "gold",
      "lightblue",
    ];

    // 获取 favCategory 数据
    const fetchFavCategories = async () => {
      try {
        const response = await axios.get("http://127.0.0.1:5001/api/fav_category");
        const categories = response.data.data || []; // 获取 favCategory 数据
        favCategoryList.value = categories.map((name, index) => ({
          name,
          color: colorPalette[index % colorPalette.length], // 循环分配颜色
        }));
        console.log(favCategoryList)
      } catch (error) {
        console.error("Error fetching favCategory:", error);
      }
    };

    // 计算总页数
    const totalPages = computed(() => Math.ceil(totalRecords.value / perPage.value));

    // 类型到颜色类名的映射
    const typeClassMap = Object.fromEntries(
      typeList.value.map((type) => [type.name, type.color])
    );

    const fetchData = async (page = 1, keyword = "", favCategory = null) => {
      try {
        const response = await axios.get("http://127.0.0.1:5001/api/local_gallery", {
          params: {
            page,
            per_page: perPage.value,
            keyword, // 添加关键词参数
            favCategory, // 类型限制参数
          },
        });

        const { data, total } = response.data;
        console.log(total)
        // 映射数据
        results.value = data.map((item) => ({
          type: item.category,
          typeClass: typeClassMap[item.category] || "default", // 根据类型映射到颜色类名
          title: item.title,
          title_jpn: item.title_jpn,
          published: new Date(item.posted * 1000).toISOString().replace('T', ' ').slice(0, 16),
          gid: item.gid,
          token: item.token,
          filecount: item.filecount ? `${item.filecount} pages` : "", // 处理 pages
          uploader: item.uploader || "Unknown",
          tags: item.tags || [],
          rating: item.rating,
          thumb: item.thumb,
        }));

        // 填充空数据
        const resultsLength = results.value.length;
        if (resultsLength < perPage.value) {
          const emptyItems = perPage.value - resultsLength;
          for (let i = 0; i < emptyItems; i++) {
            results.value.push({
              type: "", // 空类型
              typeClass: "default", // 默认类名
              title: "", // 空标题
              published: "", // 空发布时间
              gid: null,
              token: null,
              uploader: "", // 空上传者
            });
          }
        }

        currentPage.value = page;
        totalRecords.value = total;
      } catch (error) {
        console.error("Error fetching data:", error);
      }
    };


    const performSearch = async () => {
      await fetchData(1, searchQuery.value, activeFav.value); // 搜索时从第一页开始，传入关键词和类型
    };

    const clearSearch = () => {
      searchQuery.value = "";
      activeFav.value = null;
      fetchData(1); // 清空搜索条件并重新加载第一页
    };

    const onPageChange = (event) => {
      const nextPage = Math.floor(event.first / perPage.value) + 1;
      fetchData(nextPage, searchQuery.value, activeFav.value); // 保持关键词和类型分页查询
    };


    // 切换 favCategory
    const toggleFav = (fav) => {
      if (activeFav.value === fav) {
        activeFav.value = null;
      } else {
        activeFav.value = fav;
      }
      fetchData(1, searchQuery.value, activeFav.value); // 切换类型后重新加载第一页
    };

    const showPopover = (event, item) => {
      // 判断 title 是否为空，如果为空则不展示 Popover
      if (!item.title) {
        return;
      }
      popoverData.value = item;
      console.log(popoverData.value);
      popover.value.show(event);
    };

    const hidePopover = () => {
      if (popover.value) {
        popover.value.hide();
      }
    };

    // 初始化加载第一页数据
    fetchFavCategories(); // 加载 favCategory 数据
    fetchData();

    return {
      popover,
      popoverData,
      searchQuery,
      results,
      currentPage,
      perPage,
      totalRecords,
      performSearch,
      clearSearch,
      onPageChange,
      fetchData,
      totalPages,
      typeList,
      navigateToGallery,
      showPopover,
      hidePopover,
      favCategoryList,
      activeFav,
      toggleFav
    };
  },
};
</script>

<style src="../assets/Favorites.css"></style>
