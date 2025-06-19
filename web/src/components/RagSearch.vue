<template>
    <div class="container">

        <!-- Loading spinner -->
        <div v-if="loading" class="loading-overlay">
            <ProgressSpinner />
            <p>Loading, please wait...</p>
        </div>
        <div class="control-panel">
            <div class="button-group">
                <Button v-for="type in typeList" :key="type.name" :label="type.name"
                    :class="['btn', type.color, 'type-btn', { active: activeType === type.name }]"
                    @click="toggleType(type.name)" />
            </div>
            <div class="search-bar">
                <InputText v-model="searchQuery" placeholder="Search Keywords" class="custom-input" />
                <Button label="Search Tags" class="btn search-btn" @click="performSearchTags" severity="secondary" />
                <Button label="Clear" class="btn clear-btn" @click="clearSearch" severity="secondary" />
            </div>
        </div>

        <!-- Tag 搜索结果 -->
        <div v-if="tags.length > 0" class="result-table">
            <table class="tag-table">
                <thead>
                    <tr>
                        <th>Namespace</th>
                        <th>Tag</th>
                        <th>Tag (CN)</th>
                        <th>Intro</th>
                        <th>Input Keyword</th>
                        <th>Similarity</th>
                        <th>Query</th> <!-- 新增 -->
                    </tr>
                </thead>
                <tbody>
                    <tr v-for="(tag, index) in tags" :key="index">
                        <td>{{ tag.namespace }}</td>
                        <td>{{ tag.tag }}</td>
                        <td>{{ tag.tag_cn }}</td>
                        <td>{{ tag.intro }}</td>
                        <td>{{ tag.input_keyword }}</td>
                        <td>{{ (tag.similarity * 100).toFixed(2) }}%</td>
                        <td>
                            <ToggleSwitch v-model="tag.includeInQuery" />
                        </td> <!-- 新增 -->
                    </tr>
                </tbody>
            </table>
        </div>

        <!-- 查询 Tag 后，单独查询 Gallery -->
        <div v-if="tags.length > 0" class="gallery-search">
            <Button label="Search Galleries" class="btn search-btn"  @click="performSearchGalleries"
            severity="secondary" />
            <InputNumber class="num-input" v-model.number="searchNumber" :min="1" :max="20" suffix=" pages" />
        </div>

        <div v-else class="no-results">
            <p>No tags found. Try a different search query.</p>
        </div>

        <!-- Gallery 搜索结果 -->
        <div v-if="galleries.length > 0" class="gallery-list">
            <h3>Gallery Results</h3>
            <ul>
                <li v-for="(gallery, index) in galleries" :key="gallery.gid" class="gallery-item">
                    <img :src="gallery.thumb" alt="Gallery Thumbnail" class="gallery-thumb" />
                    <div class="gallery-info">
                        <h4>{{ gallery.title }}</h4>
                        <h4>{{ gallery.title_jpn }}</h4>
                        <p><strong>Category:</strong> {{ gallery.category }}</p>
                        <p><strong>Uploader:</strong> {{ gallery.uploader }}</p>
                        <p><strong>Posted:</strong> {{ formatTimestamp(gallery.posted) }}</p>
                        <p><strong>Rating:</strong> {{ gallery.rating }}</p>
                        <p><strong>Page:</strong> {{ gallery.filecount }}</p>
                        <p>
                            <!-- 遍历每个 gallery 的 tags -->
                            <Tag v-for="(tag, index) in gallery.tags" :key="index"
                                :value="tag.tag_cn ? tag.tag_cn : tag.tag"
                                :class="['tag', isMatchingTag(tag) ? 'highlighted-tag' : '']"
                                :severity="isMatchingTag(tag) ? 'danger' : 'secondary'" />
                        </p>
                    </div>
                </li>
            </ul>
        </div>

        <div v-else-if="searchPerformed" class="no-gallery-results">
            <p>No galleries found. Try a different search query.</p>
        </div>
    </div>
</template>


<script>
import { ref } from "vue";
import axios from "axios";
import Button from "primevue/button";
import InputText from "primevue/inputtext";
import Tag from "primevue/tag";
import ToggleSwitch from 'primevue/toggleswitch';
import ProgressSpinner from 'primevue/progressspinner';
import Slider from 'primevue/slider';
import InputNumber from 'primevue/inputnumber';

