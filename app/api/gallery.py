# app/api/gallery.py

from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from services.ex_gallery_service import (
    get_ex_gallery_data,
    get_ex_gallery_data_by_gid,
    get_ex_gallery_stats,
    get_ex_quarterly_stats,
    get_ex_top_tags,
)
from services.jm_gallery_service import (
    get_jm_gallery_data,
    get_jm_gallery_data_by_id,
    get_jm_gallery_stats,
    get_jm_quarterly_stats,
    get_jm_top_tags,
)
from services.sync_service import sync_ex_favorites
from starlette.concurrency import run_in_threadpool
from utils.sync_lock import sync_lock

router = APIRouter()


@router.get("/", response_model=dict)
def get_gallery(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    keyword: Optional[str] = Query(None),
    # EX 专用过滤（保持向后兼容）
    type: Optional[str] = Query(None),
    # 选择数据源：ex（默认）或 jm
    provider: str = Query("ex", pattern="^(ex|jm)$"),
    # JM 专用过滤与排序（对 EX 不生效）
    category: Optional[str] = Query(None, description="JM 主分类，可传 id 或 title"),
    subcategory: Optional[str] = Query(None, description="JM 子分类，可传 id 或 title"),
    sort: Optional[str] = Query(
        "recent",
        description="JM 排序：recent(默认)/views/likes；对 EX 无效",
        pattern="^(recent|views|likes)$",
    ),
):
    """
    通用列表接口：
      - provider=ex：走 EX 数据（支持 keyword、type）
      - provider=jm：走 JM 数据（支持 keyword、category、subcategory、sort）
    """
    if provider == "ex":
        return get_ex_gallery_data(page, per_page, keyword, type)
    elif provider == "jm":
        return get_jm_gallery_data(
            page=page,
            per_page=per_page,
            keyword=keyword,
            category=category,
            subcategory=subcategory,
            sort=sort,
        )
    else:
        raise HTTPException(status_code=400, detail="Invalid provider, must be 'ex' or 'jm'.")


@router.post("/sync")
async def sync_now():
    """
    仅同步 EX 收藏。
    """
    if sync_lock.locked():
        raise HTTPException(status_code=409, detail="已有同步任务正在进行中")
    async with sync_lock:
        result = await run_in_threadpool(sync_ex_favorites)
        return result


@router.get("/sync/status")
def get_sync_status():
    return {"syncing": sync_lock.locked()}


@router.get("/stats")
def gallery_stats(
    provider: str = Query("ex", pattern="^(ex|jm)$"),
):
    """
    统计：
      - provider=ex：返回 EX 的总量与各固定分类计数
      - provider=jm：返回 JM 的总量、主分类计数、子分类计数
    """
    if provider == "ex":
        return get_ex_gallery_stats()
    elif provider == "jm":
        return get_jm_gallery_stats()
    else:
        raise HTTPException(status_code=400, detail="Invalid provider, must be 'ex' or 'jm'.")


@router.get("/quarterly-stats")
def quarterly_stats(
    provider: str = Query("ex", pattern="^(ex|jm)$"),
):
    """
    季度统计（UTC）：
      - EX 使用 posted 字段
      - JM 使用 addtime 字段
    """
    if provider == "ex":
        return get_ex_quarterly_stats()
    elif provider == "jm":
        return get_jm_quarterly_stats()
    else:
        raise HTTPException(status_code=400, detail="Invalid provider, must be 'ex' or 'jm'.")


@router.get("/top-tags")
def top_tags(
    n: int = Query(20, ge=1, le=100),
    type: Optional[str] = Query(None, description="EX 的 namespace 过滤"),
    provider: str = Query("ex", pattern="^(ex|jm)$"),
):
    """
    热门标签：
      - provider=ex：支持按 namespace（如 'artist'）过滤
      - provider=jm：JM 标签为普通字符串，不支持 namespace，忽略 type
    """
    if provider == "ex":
        return get_ex_top_tags(n=n, type_=type)
    elif provider == "jm":
        return get_jm_top_tags(n=n)
    else:
        raise HTTPException(status_code=400, detail="Invalid provider, must be 'ex' or 'jm'.")


@router.get("/item/{gid}", response_model=dict)
def get_gallery_by_gid(gid: int):
    """
    EX：根据 gid 获取单条记录。
    """
    data = get_ex_gallery_data_by_gid(gid)
    if not data:
        raise HTTPException(status_code=404, detail="Gallery not found")
    return data


@router.get("/jm/item/{id_}", response_model=dict)
def get_jm_item_by_id(id_: str):
    """
    JM：根据 id 获取单条记录。
    """
    data = get_jm_gallery_data_by_id(id_)
    if not data:
        raise HTTPException(status_code=404, detail="Gallery not found")
    return data


@router.get("/jm/debug")
def debug_jm_data():
    """
    JM：调试数据加载状态。
    """
    from core.config import settings
    from services.jm_gallery_service import jm_gallery_data
    
    result = {
        "data_path": getattr(settings, "JM_GALLERY_DATA_PATH", "未设置"),
        "data_count": len(jm_gallery_data),
        "first_item_keys": [],
        "first_item_sample": {}
    }
    
    if jm_gallery_data:
        result["first_item_keys"] = list(jm_gallery_data[0].keys())
        first_item = jm_gallery_data[0]
        result["first_item_sample"] = {
            k: first_item.get(k) for k in ["id", "addtime", "tags", "total_views"]
            if k in first_item
        }
    
    return result


@router.post("/jm/reload")
def reload_jm_data():
    """
    JM：重新加载数据。
    """
    from services.jm_gallery_service import load_jm_gallery_data
    load_jm_gallery_data(force_reload=True)
    return {"message": "JM数据已重新加载"}
