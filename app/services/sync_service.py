# app/services/sync_service.py
import os, json, shutil, time
from core.config import settings
from utils.exhentai_utils import ExHentaiUtils
from services.gallery_service import load_gallery_data

def backup_json_file(target_file, backup_dir, keep_count=5):
    os.makedirs(backup_dir, exist_ok=True)
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    backup_file = os.path.join(backup_dir, f"backup_{timestamp}.json")

    if os.path.exists(target_file):
        shutil.copy2(target_file, backup_file)

    # 删除旧备份
    backups = sorted(
        [f for f in os.listdir(backup_dir) if f.endswith(".json")],
        key=lambda x: os.path.getmtime(os.path.join(backup_dir, x)),
        reverse=True
    )
    for old_file in backups[keep_count:]:
        os.remove(os.path.join(backup_dir, old_file))


def sync_favorites():
    cookies = {
        "ipb_member_id": settings.EXHENTAI_COOKIE_MEMBER_ID,
        "ipb_pass_hash": settings.EXHENTAI_COOKIE_PASS_HASH,
        "igneous": settings.EXHENTAI_COOKIE_IGNEOUS,
    }

    client = ExHentaiUtils(settings.EXHENTAI_BASE_URL, cookies)
    data = client.get_favorites_metadata()

    # 备份旧文件
    backup_json_file(settings.GALLERY_DATA_PATH, backup_dir=settings.GALLERY_BACKUP_PATH, keep_count=settings.BACKUP_HISTORY_COUNT)

    # 写入新文件
    with open(settings.GALLERY_DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # 重新加载数据
    load_gallery_data(force_reload=True)

    return {"status": "success", "count": len(data)}
