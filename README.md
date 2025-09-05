# SelfHentai

[中文版 README](./README_CN.md) | English

📚 **SelfHentai**: A self-hosted manga collection manager for ExHentai and JM (18comic) platforms with advanced OCR and AI translation capabilities.

---

## ✨ Features

### 📚 Collection Management
- 🖼️ **Browse & Search**: View your manga collection with titles, tags, categories, ratings, and more
- 🔍 **Advanced Filtering**: Keyword search, category filtering, and paginated browsing
- 🔁 **One-Click Sync**: Automatically sync your ExHentai and JM favorites with metadata backup
- 🏷️ **Tag Translation**: Support for Chinese/English tag recognition and translation
- 📊 **Statistics**: Comprehensive analytics with charts and quarterly reports

### 🖼️ Image Viewing & Translation
- 📷 **Smart Screenshot**: Interactive image area selection with real-time preview
- 👁️ **OCR Recognition**: manga-ocr powered Japanese text recognition with Apple Silicon optimization
- 🌐 **AI Translation**: Professional Japanese-to-Chinese translation via Volcano Engine API
- 🔍 **Full-Image Viewer**: High-quality image viewing with pagination controls
- 👶 **Mom Mode**: Configurable blur effects for sensitive content (20px default)

### 🎨 User Experience
- 🎨 **Dual Theme**: Dark and light mode support with smooth transitions
- ⚙️ **Web Configuration**: Easy setup of ExHentai/JM credentials through web interface
- 🔄 **Real-time Updates**: WebSocket-powered live sync progress tracking
- 📱 **Responsive Design**: Mobile-friendly interface with touch support

## 🏗️ Architecture

### Backend (FastAPI)
- **Python FastAPI** with async/await support
- **Dual Provider Support**: ExHentai and JM (18comic) integration
- **OCR Service**: manga-ocr integration with CPU fallback for Apple Silicon
- **AI Translation**: Volcano Engine API integration with professional prompts
- **Real-time Communication**: WebSocket for live updates
- **Auto Backup**: Automatic metadata backup before sync operations
- **Thread-safe Sync**: Concurrent processing with proper locking

### Frontend (Vue 3 + TypeScript)
- **Vue 3** with Composition API and TypeScript
- **PrimeVue** UI components with custom styling  
- **Chart.js** for data visualization
- **Canvas API**: Interactive screenshot selection and image processing
- **Responsive Design**: Mobile-friendly interface
- **Theme System**: Global dark/light mode switching with CSS variables

## 🚀 Quick Start

### Prerequisites
- **Python 3.8+**
- **Node.js 16+**
- **ExHentai/E-Hentai account** (for ExHentai sync)
- **JM account** (for 18comic sync)
- **Volcano Engine API Key** (for AI translation, optional)

### Backend Setup
```bash
cd app
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your configuration
python main.py
```
The backend will run on `http://localhost:5001`

### Frontend Setup
```bash
cd web
npm install
cp .env.example .env
# Edit .env if needed (optional)
npm run dev
```
The frontend will run on `http://localhost:5173`

### Configuration
1. Visit `http://localhost:5173/settings` 
2. Configure your ExHentai cookies and/or JM credentials
3. Test the connection and save your settings
4. Start syncing your favorites!

## ⚙️ Configuration

### Environment Variables

#### Backend (.env)
```bash
# ExHentai Configuration
EXHENTAI_COOKIE_MEMBER_ID=your_member_id
EXHENTAI_COOKIE_PASS_HASH=your_pass_hash
EXHENTAI_COOKIE_IGNEOUS=your_igneous

# JM Configuration  
JM_USERNAME=your_username
JM_PASSWORD=your_password

# AI Translation (Optional)
ARK_API_KEY=your_volcano_api_key

# Server
PORT=5001
```

#### Frontend (.env)
```bash
# API Configuration
VITE_API_BASE=http://localhost:5001
VITE_WS_BASE=ws://localhost:5001

# Mom Mode Blur Effect
VITE_MOM_MODE_BLUR=20px
```

