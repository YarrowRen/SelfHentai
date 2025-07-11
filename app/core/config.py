# app/core/config.py

import os

from dotenv import load_dotenv

load_dotenv()  # 加载 .env 文件


class Settings:
    GALLERY_DATA_PATH = os.getenv(
        "GALLERY_DATA_PATH", "data/exhentai_favs_metadata.json"
    )
    TAG_TRANSLATE_PATH = os.getenv("TAG_TRANSLATE_PATH", "data/db.text.json")
    GALLERY_BACKUP_PATH = os.getenv("GALLERY_BACKUP_PATH")
    EXHENTAI_BASE_URL = os.getenv("EXHENTAI_BASE_URL")
    EXHENTAI_COOKIE_MEMBER_ID = os.getenv("EXHENTAI_COOKIE_MEMBER_ID")
    EXHENTAI_COOKIE_PASS_HASH = os.getenv("EXHENTAI_COOKIE_PASS_HASH")
    EXHENTAI_COOKIE_IGNEOUS = os.getenv("EXHENTAI_COOKIE_IGNEOUS")
    BACKUP_HISTORY_COUNT = int(os.getenv("BACKUP_HISTORY_COUNT"))
    PORT = int(os.getenv("PORT", 5001))


settings = Settings()
