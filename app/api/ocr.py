# app/api/ocr.py

import os
import tempfile
import requests
import time
import math
from typing import List, Dict, Any, Optional, Tuple
from PIL import Image

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from core.logger import get_logger
from core.config import settings

# 获取logger
logger = get_logger(__name__)

# 只有在PaddleOCR启用时才导入
paddleocr_available = False
try:
    if settings.PADDLE_OCR_ENABLED:
        from paddleocr import PaddleOCR

        paddleocr_available = True
        logger.info("PaddleOCR导入成功")
    else:
        logger.info("PaddleOCR功能已禁用，跳过导入")
except ImportError as e:
    logger.warning(f"PaddleOCR未安装或导入失败: {e}")
    logger.warning("请安装PaddleOCR: pip install paddlepaddle paddleocr")
except Exception as e:
    logger.error(f"PaddleOCR导入出错: {e}")
    logger.error("这通常是Python版本兼容性问题，建议使用Python 3.9+")

router = APIRouter()

# OCR 实例缓存
ocr_engines: Dict[str, Any] = {}


class Rectangular:
    """矩形类，用于碰撞检测"""
    
    def __init__(self, x: float, y: float, w: float, h: float):
        self.x0 = x
        self.y0 = y
        self.x1 = x + w
        self.y1 = y + h
        self.w = w
        self.h = h
    
    def collision(self, r2) -> bool:
        """检测与另一个矩形是否碰撞"""
        return (self.x0 < r2.x1 and self.y0 < r2.y1 and 
                self.x1 > r2.x0 and self.y1 > r2.y0)
    
    def distance_to(self, other) -> float:
        """计算到另一个矩形的距离"""
        center1_x = (self.x0 + self.x1) / 2
        center1_y = (self.y0 + self.y1) / 2
        center2_x = (other.x0 + other.x1) / 2
        center2_y = (other.y0 + other.y1) / 2
        
        return math.sqrt((center1_x - center2_x)**2 + (center1_y - center2_y)**2)
    
    def expand(self, expand_ratio: float = 1.5):
        """扩展矩形区域"""
        expand_w = self.w * expand_ratio - self.w
        expand_h = self.h * expand_ratio - self.h
        
        return Rectangular(
            self.x0 - expand_w / 2,
            self.y0 - expand_h / 2,
            self.w + expand_w,
            self.h + expand_h
        )


