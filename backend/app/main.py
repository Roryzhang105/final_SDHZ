from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os

from app.core.config import settings
from app.core.database import engine
from app.models.base import Base
from app.api.api_v1.api import api_router
# 导入所有模型以确保表被创建
from app.models import Task, User, DeliveryReceipt, Courier, TrackingInfo, RecognitionTask, RecognitionResult, CourierPattern


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时创建数据库表
    Base.metadata.create_all(bind=engine)
    # 确保上传目录存在
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    yield
    # 关闭时清理资源


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="送达回证自动化处理系统",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# 设置CORS - 优化配置以正确处理预检请求
cors_origins = settings.get_cors_origins()
if not cors_origins:
    # 开发模式下的默认配置，包含前端开发服务器地址
    cors_origins = [
        "http://localhost:5173",  # Vite默认端口
        "http://127.0.0.1:5173",
        "http://localhost:3000",  # 备用端口
        "http://127.0.0.1:3000",
        "http://localhost:8080",  # 后端自身
        "http://127.0.0.1:8080"
    ]

# 开发模式：允许所有来源，优化frp环境支持
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 开发模式下允许所有来源
    allow_credentials=False,  # 当允许所有来源时，必须设为False
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH", "HEAD"],
    allow_headers=[
        "*",
        "Content-Type",
        "Authorization", 
        "Accept",
        "Accept-Language",
        "Accept-Encoding",
        "Connection",
        "User-Agent",
        "Cache-Control",
        "Origin",
        "Referer",
        "X-Requested-With",
        "X-Forwarded-For",
        "X-Forwarded-Proto",
        "X-Real-IP"
    ],
    expose_headers=["*"],
    max_age=3600,
)

# 配置静态文件服务
uploads_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "uploads"))
os.makedirs(uploads_dir, exist_ok=True)
app.mount("/static/uploads", StaticFiles(directory=uploads_dir), name="uploads")

# 配置物流截图静态文件服务
tracking_screenshots_dir = os.path.join(uploads_dir, "tracking_screenshots")
os.makedirs(tracking_screenshots_dir, exist_ok=True)
app.mount("/static/tracking_screenshots", StaticFiles(directory=tracking_screenshots_dir), name="tracking_screenshots")

# 配置物流HTML静态文件服务
tracking_html_dir = os.path.join(uploads_dir, "tracking_html")
os.makedirs(tracking_html_dir, exist_ok=True)
app.mount("/static/tracking_html", StaticFiles(directory=tracking_html_dir), name="tracking_html")

# 配置送达回证文档静态文件服务
documents_dir = os.path.join(uploads_dir, "delivery_receipts")
os.makedirs(documents_dir, exist_ok=True)
app.mount("/static/documents", StaticFiles(directory=documents_dir), name="documents")

# 注册API路由
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
async def root():
    return {"message": "送达回证自动化处理系统 API"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.get("/debug/connection")
async def debug_connection():
    """调试连接端点，返回请求信息"""
    from fastapi import Request
    
    return {
        "status": "connected",
        "message": "后端连接正常",
        "timestamp": __import__('datetime').datetime.now().isoformat(),
        "server_info": {
            "host": "0.0.0.0",
            "port": 8000,
            "cors_enabled": True
        }
    }


@app.options("/api/v1/auth/login")
async def options_login():
    """处理登录端点的OPTIONS预检请求"""
    return {"message": "OPTIONS OK"}