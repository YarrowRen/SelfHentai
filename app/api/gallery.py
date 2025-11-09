# app/api/gallery.py

from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from core.logger import get_logger
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
from services.sync_service import sync_ex_favorites, sync_jm_favorites
from starlette.concurrency import run_in_threadpool
from utils.sync_lock import sync_lock

router = APIRouter()
logger = get_logger(__name__)


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
async def sync_now(
    provider: str = Query("ex", pattern="^(ex|jm)$"),
):
    """
    同步收藏数据：
      - provider=ex：同步 EX 收藏（默认）
      - provider=jm：同步 JM 收藏
    """
    if sync_lock.locked():
        raise HTTPException(status_code=409, detail="已有同步任务正在进行中")
    async with sync_lock:
        if provider == "ex":
            result = await run_in_threadpool(sync_ex_favorites)
        elif provider == "jm":
            result = await run_in_threadpool(sync_jm_favorites)
        else:
            raise HTTPException(status_code=400, detail="Invalid provider, must be 'ex' or 'jm'.")
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
        "first_item_sample": {},
    }

    if jm_gallery_data:
        result["first_item_keys"] = list(jm_gallery_data[0].keys())
        first_item = jm_gallery_data[0]
        result["first_item_sample"] = {
            k: first_item.get(k) for k in ["id", "addtime", "tags", "total_views"] if k in first_item
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


@router.get("/ex/thumbnails/{gid}/{token}")
def get_ex_gallery_thumbnails(gid: str, token: str, page: int = Query(0, ge=0, description="页码，从0开始")):
    """
    EX：获取画廊缩略图数据

    参数:
        gid: Gallery ID
        token: Gallery token
        page: 页码，从0开始
    """
    from core.config import settings
    from utils.exhentai_utils import ExHentaiUtils

    # 检查必要的配置
    if not all(
        [
            getattr(settings, "EXHENTAI_COOKIE_MEMBER_ID", None),
            getattr(settings, "EXHENTAI_COOKIE_PASS_HASH", None),
            getattr(settings, "EXHENTAI_COOKIE_IGNEOUS", None),
        ]
    ):
        raise HTTPException(status_code=503, detail="ExHentai 认证信息未配置，请在设置页面配置 ExHentai cookies")

    cookies = {
        "ipb_member_id": settings.EXHENTAI_COOKIE_MEMBER_ID,
        "ipb_pass_hash": settings.EXHENTAI_COOKIE_PASS_HASH,
        "igneous": settings.EXHENTAI_COOKIE_IGNEOUS,
    }

    try:
        utils = ExHentaiUtils("https://exhentai.org/favorites.php", cookies)
        result = utils.fetch_gallery_thumbnails(gid, token, page)

        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取缩略图失败: {str(e)}")


@router.get("/ex/full-image/{gid}/{token}/{page}")
def get_ex_full_image(gid: str, token: str, page: int):
    """
    EX：获取画廊大图信息

    参数:
        gid: Gallery ID
        token: Gallery token
        page: 页码，从1开始
    """
    from core.config import settings
    from utils.exhentai_utils import ExHentaiUtils

    # 检查必要的配置
    if not all(
        [
            getattr(settings, "EXHENTAI_COOKIE_MEMBER_ID", None),
            getattr(settings, "EXHENTAI_COOKIE_PASS_HASH", None),
            getattr(settings, "EXHENTAI_COOKIE_IGNEOUS", None),
        ]
    ):
        raise HTTPException(status_code=503, detail="ExHentai 认证信息未配置，请在设置页面配置 ExHentai cookies")

    cookies = {
        "ipb_member_id": settings.EXHENTAI_COOKIE_MEMBER_ID,
        "ipb_pass_hash": settings.EXHENTAI_COOKIE_PASS_HASH,
        "igneous": settings.EXHENTAI_COOKIE_IGNEOUS,
    }

    # 验证页码参数
    if page < 1:
        raise HTTPException(status_code=400, detail="页码必须大于等于1")

    try:
        utils = ExHentaiUtils("https://exhentai.org/favorites.php", cookies)
        result = utils.fetch_full_image(gid, token, page)

        if "error" in result and result["error"]:
            raise HTTPException(status_code=500, detail=result["error"])

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取大图失败: {str(e)}")


@router.get("/ex/proxy-image")
def proxy_ex_image(url: str):
    """
    EX：代理图片请求，解决CORS问题
    """
    import requests
    from core.config import settings
    from fastapi.responses import StreamingResponse

    # 检查必要的配置
    if not all(
        [
            getattr(settings, "EXHENTAI_COOKIE_MEMBER_ID", None),
            getattr(settings, "EXHENTAI_COOKIE_PASS_HASH", None),
            getattr(settings, "EXHENTAI_COOKIE_IGNEOUS", None),
        ]
    ):
        raise HTTPException(status_code=503, detail="ExHentai 认证信息未配置")

    cookies = {
        "ipb_member_id": settings.EXHENTAI_COOKIE_MEMBER_ID,
        "ipb_pass_hash": settings.EXHENTAI_COOKIE_PASS_HASH,
        "igneous": settings.EXHENTAI_COOKIE_IGNEOUS,
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Referer": "https://exhentai.org/",
    }

    try:
        response = requests.get(url, cookies=cookies, headers=headers, stream=True, timeout=30)
        response.raise_for_status()

        # 获取内容类型
        content_type = response.headers.get("content-type", "image/jpeg")

        def generate():
            for chunk in response.iter_content(chunk_size=8192):
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

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"代理图片请求失败: {str(e)}")


