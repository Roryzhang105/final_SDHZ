# 部署指南

> **送达回证自动化处理系统** - 生产环境部署最佳实践

## 📋 概述

本指南详细介绍了送达回证自动化处理系统在不同环境下的部署方案，包括开发环境、测试环境和生产环境的配置。

## 🎯 部署架构

### 推荐架构
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   负载均衡器     │    │   Web服务器     │    │   数据库服务器   │
│   Nginx/ALB     │    │   Docker Host   │    │   PostgreSQL    │
│   SSL终止       │────│   + Redis       │────│   + 备份        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                       ┌─────────────────┐
                       │   文件存储      │
                       │   NFS/S3       │
                       └─────────────────┘
```

## 🐳 Docker部署 (推荐)

### 生产环境 Docker Compose

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  # Nginx反向代理
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
      - static_files:/usr/share/nginx/html/static
    depends_on:
      - frontend
      - backend
    restart: unless-stopped

  # 前端服务
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.prod
    environment:
      - NODE_ENV=production
      - VITE_API_BASE_URL=https://yourdomain.com/api
    volumes:
      - static_files:/app/dist
    restart: unless-stopped

  # 后端API服务
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    environment:
      - DATABASE_URL=postgresql://user:password@postgres:5432/delivery_receipt
      - REDIS_URL=redis://redis:6379/0
      - SECRET_KEY=${SECRET_KEY}
      - ENVIRONMENT=production
    volumes:
      - uploads_data:/app/uploads
    depends_on:
      - postgres
      - redis
    restart: unless-stopped
    deploy:
      replicas: 2
      resources:
        limits:
          memory: 1G
        reservations:
          memory: 512M

  # PostgreSQL数据库
  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=delivery_receipt
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backup:/backup
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 2G

  # Redis缓存
  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    restart: unless-stopped

  # Celery Worker
  celery-worker:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    command: celery -A app.tasks.celery_app worker --loglevel=info --concurrency=4
    environment:
      - DATABASE_URL=postgresql://user:password@postgres:5432/delivery_receipt
      - REDIS_URL=redis://redis:6379/0
      - SECRET_KEY=${SECRET_KEY}
    volumes:
      - uploads_data:/app/uploads
    depends_on:
      - postgres
      - redis
    restart: unless-stopped
    deploy:
      replicas: 2

  # Celery Beat (定时任务)
  celery-beat:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    command: celery -A app.tasks.celery_app beat --loglevel=info
    environment:
      - DATABASE_URL=postgresql://user:password@postgres:5432/delivery_receipt
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - postgres
      - redis
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
  uploads_data:
  static_files:

networks:
  default:
    driver: bridge
```

### 启动生产环境
```bash
# 1. 设置环境变量
cp .env.example .env.prod
# 编辑 .env.prod 文件

# 2. 构建并启动服务
docker-compose -f docker-compose.prod.yml up -d --build

# 3. 初始化数据库
docker-compose -f docker-compose.prod.yml exec backend python init_db.py

# 4. 创建管理员账户
docker-compose -f docker-compose.prod.yml exec backend python create_admin.py

# 5. 检查服务状态
docker-compose -f docker-compose.prod.yml ps
```

## 🔧 环境配置

### 生产环境变量 (.env.prod)
```bash
# 应用配置
PROJECT_NAME="送达回证自动化处理系统"
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=your-super-secure-secret-key-here

# 数据库配置
POSTGRES_SERVER=postgres
POSTGRES_USER=delivery_user
POSTGRES_PASSWORD=your-strong-database-password
POSTGRES_DB=delivery_receipt
DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_SERVER}:5432/${POSTGRES_DB}

# Redis配置
REDIS_PASSWORD=your-redis-password
REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
CELERY_BROKER_URL=${REDIS_URL}
CELERY_RESULT_BACKEND=${REDIS_URL}

# 安全配置
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
BACKEND_CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# 文件上传配置
MAX_UPLOAD_SIZE=20971520  # 20MB
UPLOAD_DIR=/app/uploads

# 外部服务配置
KUAIDI_API_KEY=your-kuaidi-api-key
KUAIDI_API_SECRET=your-kuaidi-api-secret

# JWT配置
ACCESS_TOKEN_EXPIRE_MINUTES=30
ALGORITHM=HS256

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=/app/logs/app.log

# 邮件配置 (可选)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_FROM=your-email@gmail.com
```

