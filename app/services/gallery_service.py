# app/services/gallery_service.py

import copy
import json
from typing import List, Optional

from core.config import settings

# 全局缓存变量（初始为空）
gallery_data = []
tag_translate_data = {}


def load_gallery_data(force_reload=False):
    """
    加载或重新加载 gallery 数据。
    """
    global gallery_data
    if not gallery_data or force_reload:
        with open(settings.GALLERY_DATA_PATH, encoding="utf-8") as f:
            gallery_data = json.load(f)


def load_tag_translate_data(force_reload=False):
    """
    加载或重新加载标签翻译数据。
    """
    global tag_translate_data
    if not tag_translate_data or force_reload:
        with open(settings.TAG_TRANSLATE_PATH, encoding="utf-8") as f:
            tag_translate_data = json.load(f)


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
            tag_detail = next(
                item
                for item in tag_translate_data["data"]
                if item.get("namespace") == namespace
            )["data"].get(value)

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


def get_gallery_data(
    page: int, per_page: int, keyword: Optional[str], type_: Optional[str]
):
    filtered = gallery_data
    if keyword:
        kw = keyword.lower()
        filtered = [
            item
            for item in filtered
            if kw in item["title"].lower()
            or any(kw in tag.lower() for tag in item.get("tags", []))
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
