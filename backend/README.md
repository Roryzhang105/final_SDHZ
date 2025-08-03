# 送达回证自动化处理系统 Backend

基于FastAPI的送达回证自动化处理系统后端API，提供完整的送达回证生成、物流跟踪、二维码识别等功能。

## 📋 功能特性

### 核心功能
- 🔐 **用户认证与授权** - JWT Token认证，用户管理
- 📦 **送达回证自动生成** - 一键生成包含二维码和物流截图的Word文档
- 🚚 **物流跟踪集成** - 支持多家快递公司的实时物流查询
- 📱 **二维码/条形码处理** - 生成、识别和管理二维码/条形码
- 📸 **自动截图功能** - 物流页面自动截图，支持多种快递网站
- 📄 **文档模板处理** - 自动填充Word文档模板
- 🗄️ **文件管理系统** - 完整的文件上传、存储和管理
- ⚡ **智能任务系统** - 图片上传后自动识别、查询、生成文档的完整流程
- 🔄 **异步处理优化** - 上传即时响应，后台异步处理，实时进度查询

### 技术特性
- ⚡ **异步任务处理** - 基于Celery的后台任务队列
- 🔄 **实时数据同步** - 物流信息自动更新和缓存
- 📊 **任务监控** - 完整的任务状态跟踪
- 🛡️ **安全防护** - SQL注入防护、文件安全检查
- 🎯 **智能识别** - AI驱动的二维码和图像识别

## 🏗️ 技术栈

- **框架**: FastAPI (异步Web框架)
- **数据库**: PostgreSQL (支持SQLite开发环境)
- **缓存**: Redis (任务队列和缓存)
- **任务队列**: Celery (异步任务处理)
- **ORM**: SQLAlchemy (数据库操作)
- **认证**: JWT (JSON Web Token)
- **截图**: Selenium + Chrome (自动化浏览器)
- **文档处理**: python-docx (Word文档生成)
- **图像处理**: Pillow + OpenCV (图像识别和处理)

## 🚀 快速开始

### 环境要求

- Python 3.12+
- Redis 6+ (可选，异步任务需要)
- Chrome浏览器 (截图功能需要)

### 本地开发

1. **克隆项目**
```bash
git clone <repository-url>
cd backend
```

2. **创建虚拟环境并安装依赖**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

3. **设置数据库**

**选项1: 使用 PostgreSQL (推荐生产环境)**
```bash
# 使用 Docker Compose 启动 PostgreSQL (推荐)
docker-compose up -d postgres redis

# 或使用一键迁移脚本
./start_postgres.sh

# 手动初始化
python init_db.py
```

**选项2: 使用 SQLite (开发环境)**
```bash
# 直接初始化 SQLite 数据库
python init_db.py
```

> 📝 如果需要从 SQLite 迁移到 PostgreSQL，参考 [POSTGRESQL_MIGRATION.md](./POSTGRESQL_MIGRATION.md)

4. **启动服务**
```bash
# 开发模式启动
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 或使用启动脚本
./start.sh dev
```

5. **启动Celery Worker**（可选，异步任务）
```bash
./celery_worker.sh worker
```

### Docker部署

```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f app
```

## 📖 API文档

启动服务后访问：

- **Swagger UI**: http://localhost:8000/docs
- **Redoc**: http://localhost:8000/redoc
- **API Health**: http://localhost:8000/health

## 📁 项目结构

