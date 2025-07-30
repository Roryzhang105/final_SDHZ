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
│   ├── delivery.ts        # 送达回证 API
│   ├── files.ts           # 文件管理 API
│   ├── qr.ts             # 二维码 API
│   ├── tracking.ts        # 物流跟踪 API
│   └── index.ts          # API 导出文件
├── assets/                # 静态资源
│   ├── base.css          # 基础样式
│   ├── main.css          # 主样式文件
│   └── styles/           # 样式模块
├── components/            # 公共组件
│   ├── Layout/           # 布局组件
│   │   └── MainLayout.vue # 主布局组件
│   └── icons/            # 图标组件
├── router/               # 路由配置
│   └── index.ts         # 路由定义和守卫
├── stores/              # Pinia 状态管理
│   ├── auth.ts         # 认证状态
│   ├── delivery.ts     # 送达回证状态
│   └── tracking.ts     # 物流跟踪状态
├── types/              # TypeScript 类型定义
│   ├── api.ts         # API 相关类型
│   └── index.ts       # 通用类型
├── utils/             # 工具函数
│   └── request.ts     # HTTP 请求封装
├── views/             # 页面组件
│   ├── auth/          # 认证页面
│   │   ├── LoginView.vue      # 登录页面
│   │   └── RegisterView.vue   # 注册页面
│   ├── delivery/      # 送达回证管理
│   │   ├── GenerateView.vue   # 生成送达回证
│   │   └── ListView.vue       # 送达回证列表
│   ├── tracking/      # 物流跟踪
│   │   └── IndexView.vue      # 物流查询页面
│   ├── qr/           # 二维码管理
│   │   ├── GenerateView.vue   # 二维码生成
│   │   └── RecognizeView.vue  # 二维码识别
│   ├── files/        # 文件管理
│   │   └── IndexView.vue      # 文件管理页面
│   ├── error/        # 错误页面
│   │   ├── 404View.vue        # 404 错误页面
│   │   └── 500View.vue        # 500 错误页面
│   └── DashboardView.vue      # 仪表盘
├── App.vue           # 根组件
└── main.ts          # 应用入口
```

## ✨ 核心功能

### 🔐 用户认证系统
- **用户登录**: 支持用户名/密码登录
- **用户注册**: 新用户账号注册
- **权限管理**: 基于JWT的认证机制
- **路由守卫**: 自动重定向未认证用户

### 📄 送达回证管理
- **回证生成**: 
  - 支持快递单号输入
  - 自动获取物流信息
  - 自定义文书标题和送达信息
  - 生成标准格式的送达回证文档
- **回证列表**: 
  - 分页展示所有生成的回证
  - 支持按单号、状态、日期筛选
  - 回证详情查看和下载
  - 批量删除操作

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

### 🔍 二维码功能
- **二维码生成**:
  - 支持多种内容类型（文本、网址、WiFi、联系人、短信、邮箱）
  - 自定义样式设置（尺寸、颜色、容错级别）
  - 支持PNG和SVG格式导出
  - 生成历史记录管理
- **二维码识别**:
  - 图片上传识别
  - 摄像头实时拍照识别
  - 智能内容解析和操作建议
  - 识别历史记录管理

### 📁 文件管理
- **文件上传**: 
  - 拖拽上传支持
  - 多文件批量上传
  - 文件类型和大小验证
- **文件管理**: 
  - 文件列表展示和筛选
  - 文件预览（图片、文本等）
  - 文件重命名和删除
  - 批量操作支持

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
- **delivery.ts**: 送达回证管理接口
- **tracking.ts**: 物流查询接口
- **qr.ts**: 二维码生成和识别接口
- **files.ts**: 文件管理接口

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

- **v1.0.0**: 初始版本，完整的送达回证管理系统
  - 用户认证系统
  - 送达回证生成和管理
  - 物流跟踪功能
  - 二维码生成和识别
  - 文件管理系统

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