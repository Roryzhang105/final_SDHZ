#!/usr/bin/env python3
"""
验证管理员账号脚本
"""
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.services.auth import AuthService
from app.models.user import User

def verify_admin_user():
    """验证管理员用户"""
    db = SessionLocal()
    try:
        # 查找管理员用户
        admin_user = db.query(User).filter(User.username == "admin").first()
        
        if not admin_user:
            print("❌ 管理员账号不存在！")
            return False
        
        print("✅ 管理员账号信息:")
        print(f"用户ID: {admin_user.id}")
        print(f"用户名: {admin_user.username}")
        print(f"邮箱: {admin_user.email}")
        print(f"全名: {admin_user.full_name}")
        print(f"是否激活: {admin_user.is_active}")
        print(f"是否为超级用户: {admin_user.is_superuser}")
        print(f"创建时间: {admin_user.created_at}")
        print(f"更新时间: {admin_user.updated_at}")
        
        # 测试密码验证
        auth_service = AuthService(db)
        password_valid = auth_service.verify_password("ww731226", admin_user.hashed_password)
        print(f"密码验证: {'✅ 正确' if password_valid else '❌ 错误'}")
        
        # 测试认证
        authenticated_user = auth_service.authenticate_user("admin", "ww731226")
        print(f"完整认证: {'✅ 成功' if authenticated_user else '❌ 失败'}")
        
        return True
        
    except Exception as e:
        print(f"验证失败: {e}")
        return False
    finally:
        db.close()

def main():
    """主函数"""
    print("=== 验证管理员账号 ===")
    verify_admin_user()

if __name__ == "__main__":
    main()