class DialogMerger:
    """对话框合并器"""
    
    def __init__(self, expand_ratio: float = 1.3, max_distance: float = 50.0, min_group_size: int = 2):
        self.expand_ratio = expand_ratio
        self.max_distance = max_distance
        self.min_group_size = min_group_size
    
    @staticmethod
    def bbox_to_rect(bbox: List[float]) -> Rectangular:
        """将bbox [x1, y1, x2, y2] 转换为矩形对象"""
        x1, y1, x2, y2 = bbox
        return Rectangular(x1, y1, x2 - x1, y2 - y1)
    
    def _find_nearby_texts(self, rect: Rectangular, all_rects: List[Tuple[Rectangular, int]], 
                          used_indices: set) -> List[int]:
        """查找附近的文本框"""
        nearby_indices = []
        expanded_rect = rect.expand(expand_ratio=self.expand_ratio)
        
        for other_rect, original_index in all_rects:
            if original_index in used_indices:
                continue
            
            # 优先考虑重叠
            if expanded_rect.collision(other_rect):
                nearby_indices.append(original_index)
            elif rect.distance_to(other_rect) <= self.max_distance:
                nearby_indices.append(original_index)
        
        return nearby_indices
    
    def _find_connected_texts(self, current_rect: Rectangular, rectangles: List[Tuple[Rectangular, int]], 
                            used_indices: set, current_group: List[int]):
        """递归查找相邻的文本框"""
        nearby_indices = self._find_nearby_texts(current_rect, rectangles, used_indices)
        
        for nearby_idx in nearby_indices:
            if nearby_idx not in used_indices:
                current_group.append(nearby_idx)
                used_indices.add(nearby_idx)
                
                # 递归查找与新加入文本框相邻的文本框
                nearby_rect = next(r for r, idx in rectangles if idx == nearby_idx)
                self._find_connected_texts(nearby_rect, rectangles, used_indices, current_group)
    
    def merge_ocr_results(self, ocr_results: List[Dict]) -> List[Dict]:
        """
        合并OCR识别结果中的对话框
        
        Args:
            ocr_results: OCR结果列表，每个元素包含text, confidence, bbox
        
        Returns:
            合并后的结果列表
        """
        if not ocr_results:
            return []
        
        logger.info(f"开始合并对话框，原始文本区域数量: {len(ocr_results)}")
        
        # 转换为矩形对象
        rectangles = []
        for i, result in enumerate(ocr_results):
            rect = self.bbox_to_rect(result['bbox'])
            rectangles.append((rect, i))
        
        # 按面积排序，从大到小处理
        rectangles.sort(key=lambda x: x[0].w * x[0].h, reverse=True)
        
        # 合并逻辑
        merged_groups = []
        used_indices = set()
        
        for rect, original_index in rectangles:
            if original_index in used_indices:
                continue
            
            # 创建新的群组
            current_group = [original_index]
            used_indices.add(original_index)
            
            # 递归查找相邻的文本框
            self._find_connected_texts(rect, rectangles, used_indices, current_group)
            
            # 保留所有群组
            merged_groups.append(current_group)
        
        # 创建合并后的结果
        merged_results = []
        
        for group_indices in merged_groups:
            if len(group_indices) >= self.min_group_size:
                # 对话框合并：按从右到左排序文字
                group_data = []
                for idx in group_indices:
                    result = ocr_results[idx]
                    bbox = result['bbox']
                    center_x = (bbox[0] + bbox[2]) / 2
                    group_data.append((idx, center_x, result))
                
                # 按x坐标从右到左排序（x值大的在前）
                group_data.sort(key=lambda x: x[1], reverse=True)
                
                # 合并文字（用空格连接）
                merged_text = " ".join([item[2]['text'] for item in group_data])
                merged_confidence = sum([item[2]['confidence'] for item in group_data]) / len(group_data)
                
                # 计算合并后的边界框
                all_x = [item[2]['bbox'][0] for item in group_data] + [item[2]['bbox'][2] for item in group_data]
                all_y = [item[2]['bbox'][1] for item in group_data] + [item[2]['bbox'][3] for item in group_data]
                
                merged_bbox = [min(all_x), min(all_y), max(all_x), max(all_y)]
                
                merged_results.append({
                    'text': merged_text,
                    'confidence': merged_confidence,
                    'bbox': merged_bbox,
                    'is_merged': True,
                    'original_count': len(group_indices),
                    'original_texts': [item[2]['text'] for item in group_data]
                })
            else:
                # 单独的文本框
                for idx in group_indices:
                    result = ocr_results[idx]
                    merged_results.append({
                        'text': result['text'],
                        'confidence': result['confidence'],
                        'bbox': result['bbox'],
                        'is_merged': False,
                        'original_count': 1,
                        'original_texts': [result['text']]
                    })
        
        # 按置信度排序
        merged_results.sort(key=lambda x: x['confidence'], reverse=True)
        
        logger.info(f"对话框合并完成，生成 {len(merged_results)} 个文本区域")
        
        return merged_results


class OCRRequest(BaseModel):
    image_url: str
    language: str = "ch"  # ch, en, ja, chinese_cht
    page_number: Optional[int] = 1
    gallery_id: Optional[str] = None
    provider: Optional[str] = "ex"
    confidence_threshold: Optional[float] = 0.75
    # OCR 引擎参数
    det_limit_type: Optional[str] = "max"
    det_limit_side_len: Optional[int] = 960
    use_doc_orientation_classify: Optional[bool] = False
    use_doc_unwarping: Optional[bool] = False


class BatchTranslateRequest(BaseModel):
    texts: List[str]
    source_language: str = "japan"
    target_language: str = "zh"


class OCRResult(BaseModel):
    text: str
    confidence: float
    bbox: List[float]  # [x1, y1, x2, y2]
    is_merged: Optional[bool] = False
    original_count: Optional[int] = 1
    original_texts: Optional[List[str]] = None


class OCRResponse(BaseModel):
    success: bool
    results: List[OCRResult] = []
    error: Optional[str] = None
    processing_time: Optional[float] = None


def get_ocr_engine(request: OCRRequest) -> Any:
    """获取或创建OCR引擎实例"""
    if not paddleocr_available:
        raise HTTPException(status_code=503, detail="OCR服务未启用或PaddleOCR未正确安装")

    # 使用参数组合作为缓存key
    cache_key = f"{request.language}_{request.det_limit_type}_{request.det_limit_side_len}_{request.use_doc_orientation_classify}_{request.use_doc_unwarping}"
    
    if cache_key not in ocr_engines:
        try:
            logger.info(f"初始化OCR引擎，语言: {request.language}, 参数: {request.det_limit_type}_{request.det_limit_side_len}")
            ocr_engines[cache_key] = PaddleOCR(
                lang=request.language,
                text_det_limit_type=request.det_limit_type,
                text_det_limit_side_len=request.det_limit_side_len,
                use_doc_orientation_classify=request.use_doc_orientation_classify,
                use_doc_unwarping=request.use_doc_unwarping
            )
            logger.info(f"OCR引擎初始化完成: {cache_key}")
        except Exception as e:
            logger.error(f"OCR引擎初始化失败 ({cache_key}): {e}")
            raise HTTPException(status_code=500, detail=f"OCR引擎初始化失败: {str(e)}")

    return ocr_engines[cache_key]


