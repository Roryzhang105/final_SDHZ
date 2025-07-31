# 送达回证系统 - 前端

基于 Vue 3 + TypeScript + Element Plus 构建的送达回证自动化处理系统前端应用。

## 📋 项目概述

本项目是一个现代化的 Web 应用程序，专为法律文书送达回证的自动化处理而设计。采用 Vue 3 Composition API、TypeScript 和 Element Plus 组件库，提供直观友好的用户界面。

## 🚀 技术栈

- **核心框架**: Vue 3.5.18 (Composition API)
- **开发语言**: TypeScript 5.8
- **UI 组件库**: Element Plus 2.10.4
- **状态管理**: Pinia 3.0.3
- **路由管理**: Vue Router 4.5.1
- **HTTP 客户端**: Axios 1.11.0
- **构建工具**: Vite 7.0.6
- **代码规范**: ESLint + Prettier

## 🏗️ 项目结构

```
src/
├── api/                    # API 请求模块
│   ├── auth.ts            # 认证相关 API
│   ├── tasks.ts           # 智能任务 API (核心新增)
│   ├── delivery.ts        # 送达回证 API
│   ├── file.ts            # 文件管理 API
│   └── index.ts          # API 导出文件
├── assets/                # 静态资源
│   ├── base.css          # 基础样式
│   ├── main.css          # 主样式文件
│   └── logo.svg          # 应用Logo
├── components/            # 公共组件
│   ├── Layout/           # 布局组件
│   │   └── MainLayout.vue # 主布局组件
│   ├── HelloWorld.vue    # 欢迎组件
│   ├── TheWelcome.vue    # 主欢迎页面
│   ├── WelcomeItem.vue   # 欢迎项组件
│   └── icons/            # 图标组件库
│       ├── IconCommunity.vue      # 社区图标
│       ├── IconDocumentation.vue  # 文档图标
│       ├── IconEcosystem.vue      # 生态图标
│       ├── IconSupport.vue        # 支持图标
│       └── IconTooling.vue        # 工具图标
├── router/               # 路由配置
│   └── index.ts         # 路由定义和守卫
├── stores/              # Pinia 状态管理
│   ├── auth.ts         # 认证状态
│   ├── tasks.ts        # 任务状态管理 (新增)
│   ├── delivery.ts     # 送达回证状态
│   ├── tracking.ts     # 物流跟踪状态
│   └── counter.ts      # 计数器示例
├── types/              # TypeScript 类型定义
│   ├── api.ts         # API 相关类型
│   └── index.ts       # 通用类型
├── utils/             # 工具函数
│   ├── request.ts     # HTTP 请求封装
│   └── tasks.ts       # 任务工具函数 (新增)
├── views/             # 页面组件
│   ├── LoginView.vue         # 登录页面
│   ├── RegisterView.vue      # 注册页面
│   ├── DashboardView.vue     # 仪表盘
│   ├── HomeView.vue          # 首页
│   ├── AboutView.vue         # 关于页面
│   ├── LoadingView.vue       # 加载页面
│   ├── delivery/      # 送达回证管理
│   │   ├── GenerateView.vue   # 智能任务生成页面 (重构)
│   │   ├── ListView.vue       # 任务列表页面 (重构)
│   │   └── TaskDetailView.vue # 任务详情页面 (新增)
│   └── error/        # 错误页面
│       ├── 404View.vue        # 404 错误页面
│       └── 500View.vue        # 500 错误页面
├── App.vue           # 根组件
└── main.ts          # 应用入口
```

## ✨ 核心功能

### 🔐 用户认证系统
- **用户登录**: 支持用户名/密码登录
- **用户注册**: 新用户账号注册
- **权限管理**: 基于JWT的认证机制
- **路由守卫**: 自动重定向未认证用户

### ⚡ 智能任务系统 (⭐ 核心特性)
- **一键上传处理**: 
  - 快递单图片拖拽上传
  - 上传后立即响应，无需等待
  - 支持多种图片格式 (JPG、PNG)
- **实时进度追踪**: 
  - 动态进度条显示处理状态
  - 详细的状态描述 ("正在识别二维码..." → "任务处理完成")
  - 自动轮询更新任务状态
- **任务管理**: 
  - 任务列表展示和筛选
  - 任务详情页面查看
  - 失败任务重试功能
  - 任务删除和清理

### 📄 送达回证管理 (基于智能任务)
- **智能生成**: 
  - 基于上传图片自动识别快递信息
  - 自动查询物流轨迹和签收状态
  - 自动生成二维码和物流截图
  - 一键生成完整的Word送达回证
