# app/services/gallery_service.py

import copy
import json
import os
from collections import Counter, defaultdict
from datetime import datetime
from typing import List, Optional

import requests
from core.config import settings
from core.logger import get_logger

# 全局缓存变量（初始为空）
gallery_data = []
tag_translate_data = {}

logger = get_logger(__name__)


def load_gallery_data(force_reload=False):
    """
    加载或重新加载 gallery 数据。
    如果文件不存在，则使用空数据并记录警告。
    """
    global gallery_data

    if not gallery_data or force_reload:
        if not os.path.exists(settings.GALLERY_DATA_PATH):
            logger.warning(f"找不到图库数据文件: {settings.GALLERY_DATA_PATH}，使用空数据。")
            gallery_data = []
            return

        try:
            with open(settings.GALLERY_DATA_PATH, encoding="utf-8") as f:
                gallery_data = json.load(f)
                logger.info(f"成功加载图库数据，共 {len(gallery_data)} 项。")
        except json.JSONDecodeError as e:
            logger.error(f"解析图库数据文件失败: {e}")
            gallery_data = []


def load_tag_translate_data(force_reload=False):
    """
    加载或重新加载标签翻译数据。
    若本地文件不存在，则自动从 GitHub 下载。
    """
    global tag_translate_data

    if not tag_translate_data or force_reload:
        # 如果本地文件不存在，或强制 reload
        need_download = not os.path.exists(settings.TAG_TRANSLATE_PATH) or force_reload
        if need_download:
            logger.info(f"下载最新标签翻译数据：{settings.TRANSLATE_LATEST_URL}")
            try:
                os.makedirs(os.path.dirname(settings.TAG_TRANSLATE_PATH), exist_ok=True)

                resp = requests.get(settings.TRANSLATE_LATEST_URL, timeout=20)
                resp.raise_for_status()

                # 使用二进制写入并确保以 utf-8 解码（防乱码）
                with open(settings.TAG_TRANSLATE_PATH, "w", encoding="utf-8") as f:
                    json_data = resp.content.decode("utf-8")  # 明确指定 UTF-8 解码
                    f.write(json_data)

                logger.info("标签翻译数据已成功下载并保存到本地。")
            except Exception as e:
                logger.error(f"下载标签翻译数据失败: {e}")
                if not os.path.exists(settings.TAG_TRANSLATE_PATH):
                    tag_translate_data = {}
                    return

        # 加载 JSON 数据
        try:
            with open(settings.TAG_TRANSLATE_PATH, encoding="utf-8") as f:
                tag_translate_data = json.load(f)
                logger.info(f"成功加载标签翻译数据")
        except json.JSONDecodeError as e:
            logger.error(f"标签翻译数据解析失败: {e}")
            tag_translate_data = {}


# 初始加载
load_gallery_data()
load_tag_translate_data()


def enrich_tags(tags: List[str]) -> List[dict]:
    enriched_tags = []
    for tag in tags:
        if ":" not in tag:
            continue
        namespace, value = tag.split(":", 1)
        try:
            tag_detail = next(item for item in tag_translate_data["data"] if item.get("namespace") == namespace)["data"].get(
                value
            )

            if tag_detail:
                enriched_tags.append(
                    {
                        "tag": tag,
                        "namespace": namespace,
                        "value": value,
                        "tag_cn": tag_detail.get("name", ""),
                        "intro": tag_detail.get("intro", ""),
                        "links": tag_detail.get("links", ""),
                    }
                )
        except (StopIteration, KeyError):
            continue
    return enriched_tags


def get_gallery_data(page: int, per_page: int, keyword: Optional[str], type_: Optional[str]):
    filtered = gallery_data
    if keyword:
        kw = keyword.lower()
        filtered = [
            item for item in filtered if kw in item["title"].lower() or any(kw in tag.lower() for tag in item.get("tags", []))
        ]
    if type_:
        filtered = [item for item in filtered if item["category"] == type_]

    total = len(filtered)
    start, end = (page - 1) * per_page, (page - 1) * per_page + per_page

    results = []
    for item in filtered[start:end]:
        item_copy = copy.deepcopy(item)
        raw_tags = item_copy.get("tags", [])
        if isinstance(raw_tags, list) and all(isinstance(t, str) for t in raw_tags):
            item_copy["tags"] = enrich_tags(raw_tags)
        results.append(item_copy)

    return {"page": page, "per_page": per_page, "total": total, "results": results}


def get_gallery_data_by_gid(gid: int):
    for item in gallery_data:
        if item.get("gid") == gid:
            item_copy = copy.deepcopy(item)
            raw_tags = item_copy.get("tags", [])
            if isinstance(raw_tags, list) and all(isinstance(t, str) for t in raw_tags):
                item_copy["tags"] = enrich_tags(raw_tags)
            return item_copy
    return None


def get_gallery_stats():
    """
    返回图库总数量及每个固定分类的数量。
    """
    fixed_categories = [
        "Doujinshi",
        "Manga",
        "Artist CG",
        "Game CG",
        "Western",
        "Non-H",
        "Image Set",
        "Cosplay",
        "Asian Porn",
        "Misc",
    ]

    # 统计总数量
    total_count = len(gallery_data)

    # 初始化分类统计
    category_counts = {cat: 0 for cat in fixed_categories}

    # 遍历 gallery_data 分类计数
    for item in gallery_data:
        category = item.get("category")
        if category in category_counts:
            category_counts[category] += 1

    return {"total": total_count, "categories": category_counts}


def get_quarterly_stats():
    """
    统计每个季度的 gallery 数量。
    返回格式：[{ "quarter": "2022-Q1", "count": 123 }, ...]
    """
    stats = defaultdict(int)

    for item in gallery_data:
        posted_str = item.get("posted")
        if not posted_str:
            continue
        try:
            ts = int(posted_str)
            dt = datetime.utcfromtimestamp(ts)  # 使用 UTC 时间
            quarter = (dt.month - 1) // 3 + 1
            key = f"{dt.year}-Q{quarter}"
            stats[key] += 1
        except (ValueError, TypeError):
            continue

    # 返回排序后的结果
    return {"data": [{"quarter": k, "count": v} for k, v in sorted(stats.items())]}


def get_top_tags(n: int = 20, type_: Optional[str] = None):
    tag_counter = Counter()

    for item in gallery_data:
        tags = item.get("tags", [])
        if not isinstance(tags, list):
            continue
        for tag in tags:
            if not isinstance(tag, str):
                continue
            if type_:
                if not tag.startswith(f"{type_}:"):
                    continue
            tag_counter[tag] += 1

    # 获取最常见的前 n 个标签
    top_tags = tag_counter.most_common(n)

    # enrich_tags 要求传入 list[str]，返回 list[dict]
    enriched = enrich_tags([tag for tag, _ in top_tags])

    # 将计数信息合并进 enrich_tags 的结果
    count_map = dict(top_tags)
    for tag in enriched:
        tag["count"] = count_map.get(tag["tag"], 0)

    return {"top_tags": enriched}
