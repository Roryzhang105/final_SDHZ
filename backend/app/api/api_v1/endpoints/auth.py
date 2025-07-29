from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.auth import AuthService

router = APIRouter()


@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    用户登录
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


@router.post("/register")
async def register(
    username: str,
    email: str,
    password: str,
    full_name: str = None,
    db: Session = Depends(get_db)
):
    """
    用户注册
    """
    auth_service = AuthService(db)
    user = auth_service.create_user(
        username=username,
        email=email,
        password=password,
        full_name=full_name
    )
    return {"message": "用户注册成功", "user_id": user.id}