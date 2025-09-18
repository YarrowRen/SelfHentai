import asyncio
import os
from contextlib import asynccontextmanager

# 保存事件循环为全局变量
main_event_loop = asyncio.get_event_loop()

from api import websocket  # 导入 websocket 路由
from api import gallery, root, settings
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.logger import get_logger

logger = get_logger(__name__)


# 创建 lifespan 上下文管理器
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时执行：确保 data 和 logs 文件夹存在
    for folder in ["data", "logs"]:
        if not os.path.exists(folder):
            os.makedirs(folder)
        else:
            continue
    
    # 初始化 OCR 服务（基于配置决定是否启用）
    try:
        from core.config import settings
        if settings.OCR_ENABLED:
            from services.ocr_service import ocr_service
            logger.info("正在加载 manga-ocr 模型，这可能需要一些时间...")
            ocr_service.load_model()
            logger.info("manga-ocr 模型加载完成！")
        else:
            logger.info("OCR 服务已禁用（OCR_ENABLED=false），跳过模型加载")
    except Exception as e:
        logger.error(f"OCR 模型加载失败: {str(e)}")
        logger.warning("OCR 功能将不可用，但应用会继续运行")
    
    # 初始化翻译服务
    try:
        from services.translation_service import translation_service
        logger.info("正在初始化 AI 翻译服务...")
        success = translation_service.initialize()
        if success:
            logger.info("AI 翻译服务初始化完成！")
        else:
            logger.error("AI 翻译服务初始化失败，请检查翻译服务配置")
    except Exception as e:
        logger.error(f"翻译服务初始化失败: {str(e)}")
        logger.warning("翻译功能将不可用，但应用会继续运行")

    yield  # 继续运行应用


app = FastAPI(lifespan=lifespan)


# 添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载路由
app.include_router(root.router)
app.include_router(gallery.router, prefix="/api/gallery", tags=["Gallery"])
app.include_router(settings.router, prefix="/api/settings", tags=["Settings"])
app.include_router(websocket.router)