@router.get("/ex/{gid}/{token}/image/{page}")
def get_ex_manga_page_image(gid: str, token: str, page: int):
    """
    EX：获取漫画页面图片（用于自动翻译）
    """
    from fastapi.responses import StreamingResponse
    import requests
    from core.config import settings
    from utils.exhentai_utils import ExHentaiUtils

    # 检查配置
    if not all([
        getattr(settings, "EXHENTAI_COOKIE_MEMBER_ID", None),
        getattr(settings, "EXHENTAI_COOKIE_PASS_HASH", None),
        getattr(settings, "EXHENTAI_COOKIE_IGNEOUS", None),
    ]):
        raise HTTPException(status_code=503, detail="ExHentai 认证信息未配置")

    cookies = {
        "ipb_member_id": settings.EXHENTAI_COOKIE_MEMBER_ID,
        "ipb_pass_hash": settings.EXHENTAI_COOKIE_PASS_HASH,
        "igneous": settings.EXHENTAI_COOKIE_IGNEOUS,
    }

    try:
        # 首先获取完整图片信息
        utils = ExHentaiUtils("https://exhentai.org/favorites.php", cookies)
        image_info = utils.fetch_full_image(gid, token, page)
        
        if "error" in image_info:
            raise HTTPException(status_code=500, detail=image_info["error"])
        
        image_url = image_info.get("image_url")
        if not image_url:
            raise HTTPException(status_code=404, detail="图片URL未找到")

        # 代理图片请求
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://exhentai.org/",
        }

        response = requests.get(image_url, cookies=cookies, headers=headers, stream=True, timeout=30)
        response.raise_for_status()

        def generate():
            for chunk in response.iter_content(chunk_size=8192):
                yield chunk

        return StreamingResponse(
            generate(),
            media_type=response.headers.get("content-type", "image/jpeg"),
            headers={
                "Access-Control-Allow-Origin": "*",
                "Cache-Control": "public, max-age=3600",
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取图片失败: {str(e)}")


@router.get("/jm/{id}/image/{page}")
def get_jm_manga_page_image(id: str, page: int):
    """
    JM：获取漫画页面图片（用于自动翻译）
    """
    from fastapi.responses import StreamingResponse
    import requests
    from core.config import settings

    try:
        # JM的图片URL格式（需要根据实际API调整）
        # 这里是示例，需要根据JM的实际图片获取逻辑调整
        image_url = f"https://cdn-msp.18comic.vip/media/photos/{id}/{page:05d}.jpg"

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://18comic.vip/",
        }

        response = requests.get(image_url, headers=headers, stream=True, timeout=30)
        response.raise_for_status()

        def generate():
            for chunk in response.iter_content(chunk_size=8192):
                yield chunk

        return StreamingResponse(
            generate(),
            media_type=response.headers.get("content-type", "image/jpeg"),
            headers={
                "Access-Control-Allow-Origin": "*",
                "Cache-Control": "public, max-age=3600",
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取JM图片失败: {str(e)}")


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

        from services.ocr_service import ocr_service

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
        import traceback

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
        from core.config import settings

        # 检查OCR服务是否启用
        if not settings.OCR_ENABLED:
            return {"is_loaded": False, "model_available": False, "enabled": False, "message": "OCR服务已禁用"}

        from services.ocr_service import ocr_service

        status = ocr_service.get_status()
        status["enabled"] = True
        return status
    except Exception as e:
        try:
            from core.config import settings

            enabled = settings.OCR_ENABLED
        except:
            enabled = False
        return {"is_loaded": False, "model_available": False, "enabled": enabled, "error": str(e)}


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
        from services.translation_service import translation_service

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
        import traceback

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
        from services.translation_service import translation_service

        return translation_service.get_status()
    except Exception as e:
        return {"is_initialized": False, "api_key_available": False, "model_name": "", "error": str(e)}
