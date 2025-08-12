# app/services/jm_gallery_service.py

import copy
import json
import os
from collections import Counter, defaultdict
from datetime import datetime
from typing import List, Optional, Union

from core.config import settings
from core.logger import get_logger

logger = get_logger(__name__)

# 全局缓存变量（初始为空）
jm_gallery_data: List[dict] = []


def _safe_int(val, default: int = 0) -> int:
    try:
        if val is None:
            return default
        return int(val)
    except (ValueError, TypeError):
        return default


def _safe_float(val, default: float = 0.0) -> float:
    try:
        if val is None:
            return default
        return float(val)
    except (ValueError, TypeError):
        return default


def _normalize_item(item: dict) -> dict:
    """
    规整化单条 JM 数据的字段类型，方便后续排序和统计：
      - id -> str
      - addtime -> int (epoch, 秒)
      - total_views/likes/comment_total -> int
      - latest_ep/latest_ep_aid -> Optional[str]
    """
    normalized = dict(item)

    # id 统一为 str
    if "id" in normalized and normalized["id"] is not None:
        normalized["id"] = str(normalized["id"])

    # 时间与计数
    normalized["addtime"] = _safe_int(normalized.get("addtime"), 0)
    normalized["total_views"] = _safe_int(normalized.get("total_views"), 0)
    normalized["likes"] = _safe_int(normalized.get("likes"), 0)
    normalized["comment_total"] = _safe_int(normalized.get("comment_total"), 0)

    # 章节 id 允许为 None 或字符串
    if normalized.get("latest_ep") is not None:
        normalized["latest_ep"] = str(normalized.get("latest_ep"))
    if normalized.get("latest_ep_aid") is not None:
        normalized["latest_ep_aid"] = str(normalized.get("latest_ep_aid"))

    # tags 确保为 list[str]
    tags = normalized.get("tags", [])
    if not isinstance(tags, list):
        tags = []
    tags = [t for t in tags if isinstance(t, str)]
    normalized["tags"] = tags

    # category / category_sub 兜底结构
    cat = normalized.get("category") or {}
    sub = normalized.get("category_sub") or {}
    normalized["category"] = {
        "id": str(cat.get("id")) if cat.get("id") is not None else "",
        "title": str(cat.get("title")) if cat.get("title") is not None else "",
    }
    normalized["category_sub"] = {
        "id": str(sub.get("id")) if sub.get("id") is not None else "",
        "title": str(sub.get("title")) if sub.get("title") is not None else "",
    }

    # 其他文本字段兜底
    for k in ["author", "description", "name"]:
        if normalized.get(k) is None:
            normalized[k] = ""

    # 生成封面 URL
    item_id = normalized.get("id")
    if item_id:
        # 使用配置的封面 URL 模板生成封面地址
        cover_url_template = getattr(settings, "JM_COVER_URL_TEMPLATE", 
                                   "https://cdn-msp.18comic.vip/media/albums/{id}_3x4.jpg")
        normalized["image"] = cover_url_template.format(id=item_id)
    else:
        normalized["image"] = ""

    return normalized


def load_jm_gallery_data(force_reload: bool = False):
    """
    加载或重新加载 JMComic 数据。
    读取 settings.JM_GALLERY_DATA_PATH 指定的 JSON 文件。
    如果文件不存在，使用空数据并记录警告。
    """
    global jm_gallery_data

    if jm_gallery_data and not force_reload:
        return

    data_path = getattr(settings, "JM_GALLERY_DATA_PATH", None)
    if not data_path:
        logger.warning("未在 settings 中找到 JM_GALLERY_DATA_PATH，使用空数据。")
        jm_gallery_data = []
        return

    if not os.path.exists(data_path):
        logger.warning(f"找不到 JM 数据文件: {data_path}，使用空数据。")
        jm_gallery_data = []
        return

    try:
        with open(data_path, encoding="utf-8") as f:
            raw = json.load(f)
            if not isinstance(raw, list):
                logger.error("JM 数据文件内容不是列表，使用空数据。")
                jm_gallery_data = []
                return

            # 规范化与只读缓存
            jm_gallery_data = [_normalize_item(x) for x in raw]
            logger.info(f"成功加载 JM 数据，共 {len(jm_gallery_data)} 项。")
    except json.JSONDecodeError as e:
        logger.error(f"解析 JM 数据文件失败: {e}")
        jm_gallery_data = []
    except Exception as e:
        logger.error(f"读取 JM 数据文件异常: {e}")
        jm_gallery_data = []


# 模块导入时进行一次加载
load_jm_gallery_data()


def _match_keyword(item: dict, kw: str) -> bool:
    """
    关键词匹配：在 name、author、tags 中查找（不区分大小写）。
    """
    if not kw:
        return True
    kw_l = kw.lower()

    name = item.get("name", "")
    author = item.get("author", "")
    tags = item.get("tags", [])

    if isinstance(name, str) and kw_l in name.lower():
        return True
    if isinstance(author, str) and kw_l in author.lower():
        return True
    for t in tags:
        if isinstance(t, str) and kw_l in t.lower():
            return True
    return False


