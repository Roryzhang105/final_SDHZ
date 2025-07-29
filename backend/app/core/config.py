from typing import Any, Dict, List, Optional, Union
from pydantic import field_validator, ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = ConfigDict(
        case_sensitive=True,
        env_file=".env",
        env_file_encoding="utf-8"
    )
    
    PROJECT_NAME: str = "送达回证自动化处理系统"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # CORS origins - 简化处理
    BACKEND_CORS_ORIGINS: str = ""

    # 数据库配置 - 使用SQLite
    DATABASE_URL: str = "sqlite:///./delivery_receipt.db"

    # Redis配置
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Celery配置
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    
    # JWT配置
    SECRET_KEY: str = "delivery-receipt-default-secret-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # 文件上传配置
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    
    # 物流查询配置
    KUAIDI_API_KEY: str = ""
    KUAIDI_API_SECRET: str = ""
    
    # 微信相关配置
    WECHAT_APP_ID: str = ""
    WECHAT_APP_SECRET: str = ""

    def get_cors_origins(self) -> List[str]:
        """获取CORS源列表"""
        if not self.BACKEND_CORS_ORIGINS:
            return []
        return [origin.strip() for origin in self.BACKEND_CORS_ORIGINS.split(",")]


settings = Settings()