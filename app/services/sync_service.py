# app/services/sync_service.py

import json
import os
import shutil
import time
import base64
import itertools
import concurrent.futures
import threading
from hashlib import md5
from typing import Any, Dict, List

import requests
from Crypto.Cipher import AES
from requests.adapters import HTTPAdapter

from core.config import settings
from core.logger import get_logger
from services.ex_gallery_service import load_ex_gallery_data
from services.jm_gallery_service import load_jm_gallery_data
from utils.exhentai_utils import ExHentaiUtils
from utils.websocket_logger import WebSocketLogHandler

logger = get_logger(__name__)

# JM API 常量
APP_TOKEN_SECRET = "18comicAPP"
APP_DATA_SECRET = "185Hcomic3PAPP7R"

HEADERS = {
    "User-Agent": "okhttp/3.12.1",
    "Accept-Encoding": "gzip",
}

# requests 会话 & 连接池
SESSION = requests.Session()
ADAPTER = HTTPAdapter(pool_connections=100, pool_maxsize=100, max_retries=0)
SESSION.mount("http://", ADAPTER)
SESSION.mount("https://", ADAPTER)

API_BASE = None
LOGIN_LOCK = threading.Lock()


def backup_json_file(target_file, backup_dir, keep_count=5, prefix="backup"):
    """将目标文件备份到指定目录，并保留最近 keep_count 个备份"""
    os.makedirs(backup_dir, exist_ok=True)
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    backup_file = os.path.join(backup_dir, f"{prefix}_{timestamp}.json")

    if os.path.exists(target_file):
        shutil.copy2(target_file, backup_file)

    # 清理旧备份文件（只清理相同前缀的文件）
    backups = sorted(
        [f for f in os.listdir(backup_dir) if f.startswith(f"{prefix}_") and f.endswith(".json")],
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
            backup_dir=settings.EX_BACKUP_PATH,
            keep_count=settings.BACKUP_HISTORY_COUNT,
            prefix="ex_backup",
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


# JM 同步功能
def md5hex(data: str) -> str:
    return md5(data.encode("utf-8")).hexdigest()


def get_token_and_param(ts: int):
    tokenparam = f"{ts},{settings.JM_APP_VERSION}"
    token = md5hex(f"{ts}{APP_TOKEN_SECRET}")
    return token, tokenparam


def decode_resp_data(data: str, ts: int):
    key = md5hex(f"{ts}{APP_DATA_SECRET}").encode("utf-8")
    raw = base64.b64decode(data)
    aes = AES.new(key, AES.MODE_ECB)
    decrypted = aes.decrypt(raw)
    decrypted = decrypted[: -decrypted[-1]]
    text = decrypted.decode("utf-8", errors="ignore").strip()
    return json.loads(text)


def try_api_base():
    global API_BASE
    ts = int(time.time())
    token, tokenparam = get_token_and_param(ts)
    headers = HEADERS.copy()
    headers.update({"token": token, "tokenparam": tokenparam})
    
    api_bases = settings.JM_API_BASES.split(',') if settings.JM_API_BASES else []
    
    for base in api_bases:
        try:
            url = f"{base.strip()}/app/version"
            resp = SESSION.get(url, headers=headers, timeout=5)
            if resp.status_code == 200:
                API_BASE = base.strip()
                logger.info(f"使用 API 域名: {API_BASE}")
                return
        except Exception:
            pass
    raise RuntimeError("所有 API 域名都不可用")


def api_request_with_failover(method, path, *, params=None, data=None, max_retries=None):
    if max_retries is None:
        max_retries = settings.JM_SYNC_RETRIES
    
    last_exc = None
    api_bases = settings.JM_API_BASES.split(',') if settings.JM_API_BASES else []
    
    for _ in range(max_retries):
        ts = int(time.time())
        token, tokenparam = get_token_and_param(ts)
        headers = HEADERS.copy()
        headers.update({"token": token, "tokenparam": tokenparam})

        for base in itertools.chain([API_BASE], api_bases):
            if not base:
                continue
            base = base.strip()
            try:
                url = f"{base}{path}"
                if method.upper() == "GET":
                    resp = SESSION.get(url, headers=headers, params=params, timeout=10)
                else:
                    resp = SESSION.post(url, headers=headers, data=data, timeout=10)

                if resp.status_code == 401:
                    logger.warning(f"401 未授权: {url}，重新登录...")
                    jm_login(settings.JM_USERNAME, settings.JM_PASSWORD)
                    continue

                resp.raise_for_status()
                raw_json = resp.json()
                return decode_resp_data(raw_json["data"], ts)
            except Exception as e:
                logger.warning(f"请求失败({base}): {e}")
                last_exc = e
        time.sleep(1)
    raise last_exc


def jm_api_get(path, params=None):
    return api_request_with_failover("GET", path, params=params)


def jm_api_post(path, data=None):
    return api_request_with_failover("POST", path, data=data)


def jm_login(username, password):
    with LOGIN_LOCK:
        logger.info("正在登录 JM...")
        resp = jm_api_post("/login", {"username": username, "password": password})
        if "s" not in resp:
            raise RuntimeError("JM 登录失败")
        SESSION.cookies.set("AVS", resp["s"])
        logger.info(f"JM 登录成功: {resp.get('username')}")


def get_jm_favorites_all():
    all_albums = []
    page = 1
    while True:
        for retry in range(5):
            try:
                logger.info(f"获取 JM 收藏夹第 {page} 页...")
                fav_page = jm_api_get("/favorite", {"page": page})
                items = fav_page.get("list", [])
                total = int(fav_page.get("total", 0) or 0)
                per_page = int(fav_page.get("count", 0) or 0)

                if not items:
                    return all_albums

                all_albums.extend(items)
                if per_page == 0 or len(items) < per_page or len(all_albums) >= total:
                    return all_albums

                page += 1
                break
            except Exception as e:
                logger.warning(f"第 {page} 页失败({retry+1}/5): {e}")
                time.sleep(1)
        else:
            break
    return all_albums


def get_jm_album_info(album_id: str) -> Dict[str, Any]:
    return jm_api_get("/album", {"id": album_id})


def enrich_jm_favorites_concurrent(
    favs: List[Dict[str, Any]],
    *,
    max_workers: int = None,
    per_request_retries: int = None,
    save_every: int = None,
    save_path: str = None,
) -> List[Dict[str, Any]]:
    if max_workers is None:
        max_workers = settings.JM_MAX_WORKERS
    if per_request_retries is None:
        per_request_retries = settings.JM_SYNC_RETRIES
    if save_every is None:
        save_every = settings.JM_SAVE_EVERY
    if save_path is None:
        save_path = settings.JM_GALLERY_DATA_PATH
    
    total = len(favs)
    enriched: List[Dict[str, Any]] = [None] * total
    done_counter = 0
    counter_lock = threading.Lock()

    def fetch_one(idx: int, item: Dict[str, Any]) -> Dict[str, Any]:
        aid = str(item.get("id"))
        last_exc = None
        for attempt in range(1, per_request_retries + 1):
            try:
                detail = get_jm_album_info(aid)
                extra = {
                    "addtime": detail.get("addtime"),
                    "total_views": detail.get("total_views"),
                    "likes": detail.get("likes"),
                    "comment_total": detail.get("comment_total"),
                    "tags": detail.get("tags", []),
                }
                merged = dict(item)
                merged.update(extra)
                return merged
            except Exception as e:
                last_exc = e
                time.sleep(0.3 * attempt)
        logger.warning(f"获取详情失败 id={aid}: {last_exc}")
        return dict(item)

    def on_result(fut, i):
        nonlocal done_counter
        try:
            res = fut.result()
        finally:
            with counter_lock:
                done_counter += 1
                if done_counter % save_every == 0 or done_counter == total:
                    partial = [x for x in enriched if x is not None]
                    with open(save_path, "w", encoding="utf-8") as f:
                        json.dump(partial, f, ensure_ascii=False, indent=2)
                    logger.info(f"进度 {done_counter}/{total}，已保存 {len(partial)} 条")

    logger.info(f"并发补充 JM 详情：{total} 条，线程数={max_workers}")
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = []
        for idx, item in enumerate(favs):
            fut = ex.submit(fetch_one, idx, item)
            futures.append((idx, fut))
        for idx, fut in futures:
            fut.add_done_callback(lambda f, i=idx: on_result(f, i))
        for idx, fut in futures:
            try:
                enriched[idx] = fut.result()
            except Exception as e:
                logger.warning(f"任务异常 idx={idx}: {e}")
                enriched[idx] = favs[idx]
    return enriched


def sync_jm_favorites():
    from main import main_event_loop

    """执行 JM 收藏夹数据同步流程，并通过 WebSocket 实时发送日志"""
    logger = get_logger("sync_jm_metadata")

    # 添加 WebSocket 日志 handler
    ws_handler = WebSocketLogHandler(loop=main_event_loop)
    ws_handler.setFormatter(logger.handlers[0].formatter)
    logger.addHandler(ws_handler)

    try:
        logger.info("开始 JM 同步任务")

        # 尝试找到可用的 API 域名
        try_api_base()

        # 登录
        jm_login(settings.JM_USERNAME, settings.JM_PASSWORD)

        # 获取收藏夹数据
        favorites = get_jm_favorites_all()
        logger.info(f"获取到 JM 基础数据，共 {len(favorites)} 条")

        # 备份旧文件
        backup_json_file(
            settings.JM_GALLERY_DATA_PATH,
            backup_dir=settings.JM_BACKUP_PATH,
            keep_count=settings.BACKUP_HISTORY_COUNT,
            prefix="jm_backup",
        )

        # 并发补充详情信息
        enriched = enrich_jm_favorites_concurrent(favorites)

        # 保存最终数据
        with open(settings.JM_GALLERY_DATA_PATH, "w", encoding="utf-8") as f:
            json.dump(enriched, f, ensure_ascii=False, indent=2)

        # 重新加载图库数据
        load_jm_gallery_data(force_reload=True)

        logger.info(f"JM 同步完成，共 {len(enriched)} 项")
        return {"status": "success", "count": len(enriched)}

    finally:
        # 清理 WebSocket handler，防止重复添加
        logger.removeHandler(ws_handler)
