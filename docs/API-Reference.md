# API 接口参考文档

> **送达回证自动化处理系统** - 完整API接口参考

## 📋 概述

本文档详细描述了送达回证自动化处理系统的所有API接口，包括请求参数、响应格式、错误代码等。

### 基础信息
- **API版本**: v1
- **基础URL**: `http://localhost:8000/api/v1`
- **认证方式**: JWT Bearer Token
- **内容类型**: `application/json` / `multipart/form-data`
- **字符编码**: UTF-8

### 通用响应格式
```json
{
  "success": true,
  "message": "操作成功",
  "data": {
    // 具体数据内容
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## 🔐 认证管理 Authentication

### 用户登录
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "ww731226"
}
```

**响应示例**:
```json
{
  "success": true,
  "message": "登录成功",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 1800,
    "user": {
      "id": 1,
      "username": "admin",
      "email": "admin@example.com",
      "created_at": "2024-01-01T12:00:00Z"
    }
  }
}
```

### 用户注册
```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "username": "newuser",
  "email": "user@example.com",
  "password": "securepassword",
  "full_name": "用户全名"
}
```

### 获取当前用户信息
```http
GET /api/v1/users/me
Authorization: Bearer <access_token>
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "id": 1,
    "username": "admin",
    "email": "admin@example.com",
    "full_name": "管理员",
    "is_active": true,
    "created_at": "2024-01-01T12:00:00Z",
    "last_login": "2024-01-01T12:00:00Z"
  }
}
```

## 🎯 智能任务管理 Tasks

### 上传图片并创建任务
```http
POST /api/v1/tasks/upload
Content-Type: multipart/form-data
Authorization: Bearer <access_token>

file: <图片文件>
```

**响应示例**:
```json
{
  "success": true,
  "message": "文件上传成功，任务已创建",
  "data": {
    "task_id": "task_20240101_120000_abc123",
    "status": "PENDING",
    "image_url": "/uploads/task_20240101_120000_abc123.jpg",
    "created_at": "2024-01-01T12:00:00Z"
  }
}
```

### 获取任务状态
```http
GET /api/v1/tasks/{task_id}/status
Authorization: Bearer <access_token>
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "task_id": "task_20240101_120000_abc123",
    "status": "GENERATING",
    "progress": 75,
    "status_message": "正在生成送达回证文档...",
    "current_step": "document_generation",
    "total_steps": 6,
    "estimated_time_remaining": 30
  }
}
```

**任务状态说明**:
- `PENDING`: 等待处理
- `RECOGNIZING`: 二维码识别中
- `TRACKING`: 物流查询中  
- `DELIVERED`: 已签收，等待生成文档
- `GENERATING`: 文档生成中
- `COMPLETED`: 任务完成
- `FAILED`: 任务失败

### 获取任务详情
```http
GET /api/v1/tasks/{task_id}
Authorization: Bearer <access_token>
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "task_id": "task_20240101_120000_abc123",
    "status": "COMPLETED",
    "progress": 100,
    "created_at": "2024-01-01T12:00:00Z",
    "completed_at": "2024-01-01T12:05:00Z",
    "processing_time": 300,
    
    // 上传图片信息
    "image_path": "/uploads/original_image.jpg",
    "image_url": "http://localhost:8000/uploads/original_image.jpg",
    "image_size": 1024768,
    
    // 识别结果
    "qr_code": "https://mini.ems.com.cn/youzheng/mini/1151242358360",
    "tracking_number": "1151242358360",
    "recognition_confidence": 0.95,
    
    // 物流信息
    "tracking_data": {
      "courier": "EMS",
      "status": "已签收",
      "current_location": "北京市海淀区",
      "timeline": [
        {
          "time": "2024-01-01 10:00:00",
          "location": "北京邮政速递物流有限公司",
          "status": "已揽收"
        }
      ]
    },
    
    // 回证信息
    "delivery_receipt": {
      "doc_title": "送达回证",
      "sender": "张三",
      "send_time": "2024-01-01 09:00:00",
      "send_location": "北京市朝阳区",
      "receiver": "李四",
      "receiver_phone": "138****5678"
    },
    
    // 生成的文件
    "files": {
      "delivery_receipt_doc": "http://localhost:8000/uploads/delivery_receipts/receipt_1151242358360.docx",
      "tracking_screenshot": "http://localhost:8000/uploads/tracking_screenshots/tracking_1151242358360.png",
      "qr_code_label": "http://localhost:8000/uploads/labels/label_1151242358360.png",
      "qr_code": "http://localhost:8000/uploads/qr_codes/qr_1151242358360.png",
      "barcode": "http://localhost:8000/uploads/barcodes/barcode_1151242358360.png"
    }
  }
}
```

