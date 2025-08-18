<template>
    <div class="container">

        <!-- 顶部行：Statistics (左) 和 Categories (右) -->
        <div class="stats-row">
            <div class="stats-left">
                <h1 class="section-title-large">Gallery Statistics</h1>
                <p class="stats-text">Total Galleries: {{ stats.total_count }}</p>
                <div class="line-chart-container">
                    <Chart type="line" :data="quarterlyLineData" :options="quarterlyLineOptions"
                        class="chart-full" />
                </div>
            </div>
            <div class="stats-right">
                <h2 class="section-title">Categories</h2>
                <div class="chart-container">
                    <Chart type="pie" :data="chartData" :options="chartOptions" class="chart-responsive" />
                </div>
            </div>
        </div>

        <!-- 中间行：Female Tags (左) 和 Male Tags (右) -->
        <div class="tags-row">
            <div class="tags-section-half">
                <h2 class="section-title">Female Tags</h2>
                <div class="chart-container">
                    <Chart type="bar" :data="femaleChartData" :options="barChartOptions" class="chart-responsive" />
                </div>
            </div>
            <div class="tags-section-half">
                <h2 class="section-title">Male Tags</h2>
                <div class="chart-container">
                    <Chart type="bar" :data="maleChartData" :options="barChartOptions" class="chart-responsive" />
                </div>
            </div>
        </div>

        <!-- 底部行 -->
        <div class="bottom-row">
            <div class="bottom-section">
                <h2 class="section-title">Other</h2>
                <table class="data-table">
                    <colgroup>
                        <col class="tag-col">
                        <col class="count-col">
                    </colgroup>
                    <thead>
                        <tr>
                            <th class="left-align">Tag</th>
                            <th class="right-align">Count</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr v-for="tag in tags.other" :key="tag.tag" v-tooltip.bottom="[
                            `${tag.tag}`,
                            `翻译: ${tag.tag_cn || 'N/A'}`,
                            tag.intro ? `介绍: ${tag.intro.length > 100 ? tag.intro.slice(0, 100) + '...' : tag.intro}` : null
                        ].filter(Boolean).join('\n')">
                            <td class="left-align">
                                {{ tag.tag_cn || tag.tag.replace(/^language:/, '') }}
                            </td>
                            <td class="right-align">
                                {{ tag.count }}
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
            
            <div class="bottom-section">
                <h2 class="section-title">Artist</h2>
                <table class="data-table">
                    <colgroup>
                        <col class="tag-col">
                        <col class="count-col">
                    </colgroup>
                    <thead>
                        <tr>
                            <th class="left-align">Tag</th>
                            <th class="right-align">Count</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr v-for="tag in tags.artist" :key="tag.tag" v-tooltip.bottom="[
                            `${tag.tag}`,
                            `翻译: ${tag.tag_cn || 'N/A'}`,
                            tag.intro ? `介绍: ${tag.intro.length > 100 ? tag.intro.slice(0, 100) + '...' : tag.intro}` : null
                        ].filter(Boolean).join('\n')">
                            <td class="left-align">
                                {{ tag.tag_cn || tag.tag.replace(/^artist:/, '') }}
                            </td>
                            <td class="right-align">{{ tag.count }}</td>
                        </tr>
                    </tbody>
                </table>
            </div>
            
            <div class="bottom-section">
                <h2 class="section-title">Parody</h2>
                <table class="data-table">
                    <colgroup>
                        <col class="tag-col">
                        <col class="count-col">
                    </colgroup>
                    <thead>
                        <tr>
                            <th class="left-align">Tag</th>
                            <th class="right-align">Count</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr v-for="tag in tags.parody" :key="tag.tag" v-tooltip.bottom="[
                            `${tag.tag}`,
                            `翻译: ${tag.tag_cn || 'N/A'}`,
                            tag.intro ? `介绍: ${tag.intro.length > 100 ? tag.intro.slice(0, 100) + '...' : tag.intro}` : null
                        ].filter(Boolean).join('\n')">
                            <td class="left-align">
                                {{ tag.tag_cn || tag.tag.replace(/^parody:/, '') }}
                            </td>
                            <td class="right-align">{{ tag.count }}</td>
                        </tr>
                    </tbody>
                </table>
            </div>
            
            <div class="bottom-section">
                <h2 class="section-title">Character</h2>
                <table class="data-table">
                    <colgroup>
                        <col class="tag-col">
                        <col class="count-col">
                    </colgroup>
                    <thead>
                        <tr>
                            <th class="left-align">Tag</th>
                            <th class="right-align">Count</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr v-for="tag in tags.character" :key="tag.tag" v-tooltip.bottom="[
                            `${tag.tag}`,
                            `翻译: ${tag.tag_cn || 'N/A'}`,
                            tag.intro ? `介绍: ${tag.intro.length > 100 ? tag.intro.slice(0, 100) + '...' : tag.intro}` : null
                        ].filter(Boolean).join('\n')">
                            <td class="left-align">
                                {{ tag.tag_cn || tag.tag.replace(/^character:/, '') }}
                            </td>
                            <td class="right-align">{{ tag.count }}</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>

    </div>
