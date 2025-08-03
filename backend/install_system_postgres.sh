#!/bin/bash
# 系统 PostgreSQL 安装和配置脚本

set -e

echo "🐘 PostgreSQL 系统安装脚本"
echo "=========================="

# 检查是否为 Ubuntu/Debian
if ! command -v apt >/dev/null 2>&1; then
    echo "❌ 此脚本仅支持 Ubuntu/Debian 系统"
    exit 1
fi

echo "📦 安装 PostgreSQL..."
echo "需要管理员权限，请输入密码："

# 更新包列表
sudo apt update

# 安装 PostgreSQL
sudo apt install -y postgresql postgresql-contrib

# 启动并启用 PostgreSQL 服务
sudo systemctl start postgresql
sudo systemctl enable postgresql

echo "✅ PostgreSQL 安装完成"

# 配置数据库
echo "🔧 配置数据库..."

# 创建数据库和用户
sudo -u postgres psql << EOF
-- 创建数据库
CREATE DATABASE delivery_receipt;

-- 创建用户（如果不存在）
DO \$\$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_user WHERE usename = 'postgres') THEN
        CREATE USER postgres WITH PASSWORD 'postgres';
    END IF;
END
\$\$;

-- 授予权限
GRANT ALL PRIVILEGES ON DATABASE delivery_receipt TO postgres;

-- 显示数据库信息
\l delivery_receipt
EOF

echo "✅ 数据库配置完成"

# 测试连接
echo "🔍 测试数据库连接..."
if sudo -u postgres psql -d delivery_receipt -c "SELECT version();" >/dev/null 2>&1; then
    echo "✅ PostgreSQL 连接测试成功"
else
    echo "❌ PostgreSQL 连接测试失败"
    exit 1
fi

# 配置 PostgreSQL 允许本地连接
echo "🔧 配置 PostgreSQL 认证..."

# 备份原始配置
sudo cp /etc/postgresql/*/main/pg_hba.conf /etc/postgresql/*/main/pg_hba.conf.backup

# 修改认证方式（允许密码认证）
sudo sed -i 's/local   all             all                                     peer/local   all             all                                     md5/' /etc/postgresql/*/main/pg_hba.conf

# 重启 PostgreSQL 服务
sudo systemctl restart postgresql

echo "✅ PostgreSQL 配置完成"

# 验证应用程序连接
echo "🧪 验证应用程序数据库连接..."
cd /home/rory/final_SDHZ/backend

if [ -d "venv" ]; then
    source venv/bin/activate
    if python test_postgres_connection.py; then
        echo "✅ 应用程序数据库连接成功"
    else
        echo "⚠️  应用程序连接失败，请检查配置"
    fi
else
    echo "⚠️  虚拟环境不存在，请先激活虚拟环境再测试"
fi

echo ""
echo "🎉 PostgreSQL 系统安装完成！"
echo ""
echo "下一步:"
echo "1. 激活虚拟环境: source venv/bin/activate"
echo "2. 测试连接: python test_postgres_connection.py"
echo "3. 初始化数据库: python init_db.py"
echo "4. 迁移数据: python scripts/migrate_to_postgres.py --sqlite-path ./delivery_receipt.db"
echo ""
echo "PostgreSQL 服务管理："
echo "- 启动: sudo systemctl start postgresql"
echo "- 停止: sudo systemctl stop postgresql"
echo "- 重启: sudo systemctl restart postgresql"
echo "- 状态: sudo systemctl status postgresql"