### 获取任务列表
```http
GET /api/v1/tasks/?page=1&size=10&status=completed&search=1151242358360
Authorization: Bearer <access_token>
```

**查询参数**:
- `page`: 页码 (默认: 1)
- `size`: 每页数量 (默认: 10, 最大: 100)
- `status`: 任务状态筛选
- `search`: 搜索关键词 (任务ID或快递单号)
- `sort`: 排序字段 (默认: created_at)
- `order`: 排序方式 (asc/desc, 默认: desc)

**响应示例**:
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "task_id": "task_20240101_120000_abc123",
        "status": "COMPLETED",
        "progress": 100,
        "tracking_number": "1151242358360",
        "image_url": "http://localhost:8000/uploads/image.jpg",
        "created_at": "2024-01-01T12:00:00Z",
        "completed_at": "2024-01-01T12:05:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "size": 10,
      "total": 50,
      "pages": 5,
      "has_next": true,
      "has_prev": false
    }
  }
}
```

### 重试任务
```http
POST /api/v1/tasks/{task_id}/retry
Authorization: Bearer <access_token>
```

### 删除任务
```http
DELETE /api/v1/tasks/{task_id}
Authorization: Bearer <access_token>
```

### 批量上传文件
```http
POST /api/v1/tasks/batch-upload
Content-Type: multipart/form-data
Authorization: Bearer <access_token>

files[]: <图片文件1>
files[]: <图片文件2>
files[]: <图片文件3>
```

**响应示例**:
```json
{
  "success": true,
  "message": "批量上传完成",
  "data": {
    "successful_uploads": [
      {
        "filename": "image1.jpg",
        "task_id": "task_20240101_120001_def456"
      },
      {
        "filename": "image2.jpg", 
        "task_id": "task_20240101_120002_ghi789"
      }
    ],
    "failed_uploads": [
      {
        "filename": "invalid_file.txt",
        "error": "不支持的文件格式"
      }
    ],
    "summary": {
      "total": 3,
      "successful": 2,
      "failed": 1
    }
  }
}
```

## 📄 送达回证管理 Delivery Receipts

### 生成送达回证
```http
POST /api/v1/delivery-receipts/generate
Content-Type: application/json
Authorization: Bearer <access_token>

{
  "tracking_number": "1151242358360",
  "doc_title": "送达回证",
  "sender": "张三",
  "send_location": "北京市朝阳区人民法院",
  "receiver": "李四",
  "receiver_phone": "138****5678",
  "custom_fields": {
    "case_number": "案件编号123",
    "document_type": "起诉状"
  }
}
```

### 获取回证列表
```http
GET /api/v1/delivery-receipts/?page=1&size=10&status=delivered
Authorization: Bearer <access_token>
```

### 根据快递单号获取回证
```http
GET /api/v1/delivery-receipts/tracking/{tracking_number}
Authorization: Bearer <access_token>
```

### 下载回证文档
```http
GET /api/v1/delivery-receipts/{tracking_number}/download
Authorization: Bearer <access_token>
```

### 更新回证状态
```http
PUT /api/v1/delivery-receipts/{id}/status
Content-Type: application/json
Authorization: Bearer <access_token>

{
  "status": "delivered",
  "notes": "已成功送达"
}
```

## 🚚 物流跟踪管理 Tracking

### 查询物流信息
```http
GET /api/v1/tracking/{tracking_number}
Authorization: Bearer <access_token>
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "tracking_number": "1151242358360",
    "courier": "EMS",
    "status": "已签收",
    "current_location": "北京市海淀区",
    "sender_info": {
      "name": "张三",
      "phone": "138****1234",
      "address": "北京市朝阳区***"
    },
    "receiver_info": {
      "name": "李四", 
      "phone": "138****5678",
      "address": "北京市海淀区***"
    },
    "timeline": [
      {
        "time": "2024-01-01 10:00:00",
        "location": "北京邮政速递物流有限公司",
        "status": "已揽收",
        "operator": "张五"
      },
      {
        "time": "2024-01-01 15:30:00", 
        "location": "北京市海淀区投递部",
        "status": "派件中",
        "operator": "王六"
      },
      {
        "time": "2024-01-01 16:45:00",
        "location": "北京市海淀区***",
        "status": "已签收",
        "operator": "李四",
        "signature": "本人签收"
      }
    ],
    "last_updated": "2024-01-01T16:45:00Z"
  }
}
```

### 强制更新物流信息
```http
POST /api/v1/tracking/{tracking_number}/update
Authorization: Bearer <access_token>
```

### 生成物流截图
```http
POST /api/v1/tracking/{tracking_number}/screenshot
Content-Type: application/json
Authorization: Bearer <access_token>

