#!/usr/bin/env python3
"""
创建默认管理员用户脚本
Usage: python create_admin_user.py
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine
from app.models.user import User
from app.services.auth import AuthService
from app.models.base import Base

# 导入所有模型以确保它们被注册到SQLAlchemy
from app.models.delivery_receipt import DeliveryReceipt
from app.models.courier import Courier
from app.models.tracking import TrackingInfo
from app.models.recognition import RecognitionTask, RecognitionResult, CourierPattern
from app.models.case_info import CaseInfo

def create_admin_user():
    """创建默认管理员用户"""
    
    # 确保数据库表已创建
    print("正在创建数据库表...")
    Base.metadata.create_all(bind=engine)
    print("数据库表创建完成")
    
    # 创建数据库会话
    db = SessionLocal()
    
    try:
        auth_service = AuthService(db)
        
        # 检查是否已存在admin用户
        existing_admin = auth_service.get_user_by_username("admin")
        if existing_admin:
            print("管理员用户 'admin' 已存在")
            print(f"用户信息:")
            print(f"  ID: {existing_admin.id}")
            print(f"  用户名: {existing_admin.username}")
            print(f"  邮箱: {existing_admin.email}")
            print(f"  全名: {existing_admin.full_name}")
            print(f"  激活状态: {existing_admin.is_active}")
            print(f"  超级用户: {existing_admin.is_superuser}")
            return existing_admin
        
        # 创建管理员用户
        print("正在创建管理员用户...")
        admin_user = auth_service.create_user(
            username="admin",
            email="admin@example.com",
            password="admin123",
            full_name="系统管理员"
        )
        
        # 设置为超级用户
        admin_user.is_superuser = True
        admin_user.is_active = True
        db.commit()
        db.refresh(admin_user)
        
        print("管理员用户创建成功!")
        print(f"用户信息:")
        print(f"  ID: {admin_user.id}")
        print(f"  用户名: {admin_user.username}")
        print(f"  邮箱: {admin_user.email}")
        print(f"  全名: {admin_user.full_name}")
        print(f"  激活状态: {admin_user.is_active}")
        print(f"  超级用户: {admin_user.is_superuser}")
        print(f"  默认密码: admin123")
        print("")
        print("请使用以下凭据登录系统:")
        print("用户名: admin")
        print("密码: admin123")
        print("")
        print("⚠️  注意: 请在首次登录后修改默认密码!")
        
        return admin_user
        
    except Exception as e:
        print(f"创建管理员用户失败: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

def main():
    """主函数"""
    print("=" * 50)
    print("送达回证系统 - 管理员用户创建工具")
    print("=" * 50)
    
    try:
        admin_user = create_admin_user()
        print("=" * 50)
        print("✅ 管理员用户创建完成")
        print("现在可以使用 admin/admin123 登录系统")
        print("=" * 50)
        
    except Exception as e:
        print("=" * 50)
        print(f"❌ 操作失败: {str(e)}")
        print("=" * 50)
        sys.exit(1)

if __name__ == "__main__":
    main()