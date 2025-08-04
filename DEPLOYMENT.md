# SDHZ 快递管理系统部署指南

## 系统要求

### 硬件要求
- **CPU**: 4核心或以上
- **内存**: 8GB RAM 或以上
- **存储**: 50GB 可用磁盘空间
- **网络**: 稳定的互联网连接

### 软件要求
- **操作系统**: Linux (Ubuntu 20.04+, CentOS 8+, Debian 11+)
- **Docker**: 24.0+
- **Docker Compose**: 2.20+

## 快速部署

### 1. 克隆项目
```bash
git clone <repository-url>
cd final_SDHZ
```

### 2. 环境配置
```bash
# 复制环境变量模板
cp backend/.env.example backend/.env

# 编辑环境变量
nano backend/.env
```

### 3. 启动服务
```bash
# 构建并启动所有服务
docker compose up -d

# 查看服务状态
docker compose ps

# 查看日志
docker compose logs -f
```

### 4. 数据库初始化
```bash
# 执行数据库迁移
docker compose exec backend alembic upgrade head

# 创建管理员用户
docker compose exec backend python create_admin_user.py
```

## 服务说明

### 核心服务
- **Frontend** (端口 80): Vue.js 前端应用
- **Backend** (端口 8000): FastAPI 后端服务
- **PostgreSQL** (端口 5432): 主数据库
- **Redis** (端口 6379): 缓存和消息队列

### 异步任务服务
- **Celery Worker**: 异步任务处理器
- **Celery Beat**: 定时任务调度器
- **Flower** (端口 5555): 任务监控面板

## 性能优化

### 数据库优化
- 使用 PostgreSQL 16 with 优化配置
- 启用 pg_stat_statements 扩展
- 配置连接池和缓存

### Redis 优化
- 内存限制: 256MB
- LRU 缓存策略
- AOF 持久化

### 应用优化
- 多阶段 Docker 构建
- 资源限制和预留
- 健康检查机制

## 监控和维护

### 健康检查
所有服务都配置了健康检查：
```bash
# 检查所有服务健康状态
docker compose ps
```

### 日志管理
```bash
# 查看特定服务日志
docker compose logs backend
docker compose logs celery-worker

# 实时日志
docker compose logs -f --tail=100
```

### 数据备份
```bash
# 备份数据库
docker compose exec postgres pg_dump -U postgres delivery_receipt > backup.sql

# 备份 Redis
docker compose exec redis redis-cli --rdb /data/dump.rdb
```

## 扩展部署

### 负载均衡
可以通过增加 backend 和 celery-worker 副本来提高性能：

```yaml
backend:
  deploy:
    replicas: 3
    
celery-worker:
  deploy:
    replicas: 2
```

### 外部数据库
生产环境建议使用外部数据库服务：

```yaml
# 注释掉 postgres 服务，修改环境变量
environment:
  - POSTGRES_SERVER=your-external-db-host
  - POSTGRES_USER=your-db-user
  - POSTGRES_PASSWORD=your-db-password
```

## 安全配置

### 防火墙设置
```bash
# 只开放必要端口
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw allow 22/tcp    # SSH
```

### SSL 证书
使用 Nginx 反向代理和 Let's Encrypt：

```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://localhost:80;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 故障排除

### 常见问题

1. **容器启动失败**
   ```bash
   # 检查日志
   docker compose logs <service-name>
   
   # 重新构建
   docker compose build --no-cache
   ```

2. **数据库连接失败**
   ```bash
   # 检查数据库状态
   docker compose exec postgres pg_isready -U postgres
   
   # 检查网络连接
   docker compose exec backend nc -zv postgres 5432
   ```

3. **内存不足**
   ```bash
   # 调整内存限制
   # 编辑 docker-compose.yml 中的 deploy.resources
   ```

### 性能监控
- **Flower**: http://localhost:5555 (用户名: admin, 密码: admin123)
- **PostgreSQL 统计**: 查询 pg_stat_statements 视图
- **系统资源**: 使用 `docker stats` 命令

## 更新部署

```bash
# 1. 拉取最新代码
git pull origin main

# 2. 停止服务
docker compose down

# 3. 重新构建
docker compose build

# 4. 启动服务
docker compose up -d

# 5. 运行迁移（如果有）
docker compose exec backend alembic upgrade head
```

## 联系支持

如果遇到部署问题，请提供以下信息：
- 操作系统版本
- Docker 和 Docker Compose 版本
- 错误日志
- 系统资源使用情况

---

**注意**: 本文档基于 Docker Compose 部署方式。生产环境部署请根据实际需求调整配置。