{
  "width": 1200,
  "height": 800,
  "quality": "high"
}
```

## 📱 二维码处理 QR Code

### 识别二维码
```http
POST /api/v1/qr-recognition/recognize
Content-Type: multipart/form-data
Authorization: Bearer <access_token>

file: <图片文件>
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "qr_contents": [
      "https://mini.ems.com.cn/youzheng/mini/1151242358360"
    ],
    "tracking_numbers": [
      "1151242358360"
    ],
    "confidence": 0.95,
    "image_info": {
      "width": 800,
      "height": 600,
      "format": "JPEG",
      "size": 102400
    },
    "processing_time": 0.25
  }
}
```

### 批量识别二维码
```http
POST /api/v1/qr-recognition/batch-recognize
Content-Type: multipart/form-data
Authorization: Bearer <access_token>

files[]: <图片文件1>
files[]: <图片文件2>
```

### 生成二维码和条形码
```http
POST /api/v1/qr-generation/generate-from-tracking-number
Content-Type: application/x-www-form-urlencoded
Authorization: Bearer <access_token>

tracking_number=1151242358360
size=large
```

**响应示例**:
```json
{
  "success": true,
  "message": "基于快递单号 1151242358360 生成标签成功",
  "data": {
    "url": "https://mini.ems.com.cn/youzheng/mini/1151242358360",
    "tracking_number": "1151242358360",
    "qr_code_path": "/uploads/qr_codes/qr_1151242358360.png",
    "barcode_path": "/uploads/barcodes/barcode_1151242358360.png", 
    "final_label_path": "/uploads/labels/label_1151242358360.png",
    "file_size": 12345,
    "processing_time": 0.123
  }
}
```

### 一站式识别并生成
```http
POST /api/v1/qr-generation/recognize-and-generate
Content-Type: multipart/form-data
Authorization: Bearer <access_token>

file: <图片文件>
```

## 📁 文件管理 Files

### 上传文件
```http
POST /api/v1/upload/file
Content-Type: multipart/form-data
Authorization: Bearer <access_token>

file: <文件>
category: images
```

### 批量上传文件
```http
POST /api/v1/upload/files
Content-Type: multipart/form-data
Authorization: Bearer <access_token>

files[]: <文件1>
files[]: <文件2>
category: documents
```

### 获取文件列表
```http
GET /api/v1/files/?type=image&page=1&size=20
Authorization: Bearer <access_token>
```

### 下载文件
```http
GET /api/v1/files/{file_id}/download
Authorization: Bearer <access_token>
```

### 删除文件
```http
DELETE /api/v1/files/{file_id}
Authorization: Bearer <access_token>
```

## ❌ 错误代码说明

### HTTP状态码
- `200`: 成功
- `201`: 创建成功
- `400`: 请求参数错误
- `401`: 未认证
- `403`: 权限不足
- `404`: 资源不存在
- `422`: 数据验证失败
- `500`: 服务器内部错误

### 业务错误代码
```json
{
  "success": false,
  "error_code": "INVALID_FILE_FORMAT",
  "message": "不支持的文件格式",
  "details": {
    "supported_formats": ["jpg", "jpeg", "png"],
    "received_format": "gif"
  }
}
```

**常见错误代码**:
- `INVALID_FILE_FORMAT`: 不支持的文件格式
- `FILE_TOO_LARGE`: 文件大小超限
- `QR_CODE_NOT_FOUND`: 图片中未找到二维码
- `TRACKING_NUMBER_INVALID`: 无效的快递单号
- `TASK_NOT_FOUND`: 任务不存在
- `INSUFFICIENT_PERMISSIONS`: 权限不足
- `RATE_LIMIT_EXCEEDED`: 请求频率超限

## 🔧 开发工具

### API测试
- **Swagger UI**: http://localhost:8000/docs
- **Redoc**: http://localhost:8000/redoc

### 健康检查
```http
GET /health
```

### API版本信息
```http
GET /api/v1/version
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "version": "2.0.0",
    "build": "20240101-abc123",
    "environment": "development",
    "features": {
      "intelligent_tasks": true,
      "batch_upload": true,
      "real_time_tracking": true
    }
  }
}
```

## 📊 速率限制

为了保护系统稳定性，API实施以下速率限制：

- **认证接口**: 每分钟5次
- **文件上传**: 每分钟10次
- **查询接口**: 每分钟100次
- **其他接口**: 每分钟50次

当超过限制时，将返回HTTP 429状态码。

## 🔐 安全说明

1. **HTTPS**: 生产环境建议使用HTTPS
2. **Token安全**: JWT Token有效期30分钟，请妥善保管
3. **文件安全**: 上传的文件会进行安全检查
4. **权限控制**: 用户只能访问自己创建的资源
5. **日志记录**: 所有API访问都会记录日志

---

*本文档最后更新: 2024-01-01*
*如有疑问，请联系技术支持团队*