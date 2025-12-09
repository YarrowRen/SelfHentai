# SelfHentai

中文版 | [English README](./README.md)

📚 **SelfHentai**: 专门针对 ExHentai 平台的自托管漫画收藏管理器，集成 OCR 和 AI 翻译功能。

---

## ✨ 功能特性

### 📚 收藏管理
- 🖼️ **浏览与搜索**: 查看您的漫画收藏，包含标题、标签、分类、评分等信息
- 🔍 **高级过滤**: 关键词搜索、分类过滤和分页浏览
- 🔁 **一键同步**: 自动同步 ExHentai 收藏，支持元数据备份
- 🏷️ **标签翻译**: 支持中英文标签识别和翻译
- 📊 **数据统计**: 全面的数据分析，包含图表和季度报告

### 🖼️ 图片查看与翻译
- 📷 **智能截图**: 交互式图片区域选择，实时预览
- 👁️ **OCR 识别**: 基于 PaddleOCR 的自动文本识别
- 🌐 **AI 翻译**: 通过 API 提供专业的日中翻译
- 🔍 **全屏查看器**: 高质量图片查看，支持分页控制
- 👶 **妈妈模式**: 可配置的敏感内容模糊效果（默认 20px）

### 🎨 用户体验
- 🎨 **双主题**: 深色和浅色模式支持，平滑过渡效果
- ⚙️ **网页配置**: 通过网页界面轻松设置 ExHentai 凭据
- 🔄 **实时更新**: WebSocket 驱动的实时同步进度跟踪
- 📱 **响应式设计**: 移动端友好界面，支持触摸操作

## 🏗️ 架构

### 后端 (FastAPI)
- **Python FastAPI** 支持 async/await
- **ExHentai 平台**: 专门针对 ExHentai 平台的深度集成
- **OCR 服务**: PaddleOCR 集成，自动文本检测
- **AI 翻译**: API 集成，专业提示词
- **实时通信**: WebSocket 实时更新
- **自动备份**: 同步操作前自动元数据备份
- **线程安全**: 并发处理，适当的锁机制

### 前端 (Vue 3 + TypeScript)
- **Vue 3** 组合式 API 和 TypeScript
- **PrimeVue** UI 组件库，自定义样式
- **Chart.js** 数据可视化
- **Canvas API**: 交互式截图选择和图像处理
- **响应式设计**: 移动端友好界面
- **主题系统**: 全局深色/浅色模式切换，支持 CSS 变量

## 🚀 快速开始

### 系统要求
- **Python 3.8+**
- **Node.js 16+**
- **ExHentai/E-Hentai 账户** （用于 ExHentai 同步）
- **火山引擎 API Key** （用于 AI 翻译，可选）

### 后端设置
```bash
cd app
pip install -r requirements.txt
cp .env.example .env
# 编辑 .env 填入您的配置信息
python main.py
```
后端将运行在 `http://localhost:5001`

### 前端设置
```bash
cd web
npm install
cp .env.example .env
# 如需要可编辑 .env（可选）
npm run dev
```
前端将运行在 `http://localhost:5173`

### 配置
1. 访问 `http://localhost:5173/settings`
2. 配置您的 ExHentai cookies
3. 测试连接并保存设置
4. 开始同步您的收藏！

## ⚙️ 配置

### 环境变量

#### 后端 (.env)
```bash
# ExHentai 配置
EXHENTAI_COOKIE_MEMBER_ID=你的member_id
EXHENTAI_COOKIE_PASS_HASH=你的pass_hash
EXHENTAI_COOKIE_IGNEOUS=你的igneous

# AI 翻译（可选）
ARK_API_KEY=你的火山引擎api_key

# 服务器
PORT=5001
```

#### 前端 (.env)
```bash
# API 配置
VITE_API_BASE=http://localhost:5001
VITE_WS_BASE=ws://localhost:5001

# 妈妈模式模糊效果
VITE_MOM_MODE_BLUR=20px
```

### 平台设置
#### ExHentai 设置
- **Base URL**: 在 ExHentai（需要账户）或 E-Hentai（公共访问）之间选择
- **Member ID**: 从 cookies 获取的 ExHentai member ID
- **Pass Hash**: 从 cookies 获取的 ExHentai pass hash
- **Igneous**: igneous cookie（可选，用于增强访问）

## 🔧 OCR 与翻译设置

### PaddleOCR 安装
```bash
# 安装 PaddleOCR
pip install paddlepaddle paddleocr
```

### 火山引擎 API
1. 在 [火山引擎](https://console.volcengine.com/) 注册
2. 为翻译服务创建 API key
3. 将您的 API key 添加到 `.env` 文件的 `ARK_API_KEY`

## 📁 数据存储

```
app/data/
├── exhentai_favs_metadata.json    # ExHentai 画廊数据
├── db.text.json                   # 标签翻译数据库
└── backup_favs/                   # ExHentai 备份

app/logs/
└── app.log                        # 应用日志
```

## 🎯 核心功能深度解析

### OCR 与翻译工作流程
1. **截图**: 使用交互式选择框选择漫画页面的任意区域
2. **OCR**: PaddleOCR 自动识别文本，支持多语言
3. **翻译**: 针对漫画内容优化的专业 AI 翻译
4. **结果**: 可编辑 OCR 结果，一键复制翻译

### 妈妈模式（内容安全）
- 可配置模糊效果（5px-25px）用于敏感内容
- 环境变量控制：`VITE_MOM_MODE_BLUR`
- 悬停显示功能
- 不同图片类型的独立设置

### 统计与分析
- 收藏增长趋势
- 热门标签和分类
- 阅读模式和偏好
- 季度活动报告
- Chart.js 可视化图表

## 🔧 开发

### 项目结构
```
SelfHentai/
├── app/                    # FastAPI 后端
│   ├── api/               # API 路由 (gallery, settings, OCR, translation)
│   ├── core/              # 核心配置和日志
│   ├── services/          # 业务逻辑 (sync, OCR, translation)
│   ├── utils/             # 工具函数 (ExHentai, WebSocket)
│   └── main.py           # 应用程序入口
├── web/                   # Vue 3 前端
│   ├── src/
│   │   ├── components/    # Vue 组件 (ImageViewer, Gallery, etc.)
│   │   ├── assets/        # CSS 和静态资源
│   │   ├── composables/   # Vue 组合式函数 (theme, etc.)
│   │   └── router/        # Vue Router 配置
│   └── package.json
└── README.md
```

### 核心技术
- **后端**: FastAPI, Python asyncio, WebSocket, PaddleOCR, 火山引擎 API
- **前端**: Vue 3, TypeScript, Vite, PrimeVue, Canvas API
- **数据**: JSON 文件存储，自动备份
- **同步**: 多线程并发处理，实时进度
- **界面**: 响应式设计，主题支持，可访问性功能

### 开发命令
```bash
# 后端开发
cd app && python main.py

# 前端开发
cd web && npm run dev

# 生产构建
cd web && npm run build
```

## 🌟 界面截图与使用

应用程序功能包括：
- **画廊浏览器**: 清晰、有组织的漫画收藏视图
- **图片查看器**: 全屏查看，集成 OCR 和翻译工具
- **截图工具**: 交互式区域选择，实时预览
- **翻译界面**: 专业的漫画文本翻译工作流程
- **统计仪表板**: 收藏的可视化分析
- **同步界面**: 终端风格输出的实时进度跟踪
- **设置面板**: ExHentai 平台的简易配置管理