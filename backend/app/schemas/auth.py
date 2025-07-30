from pydantic import BaseModel, EmailStr
from typing import Optional


class LoginRequest(BaseModel):
    """登录请求模型"""
    username: str
    password: str


class LoginResponse(BaseModel):
    """登录响应模型"""
    access_token: str
    token_type: str = "bearer"
    user: "UserResponse"


class RegisterRequest(BaseModel):
    """注册请求模型"""
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None


class UserResponse(BaseModel):
    """用户响应模型"""
    id: int
    username: str
    email: str
    full_name: Optional[str] = None
    is_active: bool
    is_superuser: bool
    
    class Config:
        from_attributes = True


class ApiResponse(BaseModel):
    """统一API响应格式"""
    success: bool = True
    message: str = "操作成功"
    data: Optional[dict] = None
    
    
# 更新前向引用
LoginResponse.model_rebuild()