# Claude Code Configuration

## 项目信息
- **项目名称**: SDHZ 快递管理系统
- **技术栈**: Python FastAPI + Vue.js + PostgreSQL + Redis + Celery
- **架构**: 微服务架构，前后端分离

## 构建和部署命令

### Docker 构建
```bash
# 构建所有服务
docker compose build

# 构建特定服务
docker compose build backend
docker compose build frontend

# 启动所有服务
docker compose up -d

# 查看服务状态
docker compose ps

# 查看日志
docker compose logs -f

# 停止所有服务
docker compose down
```

### 开发环境
```bash
# 后端开发
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 前端开发
cd frontend
npm install
npm run dev

# 启动 Celery Worker
cd backend
celery -A app.tasks.celery_app worker --loglevel=info

# 启动 Celery Beat
celery -A app.tasks.celery_app beat --loglevel=info
```

### 测试命令
```bash
# 后端测试
cd backend
python -m pytest tests/

# 前端测试
cd frontend
npm run test

# 类型检查
npm run type-check

# 代码检查
npm run lint
```

### 数据库操作
```bash
# 数据库迁移
cd backend
alembic upgrade head

# 创建新迁移
alembic revision --autogenerate -m "description"

# 创建管理员用户
python create_admin_user.py
```

## CI/CD 配置

### GitHub Actions Workflows
1. **docker-build.yml**: 自动构建和推送 Docker 镜像
2. **claude-code-ci.yml**: Claude Code 集成的 CI/CD 流水线

### 环境变量配置
在 GitHub Secrets 中配置以下环境变量：
- `ANTHROPIC_API_KEY`: Claude Code API 密钥
- `GITHUB_TOKEN`: GitHub 访问令牌（自动提供）

## 项目结构
```
├── backend/              # 后端 FastAPI 应用
│   ├── app/             # 应用核心代码
│   ├── alembic/         # 数据库迁移
│   ├── requirements.txt # Python 依赖
│   └── Dockerfile       # 后端 Docker 配置
├── frontend/            # 前端 Vue.js 应用
│   ├── src/            # 前端源码
│   ├── package.json    # Node.js 依赖
│   └── Dockerfile      # 前端 Docker 配置
├── docker-compose.yml   # Docker Compose 配置
├── Dockerfile          # 多阶段构建配置
└── .github/workflows/  # GitHub Actions 配置
```

## 功能模块
- 用户认证和授权
- 二维码/条形码生成
- 二维码识别
- 快递跟踪
- 配送单生成
- 任务管理（Celery）
- 文件上传和管理
- 活动日志记录

## 注意事项
- 项目使用 PostgreSQL 作为主数据库
- Redis 用于缓存和 Celery 任务队列
- 包含异步任务处理（截图、识别等）
- 支持多种快递公司的跟踪
- 使用 Chrome 浏览器进行页面截图