- **文件管理**: 
  - 生成的文档自动归档
  - 支持在线预览和下载
  - 相关文件（截图、二维码）统一管理

### 📦 物流跟踪系统
- **快递查询**: 
  - 输入快递单号实时查询
  - 展示完整的物流轨迹时间线
  - 支持多家快递公司
- **历史记录**: 
  - 保存查询历史
  - 快速重复查询
- **状态展示**: 
  - 直观的物流状态显示
  - 时间线形式的轨迹展示

### 📊 数据可视化
- **任务统计**: 
  - 任务处理成功率统计
  - 每日任务量趋势图
  - 处理时间分析
- **状态监控**: 
  - 实时任务状态概览
  - 系统健康状态指示
  - 错误统计和分析

### 🎨 用户界面特性
- **响应式设计**: 完全适配桌面和移动设备
- **中文界面**: 完整的中文用户界面
- **主题系统**: 基于Element Plus的一致性设计
- **错误处理**: 友好的错误页面和提示
- **加载状态**: 完善的加载状态指示

## 🛠️ 开发环境设置

### 环境要求
- Node.js >= 20.19.0 或 >= 22.12.0
- npm 或 yarn

### 安装依赖
```bash
npm install
```

### 环境配置
复制并修改环境配置文件：
```bash
cp .env.development.example .env.development
```

环境变量说明：
- `VITE_API_BASE_URL`: 后端API基础URL（默认: http://localhost:8080）
- `VITE_APP_TITLE`: 应用标题
- `VITE_SHOW_DEV_TOOLS`: 是否显示开发工具

### 启动开发服务器
```bash
npm run dev
```
访问 http://localhost:5173

### 构建生产版本
```bash
npm run build
```

### 代码检查和格式化
```bash
# ESLint 检查和修复
npm run lint

# Prettier 格式化
npm run format

# TypeScript 类型检查
npm run type-check
```

## 📚 API 集成

前端通过 Axios 与后端 FastAPI 服务进行通信，API 基础地址可通过环境变量配置。

### API 模块
- **auth.ts**: 用户认证相关接口
- **tasks.ts**: 智能任务处理接口 (核心新增)
- **delivery.ts**: 送达回证管理接口
- **file.ts**: 文件管理接口

### 请求拦截器
- 自动添加认证Token
- 统一错误处理
- 请求/响应日志记录

## 🔒 权限控制

### 路由守卫
- 未认证用户自动重定向到登录页
- 认证失效自动退出登录
- 动态路由权限控制

### 状态管理
- 用户认证状态持久化
- 自动Token刷新机制
- 全局状态统一管理

## 🎯 测试账号

系统默认管理员账号：
- **用户名**: admin
- **密码**: ww731226

## 📱 浏览器支持

- Chrome >= 87
- Firefox >= 78
- Safari >= 14
- Edge >= 88

## 🚧 开发说明

### 组件开发规范
- 使用 Composition API
- TypeScript 类型注解
- 统一的代码风格（ESLint + Prettier）
- 响应式设计原则

### 状态管理
- 使用 Pinia 进行状态管理
- 模块化状态组织
- 持久化存储支持

### 样式规范
- 使用 Element Plus 主题
- CSS 变量统一管理
- 响应式断点设计

## 📈 性能优化

- 路由懒加载
- 组件按需导入
- 图片懒加载
- 接口请求缓存
- 构建产物优化

## 🔄 版本历史

- **v2.0.0**: 智能任务系统重大升级
  - **智能任务系统**: 一键上传自动处理完整流程
  - **异步优化**: 上传立即响应，后台异步处理
  - **实时进度**: 动态进度条和状态更新
  - **任务管理**: 完整的任务生命周期管理
  - **用户体验优化**: 大幅提升响应速度和易用性

- **v1.0.0**: 初始版本，基础送达回证管理系统
  - 用户认证系统
  - 送达回证生成和管理
  - 物流跟踪功能
  - 基础文件管理系统

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/新功能`)
3. 提交更改 (`git commit -m '添加新功能'`)
4. 推送到分支 (`git push origin feature/新功能`)
5. 创建 Pull Request

## 📞 技术支持

如有问题或建议，请通过以下方式联系：
- 项目Issues: 在GitHub上提交Issue
- 邮箱: support@example.com

---

*本项目使用 MIT 许可证，详见 LICENSE 文件。*