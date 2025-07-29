from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.services.user import UserService

router = APIRouter()


@router.get("/me")
async def get_current_user(
    db: Session = Depends(get_db)
):
    """
    获取当前用户信息
    """
    # TODO: 实现获取当前用户逻辑
    pass


@router.get("/")
async def get_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    获取用户列表
    """
    user_service = UserService(db)
    users = user_service.get_users(skip=skip, limit=limit)
    return users


@router.get("/{user_id}")
async def get_user(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    获取指定用户信息
    """
    user_service = UserService(db)
    user = user_service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return user