<template>
    <div class="container">

        <!-- 顶部行：Statistics (左) 和 Categories (右) -->
        <div style="display:flex; border:1px solid #444; border-radius:8px; overflow:hidden; margin-bottom:1rem;">
            <div style="width:60%; background:#222; padding:1rem; box-sizing:border-box;">
                <h1 style="font-size:1.25rem; font-weight:bold; margin:0 0 10px;">Gallery Statistics</h1>
                <p style="margin:0;">Total Galleries: {{ stats.total_count }}</p>
                <div class="line-chart-container" style="margin-top:1rem; height:300px;">
                    <Chart type="line" :data="quarterlyLineData" :options="quarterlyLineOptions"
                        style="width:100%; height:100%;" />
                </div>
            </div>
            <div style="width:40%; background:#222; padding:1rem; box-sizing:border-box; border-left:1px solid #444;">
                <h2 style="font-size:1.125rem; font-weight:bold; margin:0 0 10px;">Categories</h2>
                <div style="max-width:100%; overflow:auto;">
                    <Chart type="pie" :data="chartData" :options="chartOptions" style="max-width:100%;" />
                </div>
            </div>
        </div>

        <!-- 中间行：Female Tags (左) 和 Male Tags (右) -->
        <div style="display:flex; border:1px solid #444; border-radius:8px; overflow:hidden; margin-bottom:1rem;">
            <div style="width:50%; background:#222; padding:1rem; box-sizing:border-box;">
                <h2 style="font-size:1.125rem; font-weight:bold; margin:0 0 10px;">Female Tags</h2>
                <div style="max-width:100%; overflow:auto;">
                    <Chart type="bar" :data="femaleChartData" :options="barChartOptions" style="max-width:100%;" />
                </div>
            </div>
            <div style="width:50%; background:#222; padding:1rem; box-sizing:border-box; border-left:1px solid #444;">
                <h2 style="font-size:1.125rem; font-weight:bold; margin:0 0 10px;">Male Tags</h2>
                <div style="max-width:100%; overflow:auto;">
                    <Chart type="bar" :data="maleChartData" :options="barChartOptions" style="max-width:100%;" />
                </div>
            </div>
        </div>

        <!-- 底部行 -->
        <div style="display:flex; border:1px solid #444; border-radius:8px; overflow:hidden;">
            <div style="width:25%; background:#222; padding:1rem; box-sizing:border-box;">
                <h2 style="font-size:1.125rem; font-weight:bold; margin:0 0 10px;">Other</h2>
                <table
                    style="width:100%; border-collapse:collapse; color:#eee; white-space:normal; word-break:break-all; table-layout:fixed;">
                    <colgroup>
                        <col style="width:70%;">
                        <col style="width:30%;">
                    </colgroup>
                    <thead>
                        <tr>
                            <th style="border-bottom:1px solid #444; padding:8px; text-align:left;">Tag</th>
                            <th style="border-bottom:1px solid #444; padding:8px; text-align:right;">Count</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr v-for="tag in tags.other" :key="tag.tag" v-tooltip.bottom="[
                            `${tag.tag}`,
                            `翻译: ${tag.tag_cn || 'N/A'}`,
                            tag.intro ? `介绍: ${tag.intro.length > 100 ? tag.intro.slice(0, 100) + '...' : tag.intro}` : null // 限制 intro 长度
                        ].filter(Boolean).join('\n')">
                            <td style="border-bottom:1px solid #444; padding:8px; text-align:left;">
                                {{ tag.tag_cn || tag.tag.replace(/^language:/, '') }}
                            </td>
                            <td style="border-bottom:1px solid #444; padding:8px; text-align:right;">
                                {{ tag.count }}
                            </td>
                        </tr>
                    </tbody>
                </table>

            </div>
            <div style="width:25%; background:#222; padding:1rem; box-sizing:border-box; border-left:1px solid #444;">
                <h2 style="font-size:1.125rem; font-weight:bold; margin:0 0 10px;">Artist</h2>
                <table
                    style="width:100%; border-collapse:collapse; color:#eee; white-space:normal; word-break:break-all; table-layout:fixed;">
                    <colgroup>
                        <col style="width:70%;">
                        <col style="width:30%;">
                    </colgroup>
                    <thead>
                        <tr>
                            <th style="border-bottom:1px solid #444; padding:8px; text-align:left;">Tag</th>
                            <th style="border-bottom:1px solid #444; padding:8px; text-align:right;">Count</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr v-for="tag in tags.artist" :key="tag.tag" v-tooltip.bottom="[
                            `${tag.tag}`,
                            `翻译: ${tag.tag_cn || 'N/A'}`,
                            tag.intro ? `介绍: ${tag.intro.length > 100 ? tag.intro.slice(0, 100) + '...' : tag.intro}` : null // 限制 intro 长度
                        ].filter(Boolean).join('\n')">
                            <td style="border-bottom:1px solid #444; padding:8px; text-align:left;">
                                {{ tag.tag_cn || tag.tag.replace(/^artist:/, '') }}
                            </td>
                            <td style="border-bottom:1px solid #444; padding:8px; text-align:right;">{{ tag.count }}
                            </td>
                        </tr>
                    </tbody>
                </table>

            </div>
            <div style="width:25%; background:#222; padding:1rem; box-sizing:border-box; border-left:1px solid #444;">
                <h2 style="font-size:1.125rem; font-weight:bold; margin:0 0 10px;">Parody</h2>
                <table
                    style="width:100%; border-collapse:collapse; color:#eee; white-space:normal; word-break:break-all; table-layout:fixed;">
                    <colgroup>
                        <col style="width:70%;">
                        <col style="width:30%;">
                    </colgroup>
                    <thead>
                        <tr>
                            <th style="border-bottom:1px solid #444; padding:8px; text-align:left;">Tag</th>
                            <th style="border-bottom:1px solid #444; padding:8px; text-align:right;">Count</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr v-for="tag in tags.parody" :key="tag.tag" v-tooltip.bottom="[
                            `${tag.tag}`,
                            `翻译: ${tag.tag_cn || 'N/A'}`,
                            tag.intro ? `介绍: ${tag.intro.length > 100 ? tag.intro.slice(0, 100) + '...' : tag.intro}` : null // 限制 intro 长度
                        ].filter(Boolean).join('\n')">
                            <td style="border-bottom:1px solid #444; padding:8px; text-align:left;">
                                {{ tag.tag_cn || tag.tag.replace(/^parody:/, '') }}
                            </td>
                            <td style="border-bottom:1px solid #444; padding:8px; text-align:right;">{{ tag.count }}
                            </td>
                        </tr>
                    </tbody>
                </table>

            </div>
            <div style="width:25%; background:#222; padding:1rem; box-sizing:border-box; border-left:1px solid #444;">
                <h2 style="font-size:1.125rem; font-weight:bold; margin:0 0 10px;">Character</h2>
                <table
                    style="width:100%; border-collapse:collapse; color:#eee; white-space:normal; word-break:break-all; table-layout:fixed;">
                    <colgroup>
                        <col style="width:70%;">
                        <col style="width:30%;">
                    </colgroup>
                    <thead>
                        <tr>
                            <th style="border-bottom:1px solid #444; padding:8px; text-align:left;">Tag</th>
                            <th style="border-bottom:1px solid #444; padding:8px; text-align:right;">Count</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr v-for="tag in tags.character" :key="tag.tag" v-tooltip.bottom="[
                            `${tag.tag}`,
                            `翻译: ${tag.tag_cn || 'N/A'}`,
                            tag.intro ? `介绍: ${tag.intro.length > 100 ? tag.intro.slice(0, 100) + '...' : tag.intro}` : null // 限制 intro 长度
                        ].filter(Boolean).join('\n')">
                            <td style="border-bottom:1px solid #444; padding:8px; text-align:left;">

                                {{ tag.tag_cn || tag.tag.replace(/^character:/, '') }}</td>
                            <td style="border-bottom:1px solid #444; padding:8px; text-align:right;">{{ tag.count }}
                            </td>
                        </tr>
                    </tbody>
                </table>

            </div>
        </div>

    </div>
