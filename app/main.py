import asyncio
import os
from contextlib import asynccontextmanager

# 保存事件循环为全局变量
main_event_loop = asyncio.get_event_loop()

from api import websocket  # 导入 websocket 路由
from api import gallery, root
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


# 创建 lifespan 上下文管理器
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时执行：确保 data 和 logs 文件夹存在
    for folder in ["data", "logs"]:
        if not os.path.exists(folder):
            os.makedirs(folder)
        else:
            continue

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
app.include_router(websocket.router)
