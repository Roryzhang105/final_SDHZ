#!/bin/bash
set -e

# PostgreSQL 数据库启动和迁移脚本

echo "🚀 PostgreSQL 数据库迁移启动脚本"
echo "=================================="

# 检查是否在正确的目录
if [ ! -f "requirements.txt" ]; then
    echo "❌ 错误：请在 backend 目录下运行此脚本"
    exit 1
fi

# 激活虚拟环境
if [ -d "venv" ]; then
    echo "📦 激活虚拟环境..."
    source venv/bin/activate
else
    echo "❌ 错误：虚拟环境不存在，请先创建虚拟环境"
    echo "运行：python -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# 检查 Docker 是否可用
if command -v docker-compose >/dev/null 2>&1; then
    echo "🐳 检测到 Docker Compose，启动 PostgreSQL 容器..."
    docker-compose up -d postgres redis
    echo "⏳ 等待 PostgreSQL 启动..."
    sleep 10
elif command -v docker >/dev/null 2>&1; then
    echo "🐳 启动 PostgreSQL Docker 容器..."
    docker run -d --name postgres-delivery \
        -e POSTGRES_DB=delivery_receipt \
        -e POSTGRES_USER=postgres \
        -e POSTGRES_PASSWORD=postgres \
        -p 5432:5432 \
        postgres:15-alpine
    echo "⏳ 等待 PostgreSQL 启动..."
    sleep 15
else
    echo "⚠️  未检测到 Docker，请确保 PostgreSQL 服务正在运行"
    echo "或参考 POSTGRESQL_MIGRATION.md 手动安装 PostgreSQL"
fi

# 测试数据库连接
echo "🔍 测试数据库连接..."
python -c "
import sys
from app.core.config import settings
from app.core.database import engine
from sqlalchemy import text

try:
    with engine.connect() as conn:
        result = conn.execute(text('SELECT version()'))
        print('✅ PostgreSQL 连接成功')
        print(f'数据库版本: {result.scalar()[:50]}...')
except Exception as e:
    print(f'❌ 数据库连接失败: {e}')
    print('请检查 PostgreSQL 服务是否运行，或参考 POSTGRESQL_MIGRATION.md')
    sys.exit(1)
"

# 检查是否存在 SQLite 数据库需要迁移
if [ -f "delivery_receipt.db" ]; then
    echo ""
    echo "📋 发现现有 SQLite 数据库"
    echo "是否要将数据迁移到 PostgreSQL？"
    echo "1) 是，立即迁移"
    echo "2) 否，仅初始化空数据库"
    echo "3) 取消操作"
    read -p "请选择 (1-3): " choice
    
    case $choice in
        1)
            echo "🔄 开始数据迁移..."
            python scripts/migrate_to_postgres.py --sqlite-path ./delivery_receipt.db --force
            if [ $? -eq 0 ]; then
                echo "✅ 数据迁移完成"
            else
                echo "❌ 数据迁移失败，请检查日志"
                exit 1
            fi
            ;;
        2)
            echo "🏗️  初始化空的 PostgreSQL 数据库..."
            python init_db.py
            ;;
        3)
            echo "❌ 操作已取消"
            exit 0
            ;;
        *)
            echo "❌ 无效选择"
            exit 1
            ;;
    esac
else
    echo "🏗️  初始化 PostgreSQL 数据库..."
    python init_db.py
fi

# 验证迁移结果
echo "🔍 验证数据库状态..."
python -c "
from app.core.database import SessionLocal
from app.models import User, DeliveryReceipt, Courier, TrackingInfo

db = SessionLocal()
try:
    user_count = db.query(User).count()
    receipt_count = db.query(DeliveryReceipt).count()
    courier_count = db.query(Courier).count()
    tracking_count = db.query(TrackingInfo).count()
    
    print(f'📊 数据库统计:')
    print(f'   用户数量: {user_count}')
    print(f'   送达回证数量: {receipt_count}')
    print(f'   快递公司数量: {courier_count}')
    print(f'   追踪信息数量: {tracking_count}')
    
    if courier_count > 0:
        print('✅ 数据库初始化完成')
    else:
        print('⚠️  数据库初始化可能不完整')
        
except Exception as e:
    print(f'❌ 验证数据库时出错: {e}')
finally:
    db.close()
"

echo ""
echo "🎉 PostgreSQL 迁移完成！"
echo ""
echo "下一步："
echo "1. 启动应用程序："
echo "   python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
echo ""
echo "2. 或使用 Docker Compose 启动完整服务："
echo "   docker-compose up -d"
echo ""
echo "3. 测试应用程序："
echo "   curl http://localhost:8000/health"
echo ""
echo "如有问题，请参考 POSTGRESQL_MIGRATION.md 文档"