</template>

<script>
import { ref, onMounted } from "vue";
import Chart from "primevue/chart";
import axios from "axios";

const API = import.meta.env.VITE_API_BASE;
export default {
    components: { Chart },
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

            const documentStyle = getComputedStyle(document.documentElement);
            const textColor = documentStyle.getPropertyValue('--p-text-color') || '#eee';
            const textColorSecondary = documentStyle.getPropertyValue('--p-text-muted-color') || '#bbb';
            const surfaceBorder = documentStyle.getPropertyValue('--p-content-border-color') || '#444';

            this.quarterlyLineData = {
                labels: quarters,
                datasets: [
                    {
                        label: 'Quarterly Counts',
                        data: counts,
                        fill: true,
                        borderColor: documentStyle.getPropertyValue('--p-cyan-500') || '#00bcd4',
                        tension: 0.4,
                        backgroundColor: 'rgba(107, 114, 128, 0.2)'
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
                            color: surfaceBorder
                        }
                    },
                    y: {
                        ticks: {
                            color: textColorSecondary
                        },
                        grid: {
                            color: surfaceBorder
                        }
                    }
                }
            };
        },
        getChartOptions() {
            // 自定义Chart样式
            const textColor = '#eee';
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
                    },
                    y: {
                        ticks: {
                            color: textColor,
                            beginAtZero: true,
                        },
                    },
                },
            };
        },
        getBarChartOptions() {
            const textColor = '#eee';
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
                    },
                    y: {
                        ticks: {
                            color: textColor,
                            font: {
                                size: 12,
                            },
                            beginAtZero: true,
                        },
                    },
                },
            };
        },
    },
};
</script>


<style scoped>
* {
    box-sizing: border-box;
}

body {
    background-color: #34353a;
    /* 设置为深灰色背景 */
    margin: 0;
    /* 移除默认外边距 */
    padding: 0;
    /* 移除默认内边距 */
}

#app {
    position: relative;
    /* 保持流式布局 */
    margin: auto;
    margin-top: 0px;
    width: 100%;
    max-width: 1500px;
    /* 设置最大宽度 */
    padding: 5px;
    /* 将 padding 设置为 20px，可以根据需要调整 */

}

.container {
    width: 100%;
    max-width: 1300px;
    /* 限制最大宽度 */
    background-color: #50535a;
    padding: 20px;
    margin: 0 auto;
    /* 水平居中 */
    border-radius: 8px;
    color: white;
    font-family: Arial, sans-serif;
    box-sizing: border-box;
    /* 确保 padding 不影响宽高 */
}
</style>