```
backend/
├── app/                            # 应用核心代码
│   ├── main.py                     # FastAPI应用入口
│   ├── core/                       # 核心配置
│   │   ├── config.py              # 配置管理
│   │   └── database.py            # 数据库配置
│   ├── models/                     # 数据模型 (350行)
│   │   ├── base.py                # 基础模型
│   │   ├── user.py                # 用户模型
│   │   ├── task.py                # 任务模型 (新增)
│   │   ├── delivery_receipt.py    # 送达回证模型
│   │   ├── tracking.py            # 物流跟踪模型
│   │   ├── recognition.py         # 识别结果模型
│   │   └── courier.py             # 快递公司模型
│   ├── api/                        # API路由层
│   │   └── api_v1/                # v1版本API
│   │       ├── api.py             # 路由汇总
│   │       └── endpoints/         # 具体端点
│   │           ├── auth.py        # 认证相关
│   │           ├── tasks.py       # 智能任务处理 (新增)
│   │           ├── delivery_receipts.py  # 送达回证
│   │           ├── tracking.py    # 物流跟踪
│   │           ├── qr_generation.py      # 二维码生成
│   │           ├── qr_recognition.py     # 二维码识别
│   │           ├── file_management.py    # 文件管理
│   │           ├── upload.py      # 文件上传
│   │           └── users.py       # 用户管理
│   ├── services/                   # 业务逻辑层 (3200行)
│   │   ├── auth.py                # 认证服务
│   │   ├── task.py                # 智能任务服务 (新增，680行)
│   │   ├── delivery_receipt.py    # 送达回证业务逻辑
│   │   ├── delivery_receipt_generator.py  # 回证生成器
│   │   ├── express_tracking.py    # 快递跟踪服务
│   │   ├── tracking_screenshot.py # 截图服务
│   │   ├── qr_generation.py       # 二维码生成服务
│   │   ├── qr_recognition.py      # 二维码识别服务
│   │   ├── file_management.py     # 文件管理服务
│   │   ├── tracking.py            # 物流跟踪服务
│   │   ├── file.py                # 文件处理服务
│   │   └── user.py                # 用户服务
│   ├── tasks/                      # 异步任务 (836行)
│   │   ├── celery_app.py          # Celery配置
│   │   ├── receipt_tasks.py       # 回证处理任务
│   │   ├── tracking_tasks.py      # 物流跟踪任务
│   │   ├── screenshot_tasks.py    # 截图任务
│   │   ├── recognition_tasks.py   # 识别任务
│   │   └── file_tasks.py          # 文件处理任务
│   └── utils/                      # 工具和遗留代码
│       └── legacy/                 # 遗留脚本
│           ├── insert_imgs_delivery_receipt.py  # Word文档处理
│           ├── kuaidi_clone_screenshot.py       # 快递截图脚本
│           ├── make_qr_and_barcode.py          # 二维码生成
│           ├── robust_qr_reader.py             # 二维码识别
│           ├── template.docx       # Word模板
│           └── ...                # 其他工具脚本
├── uploads/                        # 文件上传目录
│   ├── delivery_receipts/         # 生成的送达回证文档
│   ├── tracking_screenshots/      # 物流截图
│   ├── express_cache/             # 快递数据缓存
│   └── tracking_html/             # 物流页面HTML
├── tests/                          # 测试文件
├── requirements.txt                # Python依赖
├── start.sh                       # 启动脚本
├── celery_worker.sh               # Celery启动脚本
├── init_db.py                     # 数据库初始化
├── Dockerfile                     # Docker镜像
├── docker-compose.yml             # Docker编排
└── delivery_receipt.db            # SQLite数据库文件
```

**代码统计**: 总计 **4680行** Python代码（包含新增的智能任务系统）

## 🔌 主要API端点

### 认证模块
- `POST /api/v1/auth/login` - 用户登录
- `POST /api/v1/auth/register` - 用户注册

### 智能任务系统 (新增核心功能)
- `POST /api/v1/tasks/upload` - **图片上传并自动处理** (一键完成整个流程)
- `GET /api/v1/tasks/{task_id}/status` - 获取任务实时状态和进度
- `GET /api/v1/tasks/{task_id}` - 获取任务详细信息
- `GET /api/v1/tasks/` - 获取任务列表
- `PUT /api/v1/tasks/{task_id}` - 更新任务信息
- `POST /api/v1/tasks/{task_id}/retry` - 重试失败的任务
- `DELETE /api/v1/tasks/{task_id}` - 删除任务