def download_image(image_url: str) -> str:
    """下载图片到临时文件"""
    try:
        # 如果是本地文件路径
        if os.path.exists(image_url):
            return image_url

        # 检查是否是本地API的循环调用
        if "localhost" in image_url or "127.0.0.1" in image_url:
            # 如果是代理URL，提取原始URL
            if "proxy-image?url=" in image_url:
                from urllib.parse import unquote, parse_qs, urlparse

                parsed = urlparse(image_url)
                query_params = parse_qs(parsed.query)
                if "url" in query_params:
                    original_url = unquote(query_params["url"][0])
                    logger.debug(f"检测到代理URL，提取原始URL: {original_url}")
                    image_url = original_url
                else:
                    raise HTTPException(status_code=400, detail="无法从代理URL中提取原始图片URL")
            else:
                raise HTTPException(status_code=400, detail="不能从本地API下载图片，请提供外部图片URL")

        # 下载网络图片
        logger.debug(f"正在下载图片: {image_url}")

        # 添加必要的请求头
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Referer": "https://exhentai.org/",
        }

        # 如果是ExHentai图片，添加认证cookies
        cookies = None
        if "exhentai.org" in image_url or "ehgt.org" in image_url:
            from core.config import settings

            if all(
                [
                    getattr(settings, "EXHENTAI_COOKIE_MEMBER_ID", None),
                    getattr(settings, "EXHENTAI_COOKIE_PASS_HASH", None),
                    getattr(settings, "EXHENTAI_COOKIE_IGNEOUS", None),
                ]
            ):
                cookies = {
                    "ipb_member_id": settings.EXHENTAI_COOKIE_MEMBER_ID,
                    "ipb_pass_hash": settings.EXHENTAI_COOKIE_PASS_HASH,
                    "igneous": settings.EXHENTAI_COOKIE_IGNEOUS,
                }

        response = requests.get(image_url, headers=headers, cookies=cookies, timeout=30, stream=True)
        response.raise_for_status()

        # 创建临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
            for chunk in response.iter_content(chunk_size=8192):
                tmp_file.write(chunk)
            temp_path = tmp_file.name

        logger.debug(f"图片下载完成: {temp_path}")
        return temp_path

    except requests.exceptions.RequestException as e:
        logger.error(f"图片下载失败: {e}")
        raise HTTPException(status_code=400, detail=f"图片下载失败: {str(e)}")
    except Exception as e:
        logger.error(f"图片处理错误: {e}")
        raise HTTPException(status_code=500, detail=f"图片处理错误: {str(e)}")


def convert_image_format(image_path: str) -> str:
    """转换不支持的图像格式为JPG"""
    try:
        with Image.open(image_path) as img:
            # 检查是否需要转换
            if img.format in ["JPEG", "JPG", "PNG", "BMP"]:
                return image_path

            # 转换为RGB模式（移除alpha通道）
            if img.mode in ("RGBA", "LA"):
                background = Image.new("RGB", img.size, (255, 255, 255))
                if img.mode == "RGBA":
                    background.paste(img, mask=img.split()[-1])
                else:
                    background.paste(img, mask=img.split()[-1])
                img = background
            elif img.mode != "RGB":
                img = img.convert("RGB")

            # 创建新的临时文件
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
                img.save(tmp_file, "JPEG", quality=95)
                converted_path = tmp_file.name

            logger.debug(f"图像格式转换完成: {image_path} -> {converted_path}")
            return converted_path

    except Exception as e:
        logger.error(f"图像格式转换失败: {e}")
        return image_path  # 返回原路径，让OCR尝试处理