## 🌐 Nginx配置

### nginx.conf
```nginx
events {
    worker_connections 1024;
}

http {
    upstream backend {
        server backend:8000;
    }

    # 速率限制
    limit_req_zone $binary_remote_addr zone=login:10m rate=5r/m;
    limit_req_zone $binary_remote_addr zone=api:10m rate=100r/m;

    server {
        listen 80;
        server_name yourdomain.com www.yourdomain.com;
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name yourdomain.com www.yourdomain.com;

        # SSL配置
        ssl_certificate /etc/nginx/ssl/fullchain.pem;
        ssl_certificate_key /etc/nginx/ssl/privkey.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;

        # 安全头
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";

        # 文件上传大小限制
        client_max_body_size 20M;

        # 前端静态文件
        location / {
            root /usr/share/nginx/html/static;
            try_files $uri $uri/ /index.html;
            
            # 缓存静态资源
            location ~* \\.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
                expires 1y;
                add_header Cache-Control "public, immutable";
            }
        }

        # API代理
        location /api/ {
            limit_req zone=api burst=20 nodelay;
            
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # 超时配置
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
        }

        # 登录限制
        location /api/v1/auth/login {
            limit_req zone=login burst=3 nodelay;
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # 文件下载
        location /uploads/ {
            alias /app/uploads/;
            
            # 安全检查
            location ~ /uploads/.*\\.(php|jsp|asp|sh)$ {
                deny all;
            }
        }

        # 健康检查
        location /health {
            access_log off;
            proxy_pass http://backend/health;
        }
    }
}
```

## 🗄️ 数据库部署

### PostgreSQL优化配置
```sql
-- postgresql.conf 主要配置项
shared_buffers = 256MB                # 1/4 of total RAM
effective_cache_size = 1GB            # 3/4 of total RAM
work_mem = 4MB
maintenance_work_mem = 64MB
max_connections = 100
wal_buffers = 16MB
checkpoint_completion_target = 0.9
random_page_cost = 1.1
effective_io_concurrency = 200
```

### 数据库备份策略
```bash
#!/bin/bash
# backup.sh - 数据库备份脚本

BACKUP_DIR="/backup"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="delivery_receipt"

# 创建备份
docker-compose exec postgres pg_dump -U delivery_user $DB_NAME > $BACKUP_DIR/backup_$DATE.sql

# 压缩备份
gzip $BACKUP_DIR/backup_$DATE.sql

# 删除7天前的备份
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +7 -delete

# 上传到云存储 (可选)
# aws s3 cp $BACKUP_DIR/backup_$DATE.sql.gz s3://your-backup-bucket/
```

### 定时备份 (crontab)
```bash
# 每天凌晨2点备份数据库
0 2 * * * /path/to/backup.sh

# 每周日凌晨3点全量备份
0 3 * * 0 /path/to/full_backup.sh
```

## 📊 监控和日志

### 日志配置
```python
# backend/app/core/logging.py
import logging
from logging.handlers import RotatingFileHandler
import os

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            RotatingFileHandler(
                '/app/logs/app.log',
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5
            ),
            logging.StreamHandler()
        ]
    )
```

### Prometheus监控 (可选)
```yaml
# docker-compose.monitoring.yml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
    
  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana

volumes:
  grafana_data:
```

## 🚀 传统部署 (非Docker)

### Ubuntu/Debian服务器部署

#### 1. 系统准备
```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装依赖
sudo apt install -y python3.12 python3.12-venv python3-pip nodejs npm nginx postgresql redis-server

# 安装Chrome (截图功能需要)
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/chrome.list
sudo apt update && sudo apt install -y google-chrome-stable
```

#### 2. 后端部署
```bash
# 创建应用用户
sudo useradd -m -s /bin/bash delivery_app
sudo su - delivery_app

# 克隆代码
git clone <repository-url> /home/delivery_app/app
cd /home/delivery_app/app/backend

# 创建虚拟环境
python3.12 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env.prod
# 编辑 .env.prod

# 初始化数据库
python init_db.py
python create_admin.py
```