</template>

<script>
import { ref, onMounted, watch } from "vue";
import Chart from "primevue/chart";
import axios from "axios";
import { useTheme } from '@/composables/useTheme';
import '@/assets/DataAnalys.css';

const API = import.meta.env.VITE_API_BASE;
export default {
    components: { Chart },
    setup() {
        const { isDark } = useTheme()
        return { isDark }
    },
    data() {
        return {
            stats: {
                total_count: 0,
                categories: {},
            },
            tags: {
                artist: [],
                other: [],
                female: [],
                male: [],
                character: [],
                parody: []
            },
            types: ["artist", "other", "female", "male", "character", "parody"],
            chartData: null,
            chartOptions: null,
            femaleChartData: null,
            maleChartData: null,
            barChartOptions: null,
            categoryColors: {
                Doujinshi: "#a11",
                Manga: "#d67e22",
                "Artist CG": "#d6a922",
                "Game CG": "#4caf50",
                Western: "#d4af37",
                "Non-H": "#4ca3dd",
                "Image Set": "#2a78d6",
                Cosplay: "#7e57c2",
                "Asian Porn": "#a11548",
                Misc: "#757575",
            },
            // 新增用于季度折线图的数据和选项
            quarterlyLineData: null,
            quarterlyLineOptions: null,
        };
    },
    mounted() {
        this.fetchStats();
        this.fetchTags();
        this.fetchQuarterlyStats();
    },
    watch: {
        isDark: {
            handler() {
                // 主题切换时重新生成图表配置
                this.updateChart();
                this.updateBarCharts();
                if (this.quarterlyLineData && this.quarterlyLineData.labels && this.quarterlyLineData.labels.length > 0) {
                    // 重新创建季度图表
                    const quarters = this.quarterlyLineData.labels;
                    const counts = this.quarterlyLineData.datasets[0].data;
                    const quarterlyData = quarters.map((quarter, index) => ({
                        quarter,
                        count: counts[index]
                    }));
                    this.initQuarterlyLineChart(quarterlyData);
                }
            },
            immediate: false
        }
    },
    methods: {
        async fetchStats() {
            try {
                const response = await axios.get(`${API}/api/gallery/stats`);
                this.stats = response.data;
                this.updateChart();
            } catch (error) {
                console.error("Failed to fetch stats:", error);
            }
        },
        async fetchTags() {
            for (const type of this.types) {
                try {
                    const response = await axios.get(`${API}/api/gallery/top-tags?n=20&type=${type}`);
                    this.tags[type] = response.data.top_tags;
                } catch (error) {
                    console.error(`Failed to fetch tags for ${type}:`, error);
                }
            }
            this.updateBarCharts();
        },
        async fetchQuarterlyStats() {
            try {
                const response = await axios.get(`${API}/api/gallery/quarterly-stats`);
                const data = response.data.data || [];
                this.initQuarterlyLineChart(data);
            } catch (error) {
                console.error("Failed to fetch quarterly stats:", error);
            }
        },
        updateChart() {
            const labels = Object.keys(this.stats.categories);
            const data = Object.values(this.stats.categories);
            const backgroundColors = labels.map(
                (label) => this.categoryColors[label] || "#757575"
            );

            this.chartData = {
                labels,
                datasets: [
                    {
                        data,
                        backgroundColor: backgroundColors,
                    },
                ],
            };
            this.chartOptions = this.getChartOptions();
        },
        updateBarCharts() {
            // Female Chart Data
            const femaleLabels = this.tags.female.map((tag) => tag.tag_cn || tag.tag.replace(/^female:/, '')); // 默认显示中文
            const femaleCounts = this.tags.female.map((tag) => tag.count);
            this.femaleChartData = {
                labels: femaleLabels,
                datasets: [
                    {
                        label: "Female Tags",
                        data: femaleCounts,
                        backgroundColor: "#f06292",
                    },
                ],
            };

            // Male Chart Data
            const maleLabels = this.tags.male.map((tag) => tag.tag_cn || tag.tag.replace(/^male:/, '')); // 默认显示中文
            const maleCounts = this.tags.male.map((tag) => tag.count);
            this.maleChartData = {
                labels: maleLabels,
                datasets: [
                    {
                        label: "Male Tags",
                        data: maleCounts,
                        backgroundColor: "#42a5f5",
                    },
                ],
            };

            this.barChartOptions = this.getBarChartOptions();
        },
        initQuarterlyLineChart(quarterlyData) {
            // quarterlyData 格式假设为： [{ "quarter": "2022-Q1", "count": 123 }, ...]
            const quarters = quarterlyData.map(item => item.quarter);
            const counts = quarterlyData.map(item => item.count);

            // 动态主题颜色
            const textColor = this.isDark ? '#f1f5f9' : '#2d3748';
            const textColorSecondary = this.isDark ? '#cbd5e1' : '#64748b';
            const gridColor = this.isDark ? '#475569' : '#d6d3d1';
            const borderColor = this.isDark ? '#00bcd4' : '#0891b2';
            const bgColor = this.isDark ? 'rgba(107, 114, 128, 0.2)' : 'rgba(8, 145, 178, 0.1)';

            this.quarterlyLineData = {
                labels: quarters,
                datasets: [
                    {
                        label: 'Quarterly Counts',
                        data: counts,
                        fill: true,
                        borderColor: borderColor,
                        tension: 0.4,
                        backgroundColor: bgColor
                    }
                ]
            };

            this.quarterlyLineOptions = {
                maintainAspectRatio: false,
                aspectRatio: 0.6,
                plugins: {
                    legend: {
                        labels: {
                            color: textColor
                        }
                    }
                },
                scales: {
                    x: {
                        ticks: {
                            color: textColorSecondary
                        },
                        grid: {
                            color: gridColor
                        }
                    },
                    y: {
                        ticks: {
                            color: textColorSecondary
                        },
                        grid: {
                            color: gridColor
                        }
                    }
                }
            };
        },
        getChartOptions() {
            // 动态主题颜色
            const textColor = this.isDark ? '#f1f5f9' : '#2d3748';
            const gridColor = this.isDark ? '#475569' : '#d6d3d1';
            
            return {
                plugins: {
                    legend: {
                        labels: {
                            usePointStyle: true,
                            color: textColor,
                        },
                    },
                },
                scales: {
                    x: {
                        ticks: {
                            color: textColor,
                        },
                        grid: {
                            color: gridColor,
                        },
                    },
                    y: {
                        ticks: {
                            color: textColor,
                            beginAtZero: true,
                        },
                        grid: {
                            color: gridColor,
                        },
                    },
                },
            };
        },
        getBarChartOptions() {
            // 动态主题颜色
            const textColor = this.isDark ? '#f1f5f9' : '#2d3748';
            const gridColor = this.isDark ? '#475569' : '#d6d3d1';
            
            return {
                plugins: {
                    legend: {
                        labels: {
                            color: textColor,
                        },
                    },
                },
                scales: {
                    x: {
                        ticks: {
                            color: textColor,
                            font: {
                                size: 12,
                            },
                        },
                        grid: {
                            color: gridColor,
                        },
                    },
                    y: {
                        ticks: {
                            color: textColor,
                            font: {
                                size: 12,
                            },
                            beginAtZero: true,
                        },
                        grid: {
                            color: gridColor,
                        },
                    },
                },
            };
        },
    },
};
</script>