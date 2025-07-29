# 送达回证自动化处理系统

基于FastAPI的送达回证自动化处理系统后端API。

## 功能特性

- 🔐 用户认证与授权（JWT）
- 📦 送达回证管理
- 📱 二维码/条形码生成
- 🚚 物流跟踪集成
- 📄 文档模板填充
- 📸 自动截图功能
- ⚡ 异步任务处理（Celery）
- 📊 任务监控（Flower）
- 🗄️ 文件存储管理

## 技术栈

- **框架**: FastAPI
- **数据库**: PostgreSQL
- **缓存**: Redis
- **任务队列**: Celery
- **文件存储**: MinIO
- **认证**: JWT
- **ORM**: SQLAlchemy
- **截图**: Selenium + Chrome

## 快速开始

### 环境要求

- Python 3.11+
- PostgreSQL 12+
- Redis 6+

### 本地开发

1. **克隆项目**
```bash
git clone <repository-url>
cd backend
```

2. **配置环境变量**
```bash
cp .env.example .env
# 编辑 .env 文件，配置数据库和其他服务连接信息
```

3. **启动项目**
```bash
# 一键启动（自动安装依赖、初始化数据库、启动服务）
./start.sh

# 或者分步执行
./start.sh install    # 安装依赖
./start.sh init-db    # 初始化数据库
./start.sh dev        # 启动开发服务器
```

4. **启动Celery Worker**（另一个终端）
```bash
./celery_worker.sh worker
```

### Docker部署

1. **使用Docker Compose**
```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f app
```

2. **初始化数据库**
```bash
docker-compose exec app python init_db.py
```

## API文档

启动服务后访问：

- **API文档**: http://localhost:8000/docs
- **Redoc文档**: http://localhost:8000/redoc
- **Flower监控**: http://localhost:5555

## 项目结构

```
backend/
├── app/
│   ├── main.py                 # FastAPI应用入口
│   ├── core/                   # 核心配置
│   │   ├── config.py          # 配置管理
│   │   └── database.py        # 数据库配置
│   ├── models/                 # 数据模型
│   │   ├── user.py
│   │   ├── delivery_receipt.py
│   │   ├── courier.py
│   │   └── tracking.py
│   ├── api/                    # API路由
│   │   └── api_v1/
│   │       ├── api.py         # 路由汇总
│   │       └── endpoints/     # 具体端点
│   ├── services/               # 业务逻辑层
│   │   ├── auth.py
│   │   ├── delivery_receipt.py
│   │   └── ...
│   └── tasks/                  # 异步任务
│       ├── celery_app.py      # Celery配置
│       ├── receipt_tasks.py   # 回证处理任务
│       ├── tracking_tasks.py  # 物流跟踪任务
│       └── screenshot_tasks.py # 截图任务
├── requirements.txt            # Python依赖
├── start.sh                   # 启动脚本
├── celery_worker.sh           # Celery启动脚本
├── init_db.py                 # 数据库初始化
├── Dockerfile                 # Docker镜像
└── docker-compose.yml         # Docker编排
```

## 主要API端点

### 认证
- `POST /api/v1/auth/login` - 用户登录
- `POST /api/v1/auth/register` - 用户注册

### 送达回证
- `GET /api/v1/delivery-receipts/` - 获取回证列表
- `POST /api/v1/delivery-receipts/` - 创建新回证
- `GET /api/v1/delivery-receipts/{id}` - 获取回证详情
- `PUT /api/v1/delivery-receipts/{id}/status` - 更新回证状态

### 物流跟踪
- `GET /api/v1/tracking/{tracking_number}` - 获取物流信息
- `POST /api/v1/tracking/{tracking_number}/update` - 更新物流信息
- `POST /api/v1/tracking/{tracking_number}/screenshot` - 生成跟踪截图

### 文件上传
- `POST /api/v1/upload/file` - 上传单个文件
- `POST /api/v1/upload/files` - 批量上传文件

## 异步任务

系统使用Celery处理以下异步任务：

1. **送达回证处理** - 生成二维码、条形码、填充文档模板
2. **物流信息更新** - 定期查询物流状态
3. **截图生成** - 自动截取物流跟踪页面
4. **文件处理** - 图片处理、文档生成

## 开发工具

### 启动脚本选项

```bash
./start.sh start      # 完整启动流程
./start.sh check      # 检查依赖环境
./start.sh install    # 安装Python依赖
./start.sh init-db    # 初始化数据库
./start.sh dev        # 启动开发服务器
```

### Celery管理

```bash
./celery_worker.sh worker   # 启动Worker
./celery_worker.sh beat     # 启动Beat调度器
./celery_worker.sh flower   # 启动监控界面
./celery_worker.sh status   # 查看状态
./celery_worker.sh purge    # 清空队列
./celery_worker.sh dev      # 开发模式
```

## 环境变量配置

重要的环境变量说明：

```bash
# 数据库配置
POSTGRES_SERVER=localhost
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_DB=delivery_receipt

# Redis配置
REDIS_URL=redis://localhost:6379/0

# JWT安全
SECRET_KEY=your-secret-key-here

# 文件上传
UPLOAD_DIR=./uploads
MAX_UPLOAD_SIZE=10485760

# 快递API
KUAIDI_API_KEY=your_api_key
KUAIDI_API_SECRET=your_api_secret
```

## 故障排除

### 常见问题

1. **数据库连接失败**
   - 检查PostgreSQL服务是否启动
   - 验证数据库连接参数

2. **Redis连接失败**
   - 确认Redis服务运行状态
   - 检查Redis连接URL

3. **Celery任务不执行**
   - 确认Redis正常工作
   - 检查Worker进程是否启动

4. **截图功能失败**
   - 安装Chrome浏览器
   - 检查ChromeDriver版本

### 日志查看

```bash
# 应用日志
docker-compose logs -f app

# Celery Worker日志
docker-compose logs -f celery-worker

# 数据库日志
docker-compose logs -f postgres
```

## 许可证

[添加许可证信息]

## 贡献

欢迎提交Issue和Pull Request。

## 支持

如有问题，请联系开发团队。