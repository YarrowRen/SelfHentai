import asyncio

# 保存事件循环为全局变量
main_event_loop = asyncio.get_event_loop()

from api import websocket  # 导入 websocket 路由
from api import gallery, root
from core.config import settings
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()


# 添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载路由
app.include_router(root.router)
app.include_router(gallery.router, prefix="/api/gallery", tags=["Gallery"])
app.include_router(websocket.router)
