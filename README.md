# 送达回证自动化处理系统

> 🚀 基于 Vue 3 + FastAPI 的智能送达回证自动化生成系统

[![Frontend](https://img.shields.io/badge/Frontend-Vue%203%20%2B%20TypeScript-brightgreen)](./frontend/)
[![Backend](https://img.shields.io/badge/Backend-FastAPI%20%2B%20Python-blue)](./backend/)
[![License](https://img.shields.io/badge/License-MIT-yellow)](#)

## 📋 项目概述

**送达回证自动化处理系统** 是一个专为法律文书送达回证自动化生成而设计的现代化Web应用。通过智能任务系统，用户只需上传快递单照片，系统即可自动完成二维码识别、物流查询、截图生成、文档制作等全流程处理，大幅提升工作效率。

### ⭐ 核心优势

- **🎯 一键操作**: 上传图片即可自动完成整个送达回证生成流程
- **⚡ 即时响应**: 异步处理优化，上传后立即响应，无需等待
- **🔄 实时追踪**: 动态进度条和状态更新，用户体验友好
- **🧠 智能识别**: AI驱动的二维码识别和快递信息提取
- **📊 数据完整**: 自动获取物流轨迹、生成截图和二维码
- **📄 标准输出**: 生成符合法律要求的标准Word送达回证文档

## 🏗️ 系统架构

```
┌─────────────────┐    HTTP/JSON    ┌──────────────────┐
│   前端应用      │ <──────────────> │   后端API服务    │
│   Vue 3 + TS    │                  │   FastAPI        │
│   Element Plus  │                  │   SQLAlchemy     │
└─────────────────┘                  └──────────────────┘
                                             │
                                             ▼
                                    ┌──────────────────┐
                                    │   数据存储层     │
                                    │   SQLite/Redis   │
                                    └──────────────────┘
                                             │
                                             ▼
                                    ┌──────────────────┐
                                    │   外部服务集成   │
                                    │   快递API        │
                                    │   截图服务       │
                                    │   文档生成       │
                                    └──────────────────┘
```

## ✨ 主要功能

### 🎯 智能任务系统 (核心特性)
- **智能上传处理**: 支持快递单图片拖拽上传，多格式兼容
- **自动识别提取**: AI识别二维码，自动提取快递单号和快递公司
- **物流信息查询**: 集成主流快递公司API，实时获取物流轨迹
- **自动截图生成**: 智能截取物流页面，生成高质量截图
- **二维码标签制作**: 自动生成对应的二维码和条形码标签  
- **Word文档生成**: 基于标准模板自动填充生成送达回证文档
- **实时进度追踪**: 动态显示处理进度和详细状态信息

### 🔐 用户管理系统
- **安全认证**: JWT Token认证机制，支持用户注册和登录
- **权限控制**: 基于角色的访问控制，保护敏感数据
- **会话管理**: 自动Token刷新，无感知的用户体验

### 📊 任务管理功能
- **任务列表**: 分页展示所有处理任务，支持状态筛选
- **任务详情**: 详细显示任务处理过程和生成的文件
- **重试机制**: 失败任务支持一键重试，提高成功率
- **批量操作**: 支持批量删除和状态更新

### 📱 响应式界面
- **现代化设计**: 基于Element Plus的一致性设计语言
- **移动端适配**: 完全响应式设计，支持各种设备
- **中文界面**: 完整的中文用户界面，符合国内用户使用习惯

## 🚀 快速开始

### 环境要求

**后端环境**:
- Python 3.12+
- Redis 6+ (可选，用于异步任务)
- Chrome浏览器 (截图功能需要)

**前端环境**:
- Node.js 20.19.0+ 或 22.12.0+
- npm 或 yarn

### 一键启动

1. **克隆项目**
   ```bash
   git clone <repository-url>
   cd final_SDHZ
   ```

2. **启动后端服务**
   ```bash
   cd backend
   
   # 创建虚拟环境并安装依赖
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # venv\Scripts\activate  # Windows
   pip install -r requirements.txt
   
   # 初始化数据库
   python init_db.py
   
   # 启动API服务
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

3. **启动前端应用**
   ```bash
   cd frontend
   
   # 安装依赖
   npm install
   
   # 启动开发服务器
   npm run dev
   ```

4. **访问应用**
   - 前端应用: http://localhost:5173
   - 后端API文档: http://localhost:8000/docs
   - 默认管理员账号: admin / ww731226

### Docker 部署 (推荐)

```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

## 📁 项目结构

```
final_SDHZ/
├── backend/                     # 后端API服务 (FastAPI + SQLAlchemy)
│   ├── app/                    # 应用核心代码 (约4680行)
│   │   ├── main.py            # FastAPI应用入口
│   │   ├── api/               # API路由层
│   │   │   └── api_v1/       # v1版本API路由
│   │   │       ├── api.py    # 路由汇总注册
│   │   │       └── endpoints/ # 具体端点实现
│   │   │           ├── auth.py            # 用户认证 (JWT)
│   │   │           ├── tasks.py           # 智能任务管理 ⭐
│   │   │           ├── delivery_receipts.py # 送达回证生成
│   │   │           ├── tracking.py        # 物流跟踪
│   │   │           ├── qr_generation.py   # 二维码生成
│   │   │           ├── qr_recognition.py  # 二维码识别
│   │   │           ├── file_management.py # 文件管理
│   │   │           ├── upload.py          # 文件上传
│   │   │           └── users.py           # 用户管理
│   │   ├── core/               # 核心配置模块
│   │   │   ├── config.py      # 应用配置管理
│   │   │   └── database.py    # 数据库连接配置
│   │   ├── models/             # SQLAlchemy数据模型 (约350行)
│   │   │   ├── base.py        # 基础模型类
│   │   │   ├── user.py        # 用户模型
│   │   │   ├── task.py        # 任务模型 ⭐
│   │   │   ├── delivery_receipt.py # 送达回证模型
│   │   │   ├── tracking.py    # 物流跟踪模型
│   │   │   ├── recognition.py # 识别结果模型
│   │   │   └── courier.py     # 快递公司模型
│   │   ├── services/           # 业务逻辑层 (约3200行)
│   │   │   ├── auth.py        # 认证服务
│   │   │   ├── task.py        # 智能任务服务 ⭐ (680行)
│   │   │   ├── delivery_receipt.py        # 送达回证业务逻辑
│   │   │   ├── delivery_receipt_generator.py # 回证生成器
│   │   │   ├── express_tracking.py        # 快递跟踪服务
│   │   │   ├── tracking_screenshot.py     # 截图服务
│   │   │   ├── qr_generation.py          # 二维码生成服务
│   │   │   ├── qr_recognition.py         # 二维码识别服务
│   │   │   ├── file_management.py        # 文件管理服务
│   │   │   ├── tracking.py               # 物流跟踪服务
│   │   │   ├── file.py                   # 文件处理服务
│   │   │   └── user.py                   # 用户服务
│   │   ├── tasks/              # Celery异步任务 (约836行)
│   │   │   ├── celery_app.py  # Celery应用配置
│   │   │   ├── receipt_tasks.py   # 回证处理任务
│   │   │   ├── tracking_tasks.py  # 物流跟踪任务
│   │   │   ├── screenshot_tasks.py # 截图任务
│   │   │   ├── recognition_tasks.py # 识别任务
│   │   │   └── file_tasks.py      # 文件处理任务
│   │   ├── schemas/            # Pydantic请求/响应模型
│   │   │   ├── auth.py        # 认证相关模式
│   │   │   └── __init__.py
│   │   └── utils/              # 工具和遗留代码
│   │       └── legacy/        # 遗留脚本库
│   │           ├── insert_imgs_delivery_receipt.py # Word文档处理
│   │           ├── kuaidi_clone_screenshot.py     # 快递截图脚本
│   │           ├── make_qr_and_barcode.py        # 二维码生成
│   │           ├── robust_qr_reader.py           # 二维码识别
│   │           ├── template.docx                 # Word模板
│   │           └── ...                          # 其他工具脚本
│   ├── uploads/                # 文件存储目录
│   │   ├── delivery_receipts/ # 生成的送达回证文档
│   │   ├── tracking_screenshots/ # 物流截图
│   │   ├── express_cache/     # 快递数据缓存
│   │   └── tracking_html/     # 物流页面HTML
│   ├── alembic/               # 数据库迁移
│   ├── tests/                 # 测试文件
│   ├── requirements.txt       # Python依赖 (26个包)
│   ├── start.sh              # 启动脚本
│   ├── celery_worker.sh      # Celery启动脚本
│   ├── init_db.py            # 数据库初始化
│   ├── Dockerfile            # Docker镜像构建
│   ├── docker-compose.yml    # Docker编排
│   ├── delivery_receipt.db   # SQLite数据库文件
│   └── README.md            # 后端技术文档
├── frontend/                  # 前端Vue应用 (Vue 3 + TypeScript)
│   ├── src/                  # 源代码
│   │   ├── main.ts          # 应用入口
│   │   ├── App.vue          # 根组件
│   │   ├── api/             # API接口层
│   │   │   ├── auth.ts      # 认证相关API
│   │   │   ├── tasks.ts     # 智能任务API ⭐
│   │   │   ├── delivery.ts  # 送达回证API
│   │   │   ├── file.ts      # 文件管理API
│   │   │   └── index.ts     # API导出文件
│   │   ├── components/      # 公共组件
│   │   │   ├── Layout/      # 布局组件
│   │   │   │   └── MainLayout.vue # 主布局
│   │   │   ├── HelloWorld.vue     # 欢迎组件
│   │   │   ├── TheWelcome.vue     # 主欢迎页面
│   │   │   ├── WelcomeItem.vue    # 欢迎项组件
│   │   │   └── icons/       # 图标组件库
│   │   ├── views/           # 页面组件
│   │   │   ├── LoginView.vue      # 登录页面
│   │   │   ├── RegisterView.vue   # 注册页面
│   │   │   ├── DashboardView.vue  # 仪表盘
│   │   │   ├── HomeView.vue       # 首页
│   │   │   ├── AboutView.vue      # 关于页面
│   │   │   ├── LoadingView.vue    # 加载页面
│   │   │   ├── delivery/    # 送达回证管理
│   │   │   │   ├── GenerateView.vue   # 智能任务生成页面 ⭐
│   │   │   │   ├── ListView.vue       # 任务列表页面 ⭐
│   │   │   │   └── TaskDetailView.vue # 任务详情页面 ⭐
│   │   │   └── error/       # 错误页面
│   │   │       ├── 404View.vue        # 404错误页面
│   │   │       └── 500View.vue        # 500错误页面
│   │   ├── stores/          # Pinia状态管理
│   │   │   ├── auth.ts      # 认证状态
│   │   │   ├── tasks.ts     # 任务状态管理 ⭐
│   │   │   ├── delivery.ts  # 送达回证状态
│   │   │   ├── tracking.ts  # 物流跟踪状态
│   │   │   └── counter.ts   # 计数器示例
│   │   ├── router/          # Vue Router路由配置
│   │   │   └── index.ts     # 路由定义和守卫
│   │   ├── types/           # TypeScript类型定义
│   │   │   ├── api.ts       # API相关类型
│   │   │   └── index.ts     # 通用类型
│   │   ├── utils/           # 工具函数
│   │   │   ├── request.ts   # HTTP请求封装
│   │   │   └── tasks.ts     # 任务工具函数 ⭐
│   │   └── assets/          # 静态资源
│   │       ├── base.css     # 基础样式
│   │       ├── main.css     # 主样式文件
│   │       ├── logo.svg     # 应用Logo
│   │       └── styles/      # 样式模块
│   ├── public/              # 静态文件
│   │   └── favicon.ico     # 网站图标
│   ├── package.json         # 前端依赖 (Vue 3.5.18, TypeScript 5.8)
│   ├── vite.config.ts      # Vite构建配置
│   ├── tsconfig.json       # TypeScript配置
│   ├── eslint.config.ts    # ESLint配置
│   ├── Dockerfile          # 前端Docker镜像
│   └── README.md          # 前端开发文档
├── docs/                    # 项目文档目录
├── docker/                  # Docker相关配置
├── docker-compose.yml       # 完整服务编排
├── README-Docker.md         # Docker部署指南
├── test_connection.html     # 连接测试页面
├── 二维码条形码生成/         # 功能演示目录
├── 二维码识别/              # 功能演示目录
├── 更改表格/                # Word模板演示
├── 物流查询&物流轨迹截图/    # 物流功能演示
└── README.md               # 项目总览文档 (本文档)
```

**⭐ 标记的为核心智能任务系统相关文件**

## 🔌 核心API接口

### 🎯 智能任务处理 (核心功能)
```bash
# 上传图片并启动自动处理任务 (一键完成全流程)
POST /api/v1/tasks/upload
Content-Type: multipart/form-data
Body: file=<图片文件>
返回: {"task_id": "xxx", "status": "PENDING"}

# 查询任务实时状态和进度
GET /api/v1/tasks/{task_id}/status
返回: {"progress": 70, "status": "GENERATING", "status_message": "正在生成送达回证..."}

# 获取任务详细信息和结果文件
GET /api/v1/tasks/{task_id}
返回: 完整任务信息包含所有生成的文件链接

# 获取任务列表 (支持筛选和分页)
GET /api/v1/tasks/?status=completed&page=1&size=10

# 重试失败的任务
POST /api/v1/tasks/{task_id}/retry

# 删除任务及相关文件
DELETE /api/v1/tasks/{task_id}
```

### 🔐 用户认证管理
```bash
# 用户登录
POST /api/v1/auth/login
Content-Type: application/json
Body: {"username": "admin", "password": "ww731226"}
返回: {"access_token": "xxx", "token_type": "bearer"}

# 用户注册
POST /api/v1/auth/register
Content-Type: application/json
Body: {"username": "newuser", "email": "user@example.com", "password": "password"}

# 获取当前用户信息
GET /api/v1/users/me
Headers: Authorization: Bearer <token>
```

### 📄 送达回证管理
```bash
# 生成送达回证 (基于快递单号)
POST /api/v1/delivery-receipts/generate
Content-Type: application/json
Body: {
  "tracking_number": "1151242358360",
  "doc_title": "送达回证", 
  "sender": "送达人姓名",
  "send_location": "送达地点",
  "receiver": "收件人姓名"
}

# 获取回证列表
GET /api/v1/delivery-receipts/?page=1&size=10

# 根据快递单号获取回证
GET /api/v1/delivery-receipts/tracking/{tracking_number}

# 下载Word文档
GET /api/v1/delivery-receipts/{tracking_number}/download
返回: Word文档二进制流

# 更新回证状态
PUT /api/v1/delivery-receipts/{id}/status
Content-Type: application/json
Body: {"status": "delivered"}
```

### 🚚 物流跟踪系统
```bash
# 查询物流信息
GET /api/v1/tracking/{tracking_number}
返回: 完整物流轨迹信息

# 强制更新物流信息
POST /api/v1/tracking/{tracking_number}/update

# 生成物流截图
POST /api/v1/tracking/{tracking_number}/screenshot
返回: 截图文件路径
```

### 📱 二维码处理
```bash
# 识别上传图片中的二维码
POST /api/v1/qr-recognition/recognize
Content-Type: multipart/form-data
Body: file=<图片文件>
返回: {"qr_contents": ["快递单号"], "confidence": 0.95}

# 批量识别二维码
POST /api/v1/qr-recognition/batch-recognize
Content-Type: multipart/form-data
Body: files[]=<图片1>&files[]=<图片2>

# 基于快递单号生成二维码和条形码
POST /api/v1/qr-generation/generate-from-tracking-number
Content-Type: application/x-www-form-urlencoded
Body: tracking_number=1151242358360
返回: 二维码、条形码和合成标签的文件路径

# 生成完整标签 (二维码+条形码组合)
POST /api/v1/qr-generation/label
Content-Type: application/json
Body: {"tracking_number": "1151242358360", "size": "large"}

# 一站式识别并生成 (上传图片自动识别然后生成标签)
POST /api/v1/qr-generation/recognize-and-generate
Content-Type: multipart/form-data
Body: file=<图片文件>
```

### 📁 文件管理系统
```bash
# 上传单个文件
POST /api/v1/upload/file
Content-Type: multipart/form-data
Body: file=<文件>

# 批量上传文件
POST /api/v1/upload/files
Content-Type: multipart/form-data
Body: files[]=<文件1>&files[]=<文件2>

# 获取文件列表
GET /api/v1/files/?type=image&page=1&size=10

# 下载文件
GET /api/v1/files/{file_id}/download

# 删除文件
DELETE /api/v1/files/{file_id}
```

## 🛠️ 技术栈详情

### 前端技术栈 (现代化Vue生态)
- **核心框架**: Vue 3.5.18 (Composition API + TypeScript)
- **开发语言**: TypeScript 5.8.0 (类型安全)
- **UI组件库**: Element Plus 2.10.4 (现代化组件)
- **状态管理**: Pinia 3.0.3 (Vue官方推荐)
- **路由管理**: Vue Router 4.5.1 (SPA路由)
- **HTTP客户端**: Axios 1.11.0 (API通信)
- **构建工具**: Vite 7.0.6 (极速构建)
- **代码规范**: ESLint 9.31.0 + Prettier 3.6.2
- **包管理**: npm (Node.js 20.19.0+)

### 后端技术栈 (Python高性能异步)
- **Web框架**: FastAPI 0.104.1 (现代异步Web框架)
- **ASGI服务器**: Uvicorn 0.24.0 (高性能ASGI)
- **数据库**: SQLite (开发) / PostgreSQL (生产推荐)
- **ORM框架**: SQLAlchemy 2.0.23 (异步ORM)
- **数据库迁移**: Alembic 1.12.1
- **认证系统**: JWT + python-jose 3.3.0 (无状态认证)
- **密码加密**: bcrypt + passlib 1.7.4
- **任务队列**: Celery 5.3.4 + Redis 4.6.0 (分布式异步任务)
- **HTTP客户端**: httpx 0.25.2 (异步HTTP请求)
- **数据验证**: Pydantic 2.5.0 (类型验证)
- **配置管理**: Pydantic Settings 2.1.0

### 图像处理和识别技术
- **二维码识别**: pyzbar 0.1.9 (高精度解码)
- **图像处理**: OpenCV 4.10.0.84 + Pillow 10.1.0
- **二维码生成**: qrcode 7.4.2 (PIL支持)
- **条形码生成**: python-barcode 0.15.1
- **数值计算**: NumPy < 2.0 (稳定版本)

### 自动化和截图技术
- **浏览器自动化**: Selenium 4.15.2
- **WebDriver管理**: webdriver-manager 4.0.1 (自动驱动管理)
- **Chrome无头浏览器**: 支持无界面运行

### 文档处理技术
- **Word文档**: python-docx 1.1.0 (Word文档生成和编辑)
- **模板引擎**: 基于Word模板的动态内容填充

### 监控和管理工具
- **任务监控**: Flower 2.0.1 (Celery可视化监控)
- **环境配置**: python-dotenv 1.0.0
- **邮箱验证**: email-validator 2.1.0

### 部署和容器化
- **容器化**: Docker + Docker Compose
- **反向代理**: Nginx (生产环境)
- **进程管理**: Supervisor/systemd (可选)
- **日志管理**: 结构化日志输出

## 📈 性能特性

### 🚀 异步优化
- **即时响应**: 上传后1-2秒内返回任务ID，无需等待处理完成
- **后台处理**: 所有重计算任务在后台异步执行
- **并发处理**: 支持多任务并行处理，提高系统吞吐量

### 🔄 实时更新
- **进度追踪**: 前端自动轮询任务状态，实时更新进度条
- **状态同步**: 任务状态变化立即反映到用户界面
- **错误恢复**: 失败任务支持自动重试和手动重试

### 📊 缓存优化
- **物流缓存**: Redis缓存快递查询结果，避免重复请求
- **文件缓存**: 生成的截图和二维码本地缓存
- **接口缓存**: 前端接口请求结果缓存，提升响应速度

## 🔒 安全特性

- **JWT认证**: 基于Token的无状态认证机制
- **权限控制**: 用户级别的资源访问控制
- **文件安全**: 上传文件类型和大小限制
- **SQL防护**: ORM层自动防护SQL注入攻击
- **CORS保护**: 跨域请求安全配置

## 📊 系统监控

### 📈 任务统计
- 任务处理成功率统计
- 每日任务量趋势分析
- 平均处理时间监控
- 错误类型分布统计

### 🔍 日志系统
- 完整的请求响应日志
- 任务处理过程追踪
- 错误详情记录和分析
- 性能指标监控

## 🎯 使用场景

### 法律行业
- **律师事务所**: 批量处理送达回证生成
- **法院系统**: 标准化送达凭证制作
- **公证机构**: 法律文书送达证明

### 物流行业  
- **快递公司**: 批量生成送达凭证
- **电商平台**: 订单送达证明自动化
- **第三方物流**: 送达回证标准化处理

## 🔄 版本历史

### v2.0.0 (当前版本)
- ✨ **智能任务系统**: 一键上传自动处理完整流程
- ⚡ **异步优化**: 上传立即响应，大幅提升用户体验
- 📊 **实时进度**: 动态进度条和详细状态追踪
- 🔧 **任务管理**: 完整的任务生命周期管理
- 🛠️ **性能优化**: 数据库会话管理和文件URL同步优化

### v1.0.0
- 🔐 基础用户认证系统
- 📄 送达回证生成功能
- 🚚 物流跟踪集成
- 📁 文件管理系统

## 🤝 贡献指南

我们欢迎各种形式的贡献！

### 如何贡献
1. Fork 本项目
2. 创建功能分支 (`git checkout -b feature/新功能`)
3. 提交更改 (`git commit -m '添加新功能'`)
4. 推送到分支 (`git push origin feature/新功能`)
5. 创建 Pull Request

### 开发规范
- 遵循现有代码风格 (ESLint + Prettier)
- 编写单元测试覆盖新功能
- 更新相关文档说明
- 确保所有测试通过

## 📞 技术支持

### 📚 文档资源
- **[项目总览](./README.md)** - 项目概述和快速开始指南
- **[后端技术文档](./backend/README.md)** - FastAPI后端架构和开发指南
- **[前端开发文档](./frontend/README.md)** - Vue.js前端组件和开发规范
- **[API接口参考](./docs/API-Reference.md)** - 完整的API接口文档
- **[部署指南](./docs/Deployment-Guide.md)** - 生产环境部署最佳实践
- **[Docker部署](./README-Docker.md)** - 容器化部署快速指南
- **[API在线文档](http://localhost:8000/docs)** - Swagger UI (启动后端后访问)
- **[API替代文档](http://localhost:8000/redoc)** - ReDoc格式文档

### 问题反馈
- **GitHub Issues**: 提交Bug报告和功能请求
- **邮箱支持**: support@example.com
- **技术交流**: 欢迎提交PR和技术讨论

## 📄 许可证

本项目采用 [MIT许可证](LICENSE)，允许自由使用、修改和分发。

---

<div align="center">

**🌟 如果这个项目对您有帮助，请给我们一个Star！🌟**

Made with ❤️ by 开发团队

</div>