export default {
    components: {
        InputNumber,
        Slider,
        ProgressSpinner,
        Button,
        InputText,
        Tag,
        ToggleSwitch,
    },
    setup() {
        const searchQuery = ref(""); // 用户输入的查询
        const tags = ref([]); // 返回的标签数据
        const galleries = ref([]); // 返回的 gallery 数据
        const loading = ref(false); // 加载状态
        const errorMessage = ref(""); // 错误信息
        const activeType = ref(null); // 当前选中的类型
        const searchNumber = ref(10); // 默认查询gallery数量
        const searchPerformed = ref(false); // 是否已执行过搜索

        // 初始化 `tags` 的 includeInQuery 属性
        const initializeTags = (tagsList) => {
            tagsList.forEach(tag => {
                tag.includeInQuery = true; // 默认所有标签参与查询
            });
            tags.value = tagsList;
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

        const toggleType = (type) => {
            if (activeType.value === type) {
                activeType.value = null; // 再次点击取消选中
            } else {
                activeType.value = type; // 选中类型
            }
        };

        // 检查 gallery 的 tag 是否与查询的 tag 匹配
        const isMatchingTag = (galleryTag) => {
            return tags.value.some(
                (searchTag) =>
                    searchTag.namespace === galleryTag.namespace &&
                    searchTag.tag === galleryTag.value
            );
        };

        // 查询 Tags
        const performSearchTags = async () => {
            if (!searchQuery.value.trim()) {
                errorMessage.value = "Please enter a search query.";
                return;
            }

            errorMessage.value = ""; // 清除错误信息
            loading.value = true; // 开始加载
            tags.value = []; // 清空现有 tags 数据
            galleries.value = []; // 清空现有gallery
            searchPerformed.value = false;

            try {
                // 请求后端 API 获取 Tags
                const tagResponse = await axios.post("http://127.0.0.1:5001/api/rag_search", {
                    input_text: searchQuery.value.trim(),
                });

                // 初始化 Tags 数据并添加 includeInQuery 属性
                const fetchedTags = tagResponse.data.tags || [];
                tags.value = fetchedTags.map(tag => ({
                    ...tag,
                    includeInQuery: true, // 默认所有标签参与查询
                }));

                if (tags.value.length === 0) {
                    errorMessage.value = "No tags found for the given input.";
                }
            } catch (error) {
                errorMessage.value = error.response?.data?.error || "An error occurred while fetching tags.";
            } finally {
                loading.value = false; // 结束加载
            }
        };


        // 查询 Galleries
        const performSearchGalleries = async () => {
            if (tags.value.length === 0) {
                errorMessage.value = "Please search for tags first.";
                return;
            }

            // 过滤出 includeInQuery 为 true 的标签
            const selectedTags = tags.value.filter(tag => tag.includeInQuery);

            if (selectedTags.length === 0) {
                errorMessage.value = "Please select at least one tag to query galleries.";
                return;
            }

            errorMessage.value = ""; // 清除错误信息
            // loading.value = true; // 开始加载
            galleries.value = []; // 清空现有 gallery 数据

            try {
                const galleryResponse = await axios.post("http://127.0.0.1:5001/api/get_top_galleries", {
                    tags_list: selectedTags.map(tag => `${tag.namespace}:${tag.tag}`), // 仅传递选中的标签
                    n: searchNumber.value, // 返回的 gallery 数量
                    category: activeType.value || null, // 如果有选中的类型则传递，没有则为 null
                });
                galleries.value = galleryResponse.data.galleries || []; // 更新 gallery 数据
                searchPerformed.value = true;
            } catch (error) {
                errorMessage.value = error.response?.data?.error || "An error occurred while fetching galleries.";
            } finally {
                // loading.value = false; // 结束加载
            }
        };


        // 清除搜索
        const clearSearch = () => {
            searchQuery.value = "";
            tags.value = [];
            galleries.value = [];
            errorMessage.value = "";
            searchPerformed.value = false;
        };
        const formatTimestamp = (timestamp) => {
            if (!timestamp) return "N/A"; // 如果时间戳为空，返回 N/A

            const date = new Date(timestamp * 1000); // 假设是秒级时间戳，乘以 1000 转为毫秒
            const year = date.getFullYear();
            const month = String(date.getMonth() + 1).padStart(2, "0");
            const day = String(date.getDate()).padStart(2, "0");
            const hours = String(date.getHours()).padStart(2, "0");
            const minutes = String(date.getMinutes()).padStart(2, "0");

            return `${year}-${month}-${day} ${hours}:${minutes}`;
        };
        return {
            searchNumber,
            formatTimestamp, // 确保在这里返回
            searchQuery,
            tags,
            galleries,
            loading,
            errorMessage,
            activeType,
            searchPerformed,
            typeList,
            toggleType,
            performSearchTags,
            performSearchGalleries,
            clearSearch,
            isMatchingTag,
            initializeTags,
        };
    },
};

</script>



<style src="../assets/RagSearch.css"></style>