#### 3. Systemd服务配置
```ini
# /etc/systemd/system/delivery-backend.service
[Unit]
Description=Delivery Receipt Backend API
After=network.target postgresql.service redis.service

[Service]
Type=exec
User=delivery_app
Group=delivery_app
WorkingDirectory=/home/delivery_app/app/backend
Environment=PATH=/home/delivery_app/app/backend/venv/bin
ExecStart=/home/delivery_app/app/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
ExecReload=/bin/kill -HUP $MAINPID
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```ini
# /etc/systemd/system/delivery-celery.service
[Unit]
Description=Delivery Receipt Celery Worker
After=network.target redis.service

[Service]
Type=exec
User=delivery_app
Group=delivery_app
WorkingDirectory=/home/delivery_app/app/backend
Environment=PATH=/home/delivery_app/app/backend/venv/bin
ExecStart=/home/delivery_app/app/backend/venv/bin/celery -A app.tasks.celery_app worker --loglevel=info
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

#### 4. 启动服务
```bash
# 重载systemd配置
sudo systemctl daemon-reload

# 启用并启动服务
sudo systemctl enable delivery-backend delivery-celery
sudo systemctl start delivery-backend delivery-celery

# 检查服务状态
sudo systemctl status delivery-backend delivery-celery
```

#### 5. 前端部署
```bash
# 构建前端
cd /home/delivery_app/app/frontend
npm install
npm run build

# 复制到Nginx目录
sudo cp -r dist/* /var/www/html/
```

## 🔒 安全加固

### 1. 防火墙配置
```bash
# UFW防火墙配置
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 2. SSL证书配置
```bash
# 使用Let's Encrypt
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

### 3. 数据库安全
```bash
# PostgreSQL安全配置
sudo -u postgres psql
ALTER USER postgres PASSWORD 'strong-password';
\\q

# 编辑 pg_hba.conf
sudo nano /etc/postgresql/15/main/pg_hba.conf
# 修改为: local all all md5
```

## 📈 性能优化

### 1. 数据库连接池
```python
# backend/app/core/database.py
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True,
    pool_recycle=3600
)
```

### 2. Redis优化
```bash
# redis.conf
maxmemory 256mb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
```

### 3. Nginx缓存
```nginx
# 添加到nginx.conf
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=my_cache:10m max_size=10g inactive=60m;

location /api/v1/tracking/ {
    proxy_cache my_cache;
    proxy_cache_valid 200 30m;
    proxy_cache_key $uri$is_args$args;
    proxy_pass http://backend;
}
```

## 🔧 故障排除

### 常见问题解决

#### 1. 容器启动失败
```bash
# 查看详细日志
docker-compose logs -f <service_name>

# 检查容器状态
docker ps -a

# 重新构建镜像
docker-compose build --no-cache <service_name>
```

#### 2. 数据库连接问题
```bash
# 检查数据库是否运行
docker-compose exec postgres pg_isready

# 测试连接
docker-compose exec backend python -c "from app.core.database import engine; print(engine.execute('SELECT 1').scalar())"
```

#### 3. Redis连接问题
```bash
# 检查Redis状态
docker-compose exec redis redis-cli ping

# 查看Redis日志
docker-compose logs redis
```

#### 4. 文件权限问题
```bash
# 修复上传目录权限
sudo chown -R 1000:1000 ./backend/uploads
sudo chmod -R 755 ./backend/uploads
```

### 性能监控命令
```bash
# 查看系统资源使用
docker stats

# 查看容器资源限制
docker inspect <container_name> | grep -A 10 "Resources"

# 数据库性能查询
docker-compose exec postgres psql -U delivery_user -d delivery_receipt -c "
SELECT query, calls, total_time, mean_time 
FROM pg_stat_statements 
ORDER BY total_time DESC 
LIMIT 10;"
```

## 📞 技术支持

### 生产环境检查清单
- [ ] 所有服务正常启动
- [ ] SSL证书有效
- [ ] 数据库备份正常
- [ ] 监控告警配置
- [ ] 日志轮转配置
- [ ] 防火墙规则正确
- [ ] 性能监控正常
- [ ] 安全扫描通过

### 联系方式
- 技术文档: [项目README](../README.md)
- API文档: [API参考](./API-Reference.md)
- 问题反馈: GitHub Issues

---

*本部署指南最后更新: 2024-01-01*