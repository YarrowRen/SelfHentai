# app/api/gallery.py

from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from services.gallery_service import get_gallery_data, get_gallery_data_by_gid
from services.sync_service import sync_favorites

router = APIRouter()


@router.get("/", response_model=dict)
def get_gallery(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    keyword: Optional[str] = Query(None),
    type: Optional[str] = Query(None),
):
    return get_gallery_data(page, per_page, keyword, type)


@router.get("/{gid}", response_model=dict)
def get_gallery_by_gid(gid: int):
    data = get_gallery_data_by_gid(gid)
    if not data:
        raise HTTPException(status_code=404, detail="Gallery not found")
    return data


@router.post("/sync")
def sync_now():
    return sync_favorites()
