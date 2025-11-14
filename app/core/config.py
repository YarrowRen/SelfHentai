# app/core/config.py

import os

from dotenv import load_dotenv

load_dotenv()  # 加载 .env 文件


class Settings:
    GALLERY_DATA_PATH = os.getenv("GALLERY_DATA_PATH", "data/exhentai_favs_metadata.json")
    TAG_TRANSLATE_PATH = os.getenv("TAG_TRANSLATE_PATH", "data/db.text.json")
    EX_BACKUP_PATH = os.getenv("EX_BACKUP_PATH", "data/ex_backup_favs")
    EXHENTAI_BASE_URL = os.getenv("EXHENTAI_BASE_URL")
    EXHENTAI_COOKIE_MEMBER_ID = os.getenv("EXHENTAI_COOKIE_MEMBER_ID")
    EXHENTAI_COOKIE_PASS_HASH = os.getenv("EXHENTAI_COOKIE_PASS_HASH")
    EXHENTAI_COOKIE_IGNEOUS = os.getenv("EXHENTAI_COOKIE_IGNEOUS")
    TRANSLATE_LATEST_URL = os.getenv("TRANSLATE_LATEST_URL")

    # ExHentai 同步配置
    EX_SYNC_RETRIES = int(os.getenv("EX_SYNC_RETRIES", "5"))
    EX_RETRY_DELAY = float(os.getenv("EX_RETRY_DELAY", "2.0"))

    LOG_DIR = os.getenv("LOG_DIR", "logs")
    LOG_FILE = os.getenv("LOG_FILE", "app.log")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    BACKUP_HISTORY_COUNT = int(os.getenv("BACKUP_HISTORY_COUNT", "5"))
    PORT = int(os.getenv("PORT", 5001))

    # AI翻译配置
    TRANSLATION_PROVIDER = os.getenv("TRANSLATION_PROVIDER", "volcano")
    TRANSLATION_BASE_URL = os.getenv("TRANSLATION_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3")
    TRANSLATION_MODEL = os.getenv("TRANSLATION_MODEL", "doubao-1-5-lite-32k-250115")
    TRANSLATION_API_KEY_ENV = os.getenv("TRANSLATION_API_KEY_ENV", "ARK_API_KEY")
    
    # 各种LLM服务商的API Key
    ARK_API_KEY = os.getenv("ARK_API_KEY")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") 
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    
    # OCR服务配置
    MANGA_OCR_ENABLED = os.getenv("MANGA_OCR_ENABLED", "false").lower() in ("true", "1", "yes", "on")
    PADDLE_OCR_ENABLED = os.getenv("PADDLE_OCR_ENABLED", "false").lower() in ("true", "1", "yes", "on")
    
    # API配置项
    DEFAULT_PAGE_SIZE = int(os.getenv("DEFAULT_PAGE_SIZE", "10"))
    MAX_PAGE_SIZE = int(os.getenv("MAX_PAGE_SIZE", "100"))
    REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))
    MAX_TOP_TAGS = int(os.getenv("MAX_TOP_TAGS", "100"))
    STREAM_CHUNK_SIZE = int(os.getenv("STREAM_CHUNK_SIZE", "8192"))
    
    # CORS配置
    ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*")


settings = Settings()
