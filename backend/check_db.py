#!/usr/bin/env python3
"""
检查数据库用户表
"""
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.user import User

def check_users():
    """检查用户表"""
    db = SessionLocal()
    try:
        users = db.query(User).all()
        
        print("=== 数据库用户列表 ===")
        print(f"总用户数: {len(users)}")
        print()
        
        for user in users:
            print(f"用户ID: {user.id}")
            print(f"用户名: {user.username}")
            print(f"邮箱: {user.email}")
            print(f"全名: {user.full_name}")
            print(f"是否激活: {user.is_active}")
            print(f"是否为超级用户: {user.is_superuser}")
            print(f"创建时间: {user.created_at}")
            print("-" * 40)
        
    except Exception as e:
        print(f"查询失败: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_users()