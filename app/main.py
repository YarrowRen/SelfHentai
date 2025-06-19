from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api import gallery, root
from core.config import settings

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
