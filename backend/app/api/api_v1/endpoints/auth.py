from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError, jwt

from app.core.database import get_db
from app.services.auth import AuthService
from app.schemas.auth import LoginRequest, LoginResponse, RegisterRequest, UserResponse, ApiResponse
from app.core.config import settings
from app.models.user import User

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    """获取当前登录用户"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    auth_service = AuthService(db)
    user = auth_service.get_user_by_username(username)
    if user is None:
        raise credentials_exception
    return user


@router.post("/login", response_model=ApiResponse)
async def login_json(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    用户登录 (JSON格式)
    """
    auth_service = AuthService(db)
    user = auth_service.authenticate_user(login_data.username, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = auth_service.create_access_token(data={"sub": user.username})
    user_response = UserResponse.from_orm(user)
    
    return ApiResponse(
        success=True,
        message="登录成功",
        data={
            "access_token": access_token,
            "token_type": "bearer",
            "user": user_response.dict()
        }
    )


@router.post("/login-form")
async def login_form(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    用户登录 (表单格式，保持向后兼容)
    """
    auth_service = AuthService(db)
    user = auth_service.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = auth_service.create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/register", response_model=ApiResponse)
async def register(
    register_data: RegisterRequest,
    db: Session = Depends(get_db)
):
    """
    用户注册
    """
    auth_service = AuthService(db)
    
    # 检查用户名是否已存在
    existing_user = auth_service.get_user_by_username(register_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )
    
    try:
        user = auth_service.create_user(
            username=register_data.username,
            email=register_data.email,
            password=register_data.password,
            full_name=register_data.full_name
        )
        user_response = UserResponse.from_orm(user)
        
        return ApiResponse(
            success=True,
            message="用户注册成功",
            data=user_response.dict()
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"注册失败: {str(e)}"
        )


@router.get("/me", response_model=ApiResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    获取当前登录用户信息
    """
    user_response = UserResponse.from_orm(current_user)
    return ApiResponse(
        success=True,
        message="获取用户信息成功",
        data=user_response.dict()
    )


@router.post("/logout", response_model=ApiResponse)
async def logout(
    current_user: User = Depends(get_current_user)
):
    """
    用户退出登录
    """
    # 在实际应用中，这里可以将token加入黑名单
    # 目前只是返回成功响应
    return ApiResponse(
        success=True,
        message="退出登录成功"
    )


@router.post("/refresh", response_model=ApiResponse)
async def refresh_token(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    刷新访问令牌
    """
    auth_service = AuthService(db)
    access_token = auth_service.create_access_token(data={"sub": current_user.username})
    
    return ApiResponse(
        success=True,
        message="令牌刷新成功",
        data={
            "access_token": access_token,
            "token_type": "bearer"
        }
    )