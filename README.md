# SelfHentai

[中文版 README](./README_CN.md) | English

📚 **SelfHentai**: A self-hosted manga collection manager for ExHentai and JM (18comic) platforms.

---

## ✨ Features

- 🖼️ **Browse & Search**: View your manga collection with titles, tags, categories, ratings, and more
- 🔍 **Advanced Filtering**: Keyword search, category filtering, and paginated browsing
- 🔁 **One-Click Sync**: Automatically sync your ExHentai and JM favorites with metadata backup
- 🏷️ **Tag Translation**: Support for Chinese/English tag recognition and translation
- 📊 **Statistics**: Comprehensive analytics with charts and quarterly reports
- 🎨 **Dual Theme**: Dark and light mode support with smooth transitions
- ⚙️ **Web Configuration**: Easy setup of ExHentai/JM credentials through web interface
- 🔄 **Real-time Updates**: WebSocket-powered live sync progress tracking

## 🏗️ Architecture

### Backend (FastAPI)
- **Python FastAPI** with async/await support
- **Dual Provider Support**: ExHentai and JM (18comic) integration
- **Real-time Communication**: WebSocket for live updates
- **Auto Backup**: Automatic metadata backup before sync operations
- **Thread-safe Sync**: Concurrent processing with proper locking

### Frontend (Vue 3 + TypeScript)
- **Vue 3** with Composition API and TypeScript
- **PrimeVue** UI components with custom styling  
- **Chart.js** for data visualization
- **Responsive Design**: Mobile-friendly interface
- **Theme System**: Global dark/light mode switching

## 🚀 Quick Start

### Prerequisites
- **Python 3.8+**
- **Node.js 16+**
- **ExHentai/E-Hentai account** (for ExHentai sync)
- **JM account** (for 18comic sync)

### Backend Setup
```bash
cd app
pip install -r requirements.txt
python main.py
```
The backend will run on `http://localhost:5001`

### Frontend Setup
```bash
cd web
npm install
npm run dev
```
The frontend will run on `http://localhost:5173`

### Configuration
1. Visit `http://localhost:5173/settings` 
2. Configure your ExHentai cookies and/or JM credentials
3. Test the connection and save your settings
4. Start syncing your favorites!

## ⚙️ Configuration

### ExHentai Setup
- **Base URL**: Choose between ExHentai (requires account) or E-Hentai (public)
- **Member ID**: Your ExHentai member ID from cookies
- **Pass Hash**: Your ExHentai pass hash from cookies  
- **Igneous**: Your igneous cookie (optional, for enhanced access)

### JM (18comic) Setup
- **Username**: Your JM account username
- **Password**: Your JM account password
- **App Version**: JM app version (default: 1.8.0)
- **API Endpoints**: Multiple API base URLs for redundancy

## 📁 Data Storage

```
app/data/
├── exhentai_favs_metadata.json    # ExHentai gallery data
├── jm_favs_metadata.json          # JM gallery data
├── db.text.json                   # Tag translation database
├── ex_backup_favs/                # ExHentai backups
└── jm_backup_favs/                # JM backups
```

## 🔧 Development

### Project Structure
```
SelfHentai/
├── app/                    # FastAPI backend
│   ├── api/               # API routes
│   ├── core/              # Core configurations
│   ├── services/          # Business logic
│   ├── utils/             # Utility functions
│   └── main.py           # Application entry point
├── web/                   # Vue 3 frontend
│   ├── src/
│   │   ├── components/    # Vue components
│   │   ├── assets/        # CSS and static assets
│   │   ├── composables/   # Vue composables
│   │   └── router/        # Vue Router configuration
│   └── package.json
└── README.md
```

### Key Technologies
- **Backend**: FastAPI, Python asyncio, WebSocket
- **Frontend**: Vue 3, TypeScript, Vite, PrimeVue
- **Data**: JSON file storage with automatic backup
- **Sync**: Multi-threaded concurrent processing
- **UI**: Responsive design with theme support

## 🌟 Screenshots

The application features:
- **Gallery Browser**: Clean, organized view of your manga collection
- **Detail View**: Comprehensive information including tags, ratings, and torrents
- **Statistics Dashboard**: Visual analytics of your collection
- **Sync Interface**: Real-time progress tracking with terminal-style output
- **Settings Panel**: Easy configuration management

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues and enhancement requests.

## 📄 License

This project is for personal use. Please respect the terms of service of ExHentai and JM platforms.

---

⚠️ **Disclaimer**: This tool is designed for personal collection management only. Users are responsible for complying with the terms of service of ExHentai and JM platforms.