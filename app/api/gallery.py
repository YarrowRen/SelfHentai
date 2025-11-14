# app/api/gallery.py

from typing import Optional
from functools import wraps
from urllib.parse import urlparse
import traceback
import httpx

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from starlette.concurrency import run_in_threadpool

from core.logger import get_logger
from core.config import settings
from services.ex_gallery_service import (
    get_ex_gallery_data,
    get_ex_gallery_data_by_gid,
    get_ex_gallery_stats,
    get_ex_quarterly_stats,
    get_ex_top_tags,
)
from services.sync_service import sync_ex_favorites
from utils.sync_lock import sync_lock
from utils.exhentai_utils import ExHentaiUtils

# 延迟导入的服务，避免循环导入
def get_ocr_service():
    from services.ocr_service import ocr_service
    return ocr_service

def get_translation_service():
    from services.translation_service import translation_service
    return translation_service

router = APIRouter()
logger = get_logger(__name__)

# 配置常量
DEFAULT_PAGE_SIZE = settings.DEFAULT_PAGE_SIZE
MAX_PAGE_SIZE = settings.MAX_PAGE_SIZE
TIMEOUT_SECONDS = settings.REQUEST_TIMEOUT
MAX_TOP_TAGS = settings.MAX_TOP_TAGS
CHUNK_SIZE = settings.STREAM_CHUNK_SIZE


def require_exhentai_auth(func):
    """ExHentai认证装饰器，支持同步和异步函数"""
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        if not all([
            settings.EXHENTAI_COOKIE_MEMBER_ID,
            settings.EXHENTAI_COOKIE_PASS_HASH,
            settings.EXHENTAI_COOKIE_IGNEOUS,
        ]):
            raise HTTPException(
                status_code=503, 
                detail="ExHentai 认证信息未配置，请在设置页面配置 ExHentai cookies"
            )
        return await func(*args, **kwargs)
    
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        if not all([
            settings.EXHENTAI_COOKIE_MEMBER_ID,
            settings.EXHENTAI_COOKIE_PASS_HASH,
            settings.EXHENTAI_COOKIE_IGNEOUS,
        ]):
            raise HTTPException(
                status_code=503, 
                detail="ExHentai 认证信息未配置，请在设置页面配置 ExHentai cookies"
            )
        return func(*args, **kwargs)
    
    # 检查函数是否是异步的
    import asyncio
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper


def get_ex_cookies():
    """获取ExHentai cookies"""
    return {
        "ipb_member_id": settings.EXHENTAI_COOKIE_MEMBER_ID,
        "ipb_pass_hash": settings.EXHENTAI_COOKIE_PASS_HASH,
        "igneous": settings.EXHENTAI_COOKIE_IGNEOUS,
    }


def get_ex_headers():
    """获取ExHentai请求头"""
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Referer": "https://exhentai.org/",
    }


def validate_image_url(url: str, allowed_domains: tuple) -> bool:
    """验证图片URL域名"""
    try:
        parsed_url = urlparse(url)
        hostname = parsed_url.hostname
        if not hostname:
            return False
        
        # 检查主机名是否匹配允许的域名
        for domain in allowed_domains:
            if hostname == domain.lstrip('.') or hostname.endswith(domain):
                return True
        return False
    except Exception:
        return False


@router.get("/", response_model=dict)
def get_gallery(
    page: int = Query(1, ge=1),
    per_page: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    keyword: Optional[str] = Query(None),
    type: Optional[str] = Query(None),
):
    """
    获取ExHentai画廊列表
    """
    return get_ex_gallery_data(page, per_page, keyword, type)


