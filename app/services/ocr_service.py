"""
OCR 服务模块
使用 manga-ocr 进行日语漫画文本识别
"""

import logging
import io
import base64
import os
from PIL import Image
from typing import Optional

# 在导入任何 torch 相关模块之前设置环境变量，强制使用 CPU
os.environ['PYTORCH_ENABLE_MPS_FALLBACK'] = '1'
os.environ['PYTORCH_MPS_HIGH_WATERMARK_RATIO'] = '0.0'
os.environ['CUDA_VISIBLE_DEVICES'] = ''
os.environ['MPS_VISIBLE_DEVICES'] = ''

from core.logger import get_logger

logger = get_logger(__name__)


class OCRService:
    """OCR 服务类，管理 manga-ocr 模型"""
    
    def __init__(self):
        self.model = None
        self.is_loaded = False
        
    def load_model(self):
        """加载 manga-ocr 模型"""
        if self.is_loaded:
            logger.info("OCR 模型已经加载，跳过")
            return
            
        try:
            logger.info("开始加载 manga-ocr 模型...")
            
            # 导入 PyTorch 并禁用 MPS
            try:
                import torch
                logger.info(f"PyTorch 版本: {torch.__version__}")
                
                # 猴子补丁：强制禁用 MPS 以避免兼容性问题
                if hasattr(torch.backends, 'mps'):
                    original_is_available = torch.backends.mps.is_available
                    torch.backends.mps.is_available = lambda: False
                    logger.info("已禁用 MPS 后端，强制使用 CPU")
                    
            except ImportError:
                logger.warning("PyTorch 未找到，继续尝试加载模型")
            
            # 加载 manga-ocr
            from manga_ocr import MangaOcr
            logger.info("正在初始化 MangaOcr 模型，这可能需要下载模型文件...")
            
            # 初始化模型
            self.model = MangaOcr()
            self.is_loaded = True
            logger.info("manga-ocr 模型加载完成（CPU 模式）")
            
        except ImportError as e:
            error_msg = f"依赖包未安装: {str(e)}"
            if "manga_ocr" in str(e):
                error_msg += "\n请安装: pip install manga-ocr"
            elif "tensorflow" in str(e):
                error_msg += "\n请安装: pip install tensorflow==2.13.1"
            logger.error(error_msg)
            raise ImportError(error_msg) from e
            
        except Exception as e:
            error_msg = f"加载 manga-ocr 模型失败: {str(e)}"
            
            # 提供常见错误的解决方案
            if "tensorflow" in str(e).lower():
                error_msg += "\n建议解决方案:"
                error_msg += "\n1. 卸载当前 TensorFlow: pip uninstall tensorflow"
                error_msg += "\n2. 安装兼容版本: pip install tensorflow==2.13.1"
                error_msg += "\n3. 如果是 Apple Silicon Mac，使用: pip install tensorflow-macos==2.13.1"
            elif "torch" in str(e).lower():
                error_msg += "\n建议安装 PyTorch: pip install torch==2.0.1 torchvision==0.15.2"
            elif "transformers" in str(e).lower():
                error_msg += "\n建议安装 Transformers: pip install transformers==4.21.3"
                
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e
    
    def recognize_text(self, image_data: str) -> str:
        """
        识别图片中的文本
        
        Args:
            image_data: base64 编码的图片数据 (data:image/png;base64,...)
            
        Returns:
            识别出的文本
        """
        if not self.is_loaded:
            raise RuntimeError("OCR 模型未加载，请先调用 load_model()")
        
        try:
            # 解析 base64 图片数据
            if image_data.startswith('data:image'):
                # 移除 data:image/png;base64, 前缀
                base64_data = image_data.split(',', 1)[1]
            else:
                base64_data = image_data
            
            # 解码图片
            image_bytes = base64.b64decode(base64_data)
            image = Image.open(io.BytesIO(image_bytes))
            
            # 确保图片是RGB格式
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            logger.info(f"开始OCR识别，图片尺寸: {image.size}")
            
            # 进行OCR识别
            result = self.model(image)
            
            logger.info(f"OCR识别完成，结果长度: {len(result) if result else 0}")
            
            return result or ""
            
        except Exception as e:
            logger.error(f"OCR识别失败: {str(e)}")
            raise RuntimeError(f"OCR识别失败: {str(e)}") from e
    
    def get_status(self) -> dict:
        """获取OCR服务状态"""
        from core.config import settings
        return {
            "is_loaded": self.is_loaded,
            "model_available": self.model is not None,
            "enabled": settings.OCR_ENABLED
        }


# 全局OCR服务实例
ocr_service = OCRService()