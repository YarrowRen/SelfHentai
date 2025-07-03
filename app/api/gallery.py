# app/api/gallery.py

import asyncio
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from services.gallery_service import (
    get_gallery_data,
    get_gallery_data_by_gid,
    get_gallery_stats,
    get_quarterly_stats,
    get_top_tags,
)
from services.sync_service import sync_favorites
from starlette.concurrency import run_in_threadpool
from utils.sync_lock import sync_lock

router = APIRouter()


@router.get("/", response_model=dict)
def get_gallery(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    keyword: Optional[str] = Query(None),
    type: Optional[str] = Query(None),
):
    return get_gallery_data(page, per_page, keyword, type)


@router.post("/sync")
async def sync_now():
    if sync_lock.locked():
        raise HTTPException(status_code=409, detail="已有同步任务正在进行中")
    async with sync_lock:
        result = await run_in_threadpool(sync_favorites)
        return result


@router.get("/sync/status")
def get_sync_status():
    return {"syncing": sync_lock.locked()}


@router.get("/stats")
def gallery_stats():
    return get_gallery_stats()


@router.get("/quarterly-stats")
def quarterly_stats():
    return get_quarterly_stats()


@router.get("/top-tags")
def top_tags(n: int = Query(20, ge=1, le=100), type: Optional[str] = Query(None)):
    return get_top_tags(n=n, type_=type)


@router.get("/item/{gid}", response_model=dict)
def get_gallery_by_gid(gid: int):
    data = get_gallery_data_by_gid(gid)
    if not data:
        raise HTTPException(status_code=404, detail="Gallery not found")
    return data