@router.post("/sync")
async def sync_now():
    """
    同步ExHentai收藏数据
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
def gallery_stats():
    """
    获取ExHentai画廊统计信息
    """
    return get_ex_gallery_stats()


@router.get("/quarterly-stats")
def quarterly_stats():
    """
    获取ExHentai季度统计（UTC）
    """
    return get_ex_quarterly_stats()


@router.get("/top-tags")
def top_tags(
    n: int = Query(20, ge=1, le=MAX_TOP_TAGS),
    type: Optional[str] = Query(None, description="namespace过滤，如'artist'"),
):
    """
    获取ExHentai热门标签
    """
    return get_ex_top_tags(n=n, type_=type)


@router.get("/item/{gid}", response_model=dict)
def get_gallery_by_gid(gid: int):
    """
    根据gid获取单个画廊信息
    """
    data = get_ex_gallery_data_by_gid(gid)
    if not data:
        raise HTTPException(status_code=404, detail="Gallery not found")
    return data


@router.get("/ex/thumbnails/{gid}/{token}")
@require_exhentai_auth
def get_ex_gallery_thumbnails(gid: str, token: str, page: int = Query(0, ge=0, description="页码，从0开始")):
    """
    EX：获取画廊缩略图数据

    参数:
        gid: Gallery ID
        token: Gallery token
        page: 页码，从0开始
    """
    try:
        utils = ExHentaiUtils("https://exhentai.org/favorites.php", get_ex_cookies())
        result = utils.fetch_gallery_thumbnails(gid, token, page)

        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取缩略图失败: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"获取缩略图失败: {str(e)}")


@router.get("/ex/full-image/{gid}/{token}/{page}")
@require_exhentai_auth
def get_ex_full_image(gid: str, token: str, page: int):
    """
    EX：获取画廊大图信息

    参数:
        gid: Gallery ID
        token: Gallery token
        page: 页码，从1开始
    """
    # 验证页码参数
    if page < 1:
        raise HTTPException(status_code=400, detail="页码必须大于等于1")

    try:
        utils = ExHentaiUtils("https://exhentai.org/favorites.php", get_ex_cookies())
        result = utils.fetch_full_image(gid, token, page)

        if "error" in result and result["error"]:
            raise HTTPException(status_code=500, detail=result["error"])

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取大图失败: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"获取大图失败: {str(e)}")


@router.get("/ex/proxy-image")
@require_exhentai_auth
async def proxy_ex_image(url: str):
    """
    EX：代理图片请求，解决CORS问题
    """
    # 验证URL域名 (包括ExHentai的官方图片CDN)
    if not validate_image_url(url, ('.exhentai.org', '.e-hentai.org', '.hath.network')):
        raise HTTPException(status_code=400, detail="无效的图片URL域名")

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
            response = await client.get(
                url, 
                cookies=get_ex_cookies(), 
                headers=get_ex_headers()
            )
            response.raise_for_status()

            # 获取内容类型
            content_type = response.headers.get("content-type", "image/jpeg")

            def generate():
                for chunk in response.iter_bytes(chunk_size=CHUNK_SIZE):
                    yield chunk

            return StreamingResponse(
                generate(),
                media_type=content_type,
                headers={
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "GET",
                    "Access-Control-Allow-Headers": "*",
                    "Cache-Control": "public, max-age=3600",
                },
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"代理图片请求失败: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"代理图片请求失败: {str(e)}")


@router.get("/ex/{gid}/{token}/image/{page}")
@require_exhentai_auth
async def get_ex_manga_page_image(gid: str, token: str, page: int):
    """
    EX：获取漫画页面图片（用于自动翻译）
    """
    try:
        # 首先获取完整图片信息
        utils = ExHentaiUtils("https://exhentai.org/favorites.php", get_ex_cookies())
        image_info = utils.fetch_full_image(gid, token, page)
        
        if "error" in image_info:
            raise HTTPException(status_code=500, detail=image_info["error"])
        
        image_url = image_info.get("image_url")
        if not image_url:
            raise HTTPException(status_code=404, detail="图片URL未找到")

        # 验证图片URL (包括ExHentai的官方图片CDN)
        if not validate_image_url(image_url, ('.exhentai.org', '.e-hentai.org', '.hath.network')):
            raise HTTPException(status_code=400, detail="无效的图片URL")

        # 代理图片请求
        async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
            response = await client.get(
                image_url, 
                cookies=get_ex_cookies(), 
                headers=get_ex_headers()
            )
            response.raise_for_status()

            def generate():
                for chunk in response.iter_bytes(chunk_size=CHUNK_SIZE):
                    yield chunk

            return StreamingResponse(
                generate(),
                media_type=response.headers.get("content-type", "image/jpeg"),
                headers={
                    "Access-Control-Allow-Origin": "*",
                    "Cache-Control": "public, max-age=3600",
                }
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取图片失败: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"获取图片失败: {str(e)}")


@router.post("/ocr")
def perform_ocr_recognition(image_data: dict):
    """
    OCR文本识别接口

    参数:
        image_data: {"image": "data:image/png;base64,..."} 包含base64编码图片数据的字典

    返回:
        {"text": "识别出的文本", "success": true/false, "error": "错误信息"}
    """
    try:
        from core.config import settings

        # 检查Manga OCR服务是否启用
        if not settings.MANGA_OCR_ENABLED:
            raise HTTPException(status_code=503, detail="Manga OCR服务已禁用，请在设置中启用 MANGA_OCR_ENABLED 选项")

        ocr_service = get_ocr_service()

        # 检查OCR服务状态
        if not ocr_service.is_loaded:
            raise HTTPException(status_code=503, detail="OCR服务未启动，请检查 manga-ocr 是否正确安装")

        # 验证请求数据
        if "image" not in image_data:
            raise HTTPException(status_code=400, detail="请求缺少 'image' 字段")

        base64_image = image_data["image"]
        if not base64_image:
            raise HTTPException(status_code=400, detail="图片数据不能为空")

        # 进行OCR识别
        recognized_text = ocr_service.recognize_text(base64_image)

        return {"success": True, "text": recognized_text, "length": len(recognized_text) if recognized_text else 0}

    except HTTPException:
        # 重新抛出 HTTP 异常
        raise
    except Exception as e:
        # 捕获其他异常并返回 500 错误
        error_msg = f"OCR识别失败: {str(e)}"
        logger.error(f"OCR错误详情: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=error_msg)


@router.get("/ocr/status")
def get_ocr_status():
    """
    获取OCR服务状态

    返回:
        {"is_loaded": true/false, "model_available": true/false}
    """
    try:
        # 检查Manga OCR服务是否启用
        if not settings.MANGA_OCR_ENABLED:
            raise HTTPException(
                status_code=503, 
                detail="Manga OCR服务已禁用，请在设置中启用 MANGA_OCR_ENABLED 选项"
            )

        ocr_service = get_ocr_service()

        status = ocr_service.get_status()
        status["enabled"] = True
        return status
    except HTTPException:
        # 重新抛出 HTTP 异常
        raise
    except Exception as e:
        logger.error(f"获取OCR状态失败: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500, 
            detail=f"获取OCR状态失败: {str(e)}"
        )


@router.post("/translate")
def perform_translation(request_data: dict):
    """
    AI翻译接口

    参数:
        request_data: {
            "text": "日文原文",
            "target_language": "zh" (目标语言，默认中文)
        }

    返回:
        {
            "success": true/false,
            "translation": "翻译结果",
            "error": "错误信息",
            "original_text": "原文",
            "target_language": "目标语言"
        }
    """
    try:
        translation_service = get_translation_service()

        # 检查翻译服务状态
        status = translation_service.get_status()
        if not status["is_initialized"]:
            raise HTTPException(status_code=503, detail="翻译服务未初始化，请检查翻译服务配置")

        if not status["api_key_available"]:
            raise HTTPException(status_code=503, detail="翻译服务 API Key 未设置，请在设置页面配置")

        # 验证请求数据
        if "text" not in request_data:
            raise HTTPException(status_code=400, detail="请求缺少 'text' 字段")

        original_text = request_data["text"]
        target_language = request_data.get("target_language", "zh")

        if not original_text or not original_text.strip():
            raise HTTPException(status_code=400, detail="待翻译文本不能为空")

        # 进行翻译
        result = translation_service.translate_text(original_text, target_language)

        # 构建响应
        response = {
            "success": result["success"],
            "translation": result["translation"],
            "error": result["error"],
            "original_text": original_text,
            "target_language": target_language,
        }

        if not result["success"]:
            # 翻译失败时返回 400 错误
            raise HTTPException(status_code=400, detail=result["error"])

        return response

    except HTTPException:
        # 重新抛出 HTTP 异常
        raise
    except Exception as e:
        # 捕获其他异常并返回 500 错误
        error_msg = f"翻译服务异常: {str(e)}"
        logger.error(f"翻译错误详情: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=error_msg)


@router.get("/translate/status")
def get_translation_status():
    """
    获取翻译服务状态

    返回:
        {
            "is_initialized": true/false,
            "api_key_available": true/false,
            "model_name": "模型名称"
        }
    """
    try:
        translation_service = get_translation_service()

        return translation_service.get_status()
    except Exception as e:
        return {"is_initialized": False, "api_key_available": False, "model_name": "", "error": str(e)}
