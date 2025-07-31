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
├── backend/                 # 后端API服务
│   ├── app/                # 应用核心代码 (4680行)
│   │   ├── api/           # API路由层
│   │   ├── services/      # 业务逻辑层
│   │   ├── models/        # 数据模型
│   │   ├── tasks/         # 异步任务
│   │   └── utils/         # 工具和遗留代码
│   ├── uploads/           # 文件上传目录
│   ├── requirements.txt   # Python依赖
│   └── README.md         # 后端文档
├── frontend/               # 前端Vue应用
│   ├── src/              # 源代码
│   │   ├── api/         # API接口
│   │   ├── components/  # 公共组件
│   │   ├── views/       # 页面组件
│   │   ├── stores/      # 状态管理
│   │   └── utils/       # 工具函数
│   ├── package.json     # 前端依赖
│   └── README.md       # 前端文档
├── docker-compose.yml   # Docker编排文件
└── README.md           # 项目总览 (本文档)
```

## 🔌 核心API接口

### 智能任务处理
```bash
# 上传图片并启动自动处理任务
POST /api/v1/tasks/upload
Content-Type: multipart/form-data

# 查询任务实时状态和进度
GET /api/v1/tasks/{task_id}/status

# 获取任务详细信息和结果文件
GET /api/v1/tasks/{task_id}
```

### 用户认证
```bash
# 用户登录
POST /api/v1/auth/login
Content-Type: application/json
{"username": "admin", "password": "ww731226"}

# 用户注册
POST /api/v1/auth/register
```

## 🛠️ 技术栈详情

### 前端技术栈
- **核心框架**: Vue 3.5.18 (Composition API)
- **开发语言**: TypeScript 5.8
- **UI组件库**: Element Plus 2.10.4
- **状态管理**: Pinia 3.0.3
- **路由管理**: Vue Router 4.5.1
- **HTTP客户端**: Axios 1.11.0
- **构建工具**: Vite 7.0.6

### 后端技术栈
- **Web框架**: FastAPI (异步Web框架)
- **数据库**: SQLite (生产环境可配置PostgreSQL)
- **ORM**: SQLAlchemy 2.0.23
- **认证**: JWT (JSON Web Token)
- **任务队列**: Celery + Redis (异步任务处理)
- **截图工具**: Selenium + Chrome WebDriver
- **文档处理**: python-docx (Word文档生成)
- **图像处理**: Pillow + OpenCV + pyzbar

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

### 文档资源
- [后端API文档](./backend/README.md)
- [前端开发文档](./frontend/README.md)
- [API接口文档](http://localhost:8000/docs) (启动后端后访问)

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