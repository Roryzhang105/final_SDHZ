#!/usr/bin/env python3
"""
创建管理员账号脚本
"""
import sys
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.services.auth import AuthService
from app.models.user import User

def create_admin_user(username: str, password: str, email: str = None):
    """创建管理员用户"""
    db = SessionLocal()
    try:
        # 检查用户是否已存在
        existing_user = db.query(User).filter(User.username == username).first()
        if existing_user:
            print(f"用户 '{username}' 已存在！")
            return False
        
        # 如果没有提供邮箱，使用默认邮箱
        if not email:
            email = f"{username}@admin.local"
        
        # 创建认证服务实例
        auth_service = AuthService(db)
        
        # 创建管理员用户
        hashed_password = auth_service.get_password_hash(password)
        admin_user = User(
            username=username,
            email=email,
            hashed_password=hashed_password,
            full_name="系统管理员",
            is_active=True,
            is_superuser=True  # 设置为超级用户
        )
        
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        print(f"管理员账号创建成功！")
        print(f"用户名: {admin_user.username}")
        print(f"邮箱: {admin_user.email}")
        print(f"用户ID: {admin_user.id}")
        print(f"是否为超级用户: {admin_user.is_superuser}")
        print(f"创建时间: {admin_user.created_at}")
        
        return True
        
    except Exception as e:
        print(f"创建管理员账号失败: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def main():
    """主函数"""
    print("=== 创建管理员账号 ===")
    
    # 设置管理员信息
    username = "admin"
    password = "ww731226"
    email = "admin@sdhz.local"
    
    print(f"准备创建管理员账号:")
    print(f"用户名: {username}")
    print(f"密码: {'*' * len(password)}")
    print(f"邮箱: {email}")
    print()
    
    # 创建管理员账号
    success = create_admin_user(username, password, email)
    
    if success:
        print("\n✅ 管理员账号创建成功！")
        print("现在您可以使用以下凭据登录系统:")
        print(f"用户名: {username}")
        print(f"密码: {password}")
    else:
        print("\n❌ 管理员账号创建失败！")
        sys.exit(1)

if __name__ == "__main__":
    main()