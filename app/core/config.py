# app/core/config.py

import os

from dotenv import load_dotenv

load_dotenv()  # 加载 .env 文件


class Settings:
    GALLERY_DATA_PATH = os.getenv("GALLERY_DATA_PATH", "data/exhentai_favs_metadata.json")
    TAG_TRANSLATE_PATH = os.getenv("TAG_TRANSLATE_PATH", "data/db.text.json")
    GALLERY_BACKUP_PATH = os.getenv("GALLERY_BACKUP_PATH")
    EXHENTAI_BASE_URL = os.getenv("EXHENTAI_BASE_URL")
    EXHENTAI_COOKIE_MEMBER_ID = os.getenv("EXHENTAI_COOKIE_MEMBER_ID")
    EXHENTAI_COOKIE_PASS_HASH = os.getenv("EXHENTAI_COOKIE_PASS_HASH")
    EXHENTAI_COOKIE_IGNEOUS = os.getenv("EXHENTAI_COOKIE_IGNEOUS")
    TRANSLATE_LATEST_URL = os.getenv("TRANSLATE_LATEST_URL")
    JM_GALLERY_DATA_PATH = os.getenv("JM_GALLERY_DATA_PATH", "data/jm_favs_metadata_enriched.json")
    JM_COVER_URL_TEMPLATE = os.getenv("JM_COVER_URL_TEMPLATE", "https://cdn-msp.18comic.vip/media/albums/{id}_3x4.jpg")
    LOG_DIR = os.getenv("LOG_DIR", "logs")
    LOG_FILE = os.getenv("LOG_FILE", "app.log")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    BACKUP_HISTORY_COUNT = int(os.getenv("BACKUP_HISTORY_COUNT"))
    PORT = int(os.getenv("PORT", 5001))


settings = Settings()
