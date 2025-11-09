# app/core/config.py

import os

from dotenv import load_dotenv

load_dotenv()  # 加载 .env 文件


class Settings:
    GALLERY_DATA_PATH = os.getenv("GALLERY_DATA_PATH", "data/exhentai_favs_metadata.json")
    TAG_TRANSLATE_PATH = os.getenv("TAG_TRANSLATE_PATH", "data/db.text.json")
    EX_BACKUP_PATH = os.getenv("EX_BACKUP_PATH", "data/ex_backup_favs")
    JM_BACKUP_PATH = os.getenv("JM_BACKUP_PATH", "data/jm_backup_favs")
    EXHENTAI_BASE_URL = os.getenv("EXHENTAI_BASE_URL")
    EXHENTAI_COOKIE_MEMBER_ID = os.getenv("EXHENTAI_COOKIE_MEMBER_ID")
    EXHENTAI_COOKIE_PASS_HASH = os.getenv("EXHENTAI_COOKIE_PASS_HASH")
    EXHENTAI_COOKIE_IGNEOUS = os.getenv("EXHENTAI_COOKIE_IGNEOUS")
    TRANSLATE_LATEST_URL = os.getenv("TRANSLATE_LATEST_URL")
    JM_GALLERY_DATA_PATH = os.getenv("JM_GALLERY_DATA_PATH", "data/jm_favs_metadata.json")
    JM_COVER_URL_TEMPLATE = os.getenv("JM_COVER_URL_TEMPLATE", "https://cdn-msp.18comic.vip/media/albums/{id}_3x4.jpg")

    # JM 同步配置
    JM_USERNAME = os.getenv("JM_USERNAME")
    JM_PASSWORD = os.getenv("JM_PASSWORD")
    JM_APP_VERSION = os.getenv("JM_APP_VERSION", "1.8.0")
    JM_API_BASES = os.getenv(
        "JM_API_BASES",
        "https://www.cdnmhwscc.vip,https://www.cdnplaystation6.club,https://www.cdnplaystation6.org,https://www.cdnuc.vip,https://www.cdn-mspjmapiproxy.xyz",
    )
    JM_MAX_WORKERS = int(os.getenv("JM_MAX_WORKERS", "16"))
    JM_SYNC_RETRIES = int(os.getenv("JM_SYNC_RETRIES", "3"))
    JM_SAVE_EVERY = int(os.getenv("JM_SAVE_EVERY", "50"))
    
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


settings = Settings()