### 送达回证模块
- `POST /api/v1/delivery-receipts/generate` - **生成送达回证** (核心功能)
- `GET /api/v1/delivery-receipts/` - 获取回证列表
- `GET /api/v1/delivery-receipts/tracking/{tracking_number}` - 根据快递单号获取回证
- `GET /api/v1/delivery-receipts/{tracking_number}/download` - 下载Word文档
- `PUT /api/v1/delivery-receipts/{id}/status` - 更新回证状态

### 物流跟踪模块
- `GET /api/v1/tracking/{tracking_number}` - 获取物流信息
- `POST /api/v1/tracking/{tracking_number}/update` - 更新物流信息
- `POST /api/v1/tracking/{tracking_number}/screenshot` - 生成跟踪截图

### 二维码模块
- `POST /api/v1/qr-generation/generate` - 生成二维码/条形码
- `POST /api/v1/qr-generation/label` - 生成完整标签
- `POST /api/v1/qr-recognition/recognize` - 识别二维码
- `POST /api/v1/qr-recognition/batch-recognize` - 批量识别

### 文件管理模块
- `POST /api/v1/upload/file` - 上传单个文件
- `POST /api/v1/upload/files` - 批量上传文件
- `GET /api/v1/files/` - 获取文件列表
- `DELETE /api/v1/files/{file_id}` - 删除文件

## ⚙️ 核心功能详解

### 0. 智能任务系统 (⭐ 核心特性)

**一键式自动化处理流程**:
1. **图片上传** - 用户上传快递单照片，立即返回任务ID
2. **自动识别** - 后台异步识别二维码，提取快递单号和快递公司
3. **物流查询** - 自动查询物流信息，判断签收状态
4. **截图生成** - 自动截取物流轨迹页面
5. **二维码生成** - 生成快递单号对应的二维码和条形码
6. **文档生成** - 自动填充Word模板，生成完整的送达回证
7. **实时反馈** - 前端可实时查询处理进度和状态

**异步优化特性**:
- 上传后立即响应（1-2秒），无需等待整个流程完成
- 后台异步处理，支持高并发
- 实时进度查询，用户体验友好
- 失败任务可重试，保证成功率

**使用示例**:
```bash
# 1. 上传图片启动任务 (立即响应)
curl -X POST "http://localhost:8000/api/v1/tasks/upload" \
  -F "file=@photo.jpg"
# 返回: {"success": true, "data": {"task_id": "task_abc123", "status": "PENDING"}}

# 2. 轮询查询处理进度
curl "http://localhost:8000/api/v1/tasks/task_abc123/status"
# 返回: {"progress": 70, "status": "GENERATING", "status_message": "正在生成送达回证..."}

# 3. 获取最终结果
curl "http://localhost:8000/api/v1/tasks/task_abc123"
# 包含完整的任务信息和生成的文件链接
```

### 1. 送达回证自动生成

**核心特性**:
- 自动从物流数据提取寄出时间（揽收时间）
- 智能生成二维码和条形码
- 自动截取物流轨迹页面
- 生成包含所有信息的Word文档

**使用示例**:
```bash
curl -X POST "http://localhost:8000/api/v1/delivery-receipts/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "tracking_number": "1151242358360",
    "doc_title": "送达回证",
    "sender": "送达人姓名",
    "send_location": "送达地点",
    "receiver": "收件人姓名"
  }'
```

### 2. 物流跟踪系统

**支持的快递公司**:
- 中国邮政 (EMS)
- 顺丰速运
- 圆通快递
- 申通快递
- 韵达快递
- 等主流快递公司

**自动化功能**:
- 实时物流状态查询
- 自动页面截图
- 数据缓存优化
- 异步更新机制

### 3. 二维码处理系统

**生成功能**:
- 支持QR码和多种条形码格式
- 可定制尺寸和样式
- 批量生成能力
- 完整标签模板支持

**识别功能**:
- 多种二维码格式识别
- 图像预处理优化
- 批量识别支持
- 识别结果验证

## 🔧 异步任务系统

