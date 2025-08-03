# PostgreSQL 数据库迁移指南

## 概述

本项目已完成 PostgreSQL 迁移配置，包含完整的数据迁移脚本和Docker部署支持。

## 1. 启动 PostgreSQL 服务

### 方式一：使用 Docker Compose (推荐)

```bash
# 在 backend 目录下
cd /home/rory/final_SDHZ/backend

# 启动 PostgreSQL 和 Redis 服务
docker-compose up -d postgres redis

# 检查服务状态
docker-compose ps

# 查看日志
docker-compose logs postgres
```

### 方式二：系统安装 PostgreSQL

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y postgresql postgresql-contrib

# 启动服务
sudo systemctl start postgresql
sudo systemctl enable postgresql

# 创建数据库和用户
sudo -u postgres psql
CREATE DATABASE delivery_receipt;
CREATE USER postgres WITH PASSWORD 'postgres';
GRANT ALL PRIVILEGES ON DATABASE delivery_receipt TO postgres;
\q
```

### 方式三：使用云数据库

更新 `.env` 文件中的数据库连接信息：

```env
POSTGRES_SERVER=your-cloud-db-host
POSTGRES_USER=your-username
POSTGRES_PASSWORD=your-password
POSTGRES_DB=delivery_receipt
POSTGRES_PORT=5432
```

## 2. 数据迁移

### 自动迁移（推荐）

```bash
cd /home/rory/final_SDHZ/backend
source venv/bin/activate

# 从 SQLite 迁移到 PostgreSQL
python scripts/migrate_to_postgres.py --sqlite-path ./delivery_receipt.db

# 如果确认迁移，使用 --force 跳过确认
python scripts/migrate_to_postgres.py --sqlite-path ./delivery_receipt.db --force
```

### 手动迁移步骤

1. **备份现有数据**：
   ```bash
   cp delivery_receipt.db delivery_receipt_backup_$(date +%Y%m%d_%H%M%S).db
   ```

2. **初始化 PostgreSQL 数据库**：
   ```bash
   python init_db.py
   ```

3. **验证连接**：
   ```bash
   python -c "
   from app.core.config import settings
   from app.core.database import engine
   from sqlalchemy import text
   with engine.connect() as conn:
       result = conn.execute(text('SELECT version()'))
       print('PostgreSQL版本:', result.scalar())
   "
   ```

## 3. 验证迁移

### 检查数据完整性

```bash
# 激活虚拟环境
source venv/bin/activate

# 运行验证脚本
python -c "
from app.core.database import SessionLocal
from app.models import User, DeliveryReceipt, Courier, TrackingInfo

db = SessionLocal()
print('用户数量:', db.query(User).count())
print('送达回证数量:', db.query(DeliveryReceipt).count())
print('快递公司数量:', db.query(Courier).count())
print('追踪信息数量:', db.query(TrackingInfo).count())
db.close()
"
```

### 测试应用程序

```bash
# 启动应用程序
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 在另一个终端测试API
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/auth/test
```

## 4. 生产部署

### 使用 Docker Compose

```bash
# 启动完整服务栈
docker-compose up -d

# 检查所有服务状态
docker-compose ps

# 查看应用日志
docker-compose logs app
```

### 环境变量检查

确保 `.env` 文件包含正确的配置：

```env
# PostgreSQL Configuration
POSTGRES_SERVER=localhost
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=delivery_receipt
POSTGRES_PORT=5432

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Application Configuration
SECRET_KEY=your-production-secret-key
BACKEND_CORS_ORIGINS=http://localhost:3000,http://your-frontend-domain.com
```

## 5. 故障排除

### 常见问题

1. **连接被拒绝**：
   - 检查 PostgreSQL 服务是否运行
   - 验证端口 5432 是否开放
   - 确认防火墙设置

2. **认证失败**：
   - 验证用户名密码
   - 检查 PostgreSQL 的 pg_hba.conf 配置

3. **迁移数据不完整**：
   - 检查 migration.log 日志文件
   - 手动验证数据一致性
   - 重新运行迁移脚本

### 回滚到 SQLite

如果需要回滚到 SQLite：

```bash
# 修改 .env 文件
# 注释 PostgreSQL 配置，使用 SQLite
# DATABASE_URL=sqlite:///./delivery_receipt.db

# 重启应用程序
```

## 6. 监控和维护

### 数据库监控

```bash
# PostgreSQL 连接数
docker-compose exec postgres psql -U postgres -d delivery_receipt -c "SELECT count(*) FROM pg_stat_activity;"

# 数据库大小
docker-compose exec postgres psql -U postgres -d delivery_receipt -c "SELECT pg_size_pretty(pg_database_size('delivery_receipt'));"
```

### 备份策略

```bash
# 定期备份
docker-compose exec postgres pg_dump -U postgres delivery_receipt > backup_$(date +%Y%m%d).sql

# 恢复备份
docker-compose exec -T postgres psql -U postgres delivery_receipt < backup_20240101.sql
```

## 完成！

数据库迁移配置已完成。项目现在支持 PostgreSQL 作为主数据库，具备完整的迁移工具和部署文档。