### Platform Setup
#### ExHentai Setup
- **Base URL**: Choose between ExHentai (requires account) or E-Hentai (public)
- **Member ID**: Your ExHentai member ID from cookies
- **Pass Hash**: Your ExHentai pass hash from cookies  
- **Igneous**: Your igneous cookie (optional, for enhanced access)

#### JM (18comic) Setup
- **Username**: Your JM account username
- **Password**: Your JM account password
- **App Version**: JM app version (default: 1.8.0)
- **API Endpoints**: Multiple API base URLs for redundancy

## 🔧 OCR & Translation Setup

### manga-ocr Installation
```bash
# Install manga-ocr
pip install manga-ocr

# For Apple Silicon users (if facing MPS issues)
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
```

### Volcano Engine API
1. Sign up at [Volcano Engine](https://console.volcengine.com/)
2. Create an API key for translation services
3. Add your API key to `.env` as `ARK_API_KEY`

## 📁 Data Storage

```
app/data/
├── exhentai_favs_metadata.json    # ExHentai gallery data
├── jm_favs_metadata.json          # JM gallery data
├── db.text.json                   # Tag translation database
├── ex_backup_favs/                # ExHentai backups
└── jm_backup_favs/                # JM backups

app/logs/
└── app.log                        # Application logs
```

## 🎯 Key Features Deep Dive

### OCR & Translation Workflow
1. **Screenshot**: Select any area of a manga page with interactive selection box
2. **OCR**: manga-ocr automatically recognizes Japanese text with high accuracy
3. **Translation**: Professional AI translation optimized for manga content
4. **Results**: Edit OCR results if needed, copy translations instantly

### Mom Mode (Content Safety)
- Configurable blur effects (5px-25px) for sensitive content
- Environment variable control: `VITE_MOM_MODE_BLUR`
- Hover-to-reveal functionality
- Separate settings for different image types

### Statistics & Analytics
- Collection growth over time
- Top tags and categories
- Reading patterns and preferences
- Quarterly activity reports
- Visual charts with Chart.js

## 🔧 Development

### Project Structure
```
SelfHentai/
├── app/                    # FastAPI backend
│   ├── api/               # API routes (gallery, settings, OCR, translation)
│   ├── core/              # Core configurations and logging
│   ├── services/          # Business logic (sync, OCR, translation)
│   ├── utils/             # Utility functions (ExHentai, WebSocket)
│   └── main.py           # Application entry point
├── web/                   # Vue 3 frontend
│   ├── src/
│   │   ├── components/    # Vue components (ImageViewer, Gallery, etc.)
│   │   ├── assets/        # CSS and static assets
│   │   ├── composables/   # Vue composables (theme, etc.)
│   │   └── router/        # Vue Router configuration
│   └── package.json
└── README.md
```

### Key Technologies
- **Backend**: FastAPI, Python asyncio, WebSocket, manga-ocr, Volcano Engine API
- **Frontend**: Vue 3, TypeScript, Vite, PrimeVue, Canvas API
- **Data**: JSON file storage with automatic backup
- **Sync**: Multi-threaded concurrent processing with real-time progress
- **UI**: Responsive design with theme support and accessibility features

### Development Commands
```bash
# Backend development
cd app && python main.py

# Frontend development  
cd web && npm run dev

# Build for production
cd web && npm run build
```

## 🌟 Screenshots & Usage

The application features:
- **Gallery Browser**: Clean, organized view of your manga collection
- **Image Viewer**: Full-screen viewing with OCR and translation tools
- **Screenshot Tool**: Interactive area selection with real-time preview
- **Translation Interface**: Professional manga text translation workflow
- **Statistics Dashboard**: Visual analytics of your collection
- **Sync Interface**: Real-time progress tracking with terminal-style output
- **Settings Panel**: Easy configuration management for all platforms