系统使用Celery处理以下异步任务：

1. **送达回证处理** - 生成二维码、截图、填充文档模板
2. **物流信息更新** - 定期查询和更新物流状态
3. **截图生成** - 自动截取物流跟踪页面
4. **文件处理** - 图片处理、文档生成、文件清理
5. **识别任务** - 二维码识别、图像处理

### Celery管理

```bash
./celery_worker.sh worker   # 启动Worker
./celery_worker.sh beat     # 启动定时任务调度器
./celery_worker.sh flower   # 启动监控界面 (http://localhost:5555)
./celery_worker.sh status   # 查看Worker状态
./celery_worker.sh purge    # 清空任务队列
```

## 🔧 配置说明

### 环境变量配置

```bash
# 基础配置
PROJECT_NAME="送达回证自动化处理系统"
API_V1_STR="/api/v1"

# 数据库配置 (默认SQLite)
DATABASE_URL="sqlite:///./delivery_receipt.db"

# Redis配置 (异步任务)
REDIS_URL="redis://localhost:6379/0"
CELERY_BROKER_URL="redis://localhost:6379/0"
CELERY_RESULT_BACKEND="redis://localhost:6379/0"

# JWT安全配置
SECRET_KEY="your-secret-key-here"
ACCESS_TOKEN_EXPIRE_MINUTES=30

# 文件上传配置
UPLOAD_DIR="./uploads"
MAX_UPLOAD_SIZE=10485760  # 10MB

# 快递API配置
KUAIDI_API_KEY="your_api_key"
KUAIDI_API_SECRET="your_api_secret"

# CORS配置
BACKEND_CORS_ORIGINS=""  # 空值表示允许所有来源(开发模式)
```

### 数据库表结构

- **users** - 用户表
- **delivery_receipts** - 送达回证主表
- **tracking_info** - 物流跟踪信息表
- **recognition_results** - 识别结果表
- **courier_companies** - 快递公司表

## 🚨 故障排除

### 常见问题

1. **数据库初始化失败**
   ```bash
   python init_db.py  # 重新初始化数据库
   ```

2. **Redis连接失败**
   - 确认Redis服务运行状态: `redis-cli ping`
   - 检查Redis连接URL配置

3. **Celery任务不执行**
   - 确认Redis正常工作
   - 检查Worker进程: `./celery_worker.sh status`

4. **截图功能失败**
   - 安装Chrome浏览器
   - 确认ChromeDriver版本匹配
   - 检查系统内存使用情况

5. **Word文档生成失败**
   - 确认template.docx模板文件存在
   - 检查文件权限
   - 验证图片文件路径

### 日志查看

```bash
# 应用主日志
tail -f server.log

# Docker环境日志
docker-compose logs -f app
docker-compose logs -f celery-worker

# Celery任务日志
./celery_worker.sh worker --loglevel=info
```

## 🔒 安全特性

- JWT Token认证
- SQL注入防护
- 文件类型验证
- 上传文件大小限制
- CORS跨域保护
- 敏感信息过滤

## 📈 性能优化

- Redis缓存快递查询结果
- 异步任务处理重计算操作
- 数据库查询优化
- 文件流式上传
- 图片懒加载和压缩

## 🤝 开发指南

### 添加新的快递公司支持

1. 在 `services/express_tracking.py` 中添加新的查询逻辑
2. 在 `services/tracking_screenshot.py` 中添加截图规则
3. 更新 `models/courier.py` 中的快递公司信息

### 添加新的API端点

1. 在 `api/api_v1/endpoints/` 中创建新的端点文件
2. 在 `services/` 中实现业务逻辑
3. 在 `api/api_v1/api.py` 中注册路由

### 添加新的异步任务

1. 在 `tasks/` 目录下创建任务文件
2. 使用 `@celery_app.task` 装饰器
3. 在相应的服务中调用任务

## 📄 许可证

MIT License

## 🙏 贡献

欢迎提交Issue和Pull Request！

## 📞 支持

如有问题，请联系开发团队。