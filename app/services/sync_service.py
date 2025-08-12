# app/services/ex_sync_service.py

import json
import os
import shutil
import time

from core.config import settings
from core.logger import get_logger
from services.ex_gallery_service import load_ex_gallery_data
from utils.exhentai_utils import ExHentaiUtils
from utils.websocket_logger import WebSocketLogHandler

logger = get_logger(__name__)


def backup_json_file(target_file, backup_dir, keep_count=5):
    """将目标文件备份到指定目录，并保留最近 keep_count 个备份"""
    os.makedirs(backup_dir, exist_ok=True)
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    backup_file = os.path.join(backup_dir, f"backup_{timestamp}.json")

    if os.path.exists(target_file):
        shutil.copy2(target_file, backup_file)

    # 清理旧备份文件
    backups = sorted(
        [f for f in os.listdir(backup_dir) if f.endswith(".json")],
        key=lambda x: os.path.getmtime(os.path.join(backup_dir, x)),
        reverse=True,
    )
    for old_file in backups[keep_count:]:
        os.remove(os.path.join(backup_dir, old_file))


def sync_ex_favorites():
    from main import main_event_loop

    """执行收藏夹数据同步流程，并通过 WebSocket 实时发送日志"""
    logger = get_logger("sync_metadata")

    # 添加 WebSocket 日志 handler
    ws_handler = WebSocketLogHandler(loop=main_event_loop)
    ws_handler.setFormatter(logger.handlers[0].formatter)
    logger.addHandler(ws_handler)

    try:
        logger.info("开始同步任务")

        # 构建 Cookie 参数
        cookies = {
            "ipb_member_id": settings.EXHENTAI_COOKIE_MEMBER_ID,
            "ipb_pass_hash": settings.EXHENTAI_COOKIE_PASS_HASH,
            "igneous": settings.EXHENTAI_COOKIE_IGNEOUS,
        }

        # 初始化工具类并抓取元数据
        client = ExHentaiUtils(settings.EXHENTAI_BASE_URL, cookies, logger=logger)
        data = client.get_favorites_metadata()

        # 备份旧文件
        backup_json_file(
            settings.GALLERY_DATA_PATH,
            backup_dir=settings.GALLERY_BACKUP_PATH,
            keep_count=settings.BACKUP_HISTORY_COUNT,
        )

        # 保存新数据
        with open(settings.GALLERY_DATA_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        # 重新加载图库数据
        load_ex_gallery_data(force_reload=True)

        logger.info(f"同步完成，共 {len(data)} 项")
        return {"status": "success", "count": len(data)}

    finally:
        # 清理 WebSocket handler，防止重复添加
        logger.removeHandler(ws_handler)