@router.post("/recognize", response_model=OCRResponse)
async def recognize_text(request: OCRRequest):
    """
    OCR文本识别
    """
    if not settings.PADDLE_OCR_ENABLED:
        raise HTTPException(status_code=503, detail="PaddleOCR服务已禁用")

    temp_files = []
    start_time = time.time()

    try:
        # 获取OCR引擎
        ocr_engine = get_ocr_engine(request)

        # 下载图片
        image_path = download_image(request.image_url)
        if image_path != request.image_url:
            temp_files.append(image_path)

        # 转换图像格式（如果需要）
        converted_path = convert_image_format(image_path)
        if converted_path != image_path:
            temp_files.append(converted_path)

        # 执行OCR识别
        logger.info(f"开始OCR识别，图片: {converted_path}, 语言: {request.language}")
        ocr_results = ocr_engine.ocr(converted_path)

        # 处理OCR结果 - 新版PaddleOCR数据格式
        raw_results = []
        if ocr_results and len(ocr_results) > 0:
            result_dict = ocr_results[0]
            
            # 获取识别文本、置信度和坐标
            rec_texts = result_dict.get('rec_texts', [])
            rec_scores = result_dict.get('rec_scores', [])
            rec_polys = result_dict.get('rec_polys', [])
            
            for i, (text, confidence, bbox_points) in enumerate(zip(rec_texts, rec_scores, rec_polys)):
                # 过滤空文本和低置信度结果
                if text and text.strip() and confidence >= request.confidence_threshold:
                    # 转换bbox格式为 [x1, y1, x2, y2]
                    x_coords = [point[0] for point in bbox_points]
                    y_coords = [point[1] for point in bbox_points]
                    bbox = [
                        float(min(x_coords)),  # x1
                        float(min(y_coords)),  # y1
                        float(max(x_coords)),  # x2
                        float(max(y_coords)),  # y2
                    ]
                    
                    raw_results.append({
                        'text': text,
                        'confidence': confidence,
                        'bbox': bbox
                    })
        
        # 使用对话框合并器处理结果
        dialog_merger = DialogMerger()
        merged_results = dialog_merger.merge_ocr_results(raw_results)
        
        # 转换为OCRResult对象
        results = []
        for result in merged_results:
            results.append(OCRResult(
                text=result['text'],
                confidence=result['confidence'],
                bbox=result['bbox'],
                is_merged=result.get('is_merged', False),
                original_count=result.get('original_count', 1),
                original_texts=result.get('original_texts', [result['text']])
            ))

        processing_time = time.time() - start_time
        logger.info(f"OCR识别完成，识别到 {len(results)} 个文本区域，耗时 {processing_time:.2f}s")

        return OCRResponse(success=True, results=results, processing_time=processing_time)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OCR识别失败: {e}")
        raise HTTPException(status_code=500, detail=f"OCR识别失败: {str(e)}")
    finally:
        # 清理临时文件
        for temp_file in temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    logger.debug(f"已清理临时文件: {temp_file}")
            except Exception as e:
                logger.warning(f"清理临时文件失败 {temp_file}: {e}")


def map_language_code(lang_code: str, to_translation_service: bool = True):
    """
    映射语言代码
    to_translation_service: True表示映射到翻译服务的语言代码，False表示从翻译服务映射回来
    """
    # OCR语言代码 -> 翻译服务语言代码
    ocr_to_translation = {"japan": "ja", "ch": "zh", "chinese_cht": "zh-TW", "en": "en"}

    # 翻译服务语言代码 -> OCR语言代码
    translation_to_ocr = {v: k for k, v in ocr_to_translation.items()}

    if to_translation_service:
        return ocr_to_translation.get(lang_code, lang_code)
    else:
        return translation_to_ocr.get(lang_code, lang_code)


@router.post("/translate/batch")
async def translate_batch(request: BatchTranslateRequest):
    """
    批量翻译文本（集成现有翻译服务）
    """
    try:
        from services.translation_service import translation_service

        # 映射语言代码到翻译服务
        source_lang = map_language_code(request.source_language, True)
        target_lang = map_language_code(request.target_language, True)

        if not hasattr(translation_service, "translate_batch"):
            # 如果没有批量翻译方法，使用单个翻译
            translations = []
            for text in request.texts:
                try:
                    result = translation_service.translate_text(text, source_lang=source_lang, target_lang=target_lang)
                    translations.append(result.get("translation", text))
                except Exception as e:
                    logger.warning(f"翻译失败 '{text}': {e}")
                    translations.append(text)  # 翻译失败时返回原文
        else:
            # 使用批量翻译方法
            translations = translation_service.translate_batch(request.texts, source_lang=source_lang, target_lang=target_lang)

        return {
            "success": True,
            "translations": translations,
            "source_language": request.source_language,
            "target_language": request.target_language,
        }

    except ImportError:
        raise HTTPException(status_code=503, detail="翻译服务不可用")
    except Exception as e:
        logger.error(f"批量翻译失败: {e}")
        raise HTTPException(status_code=500, detail=f"翻译失败: {str(e)}")


@router.get("/status")
async def get_ocr_status():
    """
    获取OCR服务状态
    """
    return {
        "paddle_ocr_enabled": settings.PADDLE_OCR_ENABLED,
        "paddleocr_available": paddleocr_available,
        "active_engines": list(ocr_engines.keys()),
        "supported_languages": ["ch", "en", "japan", "chinese_cht"],
    }