def _match_category(item: dict, category: Optional[str]) -> bool:
    """
    category 可传 id 或 title，匹配 item.category。
    """
    if not category:
        return True
    c = item.get("category", {})
    return category == c.get("id") or category == c.get("title")


def _match_subcategory(item: dict, subcategory: Optional[str]) -> bool:
    """
    subcategory 可传 id 或 title，匹配 item.category_sub。
    """
    if not subcategory:
        return True
    c = item.get("category_sub", {})
    return subcategory == c.get("id") or subcategory == c.get("title")


def _sort_key(sort: Optional[str]):
    """
    支持排序：
      - None / 'recent': 按 addtime 降序（默认）
      - 'views'       : 按 total_views 降序
      - 'likes'       : 按 likes 降序
    """
    s = (sort or "recent").lower()
    if s == "views":
        return lambda x: (-_safe_int(x.get("total_views"), 0), -_safe_int(x.get("addtime"), 0))
    if s == "likes":
        return lambda x: (-_safe_int(x.get("likes"), 0), -_safe_int(x.get("addtime"), 0))
    # recent
    return lambda x: (-_safe_int(x.get("addtime"), 0), -_safe_int(x.get("total_views"), 0))


def get_jm_gallery_data(
    page: int = 1,
    per_page: int = 20,
    keyword: Optional[str] = None,
    category: Optional[str] = None,
    subcategory: Optional[str] = None,
    sort: Optional[str] = "recent",
):
    """
    分页查询 JM 数据。
    - keyword: 在 name / author / tags 中模糊匹配
    - category: 传 category.title 或 category.id
    - subcategory: 传 category_sub.title 或 category_sub.id
    - sort: recent(默认) / views / likes
    """
    filtered = [
        item
        for item in jm_gallery_data
        if _match_keyword(item, keyword or "") and _match_category(item, category) and _match_subcategory(item, subcategory)
    ]

    # 排序
    key_fn = _sort_key(sort)
    filtered.sort(key=key_fn)

    total = len(filtered)
    page = max(1, int(page))
    per_page = max(1, int(per_page))
    start, end = (page - 1) * per_page, (page - 1) * per_page + per_page

    results = []
    for item in filtered[start:end]:
        # 保持只读深拷贝，避免外部误改缓存
        item_copy = copy.deepcopy(item)
        results.append(item_copy)

    return {"page": page, "per_page": per_page, "total": total, "results": results}


def get_jm_gallery_data_by_id(id_: Union[str, int]):
    """
    根据 id（str 或 int）获取单条 JM 数据。
    """
    if id_ is None:
        return None
    target = str(id_)
    for item in jm_gallery_data:
        if str(item.get("id")) == target:
            return copy.deepcopy(item)
    return None


def get_jm_gallery_stats():
    """
    统计：
      - 总数量 total
      - 各主分类计数 categories: {title: count}
      - 各子分类计数 subcategories: {title: count}
    """
    total_count = len(jm_gallery_data)
    cat_counts = defaultdict(int)
    subcat_counts = defaultdict(int)

    for item in jm_gallery_data:
        cat = item.get("category", {})
        sub = item.get("category_sub", {})
        cat_title = cat.get("title") or ""
        sub_title = sub.get("title") or ""
        if cat_title:
            cat_counts[cat_title] += 1
        if sub_title:
            subcat_counts[sub_title] += 1

    # 转普通 dict，保证可 JSON 化
    return {
        "total": total_count,
        "categories": dict(cat_counts),
        "subcategories": dict(subcat_counts),
    }


def get_jm_quarterly_stats():
    """
    按季度统计（UTC）：
    返回格式：{"data": [{"quarter": "2024-Q3", "count": 123}, ...]}
    以 addtime(epoch 秒) 为准。
    """
    stats = defaultdict(int)

    for item in jm_gallery_data:
        ts = _safe_int(item.get("addtime"), 0)
        if ts <= 0:
            continue
        dt = datetime.utcfromtimestamp(ts)
        quarter = (dt.month - 1) // 3 + 1
        key = f"{dt.year}-Q{quarter}"
        stats[key] += 1

    return {"data": [{"quarter": k, "count": v} for k, v in sorted(stats.items())]}


def get_jm_top_tags(n: int = 20):
    """
    统计最常见的前 n 个标签（JM 标签为普通字符串，不做翻译富化）。
    返回：
      {"top_tags": [{"tag": "巨乳", "count": 123}, ...]}
    """
    tag_counter = Counter()
    for item in jm_gallery_data:
        tags = item.get("tags", [])
        if not isinstance(tags, list):
            continue
        for tag in tags:
            if isinstance(tag, str) and tag:
                tag_counter[tag] += 1

    top_tags = tag_counter.most_common(max(1, int(n)))
    return {"top_tags": [{"tag": t, "count": c} for t, c in top_tags]}
