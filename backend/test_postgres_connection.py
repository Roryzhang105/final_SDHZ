#!/usr/bin/env python3
"""
PostgreSQL 连接测试脚本
"""
import sys
from app.core.config import settings
from app.core.database import engine
from sqlalchemy import text

def test_connection():
    """测试PostgreSQL连接"""
    print(f"🔍 测试数据库连接...")
    print(f"数据库 URL: {settings.DATABASE_URL}")
    
    try:
        with engine.connect() as conn:
            # 测试基本连接
            result = conn.execute(text('SELECT version()'))
            version = result.scalar()
            print(f"✅ PostgreSQL 连接成功")
            print(f"数据库版本: {version}")
            
            # 测试数据库是否存在
            try:
                conn.execute(text('SELECT 1'))
                print(f"✅ 数据库 '{settings.POSTGRES_DB}' 可访问")
            except Exception as e:
                print(f"⚠️  数据库访问警告: {e}")
            
            return True
            
    except Exception as e:
        print(f"❌ PostgreSQL 连接失败: {e}")
        print(f"")
        print(f"可能的原因:")
        print(f"1. PostgreSQL 服务未运行")
        print(f"2. 连接参数不正确")
        print(f"3. 防火墙阻止连接")
        print(f"4. 数据库 '{settings.POSTGRES_DB}' 不存在")
        print(f"")
        print(f"解决方案:")
        print(f"1. 运行: docker-compose up -d postgres")
        print(f"2. 或运行: ./start_postgres.sh")
        print(f"3. 或参考 POSTGRESQL_MIGRATION.md")
        
        return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)