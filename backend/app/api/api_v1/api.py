from fastapi import APIRouter

from app.api.api_v1.endpoints import auth, users, delivery_receipts, tracking, upload, qr_recognition

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(users.router, prefix="/users", tags=["用户管理"])
api_router.include_router(delivery_receipts.router, prefix="/delivery-receipts", tags=["送达回证"])
api_router.include_router(tracking.router, prefix="/tracking", tags=["物流跟踪"])
api_router.include_router(upload.router, prefix="/upload", tags=["文件上传"])
api_router.include_router(qr_recognition.router, prefix="/qr", tags=["二维码识别"])