# SelfHentai

[English README](./README.md) | 中文版

📚 **SelfHentai**: E/ExHentai 和 JM (18comic) 平台的自托管漫画收藏管理器。

---

## ✨ 功能特性

- 🖼️ **浏览搜索**: 查看您的漫画收藏，包括标题、标签、分类、评分等信息
- 🔍 **高级筛选**: 关键词搜索、分类筛选、分页浏览
- 🔁 **一键同步**: 自动同步 ExHentai 和 JM 收藏夹，自动备份元数据
- 🏷️ **标签翻译**: 支持中英文标签识别和翻译
- 📊 **统计分析**: 全面的分析图表和季度报告
- 🎨 **双主题**: 深色和浅色模式支持，平滑切换
- ⚙️ **Web 配置**: 通过 Web 界面轻松设置 ExHentai/JM 凭证
- 🔄 **实时更新**: 基于 WebSocket 的同步进度实时跟踪

## 🏗️ 架构设计

### 后端 (FastAPI)
- **Python FastAPI** 支持 async/await
- **双提供商支持**: ExHentai 和 JM (18comic) 集成
- **实时通信**: WebSocket 实时更新
- **自动备份**: 同步操作前自动备份元数据
- **线程安全同步**: 并发处理与适当锁定

### 前端 (Vue 3 + TypeScript)
- **Vue 3** 使用 Composition API 和 TypeScript
- **PrimeVue** UI 组件配合自定义样式
- **Chart.js** 数据可视化
- **响应式设计**: 移动端友好界面
- **主题系统**: 全局深色/浅色模式切换

## 🚀 快速开始

### 环境要求
- **Python 3.8+**
- **Node.js 16+**
- **ExHentai/E-Hentai 账户** (用于 ExHentai 同步)
- **JM 账户** (用于 18comic 同步)

### 后端设置
```bash
cd app
pip install -r requirements.txt
python main.py
```
后端将运行在 `http://localhost:5001`

### 前端设置
```bash
cd web
npm install
npm run dev
```
前端将运行在 `http://localhost:5173`

### 配置设置
1. 访问 `http://localhost:5173/settings`
2. 配置您的 ExHentai cookies 和/或 JM 凭证
3. 测试连接并保存设置
4. 开始同步您的收藏！

## ⚙️ 配置说明

### ExHentai 设置
- **Base URL**: 选择 ExHentai（需要账户）或 E-Hentai（公开）
- **Member ID**: 从 cookies 中获取的 ExHentai 会员 ID
- **Pass Hash**: 从 cookies 中获取的 ExHentai pass hash
- **Igneous**: Igneous cookie（可选，用于增强访问）

### JM (18comic) 设置
- **用户名**: 您的 JM 账户用户名
- **密码**: 您的 JM 账户密码
- **App 版本**: JM app 版本（默认：1.8.0）
- **API 端点**: 多个 API 基础 URL 以确保冗余

## 📁 数据存储

```
app/data/
├── exhentai_favs_metadata.json    # ExHentai 画廊数据
├── jm_favs_metadata.json          # JM 画廊数据
├── db.text.json                   # 标签翻译数据库
├── ex_backup_favs/                # ExHentai 备份
└── jm_backup_favs/                # JM 备份
```

## 🔧 开发说明

### 项目结构
```
SelfHentai/
├── app/                    # FastAPI 后端
│   ├── api/               # API 路由
│   ├── core/              # 核心配置
│   ├── services/          # 业务逻辑
│   ├── utils/             # 工具函数
│   └── main.py           # 应用程序入口点
├── web/                   # Vue 3 前端
│   ├── src/
│   │   ├── components/    # Vue 组件
│   │   ├── assets/        # CSS 和静态资源
│   │   ├── composables/   # Vue 组合式函数
│   │   └── router/        # Vue Router 配置
│   └── package.json
└── README.md
```

### 核心技术
- **后端**: FastAPI, Python asyncio, WebSocket
- **前端**: Vue 3, TypeScript, Vite, PrimeVue
- **数据**: JSON 文件存储与自动备份
- **同步**: 多线程并发处理
- **UI**: 响应式设计与主题支持

## 🌟 界面展示

应用程序功能包括：
- **画廊浏览器**: 清洁有序的漫画收藏视图
- **详情视图**: 包含标签、评分和种子的全面信息
- **统计仪表盘**: 收藏的可视化分析
- **同步界面**: 终端风格输出的实时进度跟踪
- **设置面板**: 简单的配置管理

## 🤝 贡献

欢迎贡献！请随时提交问题和功能请求。

## 📄 许可证

本项目仅供个人使用。请遵守 ExHentai 和 JM 平台的服务条款。

---

⚠️ **免责声明**: 此工具仅用于个人收藏管理。用户有责任遵守 ExHentai 和 JM 平台的服务条款。